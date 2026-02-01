"""Codex agent implementation."""

import json
import re
import threading
import time
from pathlib import Path
from typing import List, Optional, Tuple

from .base import BaseAgent


class CodexAgent(BaseAgent):
    """Codex agent with session/log-based state detection."""

    ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    ESC_INTERRUPT_MARKER = "esc to interrupt"
    DEFAULT_LOG_FILE = Path.home() / ".codex" / "log" / "codex-tui.log"
    ACTIVE_MARKERS = (
        "run_turn",
        "receiving_stream",
        "ToolCall",
        "stream_events_utils",
    )
    IDLE_MARKERS = (
        "close time.busy",
        "close time.idle",
    )
    SESSION_ACTIVE_EVENT_TYPES = {
        "agent_reasoning",
        "agent_message",
        "command_execution",
        "tool_call",
        "tool",
    }
    SESSION_TURN_START_EVENTS = {
        "turn/started",
        "item/started",
        "thread/started",
    }
    SESSION_TURN_END_EVENTS = {
        "turn/completed",
        "item/completed",
        "turn_aborted",
    }
    SESSION_RESPONSE_ITEM_TYPES = {
        "reasoning",
        "message",
        "function_call",
        "function_call_output",
        "custom_tool_call",
        "custom_tool_call_output",
        "tool_call",
        "tool_call_output",
    }

    def __init__(self, config):
        """
        Initialize Codex agent.

        Args:
            config: AgentConfig instance
        """
        super().__init__(config)

        log_path = config.log_file or str(self.DEFAULT_LOG_FILE)
        self.log_file = Path(log_path).expanduser()

        self.inactivity_timeout = 2.0
        self.check_interval = 0.2

        self._is_idle = True
        self._running = False
        self._monitor_thread = None
        self._last_position = 0
        self._last_activity = time.time()
        self._session_dir = Path.home() / ".codex" / "sessions"
        self._session_file: Optional[Path] = None
        self._session_last_position = 0
        self._session_last_activity = time.time()
        self._tmux_last_output = ""
        self._tmux_missing_since: Optional[float] = None
        self._tmux_marker_seen = False
        self.tmux = None
        self.buffer_lines = 50

    def set_tmux_manager(self, tmux_manager) -> None:
        """
        Set tmux manager for output monitoring.

        Args:
            tmux_manager: TmuxManager instance
        """
        self.tmux = tmux_manager

    def get_launch_command(self) -> Tuple[str, List[str]]:
        """
        Get command to launch Codex.

        Returns:
            (command, args) tuple
        """
        return (self.config.command, self.config.args)

    def start_detection(self) -> None:
        """Start log-based state detection."""
        if self._running:
            return

        self._prime_log_position()
        self._prime_session_position()

        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_activity, daemon=True)
        self._monitor_thread.start()

    def stop_detection(self) -> None:
        """Stop log-based state detection."""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)

    def get_current_state(self) -> bool:
        """
        Get current agent state.

        Returns:
            True if idle, False if active
        """
        return self._is_idle

    def _prime_log_position(self) -> None:
        """Start reading from the end of the log file."""
        try:
            if self.log_file.exists():
                self._last_position = self.log_file.stat().st_size
        except Exception:
            self._last_position = 0

    def _prime_session_position(self) -> None:
        """Start reading from the end of the most recent session log."""
        session_file = self._find_latest_session_file()
        if not session_file:
            return
        self._session_file = session_file
        try:
            self._session_last_position = session_file.stat().st_size
        except Exception:
            self._session_last_position = 0

    def _find_latest_session_file(self) -> Optional[Path]:
        """Find the most recently modified session JSONL file."""
        if not self._session_dir.exists():
            return None
        latest_file = None
        latest_mtime = 0.0
        for path in self._session_dir.rglob("rollout-*.jsonl"):
            try:
                mtime = path.stat().st_mtime
            except Exception:
                continue
            if mtime > latest_mtime:
                latest_mtime = mtime
                latest_file = path
        return latest_file

    def _set_idle(self, is_idle: bool) -> None:
        """Update idle state and notify if changed."""
        if is_idle != self._is_idle:
            self._is_idle = is_idle
            if self.on_state_change:
                self.on_state_change(self._is_idle)

    def _monitor_activity(self) -> None:
        """Monitor Codex session or log files for activity."""
        while self._running:
            try:
                if self._monitor_tmux_output():
                    time.sleep(self.check_interval)
                    continue
                if self._monitor_session():
                    time.sleep(self.check_interval)
                    continue
                self._monitor_log()
                time.sleep(self.check_interval)
            except Exception as e:
                print(f"Codex activity monitor error: {e}")
                time.sleep(self.check_interval)

    @classmethod
    def _strip_ansi_codes(cls, text: str) -> str:
        """Remove ANSI escape sequences from text."""
        return cls.ANSI_ESCAPE.sub('', text)

    def _monitor_tmux_output(self) -> bool:
        """Monitor tmux pane for the Codex activity indicator."""
        if not self.tmux:
            return False
        try:
            if self.tmux.is_pane_dead(self.tmux.ai_window_index):
                return False
        except Exception:
            return False

        try:
            output = self.tmux.capture_window_output(
                self.tmux.ai_window_index,
                lines=self.buffer_lines
            )
        except Exception:
            return False
        if output != self._tmux_last_output:
            self._tmux_last_output = output

        clean_output = self._strip_ansi_codes(output).lower()
        now = time.time()

        if self.ESC_INTERRUPT_MARKER in clean_output:
            self._last_activity = now
            self._tmux_marker_seen = True
            self._tmux_missing_since = None
            self._set_idle(False)
            return True

        if self._tmux_marker_seen:
            if self._tmux_missing_since is None:
                self._tmux_missing_since = now
            elif now - self._tmux_missing_since >= self.inactivity_timeout:
                self._tmux_marker_seen = False
                self._set_idle(True)
        else:
            self._set_idle(True)

        return True

    def _monitor_session(self) -> bool:
        """Monitor Codex session JSONL for turn-based activity."""
        session_file = self._find_latest_session_file()
        if not session_file:
            return False

        if session_file != self._session_file:
            self._session_file = session_file
            try:
                self._session_last_position = session_file.stat().st_size
            except Exception:
                self._session_last_position = 0

        size = session_file.stat().st_size
        if size < self._session_last_position:
            # Session log rotated/truncated.
            self._session_last_position = 0

        lines = []
        if size > self._session_last_position:
            with session_file.open("r") as handle:
                handle.seek(self._session_last_position)
                lines = handle.read().splitlines()
                self._session_last_position = handle.tell()

        now = time.time()
        active_seen = False
        idle_seen = False
        for line in lines:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            entry_type = entry.get("type")
            payload = entry.get("payload", {})
            if entry_type == "event_msg":
                payload_type = payload.get("type")
                if payload_type in self.SESSION_TURN_START_EVENTS:
                    self._session_last_activity = now
                    active_seen = True
                elif payload_type in self.SESSION_TURN_END_EVENTS:
                    idle_seen = True
                elif payload_type in self.SESSION_ACTIVE_EVENT_TYPES:
                    self._session_last_activity = now
                    active_seen = True
            elif entry_type == "response_item":
                payload_type = payload.get("type")
                if payload_type in self.SESSION_RESPONSE_ITEM_TYPES:
                    self._session_last_activity = now
                    active_seen = True

        if idle_seen and not active_seen:
            self._set_idle(True)
        elif active_seen:
            self._set_idle(False)

        if not self._is_idle:
            if now - self._session_last_activity >= self.inactivity_timeout:
                self._set_idle(True)

        return True

    def _monitor_log(self) -> None:
        """Monitor Codex TUI log file for activity."""
        if not self.log_file.exists():
            return

        size = self.log_file.stat().st_size
        if size < self._last_position:
            # Log rotated/truncated.
            self._last_position = 0

        lines = []
        if size > self._last_position:
            with self.log_file.open("r") as handle:
                handle.seek(self._last_position)
                lines = handle.read().splitlines()
                self._last_position = handle.tell()

        now = time.time()
        active_seen = False
        idle_seen = False
        for line in lines:
            if any(marker in line for marker in self.ACTIVE_MARKERS):
                self._last_activity = now
                self._set_idle(False)
                active_seen = True
                continue
            if any(marker in line for marker in self.IDLE_MARKERS):
                idle_seen = True

        # If we saw idle markers without any active markers in the same batch,
        # mark idle; otherwise let activity (or the inactivity timeout) decide.
        if idle_seen and not active_seen:
            self._set_idle(True)

        if not self._is_idle:
            if now - self._last_activity >= self.inactivity_timeout:
                self._set_idle(True)
