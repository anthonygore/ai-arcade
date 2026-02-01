"""Base agent interface for AI agents."""

import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional, Pattern, Tuple


@dataclass
class AgentStatus:
    """Current status of an AI agent."""

    is_ready: bool
    confidence: float  # 0.0 to 1.0
    last_output_time: float  # timestamp
    matched_pattern: str = ""


class BaseAgent(ABC):
    """Abstract base class for AI agents."""

    def __init__(self, config):
        """
        Initialize agent.

        Args:
            config: AgentConfig instance
        """
        self.config = config
        self.ready_patterns: List[Pattern] = self._compile_patterns()

        # State change callback
        # Called with is_idle parameter when state changes
        self.on_state_change: Optional[Callable[[bool], None]] = None

    def _compile_patterns(self) -> List[Pattern]:
        """
        Compile regex patterns from config.

        Returns:
            List of compiled patterns
        """
        patterns = []
        for pattern_str in self.config.ready_patterns:
            try:
                patterns.append(re.compile(pattern_str, re.MULTILINE))
            except re.error as e:
                print(f"Warning: Invalid pattern '{pattern_str}': {e}")
        return patterns

    def check_ready(self, output: str) -> AgentStatus:
        """
        Check if agent is ready based on output.

        Args:
            output: Recent output from agent's pane

        Returns:
            AgentStatus indicating readiness
        """
        # Check against ready patterns
        for pattern in self.ready_patterns:
            match = pattern.search(output)
            if match:
                return AgentStatus(
                    is_ready=True,
                    confidence=1.0,
                    last_output_time=time.time(),
                    matched_pattern=pattern.pattern
                )

        # No pattern matched
        return AgentStatus(
            is_ready=False,
            confidence=0.0,
            last_output_time=time.time()
        )

    @abstractmethod
    def get_launch_command(self) -> Tuple[str, List[str]]:
        """
        Return command and args to launch agent.

        Returns:
            (command, args) tuple
        """
        pass

    def get_working_directory(self) -> Optional[Path]:
        """
        Return working directory for agent.

        Returns:
            Path to working directory, or None for current
        """
        if self.config.working_directory:
            return Path(self.config.working_directory).expanduser()
        return None

    @abstractmethod
    def start_detection(self) -> None:
        """
        Start detecting agent state (idle/active).

        Agent should monitor its state and call on_state_change callback
        when the state changes between idle and active.
        """
        pass

    @abstractmethod
    def stop_detection(self) -> None:
        """
        Stop detecting agent state.

        Clean up any monitoring threads or resources.
        """
        pass

    @abstractmethod
    def get_current_state(self) -> bool:
        """
        Get current agent state.

        Returns:
            True if idle (waiting for user input)
            False if active (thinking/generating/executing)
        """
        pass
