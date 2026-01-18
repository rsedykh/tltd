"""Main entry point for the todo application."""
import sys
import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import traceback

# Add parent directory to path to allow imports when run as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app import TodoApp

# Log directory and file
LOG_DIR = Path.home() / ".tltd"
LOG_FILE = LOG_DIR / "crash.log"
MAX_LOG_SIZE = 1024 * 1024  # 1 MB
BACKUP_COUNT = 2  # Keep 2 backup files


def setup_crash_logging():
    """Set up crash logging to ~/.tltd/crash.log with rotation."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding='utf-8'
    )
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))

    logger = logging.getLogger('tltd')
    logger.setLevel(logging.ERROR)
    logger.addHandler(handler)
    return logger


def main():
    """Run the todo application."""
    logger = setup_crash_logging()

    app = TodoApp()
    try:
        app.run()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        error_msg = f"Application crashed: {e}\n{traceback.format_exc()}"
        logger.error(error_msg)
        print(f"Error: {e}", file=sys.stderr)
        print(f"Crash log written to: {LOG_FILE}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
