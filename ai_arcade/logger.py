"""Logging utility for AI Arcade.

Provides a simple logger that writes to a file for debugging games and apps.
This is especially useful for Textual apps where print() doesn't work.

Usage:
    from ai_arcade.logger import logger

    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
"""

import logging
from pathlib import Path

# Create logs directory in user's home
LOG_DIR = Path.home() / ".ai-arcade" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "debug.log"

# Configure logger
logger = logging.getLogger("ai_arcade")
logger.setLevel(logging.DEBUG)

# Remove any existing handlers
logger.handlers.clear()

# Create file handler
file_handler = logging.FileHandler(LOG_FILE, mode='a')
file_handler.setLevel(logging.DEBUG)

# Create formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(file_handler)


def get_log_file_path() -> Path:
    """
    Get the path to the current log file.

    Returns:
        Path to the log file
    """
    return LOG_FILE


def tail_log(lines: int = 50) -> str:
    """
    Get the last N lines from the log file.

    Args:
        lines: Number of lines to retrieve

    Returns:
        Last N lines from the log
    """
    try:
        if not LOG_FILE.exists():
            return "No log file yet"

        with open(LOG_FILE, 'r') as f:
            all_lines = f.readlines()
            return ''.join(all_lines[-lines:])
    except Exception as e:
        return f"Error reading log: {e}"

# Don't propagate to root logger
logger.propagate = False


# Log startup
logger.info("=" * 80)
logger.info("AI Arcade logging initialized")
logger.info(f"Log file: {LOG_FILE}")
logger.info("=" * 80)
