"""Game runner for AI Arcade."""

import subprocess
import threading
import time

from textual.app import App, ComposeResult
from textual.widgets import Header

from .config import Config
from .game_library import GameLibrary, SaveStateManager
from .games.base_game import BaseGame, GameState
from .ui.game_selector import GameSelectorScreen


def _set_tmux_game_keys(config: Config, bindings) -> None:
    """Update tmux key bindings bar with current game bindings."""
    key_text = " | ".join(bindings) if bindings else ""
    try:
        subprocess.run(
            [
                "tmux",
                "set-option",
                "-t",
                config.tmux.session_name,
                "@game-keys",
                key_text,
            ],
            check=False,
        )
    except FileNotFoundError:
        # tmux not available; skip updating key bar
        pass


class WindowFocusMonitor:
    """Monitors tmux window focus and pauses/resumes game accordingly."""

    def __init__(self, config: Config, game: BaseGame, game_window_index: int = 1):
        """
        Initialize window focus monitor.

        Args:
            config: Config instance
            game: Game instance to control
            game_window_index: Index of the game window (default 1)
        """
        self.config = config
        self.game = game
        self.game_window_index = game_window_index
        self.session_name = config.tmux.session_name

        self._running = False
        self._thread = None
        self._was_focused = True  # Start as focused

    def start(self) -> None:
        """Start monitoring window focus."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop monitoring."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)

    def _monitor_loop(self) -> None:
        """Monitor loop that runs in background thread."""
        while self._running:
            try:
                is_focused = self._is_game_window_focused()

                # Detect focus changes
                if is_focused and not self._was_focused:
                    # Window gained focus - resume game
                    self.game.resume()
                    self._was_focused = True
                elif not is_focused and self._was_focused:
                    # Window lost focus - pause game
                    self.game.pause()
                    self._was_focused = False

                # Check every 0.5 seconds
                time.sleep(0.5)

            except Exception:
                # Ignore errors and keep monitoring
                time.sleep(0.5)

    def _is_game_window_focused(self) -> bool:
        """
        Check if the game window is currently focused.

        Returns:
            True if game window is focused
        """
        try:
            result = subprocess.run([
                "tmux", "display-message", "-t", self.session_name,
                "-p", "#{window_index}"
            ], capture_output=True, text=True, check=True)

            active_window = int(result.stdout.strip())
            return active_window == self.game_window_index

        except (subprocess.CalledProcessError, ValueError):
            # If we can't determine, assume focused to avoid unwanted pauses
            return True


class GameRunnerApp(App):
    """Main game runner application."""

    def __init__(self, config: Config):
        """
        Initialize game runner.

        Args:
            config: Config instance
        """
        super().__init__()
        self.config = config
        self.library = GameLibrary()
        self.save_manager = SaveStateManager()

    def compose(self) -> ComposeResult:
        """Compose UI layout."""
        yield Header()

    def on_mount(self) -> None:
        """Called when app starts."""
        # Show game selector immediately
        self.show_game_selector()

    def show_game_selector(self) -> None:
        """Show the game selection screen."""
        selector = GameSelectorScreen(self.library, self.save_manager)

        def handle_selection(result):
            """Handle game selection."""
            if result is None:
                # User quit
                self.exit()
            else:
                self.launch_game(result["game_id"], result["resume"])

        self.push_screen(selector, handle_selection)

    def launch_game(self, game_id: str, resume: bool = False) -> None:
        """
        Launch a game.

        Args:
            game_id: Game identifier
            resume: Whether to resume from save
        """
        # Exit the runner app and return the game selection
        self.exit(result={"game_id": game_id, "resume": resume})


def main():
    """Entry point for game runner."""
    while True:
        config = Config.load()
        library = GameLibrary()
        save_manager = SaveStateManager()

        _set_tmux_game_keys(config, ())

        # Show game selector
        app = GameRunnerApp(config)
        result = app.run()

        # If user quit, exit the loop
        if result is None:
            break

        # Otherwise, run the selected game
        game_id = result["game_id"]
        resume = result["resume"]

        # Get game instance
        game = library.get_game(game_id)

        if not game:
            print(f"Error: Could not load game {game_id}")
            continue

        _set_tmux_game_keys(config, game.key_bindings)

        # Load save state if resuming
        if resume and save_manager.has_save(game_id):
            save_state = save_manager.load_game(game_id)
            if save_state:
                try:
                    game.load_save_state(save_state)
                except Exception as e:
                    print(f"Warning: Could not load save: {e}")

        # Track start time
        game_start_time = time.time()

        # Start window focus monitor for auto-pause/resume
        focus_monitor = WindowFocusMonitor(config, game, game_window_index=1)
        focus_monitor.start()

        # Run the game (blocking)
        try:
            game.run()

            # Game finished, update stats
            play_time = int(time.time() - game_start_time)
            score = game.score

            library.update_play_stats(
                game.metadata.id,
                play_time,
                score
            )

            # Save state if paused
            if game.state == GameState.PAUSED:
                save_state = game.get_save_state()
                save_manager.save_game(
                    game.metadata.id,
                    save_state
                )
            elif game.state == GameState.GAME_OVER:
                # Clear save on game over
                save_manager.delete_save(game.metadata.id)

        except Exception as e:
            print(f"Error running game: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Stop focus monitor
            focus_monitor.stop()
            _set_tmux_game_keys(config, ())

        # Loop back to show selector again


if __name__ == "__main__":
    main()
