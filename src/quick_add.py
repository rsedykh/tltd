"""Quick-add CLI for adding tasks to Inbox via command line."""
import sys

from .models import Task
from .storage import StorageManager


def main() -> int:
    """
    Add a task to Inbox from command line arguments.

    Usage:
        td Task title here
        td Task title \\ optional description here

    Returns 0 on success, 1 on error.
    """
    # Join all arguments into a single string
    text = " ".join(sys.argv[1:]).strip()

    if not text:
        print("Usage: td <task title> [\\\\ description]")
        return 1

    # Split on " \\ " to separate title from description
    if " \\\\ " in text:
        title, description = text.split(" \\\\ ", 1)
        title = title.strip()
        description = description.strip()
    else:
        title = text
        description = ""

    if not title:
        print("Error: Task title cannot be empty")
        return 1

    # Load existing data
    storage = StorageManager()
    todo_data = storage.load()

    # Create and add task
    task = Task(title=title, description=description)
    todo_data.add_task("Inbox", task)

    # Save
    if storage.save(todo_data):
        if description:
            print(f"Added to Inbox: {title}")
            print(f"  Description: {description}")
        else:
            print(f"Added to Inbox: {title}")
        return 0
    else:
        print("Error: Failed to save task")
        return 1


if __name__ == "__main__":
    sys.exit(main())
