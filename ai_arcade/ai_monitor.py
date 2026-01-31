"""AI agent output monitoring."""

import threading
import time
from typing import Callable, Optional

from .agents.base import BaseAgent, AgentStatus
from .tmux_manager import TmuxManager


class AIMonitor:
    """Monitors AI agent output for readiness."""

    def __init__(self, tmux_manager: TmuxManager, agent: BaseAgent, config):
        """
        Initialize AI monitor.

        Args:
            tmux_manager: TmuxManager instance
            agent: Agent instance
            config: Config instance
        """
        self.tmux = tmux_manager
        self.agent = agent
        self.config = config

        self.check_interval = config.monitoring.check_interval
        self.inactivity_timeout = config.monitoring.inactivity_timeout
        self.buffer_lines = config.monitoring.buffer_lines

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_output = ""
        self._last_change_time = time.time()
        self._is_ready = False

        # Callback when readiness changes
        self.on_ready_changed: Optional[Callable[[bool], None]] = None

    def start(self) -> None:
        """Start monitoring in background thread."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop monitoring thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)

    def _monitor_loop(self) -> None:
        """Main monitoring loop (runs in thread)."""
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

                # Check agent-specific ready patterns
                status = self.agent.check_ready(output)

                # If no pattern matched, check inactivity
                if not status.is_ready:
                    time_since_change = time.time() - self._last_change_time
                    if time_since_change >= self.inactivity_timeout:
                        status.is_ready = True
                        status.confidence = 0.7  # Lower confidence
                        status.matched_pattern = "inactivity_timeout"

                # Update ready state and notify if changed
                if status.is_ready != self._is_ready:
                    self._is_ready = status.is_ready

                    # Send notification to game pane
                    if self._is_ready and self.config.notifications.enabled:
                        self._send_notification()

                    # Call callback if set
                    if self.on_ready_changed:
                        self.on_ready_changed(self._is_ready)

                # Sleep until next check
                time.sleep(self.check_interval)

            except Exception as e:
                # Don't crash the monitor thread on errors
                print(f"Monitor error: {e}")
                time.sleep(self.check_interval)

    def _send_notification(self) -> None:
        """Send notification to game window that AI is ready."""
        if not self.config.notifications.visual:
            return

        try:
            message = self.config.notifications.message
            duration = int(self.config.notifications.flash_duration * 1000)  # Convert to ms

            target = f"{self.tmux.session_name}:{self.tmux.game_window_index}"
            self.tmux._send_tmux_cmd([
                "display-message", "-t", target,
                "-d", str(duration),
                message
            ])
        except Exception as e:
            print(f"Warning: Could not send notification: {e}")

    @property
    def is_ready(self) -> bool:
        """
        Current readiness state.

        Returns:
            True if agent is ready
        """
        return self._is_ready
