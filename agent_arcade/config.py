"""Configuration management for Agent Arcade."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


def get_data_dir() -> str:
    """
    Get the data directory name for Agent Arcade.

    Returns ".agent-arcade-dev" in development mode, ".agent-arcade" otherwise.
    Development mode is detected by:
    - AGENT_ARCADE_DEV environment variable
    - Running from source (not installed in site-packages)
    """
    # Explicit dev mode flag
    if os.environ.get("AGENT_ARCADE_DEV"):
        return ".agent-arcade-dev"

    # Check if running from source (development mode)
    # In dev: __file__ is in the project directory
    # In production: __file__ is in site-packages
    try:
        # Get the directory containing this file
        config_file = Path(__file__).resolve()

        # Check if we're in site-packages (production install)
        if "site-packages" in str(config_file):
            return ".agent-arcade"

        # Not in site-packages = running from source = dev mode
        return ".agent-arcade-dev"
    except Exception:
        # Fallback to production
        return ".agent-arcade"


@dataclass
class AgentConfig:
    """Configuration for an AI agent."""

    id: str
    name: str
    command: str
    args: List[str] = field(default_factory=list)
    ready_patterns: List[str] = field(default_factory=list)
    working_directory: Optional[str] = None
    log_file: Optional[str] = None


@dataclass
class TmuxConfig:
    """Configuration for tmux session."""

    session_name: str = "agent-arcade"
    status_bar: bool = True
    mouse_mode: bool = False


@dataclass
class MonitoringConfig:
    """Configuration for AI monitoring."""

    check_interval: float = 0.5  # Seconds between checks
    inactivity_timeout: float = 2.0  # Seconds of no output = ready
    buffer_lines: int = 50  # Lines of tmux buffer to check


@dataclass
class GamesConfig:
    """Configuration for games."""

    metadata_file: str = field(default_factory=lambda: f"~/{get_data_dir()}/games_metadata.json")


@dataclass
class NotificationsConfig:
    """Configuration for notifications."""

    enabled: bool = True
    visual: bool = True
    message: str = "🤖 AI Ready"
    flash_duration: float = 1.5  # Seconds


@dataclass
class UIConfig:
    """Configuration for UI preferences."""

    theme: str = "default"
    show_last_played: bool = True
    confirm_exit: bool = True
    animation_speed: str = "normal"  # slow, normal, fast


@dataclass
class KeybindingsConfig:
    """Configuration for keybindings."""

    toggle_window: str = "C-Space"  # Ctrl+Space to toggle between AI and Games
    exit_app: str = "C-x"  # Ctrl+x to exit application


class Config:
    """Main configuration class for Agent Arcade."""

    def __init__(
        self,
        agents: Dict[str, AgentConfig],
        tmux: TmuxConfig,
        monitoring: MonitoringConfig,
        games: GamesConfig,
        notifications: NotificationsConfig,
        ui: UIConfig,
        keybindings: KeybindingsConfig,
    ):
        self.agents = agents
        self.tmux = tmux
        self.monitoring = monitoring
        self.games = games
        self.notifications = notifications
        self.ui = ui
        self.keybindings = keybindings

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "Config":
        """
        Load configuration from built-in defaults.

        Args:
            config_path: Unused (kept for compatibility).

        Returns:
            Config instance
        """
        return cls.from_dict(cls.get_default_config())

    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """Return default configuration as dictionary."""
        return {
            "tmux": {
                "session_name": "agent-arcade",
                "status_bar": True,
                "mouse_mode": False
            },
            "monitoring": {
                "check_interval": 0.5,
                "inactivity_timeout": 2.0,
                "buffer_lines": 50
            },
            "games": {
                "metadata_file": f"~/{get_data_dir()}/games_metadata.json",
            },
            "notifications": {
                "enabled": True,
                "visual": True,
                "message": "🤖 AI Ready",
                "flash_duration": 1.5
            },
            "ui": {
                "theme": "default",
                "show_last_played": True,
                "confirm_exit": True,
                "animation_speed": "normal"
            },
            "keybindings": {
                "toggle_window": "C-Space",
                "exit_app": "C-x"
            }
        }

    @staticmethod
    def _default_agents() -> Dict[str, AgentConfig]:
        """Return built-in agent configs."""
        return {
            "claude_code": AgentConfig(
                id="claude_code",
                name="Claude Code",
                command="claude",
                args=[],
                ready_patterns=[
                    "What would you like to do\\?",
                    "^> ",
                ],
                working_directory=None,
                log_file=None,
            ),
            "codex": AgentConfig(
                id="codex",
                name="Codex",
                command="codex",
                args=[],
                ready_patterns=[],
                working_directory=None,
                log_file="~/.codex/log/codex-tui.log",
            ),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """
        Create Config from dictionary.

        Args:
            data: Configuration dictionary

        Returns:
            Config instance
        """
        agents = cls._default_agents()

        # Parse tmux config
        tmux_data = data.get("tmux", {})
        tmux = TmuxConfig(
            session_name=tmux_data.get("session_name", "agent-arcade"),
            status_bar=tmux_data.get("status_bar", True),
            mouse_mode=tmux_data.get("mouse_mode", False)
        )

        # Parse monitoring config
        mon_data = data.get("monitoring", {})
        monitoring = MonitoringConfig(
            check_interval=mon_data.get("check_interval", 0.5),
            inactivity_timeout=mon_data.get("inactivity_timeout", 2.0),
            buffer_lines=mon_data.get("buffer_lines", 50)
        )

        # Parse games config
        games_data = data.get("games", {})
        games = GamesConfig(
            metadata_file=games_data.get("metadata_file", f"~/{get_data_dir()}/games_metadata.json")
        )

        # Parse notifications config
        notif_data = data.get("notifications", {})
        notifications = NotificationsConfig(
            enabled=notif_data.get("enabled", True),
            visual=notif_data.get("visual", True),
            message=notif_data.get("message", "🤖 AI Ready"),
            flash_duration=notif_data.get("flash_duration", 1.5)
        )

        # Parse UI config
        ui_data = data.get("ui", {})
        ui = UIConfig(
            theme=ui_data.get("theme", "default"),
            show_last_played=ui_data.get("show_last_played", True),
            confirm_exit=ui_data.get("confirm_exit", True),
            animation_speed=ui_data.get("animation_speed", "normal")
        )

        # Parse keybindings (handle both old and new format)
        kb_data = data.get("keybindings", {})
        # New format has toggle_window, old format had prefix/next_window/previous_window
        if "toggle_window" in kb_data:
            toggle_key = kb_data.get("toggle_window", "C-Space")
        else:
            # Migrate from old format - just use C-Space
            toggle_key = "C-Space"

        exit_key = kb_data.get("exit_app", "C-x")

        keybindings = KeybindingsConfig(
            toggle_window=toggle_key,
            exit_app=exit_key
        )

        return cls(
            agents=agents,
            tmux=tmux,
            monitoring=monitoring,
            games=games,
            notifications=notifications,
            ui=ui,
            keybindings=keybindings
        )

    def get_agent(self, agent_id: str) -> Optional[AgentConfig]:
        """
        Get agent configuration by ID.

        Args:
            agent_id: Agent identifier (e.g., "claude_code")

        Returns:
            AgentConfig if found, None otherwise
        """
        return self.agents.get(agent_id)

    def resolve_agent(self, selector: str) -> Optional[AgentConfig]:
        """
        Resolve an agent from a selector string.

        Matches config keys, agent IDs, or agent names (case-insensitive).
        """
        if not selector:
            return None

        if selector in self.agents:
            return self.agents[selector]

        selector_lower = selector.lower()
        for agent in self.agents.values():
            if agent.id == selector or agent.id.lower() == selector_lower:
                return agent
            if agent.name and agent.name.lower() == selector_lower:
                return agent

        return None

    def list_available_agents(self) -> List[str]:
        """
        List all configured agent IDs.

        Returns:
            List of agent IDs
        """
        return list(self.agents.keys())
