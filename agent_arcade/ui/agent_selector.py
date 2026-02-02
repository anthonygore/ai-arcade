"""Agent selection UI for Agent Arcade."""

import subprocess

from textual.widgets import DataTable
from rich.text import Text

from ..config import Config
from .base_selector import BaseSelectorScreen


class AgentSelectorScreen(BaseSelectorScreen):
    """Agent selection menu screen."""

    TITLE = "Select agent"

    def __init__(self, config: Config):
        """
        Initialize agent selector.

        Args:
            config: Config instance
        """
        super().__init__()
        self.config = config
        self.selected_agent_id: str = None

    def get_instructions(self) -> str:
        """Return instructions text."""
        return (
            "🤖 AGENT ARCADE\n\n"
            "Select an AI coding agent to start working.\n\n"
            "Tip: When you quit the agent (Ctrl+C), you'll return to this menu."
        )

    def get_table_columns(self) -> tuple:
        """Return table column names."""
        return ("Name", "Command")

    def populate_table(self, table: DataTable) -> None:
        """
        Populate table with agent data.

        Args:
            table: DataTable to populate
        """
        if not self.config.agents:
            table.add_row(
                Text("No agents configured", style="italic red"),
                Text("Check your config", style="italic red"),
                key="none"
            )
            return

        for agent_id, agent_config in self.config.agents.items():
            # Truncate command to max 60 chars
            command = agent_config.command
            if len(command) > 60:
                command = command[:57] + "..."

            table.add_row(
                Text(agent_config.name, style="italic #03AC13"),
                Text(command, style="italic #03AC13"),
                key=agent_id
            )

    def on_item_selected(self, item_id: str) -> None:
        """
        Handle agent selection.

        Args:
            item_id: Selected agent ID
        """
        if item_id == "none":
            return  # No agents configured

        self.selected_agent_id = item_id

        # Set tmux option variable (for wrapper to read)
        try:
            subprocess.run(
                [
                    "tmux",
                    "set-option",
                    "-t",
                    self.config.tmux.session_name,
                    "@selected-agent",
                    item_id,
                ],
                check=False,
            )
        except FileNotFoundError:
            pass  # tmux not available

        # Exit cleanly (code 0) so wrapper knows to launch agent
        self.app.exit(0)
