"""AI agent integrations."""

from .base import BaseAgent, AgentStatus
from .claude_code import ClaudeCodeAgent
from .codex import CodexAgent
from .generic import GenericAgent

# Agent class registry
AGENT_CLASSES = {
    "claude_code": ClaudeCodeAgent,
    "codex": CodexAgent,
}


def create_agent(agent_id: str, config) -> BaseAgent:
    """
    Factory function to create agent instance.

    Args:
        agent_id: Agent identifier
        config: AgentConfig instance

    Returns:
        Agent instance
    """
    agent_class = AGENT_CLASSES.get(agent_id, GenericAgent)
    return agent_class(config)


__all__ = ["BaseAgent", "AgentStatus", "GenericAgent", "create_agent"]
