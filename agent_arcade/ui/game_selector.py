"""Game selection UI for Agent Arcade."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.widgets import DataTable, Header, Static


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
        padding-top: 1;
        padding-right: 1;
        background: $surface;
        content-align: left top;
    }

    #game-table {
        height: 100%;
        width: 2fr;
        padding-right: 1;
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
        self.games = library.list_games(sort_by="last_played")
        self.selected_game_id: str = None

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

                for game_meta in self.games:
                    game_id = game_meta.id

                    table.add_row(
                        game_meta.name,
                        game_meta.description,
                        key=game_id
                    )

                with Container(id="games-column"):
                    yield table

                with Container(id="instructions-column"):
                    yield Static(
                        "Tip: games automatically pause when "
                        "you switch back to your Agent"
                    )

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
        self.games = self.library.list_games(sort_by="last_played")
        table = self.query_one(DataTable)
        table.clear()

        for game_meta in self.games:
            table.add_row(
                game_meta.name,
                game_meta.description,
                key=game_meta.id,
            )
