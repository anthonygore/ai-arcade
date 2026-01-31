"""tmux session management for AI Arcade."""

import shlex
import subprocess
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
            self._send_tmux_cmd(["set-option", "-t", self.session_name, "status", "on"])
            self._send_tmux_cmd([
                "set-option", "-t", self.session_name, "status-left",
                "🎮 AI ARCADE | "
            ])
            self._send_tmux_cmd([
                "set-option", "-t", self.session_name, "status-right",
                "#{window_index}:#{window_name} | Ctrl+Space to toggle"
            ])
        else:
            self._send_tmux_cmd(["set-option", "-t", self.session_name, "status", "off"])

        # Bind Ctrl+Space to toggle between windows (last-window command)
        # Using -n flag to bind in root table (no prefix needed)
        toggle_key = self.config.keybindings.toggle_window
        self._send_tmux_cmd([
            "bind-key", "-n", toggle_key, "last-window"
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

        # Change directory if specified
        if working_dir:
            self.send_to_window(
                self.ai_window_index,
                f"cd {shlex.quote(str(working_dir))}"
            )

        # Launch agent
        self.send_to_window(self.ai_window_index, full_command)

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

    def _send_tmux_cmd(self, args: List[str]) -> None:
        """
        Send arbitrary tmux command.

        Args:
            args: Command arguments
        """
        subprocess.run(["tmux"] + args, check=True)
