"""Main entry point for the todo application."""
import sys
import os

# Add parent directory to path to allow imports when run as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app import TodoApp


def main():
    """Run the todo application."""
    app = TodoApp()
    try:
        app.run()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"Error running application: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
