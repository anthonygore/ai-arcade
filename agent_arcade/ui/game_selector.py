"""Game selection UI for Agent Arcade."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.widgets import DataTable, Header, Static
from rich.text import Text


class GameSelectorScreen(Screen):
    """Game selection menu screen."""

    TITLE = "Select a game"

    BINDINGS = [
        ("enter", "select_game", "Play"),
    ]

    CSS = """
    Screen {
        background: $surface;
    }

    Header {
        dock: top;
    }

    #selector-wrapper {
        width: 100%;
        height: 100%;
    }

    #selector-columns {
        width: 100%;
        height: 100%;
        margin: 1;
    }

    #games-column {
        width: 2fr;
        height: 100%;
        padding-right: 1;
    }

    #instructions-column {
        width: 1fr;
        height: 100%;
        padding-top: 0;
        padding-right: 4;
        background: $surface;
        content-align: left top;
    }

    #game-table {
        height: 100%;
        width: 2fr;
    }

    """

    def __init__(self, library):
        """
        Initialize game selector.

        Args:
            library: GameLibrary instance
        """
        super().__init__()
        self.library = library
        self.games = library.list_games(sort_by="name")
        self.selected_game_id: str = None

    def _populate_table(self, table: DataTable) -> None:
        """
        Populate table with game data.

        Args:
            table: DataTable to populate
        """
        for game_meta in self.games:
            # Truncate description to max 60 chars
            description = str(game_meta.description)
            if len(description) > 60:
                description = description[:57] + "..."

            table.add_row(
                Text(str(game_meta.name), style="italic #03AC13"),
                Text(description, style="italic #03AC13"),
                key=game_meta.id
            )

    def compose(self) -> ComposeResult:
        """Compose UI layout."""
        yield Header()
        with Container(id="selector-wrapper"):
            with Horizontal(id="selector-columns"):
                # Create game table
                table = DataTable(cursor_type="row", id="game-table")
                table.add_columns(
                    "Title",
                    "Description",
                )
                self._populate_table(table)

                with Container(id="instructions-column"):
                    yield Static(
                        "🤖 🎮 AGENT ARCADE\n\n"
                        "Play fun arcade games while you wait on your AI agent.\n\n"
                        "Tip: games automatically pause when you switch back to your Agent."
                    )

                with Container(id="games-column"):
                    yield table

    def on_mount(self) -> None:
        """Focus the table when screen mounts."""
        table = self.query_one(DataTable)
        table.focus()

    def on_screen_resume(self) -> None:
        """Restore focus and title when returning to the menu."""
        if hasattr(self.app, "on_return_to_menu"):
            self.app.on_return_to_menu()
        table = self.query_one(DataTable)
        table.focus()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """
        Handle row selection (Enter key on table).

        Args:
            event: Row selection event
        """
        if event.row_key:
            self.selected_game_id = event.row_key.value
            self.app.launch_game(self.selected_game_id)

    def action_select_game(self) -> None:
        """Play selected game (new game)."""
        table = self.query_one(DataTable)
        if table.cursor_row is not None:
            cursor_key = table.coordinate_to_cell_key(table.cursor_coordinate)
            if cursor_key.row_key:
                self.selected_game_id = cursor_key.row_key.value
                self.app.launch_game(self.selected_game_id)

    def refresh_games(self) -> None:
        """Reload the game list and refresh the table."""
        self.games = self.library.list_games(sort_by="name")
        table = self.query_one(DataTable)
        table.clear()
        self._populate_table(table)
