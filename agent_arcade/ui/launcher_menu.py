"""Launcher menu for Agent Arcade."""

import shutil
from typing import Dict, Optional

from textual import events
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Button, Header, Static


class LauncherMenuApp(App):
    """Initial launcher menu for Agent Arcade."""

    CSS = """
    Screen {
        align: center middle;
        background: $surface;
    }

    #title {
        content-align: center middle;
        text-style: bold;
        height: 7;
        color: $accent;
        margin: 1;
    }

    #menu-container {
        align: center middle;
        width: 50;
        height: auto;
    }

    Button {
        width: 100%;
        margin: 0 2 1 2;
    }

    .agent-button {
        background: $primary;
    }

    #games-button {
        background: $success;
    }

    #exit-button {
        background: $error;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("1", "select_first", "First option"),
        ("2", "select_second", "Second option"),
        ("3", "select_third", "Third option"),
    ]

    def __init__(self, config):
        """
        Initialize launcher menu.

        Args:
            config: Config instance
        """
        super().__init__()
        self.config = config
        self.selected_agent: Optional[str] = None
        self.games_only = False

    def compose(self) -> ComposeResult:
        """Compose UI layout."""
        yield Header()

        with Container(id="menu-container"):
            with Vertical():
                yield Static(self._get_title_art(), id="title")

                # Detect and show available agents
                available_agents = self._detect_available_agents()

                if available_agents:
                    for agent_id, agent_config in available_agents.items():
                        yield Button(
                            f"🤖 {agent_config.name} + Games",
                            id=f"btn-{agent_id}",
                            classes="agent-button"
                        )
                else:
                    yield Static(
                        "\n⚠️  No AI agents detected!\n"
                        "Install Codex, Claude Code, Aider, or configure manually.\n",
                        id="no-agents-warning"
                    )

                yield Button("🎮 Games Only", id="games-button")
                yield Button("❌ Exit", id="exit-button")

    def _get_title_art(self) -> str:
        """
        Return ASCII art title.

        Returns:
            Title art string
        """
        return """
╔═══════════════════════════════════╗
║         🎮 AI ARCADE 🎮          ║
║   Play while your AI thinks      ║
╚═══════════════════════════════════╝
"""

    def _detect_available_agents(self) -> Dict:
        """
        Check which configured agents are installed.

        Returns:
            Dictionary of available agent configs
        """
        available = {}

        for agent_id, agent_config in self.config.agents.items():
            if shutil.which(agent_config.command):
                available[agent_id] = agent_config

        return available

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Handle button clicks.

        Args:
            event: Button press event
        """
        button_id = event.button.id

        if button_id == "games-button":
            self.games_only = True
            self.exit()
        elif button_id == "exit-button":
            self.exit()
        elif button_id and button_id.startswith("btn-"):
            # Agent selected
            agent_id = button_id[4:]  # Remove "btn-" prefix
            self.selected_agent = agent_id
            self.exit()

    def action_select_first(self) -> None:
        """Select first available option."""
        buttons = list(self.query("Button"))
        if buttons:
            self.on_button_pressed(Button.Pressed(buttons[0]))

    def action_select_second(self) -> None:
        """Select second available option."""
        buttons = list(self.query("Button"))
        if len(buttons) > 1:
            self.on_button_pressed(Button.Pressed(buttons[1]))

    def action_select_third(self) -> None:
        """Select third available option."""
        buttons = list(self.query("Button"))
        if len(buttons) > 2:
            self.on_button_pressed(Button.Pressed(buttons[2]))


def show_launcher(config) -> Dict[str, any]:
    """
    Show launcher menu and return user selection.

    Args:
        config: Config instance

    Returns:
        Dictionary with 'agent' and 'games_only' keys
    """
    app = LauncherMenuApp(config)
    app.run()

    return {
        "agent": app.selected_agent,
        "games_only": app.games_only
    }
