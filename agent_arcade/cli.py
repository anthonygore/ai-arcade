"""Main CLI entry point for Agent Arcade."""

import atexit
import os
import signal
import sys
import threading
import time
import tempfile
from pathlib import Path

from .agents import create_agent
from .ai_monitor import AIMonitor
from .config import Config
from .tmux_manager import TmuxManager


def print_help(config: Config):
    """Print CLI help/usage information."""
    agent_lines = []
    for agent in config.agents.values():
        label = agent.id
        if agent.name:
            label = f"{agent.id} ({agent.name})"
        agent_lines.append(f"  - {label}")

    usage = [
        "Agent Arcade - run an AI agent alongside the game runner",
        "",
        "Usage:",
        "  agent-arcade [agent]",
        "",
        "Arguments:",
        "  agent        Agent id or name to launch (default: claude_code)",
        "",
        "Options:",
        "  -h, --help   Show this help message and exit",
        "",
        "Available agents:",
        *agent_lines,
    ]
    print("\n".join(usage))


def main():
    """Main entry point for agent-arcade command."""
    try:
        # Load configuration
        config = Config.load()

        # Show help early
        if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help", "help"):
            print_help(config)
            sys.exit(0)

        # Pick agent from CLI arg (default to Claude Code)
        agent_selector = sys.argv[1] if len(sys.argv) > 1 else "claude_code"

        # Launch directly with agent + Games
        run_with_agent(config, agent_selector)

    except KeyboardInterrupt:
        print("\n👋 Exiting Agent Arcade.")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


def run_with_agent(config, agent_selector: str):
    """
    Run dual-pane mode with AI agent and games.

    Args:
        config: Config instance
        agent_selector: Agent selector (id or name, e.g., "codex")
    """
    # Get agent configuration
    agent_config = config.resolve_agent(agent_selector)
    if not agent_config:
        print(f"❌ Error: Unknown agent '{agent_selector}'")
        sys.exit(1)

    print(f"agent-arcade launching with {agent_config.name}")

    # Create agent instance
    agent = create_agent(agent_config.id, agent_config)

    # Get working directory
    working_dir = agent.get_working_directory()

    # Create tmux manager
    # Minimal launch output to keep the parent terminal clean.

    try:
        crash_file = Path(tempfile.gettempdir()) / f"agent-arcade-crash-{os.getpid()}.txt"
        if crash_file.exists():
            crash_file.unlink()
        tmux = TmuxManager(config, crash_file=crash_file)
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
        print("\n👋 Exiting Agent Arcade...")
        cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    stop_event = threading.Event()
    monitor_thread = None

    def start_pane_monitor():
        """Restart panes if they exit unexpectedly."""
        def monitor():
            ai_failures = 0
            game_failures = 0
            while not stop_event.is_set():
                try:
                    if tmux.is_pane_dead(tmux.ai_window_index):
                        try:
                            tmux.launch_ai_agent(cmd, args, working_dir)
                            ai_failures = 0
                        except Exception:
                            ai_failures += 1
                    else:
                        ai_failures = 0

                    if tmux.is_pane_dead(tmux.game_window_index):
                        try:
                            tmux.launch_game_runner()
                            game_failures = 0
                        except Exception:
                            game_failures += 1
                    else:
                        game_failures = 0

                    if ai_failures >= 3 or game_failures >= 3:
                        raise RuntimeError("Pane restart failed repeatedly")
                except Exception:
                    stop_event.set()
                    try:
                        tmux.kill_session()
                    finally:
                        sys.exit(1)
                time.sleep(1.0)

        nonlocal monitor_thread
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()

    try:
        # Create split-pane session
        tmux.create_session(working_dir)

        # Launch AI agent in top pane
        cmd, args = agent.get_launch_command()
        # launch agent
        crash_label = agent_config.name or agent_config.id
        crash_subject = "Claude" if agent_config.id == "claude_code" else crash_label
        tmux.launch_ai_agent(
            cmd,
            args,
            working_dir,
            crash_label=crash_label,
            crash_subject=crash_subject
        )

        # Launch game runner in bottom pane
        # launch game runner
        tmux.launch_game_runner()

        # Start AI monitoring
        # start AI monitor
        monitor = AIMonitor(tmux, agent, config)
        monitor.start()
        start_pane_monitor()

        # No banner output; keep startup minimal.

        # Attach to tmux session (blocking)
        tmux.attach()
        if crash_file.exists():
            message = crash_file.read_text().strip()
            crash_file.unlink()
            if message:
                print(f"\033[31m{message}\033[0m", file=sys.stderr)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        cleanup()
        sys.exit(1)

    finally:
        # Cleanup
        if 'monitor' in locals():
            monitor.stop()
        stop_event.set()
        cleanup()


if __name__ == "__main__":
    main()
