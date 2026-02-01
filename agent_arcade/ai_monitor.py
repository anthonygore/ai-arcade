"""AI agent output monitoring."""

import threading
import time
from typing import Callable, Optional

from .agents.base import BaseAgent
from .tmux_manager import TmuxManager


class AIMonitor:
    """Monitors AI agent state and game status."""

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

        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Callback when state changes
        self.on_state_changed: Optional[Callable[[bool], None]] = None

        # Set tmux manager on agent if it supports pattern-based detection
        if hasattr(agent, 'set_tmux_manager'):
            agent.set_tmux_manager(tmux_manager)

    def start(self) -> None:
        """Start monitoring agent state and game status."""
        if self._running:
            return

        # Set up agent state change callback
        self.agent.on_state_change = self._on_agent_state_changed

        # Start agent's own detection mechanism
        self.agent.start_detection()

        # Start game monitoring thread
        self._running = True
        self._thread = threading.Thread(target=self._monitor_game_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop monitoring."""
        self._running = False

        # Stop agent detection
        self.agent.stop_detection()

        # Stop game monitoring thread
        if self._thread:
            self._thread.join(timeout=2.0)

    def _on_agent_state_changed(self, is_idle: bool) -> None:
        """
        Called by agent when state changes.

        Args:
            is_idle: True if idle, False if active
        """
        # Update status bar
        self.tmux.set_agent_state(is_idle)

        # Call external callback if set
        if self.on_state_changed:
            self.on_state_changed(is_idle)

    def _monitor_game_loop(self) -> None:
        """Monitor game window for current game (runs in thread)."""
        while self._running:
            try:
                self._monitor_game_status()
                time.sleep(self.check_interval)
            except Exception as e:
                # Don't crash the monitor thread on errors
                print(f"Game monitor error: {e}")
                time.sleep(self.check_interval)

    def _monitor_game_status(self) -> None:
        """Monitor game window to detect current game."""
        try:
            # Read game name from tmux session option (set by game runner).
            current_game = self.tmux.get_session_option("@current-game")

            # Update status bar if game changed
            if current_game != self.tmux.current_game:
                self.tmux.set_game_status(current_game)

        except Exception:
            # Ignore errors in game monitoring
            pass

    @property
    def is_idle(self) -> bool:
        """
        Current agent state.

        Returns:
            True if idle (user typing or agent waiting)
            False if active (agent thinking or generating)
        """
        return self.agent.get_current_state()
