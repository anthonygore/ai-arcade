"""Claude Code agent implementation."""

import json
import os
import threading
import time
from pathlib import Path
from typing import List, Tuple

from .base import BaseAgent


class ClaudeCodeAgent(BaseAgent):
    """Claude Code specific configuration with hook-based state detection."""

    def __init__(self, config):
        """
        Initialize Claude Code agent.

        Args:
            config: AgentConfig instance
        """
        super().__init__(config)

        # State file for hook-based detection
        # Use fixed path that hooks can write to
        self.state_file = Path("/tmp/claude_arcade_state.json")

        # State tracking
        self._is_idle = True  # Default to idle
        self._running = False
        self._monitor_thread = None
        self._last_mtime = 0.0

    def get_launch_command(self) -> Tuple[str, List[str]]:
        """
        Get command to launch Claude Code.

        Returns:
            (command, args) tuple
        """
        return (self.config.command, self.config.args)

    def start_detection(self) -> None:
        """Start monitoring state file written by Claude Code hooks."""
        if self._running:
            return

        # Initialize state file
        self._write_initial_state()

        # Start monitoring thread
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_state_file, daemon=True)
        self._monitor_thread.start()

    def stop_detection(self) -> None:
        """Stop monitoring state file."""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)

        # Clean up state file
        try:
            if self.state_file.exists():
                self.state_file.unlink()
        except Exception:
            pass

    def get_current_state(self) -> bool:
        """
        Get current agent state.

        Returns:
            True if idle, False if active
        """
        return self._is_idle

    def _write_initial_state(self) -> None:
        """Write initial idle state to state file."""
        try:
            state = {
                "state": "idle",
                "timestamp": time.time()
            }
            self.state_file.write_text(json.dumps(state))
        except Exception as e:
            print(f"Warning: Could not write initial state file: {e}")

    def _monitor_state_file(self) -> None:
        """Monitor state file for changes (runs in background thread)."""
        while self._running:
            try:
                # Check if file exists and has been modified
                if self.state_file.exists():
                    mtime = self.state_file.stat().st_mtime

                    # Only read if file has changed
                    if mtime != self._last_mtime:
                        self._last_mtime = mtime

                        # Read state from file
                        try:
                            data = json.loads(self.state_file.read_text())
                            state_str = data.get("state", "idle")

                            # Convert state string to boolean
                            # idle = True, active/processing = False
                            new_is_idle = state_str == "idle"

                            # Update state and notify if changed
                            if new_is_idle != self._is_idle:
                                self._is_idle = new_is_idle

                                # Call callback if set
                                if self.on_state_change:
                                    self.on_state_change(self._is_idle)

                        except (json.JSONDecodeError, KeyError) as e:
                            # Ignore malformed state file
                            pass

                # Sleep before next check
                time.sleep(0.1)  # Check every 100ms for responsiveness

            except Exception as e:
                # Don't crash monitor thread on errors
                print(f"State monitor error: {e}")
                time.sleep(0.1)
