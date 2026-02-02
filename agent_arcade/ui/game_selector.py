"""Game selection UI for Agent Arcade."""

from textual.widgets import DataTable
from rich.text import Text

from .base_selector import BaseSelectorScreen


class GameSelectorScreen(BaseSelectorScreen):
    """Game selection menu screen."""

    TITLE = "Select a game"

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

    def get_instructions(self) -> str:
        """Return instructions text."""
        return (
            "🤖 🎮 AGENT ARCADE\n\n"
            "Play fun arcade games while you wait on your AI agent.\n\n"
            "Tip: games automatically pause when you switch back to your Agent."
        )

    def get_table_columns(self) -> tuple:
        """Return table column names."""
        return ("Title", "Description")

    def populate_table(self, table: DataTable) -> None:
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

    def on_item_selected(self, item_id: str) -> None:
        """
        Handle game selection.

        Args:
            item_id: Selected game ID
        """
        self.selected_game_id = item_id
        self.app.launch_game(item_id)

    def refresh_games(self) -> None:
        """Reload the game list and refresh the table."""
        self.games = self.library.list_games(sort_by="name")
        table = self.query_one(DataTable)
        table.clear()
        self.populate_table(table)
