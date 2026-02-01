"""Game runner for AI Arcade."""

import subprocess
import threading
import time

from textual.app import App, ComposeResult
from textual.widgets import Header

from .config import Config
from .game_library import GameLibrary
from .games.base_game import BaseGame, GameEvent, GameState
from .logger import logger
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


def _set_tmux_current_game(config: Config, game_name: str | None) -> None:
    """Update tmux status bar with current game name."""
    try:
        subprocess.run(
            [
                "tmux",
                "set-option",
                "-t",
                config.tmux.session_name,
                "@current-game",
                game_name or "",
            ],
            check=False,
        )
    except FileNotFoundError:
        # tmux not available; skip updating status bar
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
        self._game_keys = tuple(game.key_bindings)

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

    def update_game_keys(self, bindings) -> None:
        """Update key bindings shown when the game window is focused."""
        self._game_keys = tuple(bindings) if bindings else ()
        if self._was_focused:
            _set_tmux_game_keys(self.config, self._game_keys)

    def _monitor_loop(self) -> None:
        """Monitor loop that runs in background thread."""
        logger.debug(f"WindowFocusMonitor started, initial state: _was_focused={self._was_focused}")
        while self._running:
            try:
                is_focused = self._is_game_window_focused()

                # Detect focus changes
                if is_focused and not self._was_focused:
                    # Window gained focus - do not auto-resume
                    logger.info("WindowFocusMonitor: Game window gained focus")
                    _set_tmux_game_keys(self.config, self._game_keys)
                    self._was_focused = True
                elif not is_focused and self._was_focused:
                    # Window lost focus - pause game
                    logger.info("WindowFocusMonitor: Game window lost focus -> calling pause()")
                    self.game.pause()
                    _set_tmux_game_keys(self.config, ())
                    self._was_focused = False

                # Check every 0.5 seconds
                time.sleep(0.5)

            except Exception as e:
                # Log errors instead of silently ignoring them
                logger.error(f"WindowFocusMonitor error: {e}")
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

    CSS = """
    Screen {
        background: $surface;
    }

    Header {
        background: $panel;
    }
    """

    def __init__(self, config: Config):
        """
        Initialize game runner.

        Args:
            config: Config instance
        """
        super().__init__()
        self.config = config
        self.library = GameLibrary()
        self.menu_screen = GameSelectorScreen(self.library)
        self.current_game: BaseGame | None = None
        self.current_game_start_time: float | None = None
        self.focus_monitor: WindowFocusMonitor | None = None
        self._current_game_keys: tuple[str, ...] = ()

    def compose(self) -> ComposeResult:
        """Compose UI layout."""
        yield Header()

    def on_mount(self) -> None:
        """Called when app starts."""
        _set_tmux_game_keys(self.config, ())
        _set_tmux_current_game(self.config, None)
        self.title = self.menu_screen.TITLE
        self.push_screen(self.menu_screen)

    def on_return_to_menu(self) -> None:
        """Reset tmux status when returning to the menu."""
        _set_tmux_game_keys(self.config, ())
        _set_tmux_current_game(self.config, None)
        self.title = self.menu_screen.TITLE

    def _handle_game_event(self, event: GameEvent, payload) -> None:
        """Handle game events and update tmux state."""
        if event == GameEvent.KEY_BINDINGS:
            bindings = tuple(payload) if payload else ()
            self._current_game_keys = bindings
            if self.focus_monitor:
                self.focus_monitor.update_game_keys(bindings)
            _set_tmux_game_keys(self.config, bindings)
        elif event == GameEvent.STATE and payload == GameState.QUIT:
            _set_tmux_current_game(self.config, None)
            self._cleanup_after_game()

    def launch_game(self, game_id: str) -> None:
        """
        Launch a game.

        Args:
            game_id: Game identifier
        """
        if self.current_game is not None:
            if self.current_game.state == GameState.QUIT:
                self._cleanup_after_game()
            else:
                return

        game = self.library.get_game(game_id)
        if not game:
            self.notify(f"Error: Could not load game {game_id}", severity="error")
            return

        stats = self.library.get_game_stats(game_id) or {}
        game.high_score = stats.get("high_score", 0)

        if hasattr(game, "set_config"):
            game.set_config(self.config)
        game.set_event_callback(self._handle_game_event)

        self.current_game = game
        self.current_game_start_time = time.time()

        self._current_game_keys = tuple(game.key_bindings)
        _set_tmux_game_keys(self.config, self._current_game_keys)
        _set_tmux_current_game(self.config, game.metadata.name)
        self.title = game.metadata.name

        self.focus_monitor = WindowFocusMonitor(self.config, game, game_window_index=1)
        self.focus_monitor.start()

        screen = game.create_screen()
        self.push_screen(screen, self._handle_game_exit)

    def _cleanup_after_game(self) -> None:
        """Handle game cleanup after a game screen is dismissed."""
        if not self.current_game:
            return

        if self.focus_monitor:
            self.focus_monitor.stop()
            self.focus_monitor = None

        _set_tmux_game_keys(self.config, ())
        _set_tmux_current_game(self.config, None)

        play_time = 0
        if self.current_game_start_time is not None:
            play_time = int(time.time() - self.current_game_start_time)

        game = self.current_game

        self.library.update_play_stats(
            game.metadata.id,
            play_time,
            game.score,
        )

        self.menu_screen.refresh_games()
        self.current_game = None
        self.current_game_start_time = None

    def _handle_game_exit(self, _result) -> None:
        """Handle game cleanup when a game screen is dismissed."""
        self._cleanup_after_game()


def main():
    """Entry point for game runner."""
    config = Config.load()
    app = GameRunnerApp(config)
    try:
        app.run()
    finally:
        _set_tmux_game_keys(config, ())
        _set_tmux_current_game(config, None)


if __name__ == "__main__":
    main()
