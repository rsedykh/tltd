"""TaskTree widget for displaying hierarchical task list."""
from __future__ import annotations

import time
from typing import TYPE_CHECKING, Optional, List, Tuple, Set
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Label, Input
from textual.message import Message
from textual.reactive import reactive

from ..models import TodoData, Task
from .task_line import TaskLine

if TYPE_CHECKING:
    from ..app import TodoApp


class TaskTree(Vertical):
    """Widget displaying the hierarchical task tree."""

    selected_index: reactive[int] = reactive(0)
    show_completed: reactive[bool] = reactive(False)

    def __init__(self, basket: str, todo_data: TodoData, todo_app: Optional[TodoApp] = None):
        super().__init__()
        self.basket = basket
        self.todo_data = todo_data
        self.todo_app = todo_app
        self.flat_list: List[Tuple[Task, int]] = []  # (task, level)
        self.border_title = basket
        # Multi-select state
        self.marked_task_ids: Set[str] = set()
        # Inline editing state
        self.editing_index: Optional[int] = None
        self.editing_initial_value: str = ""
        self.editing_mode: Optional[str] = None  # 'create' or 'edit'
        self.editing_task_id: Optional[str] = None  # For edit mode
        self.editing_level: int = 0  # Indentation level for create mode

    def compose(self) -> ComposeResult:
        """Build the task list."""
        yield Label(f"[{self.basket}]", id="basket-title")
        yield Container(id="task-container")

    def refresh_tasks(self) -> None:
        """Rebuild the flat task list and re-render."""
        self.flat_list = []
        self._build_flat_list(self.todo_data.baskets[self.basket], 0)
        self._render_tasks()

    def _build_flat_list(self, tasks: List[Task], level: int) -> None:
        """Recursively build a flat list of visible tasks."""
        for task in tasks:
            # Skip completed tasks if not showing them (unless recently completed)
            if task.completed and not self.show_completed:
                # Check if task was recently completed (within 5 seconds)
                if self.todo_app and task.id in self.todo_app.recently_completed:
                    completion_time = self.todo_app.recently_completed[task.id]
                    if time.time() - completion_time < 5.0:
                        # Still in grace period, show it
                        pass
                    else:
                        # Grace period expired, skip it
                        continue
                else:
                    # Not recently completed, skip it
                    continue

            self.flat_list.append((task, level))

            # Add children if not collapsed
            if not task.collapsed and task.children:
                self._build_flat_list(task.children, level + 1)

    def _render_tasks(self) -> None:
        """Render all tasks to the container."""
        container = self.query_one("#task-container", Container)
        container.remove_children()

        if not self.flat_list and self.editing_index is None:
            container.mount(Label("[dim]No tasks[/dim]"))
            return

        rendered_editor = False

        for i, (task, level) in enumerate(self.flat_list):
            # Show inline editor for create mode BEFORE this task
            if self.editing_mode == 'create' and self.editing_index == i and not rendered_editor:
                indent_text = "  " * self.editing_level
                # Add visual indicator for nesting level
                prefix = "☐ "
                full_content = f"{indent_text}{prefix}"
                input_widget = Input(value="", id="inline-editor", placeholder="New task...", max_length=512)
                # Use CSS to add padding based on indentation
                padding_left = len(full_content)
                input_widget.styles.padding = (0, 0, 0, padding_left)
                container.mount(input_widget)
                input_widget.focus()
                rendered_editor = True

            # Show inline editor for edit mode IN PLACE of this task
            if self.editing_index == i and self.editing_mode == 'edit':
                indent_text = "  " * level
                # Show collapse indicator and checkbox
                collapse_icon = "▼" if (task.children and not task.collapsed) else ("▶" if task.children else " ")
                check = "☑" if task.completed else "☐"
                prefix = f"{collapse_icon} {check} "
                full_content = f"{indent_text}{prefix}"
                input_widget = Input(value=self.editing_initial_value, id="inline-editor", max_length=512)
                padding_left = len(full_content)
                input_widget.styles.padding = (0, 0, 0, padding_left)
                container.mount(input_widget)
                input_widget.focus()
                # Move cursor to end - check widget still exists before calling
                def deselect():
                    try:
                        if input_widget.is_mounted:
                            input_widget.action_end()
                    except Exception:
                        pass  # Widget was destroyed, ignore
                self.app.set_timer(0.05, deselect)
                rendered_editor = True
            else:
                # Regular task line
                # Get terminal width, default to 80 if not available
                try:
                    max_width = self.app.size.width - 25  # Account for basket pane and padding
                except Exception:
                    max_width = 80
                line = TaskLine(task, level, self.show_completed, max_width)
                if i == self.selected_index and self.editing_index is None:
                    line.add_class("selected")
                if task.id in self.marked_task_ids:
                    line.add_class("marked")
                container.mount(line)

        # Show inline editor for create mode at the end if not yet rendered
        if self.editing_mode == 'create' and not rendered_editor:
            indent_text = "  " * self.editing_level
            prefix = "☐ "
            full_content = f"{indent_text}{prefix}"
            input_widget = Input(value="", id="inline-editor", placeholder="New task...", max_length=512)
            padding_left = len(full_content)
            input_widget.styles.padding = (0, 0, 0, padding_left)
            container.mount(input_widget)
            input_widget.focus()

    def get_selected_task(self) -> Optional[Task]:
        """Get the currently selected task."""
        if 0 <= self.selected_index < len(self.flat_list):
            return self.flat_list[self.selected_index][0]
        return None

    def move_selection(self, delta: int) -> None:
        """Move selection up or down."""
        if not self.flat_list:
            return

        self.selected_index = max(0, min(len(self.flat_list) - 1, self.selected_index + delta))
        self._render_tasks()

    def toggle_collapse(self) -> None:
        """Toggle collapse state of selected task."""
        task = self.get_selected_task()
        if task and task.children:
            task.collapsed = not task.collapsed
            self.refresh_tasks()

    def toggle_completion(self) -> None:
        """Toggle completion state of selected task."""
        task = self.get_selected_task()
        if task:
            task.completed = not task.completed
            self.refresh_tasks()

    def toggle_show_completed(self) -> None:
        """Toggle showing completed tasks."""
        self.show_completed = not self.show_completed
        self.refresh_tasks()

    def toggle_mark(self, task_id: str) -> None:
        """Toggle mark on a task (add if not marked, remove if marked)."""
        if task_id in self.marked_task_ids:
            self.marked_task_ids.remove(task_id)
        else:
            self.marked_task_ids.add(task_id)
        self._render_tasks()

    def clear_marks(self) -> None:
        """Clear all marks."""
        self.marked_task_ids.clear()
        self._render_tasks()

    def get_marked_tasks(self) -> List[Task]:
        """Return Task objects for all marked IDs."""
        if not self.todo_app:
            return []
        tasks = []
        for task_id in self.marked_task_ids:
            task = self.todo_app.todo_data.find_task(task_id)
            if task:
                tasks.append(task)
        return tasks

    def start_edit_task(self, task_id: str, initial_value: str) -> None:
        """Start inline editing of an existing task."""
        self.editing_mode = 'edit'
        self.editing_task_id = task_id
        self.editing_initial_value = initial_value
        # Find the task's index in flat_list
        for i, (task, level) in enumerate(self.flat_list):
            if task.id == task_id:
                self.editing_index = i
                break
        self._render_tasks()

    def start_create_task(self, at_index: Optional[int] = None, level: int = 0) -> None:
        """Start inline creation of a new task."""
        self.editing_mode = 'create'
        self.editing_initial_value = ""
        self.editing_level = level  # Store the indentation level
        if at_index is not None:
            self.editing_index = at_index
        else:
            self.editing_index = len(self.flat_list)
        self._render_tasks()

    def cancel_editing(self) -> None:
        """Cancel inline editing."""
        self.editing_index = None
        self.editing_mode = None
        self.editing_initial_value = ""
        self.editing_task_id = None
        self._render_tasks()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in inline editor."""
        if event.input.id != "inline-editor":
            return

        new_value = event.value.strip()
        if not new_value:
            self.cancel_editing()
            return

        if self.editing_mode == 'edit' and self.editing_task_id:
            # Post message to TodoApp to handle the edit
            self.post_message(self.TaskEdited(self.editing_task_id, new_value))
        elif self.editing_mode == 'create':
            # Post message to TodoApp to handle the creation
            self.post_message(self.TaskCreated(new_value, self.editing_index))

        self.cancel_editing()

    def on_key(self, event) -> None:
        """Handle ESC key to cancel inline editing."""
        if event.key == "escape" and self.editing_index is not None:
            self.cancel_editing()
            event.stop()

    # Message classes for communication with TodoApp
    class TaskEdited(Message):
        def __init__(self, task_id: str, new_title: str):
            super().__init__()
            self.task_id = task_id
            self.new_title = new_title

    class TaskCreated(Message):
        def __init__(self, title: str, at_index: Optional[int]):
            super().__init__()
            self.title = title
            self.at_index = at_index
