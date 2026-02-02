"""Base selector screen for Agent Arcade menus."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.widgets import DataTable, Header, Static


class BaseSelectorScreen(Screen):
    """Base class for selector screens (games, agents, etc)."""

    BINDINGS = [
        ("enter", "select_item", "Select"),
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

    #items-column {
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

    #item-table {
        height: 100%;
        width: 2fr;
    }
    """

    @property
    def TITLE(self) -> str:
        """Return the screen title. Override in subclass."""
        raise NotImplementedError("Subclass must implement TITLE")

    def get_instructions(self) -> str:
        """
        Return instructions text for the left column.

        Returns:
            Instructions text (can include newlines)
        """
        raise NotImplementedError("Subclass must implement get_instructions()")

    def get_table_columns(self) -> tuple:
        """
        Return column names for the DataTable.

        Returns:
            Tuple of column name strings
        """
        raise NotImplementedError("Subclass must implement get_table_columns()")

    def populate_table(self, table: DataTable) -> None:
        """
        Populate the DataTable with items.

        Args:
            table: DataTable to populate
        """
        raise NotImplementedError("Subclass must implement populate_table()")

    def on_item_selected(self, item_id: str) -> None:
        """
        Handle item selection.

        Args:
            item_id: ID of the selected item (from row key)
        """
        raise NotImplementedError("Subclass must implement on_item_selected()")

    def compose(self) -> ComposeResult:
        """Compose UI layout."""
        yield Header()
        with Container(id="selector-wrapper"):
            with Horizontal(id="selector-columns"):
                # Create item table
                table = DataTable(cursor_type="row", id="item-table")
                columns = self.get_table_columns()
                table.add_columns(*columns)
                self.populate_table(table)

                # Instructions column
                with Container(id="instructions-column"):
                    yield Static(self.get_instructions())

                # Items column
                with Container(id="items-column"):
                    yield table

    def on_mount(self) -> None:
        """Focus the table when screen mounts."""
        table = self.query_one(DataTable)
        table.focus()

    def on_screen_resume(self) -> None:
        """Restore focus when returning to the menu."""
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
            item_id = event.row_key.value
            self.on_item_selected(item_id)

    def action_select_item(self) -> None:
        """Select current item (bound to enter key)."""
        table = self.query_one(DataTable)
        if table.cursor_row is not None:
            cursor_key = table.coordinate_to_cell_key(table.cursor_coordinate)
            if cursor_key.row_key:
                item_id = cursor_key.row_key.value
                self.on_item_selected(item_id)
