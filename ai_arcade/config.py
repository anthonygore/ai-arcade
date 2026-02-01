"""Configuration management for AI Arcade."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml


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

    session_name: str = "ai-arcade"
    status_bar: bool = True
    mouse_mode: bool = True


@dataclass
class MonitoringConfig:
    """Configuration for AI monitoring."""

    check_interval: float = 0.5  # Seconds between checks
    inactivity_timeout: float = 2.0  # Seconds of no output = ready
    buffer_lines: int = 50  # Lines of tmux buffer to check


@dataclass
class GamesConfig:
    """Configuration for games."""

    metadata_file: str = "~/.ai-arcade/games_metadata.json"
    save_state_dir: str = "~/.ai-arcade/save_states"


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
    exit_app: str = "C-q"  # Ctrl+q to exit application


class Config:
    """Main configuration class for AI Arcade."""

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
        Load configuration from YAML file.

        Args:
            config_path: Path to config file. Defaults to ~/.ai-arcade/config.yaml

        Returns:
            Config instance
        """
        if config_path is None:
            config_path = Path.home() / ".ai-arcade" / "config.yaml"

        # Create default config if not exists
        if not config_path.exists():
            return cls.create_default(config_path)

        # Load existing config
        try:
            with open(config_path) as f:
                data = yaml.safe_load(f)

            return cls.from_dict(data)
        except Exception as e:
            print(f"Warning: Error loading config from {config_path}: {e}")
            print("Using default configuration.")
            return cls.create_default(config_path)

    @classmethod
    def create_default(cls, config_path: Path) -> "Config":
        """
        Create default configuration file.

        Args:
            config_path: Path where config should be created

        Returns:
            Config instance with defaults
        """
        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Get default config
        default_data = cls.get_default_config()

        # Write to file
        try:
            with open(config_path, 'w') as f:
                yaml.dump(default_data, f, default_flow_style=False, sort_keys=False)
            print(f"Created default config at {config_path}")
        except Exception as e:
            print(f"Warning: Could not write config to {config_path}: {e}")

        return cls.from_dict(default_data)

    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """Return default configuration as dictionary."""
        return {
            "agents": {
                "claude_code": {
                    "id": "claude_code",
                    "name": "Claude Code",
                    "command": "claude",
                    "args": [],
                    "ready_patterns": [
                        "What would you like to do\\?",
                        "^> "
                    ],
                    "working_directory": None
                },
                "codex": {
                    "id": "codex",
                    "name": "Codex",
                    "command": "codex",
                    "args": [],
                    "ready_patterns": [],
                    "working_directory": None,
                    "log_file": "~/.codex/log/codex-tui.log"
                },
                "aider": {
                    "id": "aider",
                    "name": "Aider",
                    "command": "aider",
                    "args": [],
                    "ready_patterns": [
                        "^> ",
                        "Add .+ to the chat\\?"
                    ],
                    "working_directory": None
                },
                "cursor": {
                    "id": "cursor",
                    "name": "Cursor AI",
                    "command": "cursor-cli",
                    "args": [],
                    "ready_patterns": [
                        "^> "
                    ],
                    "working_directory": None
                }
            },
            "tmux": {
                "session_name": "ai-arcade",
                "status_bar": True,
                "mouse_mode": True
            },
            "monitoring": {
                "check_interval": 0.5,
                "inactivity_timeout": 2.0,
                "buffer_lines": 50
            },
            "games": {
                "metadata_file": "~/.ai-arcade/games_metadata.json",
                "save_state_dir": "~/.ai-arcade/save_states"
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
                "exit_app": "C-q"
            }
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
        # Parse agents
        agents = {}
        for agent_id, agent_data in data.get("agents", {}).items():
            agents[agent_id] = AgentConfig(
                id=agent_data.get("id", agent_id),
                name=agent_data.get("name", ""),
                command=agent_data.get("command", ""),
                args=agent_data.get("args", []),
                ready_patterns=agent_data.get("ready_patterns", []),
                working_directory=agent_data.get("working_directory"),
                log_file=agent_data.get("log_file")
            )
        if "codex" not in agents:
            agents["codex"] = AgentConfig(
                id="codex",
                name="Codex",
                command="codex",
                args=[],
                ready_patterns=[],
                working_directory=None,
                log_file="~/.codex/log/codex-tui.log",
            )

        # Parse tmux config
        tmux_data = data.get("tmux", {})
        tmux = TmuxConfig(
            session_name=tmux_data.get("session_name", "ai-arcade"),
            status_bar=tmux_data.get("status_bar", True),
            mouse_mode=tmux_data.get("mouse_mode", True)
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
            metadata_file=games_data.get("metadata_file", "~/.ai-arcade/games_metadata.json"),
            save_state_dir=games_data.get("save_state_dir", "~/.ai-arcade/save_states")
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

        exit_key = kb_data.get("exit_app", "C-q")

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
