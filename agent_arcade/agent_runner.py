"""Agent runner for Agent Arcade."""

from textual.app import App, ComposeResult
from textual.widgets import Header

from .config import Config
from .ui.agent_selector import AgentSelectorScreen


class AgentRunnerApp(App):
    """Agent selector application."""

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
        Initialize agent runner.

        Args:
            config: Config instance
        """
        super().__init__()
        self.config = config
        self.menu_screen = AgentSelectorScreen(config)

    def compose(self) -> ComposeResult:
        """Compose UI layout."""
        yield Header()

    def on_mount(self) -> None:
        """Called when app starts."""
        self.title = self.menu_screen.TITLE
        self.push_screen(self.menu_screen)


def main():
    """Entry point for agent runner."""
    config = Config.load()
    app = AgentRunnerApp(config)
    app.run()


if __name__ == "__main__":
    main()
