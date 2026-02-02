"""Helper script to launch an agent with AIMonitor."""

import subprocess
import sys
from pathlib import Path

from .ai_monitor import AIMonitor
from .agents import create_agent
from .config import Config


def main():
    """Launch agent with monitoring."""
    if len(sys.argv) < 2:
        print("Usage: agent_launcher.py <agent_id>", file=sys.stderr)
        sys.exit(1)

    agent_id = sys.argv[1]

    # Load config
    config = Config.load()

    # Get agent config
    agent_config = config.resolve_agent(agent_id)
    if not agent_config:
        print(f"Error: Unknown agent '{agent_id}'", file=sys.stderr)
        sys.exit(1)

    # Create agent instance
    agent = create_agent(agent_config.id, agent_config)

    # Get launch command
    cmd, args = agent.get_launch_command()
    working_dir = agent.get_working_directory()

    # Start AIMonitor
    from .tmux_manager import TmuxManager
    tmux = TmuxManager(config)

    # Set agent as selected in status
    tmux.agent_state_idle = True
    tmux.update_status_bar()

    monitor = AIMonitor(tmux, agent, config)
    monitor.start()

    # Build command
    full_cmd = [cmd] + args

    try:
        # Launch agent process
        if working_dir:
            result = subprocess.run(full_cmd, cwd=working_dir)
        else:
            result = subprocess.run(full_cmd)

        exit_code = result.returncode
    except KeyboardInterrupt:
        exit_code = 130
    finally:
        # Stop monitor
        monitor.stop()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
