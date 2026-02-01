"""Generic agent implementation with pattern-based detection."""

import re
import threading
import time
from typing import List, Optional, Tuple, TYPE_CHECKING

from .base import BaseAgent

if TYPE_CHECKING:
    from ..tmux_manager import TmuxManager


class GenericAgent(BaseAgent):
    """
    Generic agent with pattern-based state detection.

    Uses terminal output pattern matching to detect idle/active state.
    Suitable for agents without hook support (Aider, Cursor, etc.).
    """

    # Regex to match ANSI escape sequences
    ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    def __init__(self, config, tmux_manager: Optional['TmuxManager'] = None):
        """
        Initialize generic agent.

        Args:
            config: AgentConfig instance
            tmux_manager: Optional TmuxManager for output monitoring
        """
        super().__init__(config)

        self.tmux = tmux_manager
        self.buffer_lines = 50
        self.check_interval = 0.5
        self.inactivity_timeout = 2.0

        # State tracking
        self._is_idle = True
        self._running = False
        self._monitor_thread = None
        self._last_output = ""
        self._last_change_time = time.time()

    def set_tmux_manager(self, tmux_manager: 'TmuxManager') -> None:
        """
        Set tmux manager for output monitoring.

        Args:
            tmux_manager: TmuxManager instance
        """
        self.tmux = tmux_manager

    def get_launch_command(self) -> Tuple[str, List[str]]:
        """
        Get command to launch agent.

        Returns:
            (command, args) tuple
        """
        return (self.config.command, self.config.args)

    def start_detection(self) -> None:
        """Start pattern-based state detection."""
        if self._running or not self.tmux:
            return

        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def stop_detection(self) -> None:
        """Stop pattern-based state detection."""
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

    @classmethod
    def _strip_ansi_codes(cls, text: str) -> str:
        """
        Remove ANSI escape sequences from text.

        Args:
            text: Text potentially containing ANSI codes

        Returns:
            Text with ANSI codes removed
        """
        return cls.ANSI_ESCAPE.sub('', text)

    def _monitor_loop(self) -> None:
        """Monitor terminal output for pattern matches (runs in thread)."""
        while self._running:
            try:
                # Capture recent output from AI window
                output = self.tmux.capture_window_output(
                    self.tmux.ai_window_index,
                    lines=self.buffer_lines
                )

                # Check if output has changed
                if output != self._last_output:
                    self._last_output = output
                    self._last_change_time = time.time()

                # Strip ANSI codes before pattern matching
                clean_output = self._strip_ansi_codes(output)

                # Check agent-specific ready patterns
                status = self.check_ready(clean_output)

                # Determine state: idle or active
                is_idle = status.is_ready

                # If no pattern matched, check inactivity timeout as fallback
                if not is_idle:
                    time_since_change = time.time() - self._last_change_time
                    if time_since_change >= self.inactivity_timeout:
                        is_idle = True

                # Update state and notify if changed
                if is_idle != self._is_idle:
                    self._is_idle = is_idle

                    # Call callback if set
                    if self.on_state_change:
                        self.on_state_change(self._is_idle)

                # Sleep until next check
                time.sleep(self.check_interval)

            except Exception as e:
                # Don't crash the monitor thread on errors
                print(f"Pattern monitor error: {e}")
                time.sleep(self.check_interval)
