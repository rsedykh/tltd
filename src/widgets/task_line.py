"""TaskLine widget for displaying a single task."""
from textual.widgets import Static
from rich.markup import escape as escape_markup

from ..models import Task


class TaskLine(Static):
    """A single task line in the tree."""

    def __init__(self, task: Task, level: int, show_completed: bool = False, max_width: int = 80):
        indent = "  " * level

        # Collapse indicator
        if task.children:
            collapse_icon = "▼" if not task.collapsed else "▶"
        else:
            collapse_icon = " "

        # Completion indicator
        check = "☑" if task.completed else "☐"

        # Child count when collapsed
        child_count = ""
        if task.children and task.collapsed:
            # Count only visible children based on show_completed setting
            if show_completed:
                visible_count = len(task.children)
            else:
                visible_count = sum(1 for child in task.children if not child.completed)
            child_count = f" ({visible_count})"

        # Escape user content to prevent Rich markup injection
        escaped_title = escape_markup(task.title)

        # Build the display text with strikethrough for completed tasks
        if task.completed:
            content = f"{indent}{collapse_icon} {check} [strike]{escaped_title}[/strike]{child_count}"
        else:
            content = f"{indent}{collapse_icon} {check} {escaped_title}{child_count}"

        # Add description line if present
        if task.description:
            # Description indent: align with title text (after collapse + check + space)
            desc_indent = indent + "    "  # 4 spaces to align under title
            # Get first line of description
            first_line = task.description.split('\n')[0]
            has_more_lines = '\n' in task.description
            # Calculate available width for description
            available_width = max_width - len(desc_indent) - 3  # -3 for "..."
            # Truncate if needed
            if len(first_line) > available_width or has_more_lines:
                truncated = first_line[:available_width].rstrip() + "..."
            else:
                truncated = first_line
            # Escape description to prevent Rich markup injection
            escaped_desc = escape_markup(truncated)
            content += f"\n{desc_indent}[dim]{escaped_desc}[/dim]"

        super().__init__(content)

        # Apply styling
        if task.completed:
            self.add_class("dim")
