"""Helper script to update status bar."""

from .config import Config
from .tmux_manager import TmuxManager


def main():
    """Update status bar."""
    config = Config.load()
    tmux = TmuxManager(config)
    tmux.update_status_bar()


if __name__ == "__main__":
    main()
