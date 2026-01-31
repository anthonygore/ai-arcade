"""Main CLI entry point for AI Arcade."""

import atexit
import signal
import sys

from .agents import create_agent
from .ai_monitor import AIMonitor
from .config import Config
from .tmux_manager import TmuxManager


def main():
    """Main entry point for ai-arcade command."""
    try:
        # Load configuration
        config = Config.load()

        # Launch directly with Claude Code + Games
        print("🎮 Starting AI Arcade...")
        run_with_agent(config, "claude_code")

    except KeyboardInterrupt:
        print("\n👋 Exiting AI Arcade.")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


def run_with_agent(config, agent_id: str):
    """
    Run dual-pane mode with AI agent and games.

    Args:
        config: Config instance
        agent_id: ID of agent to launch (e.g., "claude_code")
    """
    # Get agent configuration
    agent_config = config.get_agent(agent_id)
    if not agent_config:
        print(f"❌ Error: Unknown agent '{agent_id}'")
        sys.exit(1)

    # Create agent instance
    agent = create_agent(agent_id, agent_config)

    # Get working directory
    working_dir = agent.get_working_directory()

    # Create tmux manager
    print(f"⚙️  Setting up tmux session for {agent_config.name}...")

    try:
        tmux = TmuxManager(config)
    except RuntimeError as e:
        print(f"❌ {e}")
        sys.exit(1)

    # Set up cleanup handlers
    def cleanup():
        """Clean up tmux session on exit."""
        try:
            tmux.kill_session()
        except:
            pass

    atexit.register(cleanup)

    def signal_handler(sig, frame):
        """Handle termination signals."""
        print("\n👋 Exiting AI Arcade...")
        cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Create split-pane session
        tmux.create_session(working_dir)

        # Launch AI agent in top pane
        cmd, args = agent.get_launch_command()
        print(f"🤖 Launching {agent_config.name}...")
        tmux.launch_ai_agent(cmd, args, working_dir)

        # Launch game runner in bottom pane
        print("🎮 Starting game runner...")
        tmux.launch_game_runner()

        # Start AI monitoring
        print("👁️  Starting AI monitor...")
        monitor = AIMonitor(tmux, agent, config)
        monitor.start()

        # Show usage instructions
        print("\n" + "="*60)
        print("🎮 AI ARCADE is ready!")
        print("="*60)
        print(f"  Ctrl+Space: Toggle between AI and Games windows")
        print("\nPress Ctrl+C to exit AI Arcade")
        print("="*60 + "\n")

        # Attach to tmux session (blocking)
        tmux.attach()

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        cleanup()
        sys.exit(1)

    finally:
        # Cleanup
        if 'monitor' in locals():
            monitor.stop()
        cleanup()


if __name__ == "__main__":
    main()
