"""Game runner for AI Arcade."""

import time

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header

from .config import Config
from .game_library import GameLibrary, SaveStateManager
from .games.base_game import GameState
from .ui.game_selector import GameSelectorScreen


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
        yield Footer()

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

        # Loop back to show selector again


if __name__ == "__main__":
    main()
