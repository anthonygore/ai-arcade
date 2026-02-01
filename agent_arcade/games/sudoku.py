"""Placeholder game: Sudoku."""

from typing import Tuple

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Header, Static

from .base_game import BaseGame, GameEvent, GameState


class SudokuGame(BaseGame):
    """Placeholder game for Sudoku."""

    ID = "sudoku"
    NAME = "Sudoku"
    DESCRIPTION = "Fill the grid with logic. Every row, column must be 1-9."
    CATEGORY = "puzzle"
    AUTHOR = "Agent Arcade Team"
    CONTROLS_HELP = "Q: Quit"
    MIN_TERMINAL_SIZE = (40, 12)

    def __init__(self):
        """Initialize the placeholder game."""
        super().__init__()
        self.screen = None

    @property
    def key_bindings(self) -> Tuple[str, ...]:
        """Key bindings used by the game."""
        return ("Q: Quit",)

    def run(self) -> None:
        """Run the game standalone."""
        app = SudokuStandaloneApp(self)
        app.run()

    def create_screen(self) -> "SudokuScreen":
        """Create the game screen for use in the hub app."""
        self.screen = SudokuScreen(self)
        return self.screen


class SudokuScreen(Screen):
    """Textual screen for Sudoku."""

    TITLE = "Sudoku"

    CSS = """
    Screen {
        background: $surface;
    }

    Header {
        dock: top;
    }

    #content {
        width: 100%;
        height: 100%;
        align: center middle;
    }

    #card {
        width: 52;
        height: auto;
        background: $panel;
        padding: 1 2;
        border: solid $boost;
    }

    #message {
        content-align: center middle;
    }
    """

    BINDINGS = [
        ("q", "quit_game", "Quit"),
    ]

    def __init__(self, game: SudokuGame):
        """Initialize the screen."""
        super().__init__()
        self.game_ref = game

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        with Container(id="content"):
            with Vertical(id="card"):
                yield Static(
                    "Sudoku\n\n"
                    "Placeholder game.\n\n"
                    "Press Q to quit.",
                    id="message",
                )

    def on_mount(self) -> None:
        """Set initial state and bindings."""
        self.game_ref.update_state(GameState.PLAYING)
        self.game_ref.emit_event(GameEvent.KEY_BINDINGS, ("Q: Quit",))

    def action_quit_game(self) -> None:
        """Quit the game."""
        self.game_ref.update_state(GameState.QUIT)
        self.dismiss()


class SudokuStandaloneApp(App):
    """Standalone app wrapper for Sudoku."""

    CSS = """
    Screen {
        background: $surface;
    }
    """

    def __init__(self, game: SudokuGame):
        """Initialize the standalone app."""
        super().__init__()
        self.game = game

    def compose(self) -> ComposeResult:
        """Compose UI layout."""
        yield from ()

    def on_mount(self) -> None:
        """Mount the game screen."""
        self.push_screen(self.game.create_screen(), self._handle_game_exit)

    def _handle_game_exit(self, _result) -> None:
        """Exit once the game screen dismisses."""
        self.exit()
