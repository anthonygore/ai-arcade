"""tmux session management for Agent Arcade."""

import platform
import shlex
import subprocess
import time
from pathlib import Path
from typing import List, Optional


class TmuxManager:
    """Manages tmux session for Agent Arcade."""

    def __init__(self, config, crash_file: Optional[Path] = None):
        """
        Initialize tmux manager.

        Args:
            config: Config instance
            crash_file: Optional path to write crash-loop messages

        Raises:
            RuntimeError: If tmux is not installed
        """
        self.config = config
        self.session_name = config.tmux.session_name
        self.ai_window_index = 0
        self.game_window_index = 1
        self.crash_file = crash_file

        # Status tracking
        # Agent state: idle (default) or active
        # idle = user typing or agent waiting
        # active = agent thinking or generating
        self.agent_state_idle = True
        self.agent_selected = False  # True once user selects an agent from menu
        self.current_game = None

        # Check tmux availability
        if not self._is_tmux_available():
            install_hint = "Install tmux with your system package manager."
            system = platform.system().lower()
            if system == "darwin":
                install_hint = "Install tmux with: brew install tmux"
            elif system == "linux":
                install_hint = "Install tmux with: sudo apt-get install tmux (Debian/Ubuntu) or sudo yum install tmux (RHEL/CentOS)"
            raise RuntimeError(
                "tmux is required but not installed.\n"
                f"{install_hint}\n"
                "After installing tmux, re-run agent-arcade."
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
        else:
            self._send_tmux_cmd(["set-option", "-t", self.session_name, "mouse", "off"])

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
            keybar_left = "#{?@game-keys, #{@game-keys} ,}"
            keybar_right = " Ctrl+Space: Switch View | Ctrl+X: Exit "
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
            # Initialize status bar with dynamic content
            # Status bar will read @selected-agent variable directly
            self._send_tmux_cmd(["set-option", "-t", self.session_name, "@selected-agent", ""])
            self._send_tmux_cmd(["set-option", "-t", self.session_name, "@current-game", ""])
            self._setup_dynamic_status_bar()
        else:
            self._send_tmux_cmd(["set-option", "-t", self.session_name, "status", "off"])

        # Bind Ctrl+Space to toggle between windows (last-window command)
        # Using -n flag to bind in root table (no prefix needed)
        toggle_key = self.config.keybindings.toggle_window

        # Simple approach: just toggle windows, mouse mode handled separately
        self._send_tmux_cmd([
            "bind-key", "-n", toggle_key, "last-window"
        ])

        # If mouse mode is enabled, keep it on globally
        # Users can hold Shift to select text in tmux even with mouse mode on
        if self.config.tmux.mouse_mode:
            self._send_tmux_cmd([
                "set-option", "-t", self.session_name, "mouse", "on"
            ])

        # Bind Ctrl+x to exit application (kill session)
        # Using -n flag to bind in root table (no prefix needed)
        exit_key = self.config.keybindings.exit_app
        self._send_tmux_cmd([
            "bind-key", "-n", exit_key, "kill-session"
        ])

    def launch_ai_agent(
        self,
        agent_command: str,
        args: Optional[List[str]] = None,
        working_dir: Optional[Path] = None,
        crash_label: Optional[str] = None,
        crash_subject: Optional[str] = None
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
        full_command = f"{agent_command} {' '.join(args)}".strip()

        # Add cd command if working directory specified
        if working_dir:
            full_command = f"cd {shlex.quote(str(working_dir))} && {full_command}"

        # Wrap in restart loop so Ctrl+C or exits restart the process
        wrapped = self._wrap_restart_command(
            full_command,
            crash_label=crash_label or agent_command,
            crash_subject=crash_subject or (crash_label or agent_command)
        )
        self._respawn_pane(self.ai_window_index, wrapped)

    def launch_game_runner(self) -> None:
        """Launch game runner in game window."""
        # Use Poetry to run the game runner module in the virtual environment
        runner_cmd = "export PATH=\"/Users/anthonygore/.local/bin:$PATH\" && poetry run python -m agent_arcade.game_runner"
        wrapped = self._wrap_restart_command(
            runner_cmd,
            crash_label="Game runner",
            crash_subject="the game runner"
        )
        self._respawn_pane(self.game_window_index, wrapped)

    def launch_agent_runner(self) -> None:
        """Launch agent runner in AI window."""
        # Use Poetry to run the agent runner module in the virtual environment
        runner_cmd = "export PATH=\"/Users/anthonygore/.local/bin:$PATH\" && poetry run python -m agent_arcade.agent_runner"
        wrapped = self._wrap_agent_launcher(runner_cmd)
        self._respawn_pane(self.ai_window_index, wrapped)

    def _wrap_agent_launcher(self, menu_cmd: str) -> str:
        """
        Wrap agent selector menu in a loop that launches selected agents.

        When menu exits:
        - Exit code 130 (Ctrl+C): exit entire app
        - Exit code 0: read selected agent and launch it
        - No selection: exit entire app

        When agent exits: return to menu (no crash detection)

        Args:
            menu_cmd: Command to launch agent selector menu

        Returns:
            Wrapped bash command string
        """
        loop = (
            "trap \"\" INT; "  # Ignore Ctrl+C in wrapper
            "while true; do "
            # Clear previous selection
            f"tmux set-option -t {shlex.quote(self.session_name)} -u @selected-agent 2>/dev/null || true; "
            # Launch agent selector menu
            "clear; "
            f"{menu_cmd}; "
            "exit_code=$?; "
            # Read selected agent from tmux options
            f"selected=$(tmux show-options -t {shlex.quote(self.session_name)} -v @selected-agent 2>/dev/null || echo ''); "
            # If agent was selected, launch it
            "if [ -n \"$selected\" ]; then "
            "clear; "
            "export PATH=\"/Users/anthonygore/.local/bin:$PATH\"; "
            "poetry run python -m agent_arcade.agent_launcher \"$selected\"; "
            # Agent exited - clear selection and update status bar
            f"tmux set-option -t {shlex.quote(self.session_name)} -u @selected-agent 2>/dev/null || true; "
            "export PATH=\"/Users/anthonygore/.local/bin:$PATH\"; "
            "poetry run python -m agent_arcade.update_status 2>/dev/null || true; "
            "fi; "
            # Loop back to menu (whether agent was selected or not)
            "done"
        )
        return f"bash -c {shlex.quote(loop)}"

    def is_pane_dead(self, window_index: int) -> bool:
        """
        Check if a tmux pane is dead.

        Args:
            window_index: Window index to check

        Returns:
            True if pane is dead
        """
        try:
            result = subprocess.run(
                [
                    "tmux",
                    "list-panes",
                    "-t",
                    f"{self.session_name}:{window_index}",
                    "-F",
                    "#{pane_dead}",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip() == "1"
        except subprocess.CalledProcessError:
            return False

    def _respawn_pane(self, window_index: int, command: str) -> None:
        """
        Respawn a pane with a command.

        Args:
            window_index: Window index to respawn
            command: Command string to run
        """
        subprocess.run(
            [
                "tmux",
                "respawn-pane",
                "-t",
                f"{self.session_name}:{window_index}",
                "-k",
                command,
            ],
            check=True,
        )

    def _wrap_restart_command(
        self,
        command: str,
        crash_label: str,
        crash_subject: str
    ) -> str:
        """
        Wrap a command in a restart loop that ignores Ctrl+C in the wrapper.
        If the command crashes rapidly multiple times, exit the app.

        Args:
            command: Command string to run
            crash_label: Label for crash message
            upgrade_hint: Optional upgrade hint for message
        """
        message = (
            f"Exiting app because {crash_label} crashed. "
            f"This might happen if {crash_subject} is not installed or needs to be upgraded."
        )
        crash_env = ""
        if self.crash_file:
            crash_env = f"export AGENT_ARCADE_CRASH_FILE={shlex.quote(str(self.crash_file))}; "
        loop = (
            f"{crash_env}"
            "trap \"\" INT; "
            "fast_count=0; "
            "while true; do "
            "clear; "
            "start=$(date +%s); "
            f"{command}; "
            "end=$(date +%s); "
            "runtime=$((end-start)); "
            "if [ $runtime -lt 5 ]; then fast_count=$((fast_count+1)); else fast_count=0; fi; "
            "if [ $fast_count -ge 2 ]; then "
            "if [ -n \"$AGENT_ARCADE_CRASH_FILE\" ]; then "
            f"printf %s\\\\n {shlex.quote(message)} > \"$AGENT_ARCADE_CRASH_FILE\"; "
            "fi; "
            "sleep 2; "
            f"tmux kill-session -t {shlex.quote(self.session_name)}; "
            "exit 1; "
            "fi; "
            "sleep 1; "
            "done"
        )
        return f"bash -c {shlex.quote(loop)}"


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

    def _setup_dynamic_status_bar(self) -> None:
        """Set up initial status bar - will be updated by update_status_bar()."""
        # Just call update_status_bar to set initial state
        self.update_status_bar()

    def update_status_bar(self) -> None:
        """Update the status bar with current state."""
        if not self.config.tmux.status_bar:
            return

        # Check if agent is selected (read from tmux option)
        selected_agent = self.get_session_option("@selected-agent")
        agent_is_selected = bool(selected_agent)

        # Three states: no agent, idle, or active
        if not agent_is_selected:
            # No agent selected yet (still in menu)
            status_color = "cyan"
            agent_status = "🤖 No agent selected"
        elif self.agent_state_idle:
            # idle = user typing or agent waiting
            status_color = "green"
            agent_status = "🤖 Agent idle"
        else:
            # active = agent thinking or generating
            status_color = "yellow"
            agent_status = "🤖 Agent working..."

        # Game status
        if self.current_game:
            game_status = f"🎮 Playing: {self.current_game}"
        else:
            game_status = "🎮 No game selected"

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

    def get_session_option(self, option: str) -> Optional[str]:
        """
        Read a tmux option value for the session.

        Args:
            option: Option name (e.g. "@current-game")

        Returns:
            Option value or None if unavailable
        """
        try:
            result = subprocess.run(
                [
                    "tmux",
                    "display-message",
                    "-t",
                    self.session_name,
                    "-p",
                    f"#{{{option}}}",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            value = result.stdout.strip()
            return value if value else None
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
