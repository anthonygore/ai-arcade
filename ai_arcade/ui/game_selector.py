"""Game selection UI for AI Arcade."""

from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import DataTable, Header, Static


class GameSelectorScreen(Screen):
    """Game selection menu screen."""

    BINDINGS = [
        ("q", "quit_to_menu", "Quit"),
        ("enter", "select_game", "Play"),
        ("r", "resume_game", "Resume"),
    ]

    CSS = """
    Screen {
        background: $surface;
    }

    #header-text {
        dock: top;
        height: 5;
        content-align: center middle;
        background: $panel;
        text-style: bold;
    }

    DataTable {
        height: 100%;
        margin: 1;
    }

    """

    def __init__(self, library, save_manager):
        """
        Initialize game selector.

        Args:
            library: GameLibrary instance
            save_manager: SaveStateManager instance
        """
        super().__init__()
        self.library = library
        self.save_manager = save_manager
        self.games = library.list_games(sort_by="last_played")
        self.selected_game_id: str = None
        self.resume: bool = False

    def compose(self) -> ComposeResult:
        """Compose UI layout."""
        yield Header()

        yield Static("🎮 AI ARCADE - SELECT A GAME 🎮", id="header-text")

        with Container():
            # Create game table
            table = DataTable(cursor_type="row")
            table.add_columns(
                "Game",
                "Category",
                "Last Played",
                "Plays",
                "High Score",
                "Resume?"
            )

            for game_meta in self.games:
                game_id = game_meta.id

                # Get stats from library metadata
                stats = self.library.metadata["games"].get(game_id, {})

                last_played = stats.get("last_played", "Never")
                if last_played and last_played != "Never":
                    try:
                        dt = datetime.fromisoformat(last_played.replace('Z', '+00:00'))
                        last_played = dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        last_played = "Never"

                play_count = stats.get("play_count", 0)
                high_score = stats.get("high_score", "-")

                has_save = "✓" if self.save_manager.has_save(game_id) else ""

                table.add_row(
                    game_meta.name,
                    game_meta.category.title(),
                    last_played,
                    str(play_count),
                    str(high_score),
                    has_save,
                    key=game_id
                )

            yield table

    def on_mount(self) -> None:
        """Focus the table when screen mounts."""
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
            self.resume = False
            self.dismiss({"game_id": self.selected_game_id, "resume": self.resume})

    def action_select_game(self) -> None:
        """Play selected game (new game)."""
        table = self.query_one(DataTable)
        if table.cursor_row is not None:
            cursor_key = table.coordinate_to_cell_key(table.cursor_coordinate)
            if cursor_key.row_key:
                self.selected_game_id = cursor_key.row_key.value
                self.resume = False
                self.dismiss({"game_id": self.selected_game_id, "resume": self.resume})

    def action_resume_game(self) -> None:
        """Resume selected game if save exists."""
        table = self.query_one(DataTable)
        if table.cursor_row is not None:
            cursor_key = table.coordinate_to_cell_key(table.cursor_coordinate)
            if cursor_key.row_key:
                game_id = cursor_key.row_key.value

                if self.save_manager.has_save(game_id):
                    self.selected_game_id = game_id
                    self.resume = True
                    self.dismiss({"game_id": self.selected_game_id, "resume": self.resume})
                else:
                    # Show notification that no save exists
                    self.notify("No saved game", severity="warning")

    def action_quit_to_menu(self) -> None:
        """Quit to menu."""
        self.dismiss(None)
