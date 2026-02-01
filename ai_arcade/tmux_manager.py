"""tmux session management for AI Arcade."""

import shlex
import subprocess
import time
from pathlib import Path
from typing import List, Optional


class TmuxManager:
    """Manages tmux session for AI Arcade."""

    def __init__(self, config):
        """
        Initialize tmux manager.

        Args:
            config: Config instance

        Raises:
            RuntimeError: If tmux is not installed
        """
        self.config = config
        self.session_name = config.tmux.session_name
        self.ai_window_index = 0
        self.game_window_index = 1

        # Status tracking
        # Agent state: idle (default) or active
        # idle = user typing or agent waiting
        # active = agent thinking or generating
        self.agent_state_idle = True
        self.current_game = None

        # Check tmux availability
        if not self._is_tmux_available():
            raise RuntimeError(
                "tmux is not installed.\n"
                "Install with: brew install tmux (macOS) or apt-get install tmux (Linux)"
            )

    def _is_tmux_available(self) -> bool:
        """
        Check if tmux command exists.

        Returns:
            True if tmux is available
        """
        try:
            subprocess.run(
                ["tmux", "-V"],
                capture_output=True,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def create_session(self, working_dir: Optional[Path] = None) -> None:
        """
        Create new tmux session with separate windows.

        Creates:
        - Window 0: AI agent (full screen)
        - Window 1: Game runner (full screen)

        Args:
            working_dir: Working directory for session
        """
        # Kill existing session if present
        self._kill_session_if_exists()

        # Build create session command for AI window
        cmd = ["tmux", "new-session", "-d", "-s", self.session_name, "-n", "AI Agent"]

        if working_dir:
            cmd.extend(["-c", str(working_dir)])

        # Create new detached session with first window (AI)
        subprocess.run(cmd, check=True)

        # Create second window for games
        subprocess.run([
            "tmux", "new-window", "-t", f"{self.session_name}:{self.game_window_index}",
            "-n", "Games"
        ], check=True)

        # Configure session
        self._configure_session()

    def _configure_session(self) -> None:
        """Set tmux session options."""
        # Enable mouse mode if configured
        if self.config.tmux.mouse_mode:
            self._send_tmux_cmd(["set-option", "-t", self.session_name, "mouse", "on"])

        # Configure status bar
        if self.config.tmux.status_bar:
            self._send_tmux_cmd(["set-option", "-t", self.session_name, "status", "2"])
            self._send_tmux_cmd(["set-option", "-t", self.session_name, "status-position", "bottom"])
            # Set status bar to fill width
            self._send_tmux_cmd(["set-option", "-t", self.session_name, "status-left-length", "100"])
            self._send_tmux_cmd(["set-option", "-t", self.session_name, "status-right-length", "100"])
            # Hide window list immediately to prevent flash
            self._send_tmux_cmd(["set-option", "-t", self.session_name, "window-status-current-format", ""])
            self._send_tmux_cmd(["set-option", "-t", self.session_name, "window-status-format", ""])
            self._send_tmux_cmd(["set-option", "-t", self.session_name, "window-status-separator", ""])
            # Key bindings bar (top line)
            self._send_tmux_cmd(["set-option", "-t", self.session_name, "@game-keys", ""])
            keybar_left = " Ctrl+Space: Toggle | Ctrl+Q: Quit "
            keybar_right = "#{?@game-keys, #{@game-keys} ,}"
            keybar_format = (
                "#[bg=colour238,fg=white,bold,align=left]"
                f"{keybar_left}"
                "#[align=right]"
                f"{keybar_right}"
                "#[default]"
            )
            self._send_tmux_cmd([
                "set-option",
                "-t",
                self.session_name,
                "status-format[0]",
                keybar_format,
            ])
            # Initialize status bar
            self.update_status_bar()
        else:
            self._send_tmux_cmd(["set-option", "-t", self.session_name, "status", "off"])

        # Bind Ctrl+Space to toggle between windows (last-window command)
        # Using -n flag to bind in root table (no prefix needed)
        toggle_key = self.config.keybindings.toggle_window
        self._send_tmux_cmd([
            "bind-key", "-n", toggle_key, "last-window"
        ])

        # Bind Ctrl+q to exit application (kill session)
        # Using -n flag to bind in root table (no prefix needed)
        exit_key = self.config.keybindings.exit_app
        self._send_tmux_cmd([
            "bind-key", "-n", exit_key, "kill-session"
        ])

    def launch_ai_agent(
        self,
        agent_command: str,
        args: Optional[List[str]] = None,
        working_dir: Optional[Path] = None
    ) -> None:
        """
        Launch AI agent in AI window.

        Args:
            agent_command: Command to launch agent
            args: Optional command arguments
            working_dir: Optional working directory
        """
        if args is None:
            args = []

        # Build full command
        full_command = f"{agent_command} {' '.join(args)}"

        # Add cd command if working directory specified
        if working_dir:
            full_command = f"cd {shlex.quote(str(working_dir))} && {full_command}"

        # Launch agent using respawn-pane to avoid showing the command being typed
        subprocess.run([
            "tmux", "respawn-pane", "-t",
            f"{self.session_name}:{self.ai_window_index}",
            "-k", full_command
        ], check=True)

    def launch_game_runner(self) -> None:
        """Launch game runner in game window."""
        # Use Poetry to run the game runner module in the virtual environment
        runner_cmd = "export PATH=\"/Users/anthonygore/.local/bin:$PATH\" && poetry run python -m ai_arcade.game_runner"
        self.send_to_window(self.game_window_index, runner_cmd)

    def send_to_window(
        self,
        window_index: int,
        command: str,
        literal: bool = False
    ) -> None:
        """
        Send command to specific window.

        Args:
            window_index: Window index (0 for AI, 1 for games)
            command: Command string to send
            literal: If True, send keys literally without Enter
        """
        target = f"{self.session_name}:{window_index}"

        if literal:
            subprocess.run([
                "tmux", "send-keys", "-t", target, "-l", command
            ], check=True)
        else:
            subprocess.run([
                "tmux", "send-keys", "-t", target, command, "Enter"
            ], check=True)

    def capture_window_output(self, window_index: int, lines: int = 50) -> str:
        """
        Capture recent output from window.

        Args:
            window_index: Window to capture (0 for AI, 1 for games)
            lines: Number of lines of history to capture

        Returns:
            String containing window content
        """
        target = f"{self.session_name}:{window_index}"

        result = subprocess.run([
            "tmux", "capture-pane", "-t", target,
            "-p",  # Print to stdout
            "-S", f"-{lines}",  # Start from N lines back
            "-e"  # Include escape sequences
        ], capture_output=True, text=True, check=True)

        return result.stdout

    def get_active_window_index(self) -> int:
        """
        Get the currently active window index.

        Returns:
            Window index (0 for AI, 1 for games)
        """
        try:
            result = subprocess.run([
                "tmux", "display-message", "-t", self.session_name,
                "-p", "#{window_index}"
            ], capture_output=True, text=True, check=True)
            return int(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError):
            return -1

    def attach(self) -> None:
        """Attach to tmux session (blocking)."""
        # Focus on AI window first
        subprocess.run([
            "tmux", "select-window", "-t", f"{self.session_name}:{self.ai_window_index}"
        ], check=True)

        # Attach to session
        subprocess.run([
            "tmux", "attach-session", "-t", self.session_name
        ], check=True)

    def kill_session(self) -> None:
        """Terminate tmux session."""
        subprocess.run([
            "tmux", "kill-session", "-t", self.session_name
        ], check=False)  # Don't fail if session doesn't exist

    def _kill_session_if_exists(self) -> None:
        """Kill session if it already exists."""
        result = subprocess.run([
            "tmux", "has-session", "-t", self.session_name
        ], capture_output=True)

        if result.returncode == 0:
            self.kill_session()

    def set_agent_state(self, is_idle: bool) -> None:
        """
        Update agent state.

        Args:
            is_idle: True if idle (user typing or agent waiting)
                    False if active (agent thinking or generating)
        """
        self.agent_state_idle = is_idle
        self.update_status_bar()

    def set_game_status(self, game_name: Optional[str]) -> None:
        """
        Update current game status.

        Args:
            game_name: Name of current game or None
        """
        self.current_game = game_name
        self.update_status_bar()

    def update_status_bar(self) -> None:
        """Update the status bar with current state."""
        if not self.config.tmux.status_bar:
            return

        # Two states: idle or active
        if self.agent_state_idle:
            # idle = user typing or agent waiting
            status_color = "green"
            agent_status = "🤖 Agent idle"
        else:
            # active = agent thinking or generating
            status_color = "yellow"
            agent_status = "🤖 Agent working..."

        # Game status
        if self.current_game:
            game_status = f"Playing {self.current_game}"
        else:
            game_status = "No game selected"

        # Build status bar components
        # Left: Agent status
        status_left = f" {agent_status} "

        # Right: Game status
        status_right = f" {game_status} "

        # Set status bar with colored background
        self._send_tmux_cmd([
            "set-option", "-t", self.session_name, "status-style",
            f"bg={status_color},fg=black,bold"
        ])
        status_format = (
            "#[align=left]"
            f"{status_left}"
            "#[align=right]"
            f"{status_right}"
        )
        self._send_tmux_cmd([
            "set-option",
            "-t",
            self.session_name,
            "status-format[1]",
            status_format,
        ])

        # Hide window list in center
        self._send_tmux_cmd([
            "set-option", "-t", self.session_name, "window-status-current-format",
            ""
        ])
        self._send_tmux_cmd([
            "set-option", "-t", self.session_name, "window-status-format",
            ""
        ])
        self._send_tmux_cmd([
            "set-option", "-t", self.session_name, "window-status-separator",
            ""
        ])

    def _send_tmux_cmd(self, args: List[str]) -> None:
        """
        Send arbitrary tmux command.

        Args:
            args: Command arguments
        """
        subprocess.run(["tmux"] + args, check=True)
