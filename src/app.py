"""Main UI application using Textual."""
from __future__ import annotations

import time
from typing import Optional, List, Tuple, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Self
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static, Input, Button, Label, Footer
from textual.binding import Binding
from textual.message import Message
from textual.screen import ModalScreen
from textual.reactive import reactive

from .models import TodoData, Task
from .storage import StorageManager


class TaskLine(Static):
    """A single task line in the tree."""

    def __init__(self, task: Task, level: int, show_completed: bool = False):
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

        # Build the display text with strikethrough for completed tasks
        if task.completed:
            content = f"{indent}{collapse_icon} {check} [strike]{task.title}[/strike]{child_count}"
        else:
            content = f"{indent}{collapse_icon} {check} {task.title}{child_count}"

        super().__init__(content)

        # Apply styling
        if task.completed:
            self.add_class("dim")


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
                input_widget = Input(value="", id="inline-editor", placeholder="New task...")
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
                input_widget = Input(value=self.editing_initial_value, id="inline-editor")
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
                line = TaskLine(task, level, self.show_completed)
                if i == self.selected_index and self.editing_index is None:
                    line.add_class("selected")
                container.mount(line)

        # Show inline editor for create mode at the end if not yet rendered
        if self.editing_mode == 'create' and not rendered_editor:
            indent_text = "  " * self.editing_level
            prefix = "☐ "
            full_content = f"{indent_text}{prefix}"
            input_widget = Input(value="", id="inline-editor", placeholder="New task...")
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


class BasketPane(Vertical):
    """Left sidebar showing available baskets."""

    selected_basket: reactive[str] = reactive("Inbox")
    show_completed_mode: reactive[bool] = reactive(False)

    def __init__(self, todo_data: TodoData):
        super().__init__()
        self.todo_data = todo_data
        self.border_title = "Baskets"

    def compose(self) -> ComposeResult:
        """Build the basket list."""
        for basket in TodoData.BASKETS:
            count = self.todo_data.get_basket_count(basket)
            label = f"{basket} ({count})"
            widget = Label(label, classes="basket-item")
            if basket == self.selected_basket:
                widget.add_class("selected")
            yield widget

    def refresh_baskets(self) -> None:
        """Refresh basket counts and selection."""
        self.remove_children()
        for basket in TodoData.BASKETS:
            count = self.todo_data.get_basket_count(basket)
            label = f"{basket} ({count})"
            widget = Label(label, classes="basket-item")
            if basket == self.selected_basket:
                widget.add_class("selected")
            if self.show_completed_mode:
                widget.add_class("show-completed-mode")
            self.mount(widget)

    def select_next(self) -> None:
        """Select next basket."""
        baskets = TodoData.BASKETS
        idx = baskets.index(self.selected_basket)
        self.selected_basket = baskets[(idx + 1) % len(baskets)]
        self.refresh_baskets()

    def select_previous(self) -> None:
        """Select previous basket."""
        baskets = TodoData.BASKETS
        idx = baskets.index(self.selected_basket)
        self.selected_basket = baskets[(idx - 1) % len(baskets)]
        self.refresh_baskets()


class BasketSelectorDialog(ModalScreen[str]):
    """Modal dialog for selecting a basket."""

    def __init__(self):
        super().__init__()
        self.selected_index = 0

    def compose(self) -> ComposeResult:
        with Container(id="dialog-container"):
            yield Label("Move to basket (↑/↓ to select, Enter to confirm, ESC to cancel):", id="dialog-title")
            with Vertical(id="basket-list"):
                for i, basket in enumerate(TodoData.BASKETS):
                    label = Label(basket, classes="basket-option")
                    if i == self.selected_index:
                        label.add_class("selected")
                    yield label

    def _update_selection(self) -> None:
        """Update visual selection of basket items."""
        basket_list = self.query_one("#basket-list")
        labels = basket_list.query(".basket-option")
        for i, label in enumerate(labels):
            if i == self.selected_index:
                label.add_class("selected")
            else:
                label.remove_class("selected")

    # Quick-jump key mapping: key -> basket name
    QUICK_JUMP_KEYS = {
        "grave_accent": "Inbox",
        "1": "Monday",
        "2": "Tuesday",
        "3": "Wednesday",
        "4": "Thursday",
        "5": "Friday",
        "6": "Saturday",
        "7": "Sunday",
        "0": "Later",
    }

    def on_key(self, event) -> None:
        """Handle key presses."""
        if event.key == "escape":
            self.dismiss("")
            event.stop()  # Prevent ESC from reaching TodoApp quit binding
        elif event.key == "enter":
            self.dismiss(TodoData.BASKETS[self.selected_index])
            event.stop()
        elif event.key == "up":
            if self.selected_index > 0:
                self.selected_index -= 1
                self._update_selection()
            event.stop()
        elif event.key == "down":
            if self.selected_index < len(TodoData.BASKETS) - 1:
                self.selected_index += 1
                self._update_selection()
            event.stop()
        elif event.key in self.QUICK_JUMP_KEYS:
            # Quick-jump to basket and confirm
            self.dismiss(self.QUICK_JUMP_KEYS[event.key])
            event.stop()


class TodoApp(App):
    """Main todo application."""

    CSS = """
    Screen {
        background: $surface;
    }

    #main-container {
        width: 100%;
        height: 100%;
    }

    #basket-pane {
        width: 20;
        border: solid $primary;
        padding: 1;
    }

    #basket-pane.focused {
        border: heavy $accent;
    }

    #task-pane {
        width: 1fr;
        border: solid $primary;
        padding: 1;
    }

    #task-pane.focused {
        border: heavy $accent;
    }

    #task-pane.show-completed-mode {
        border: solid #808080;
    }

    #task-pane.focused.show-completed-mode {
        border: heavy #808080;
    }

    .selected {
        background: $primary;
        color: $text;
    }

    .basket-item {
        padding: 0 1;
    }

    .basket-item.show-completed-mode {
        color: #808080;
    }

    .basket-item.selected.show-completed-mode {
        background: #1a1a1a;
        color: #808080;
    }

    #dialog-container {
        width: 60;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    #dialog-title {
        margin-bottom: 1;
        text-style: bold;
    }

    #basket-list {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }

    .basket-option {
        padding: 0 1;
    }

    #help-container {
        width: 80;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    #help-text {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }

    Footer {
        height: auto;
    }
    """

    BINDINGS = [
        Binding("c", "add_task", "Create", show=True),
        Binding("enter", "edit_task", "Edit", show=True),
        Binding("x", "toggle_complete", "✓ Done", show=True),
        Binding("backspace", "delete_task", "Delete", show=True),
        Binding("f", "move_task", "Move to Basket", show=True),
        Binding("up", "navigate_up", "↑", show=False),
        Binding("down", "navigate_down", "↓", show=False),
        Binding("left", "switch_to_baskets", "◀ Baskets", show=True),
        Binding("right", "switch_to_tasks", "▶ Tasks", show=True),
        Binding("a", "collapse_task", "Collapse", show=True),
        Binding("d", "expand_task", "Expand", show=True),
        Binding("A", "collapse_all", "Collapse All", show=False),
        Binding("D", "expand_all", "Expand All", show=False),
        Binding("w", "move_task_up", "Move Up", show=True),
        Binding("s", "move_task_down", "Move Down", show=True),
        Binding("e", "nest_task", "Nest →", show=True),
        Binding("q", "unnest_task", "← Unnest", show=True),
        Binding("z", "toggle_show_completed", "Show Done", show=True),
        Binding("backslash", "undo", "Undo", show=True),
        Binding("?", "show_help", "Help", show=True),
        Binding("escape", "quit", "Quit", show=True),
        # Quick basket jump keys (` for Inbox, 1-7 for Mon-Sun, 0 for Later)
        Binding("grave_accent", "jump_inbox", "Inbox", show=False),
        Binding("1", "jump_monday", "Mon", show=False),
        Binding("2", "jump_tuesday", "Tue", show=False),
        Binding("3", "jump_wednesday", "Wed", show=False),
        Binding("4", "jump_thursday", "Thu", show=False),
        Binding("5", "jump_friday", "Fri", show=False),
        Binding("6", "jump_saturday", "Sat", show=False),
        Binding("7", "jump_sunday", "Sun", show=False),
        Binding("0", "jump_later", "Later", show=False),
        # Russian keyboard layout equivalents (ЙЦУКЕН)
        Binding("с", "add_task", "Create", show=False),  # c
        Binding("ч", "toggle_complete", "Done", show=False),  # x
        Binding("а", "move_task", "Move", show=False),  # f
        Binding("ф", "collapse_task", "Collapse", show=False),  # a
        Binding("в", "expand_task", "Expand", show=False),  # d
        Binding("Ф", "collapse_all", "Collapse All", show=False),  # A (Shift+a)
        Binding("В", "expand_all", "Expand All", show=False),  # D (Shift+d)
        Binding("ц", "move_task_up", "Up", show=False),  # w
        Binding("ы", "move_task_down", "Down", show=False),  # s
        Binding("у", "nest_task", "Nest", show=False),  # e
        Binding("й", "unnest_task", "Unnest", show=False),  # q
        Binding("я", "toggle_show_completed", "Show Done", show=False),  # z
        Binding("ё", "jump_inbox", "Inbox", show=False),  # ` (backtick)
    ]

    def __init__(self):
        super().__init__()
        self.storage = StorageManager()
        self.todo_data = self.storage.load()
        self.basket_pane: Optional[BasketPane] = None
        self.task_tree: Optional[TaskTree] = None
        self.focused_panel: str = "tasks"  # "baskets" or "tasks"
        self.history: List[Dict[str, Any]] = []  # Undo history
        self.max_history = 50  # Maximum undo steps
        self.recently_completed: Dict[str, float] = {}  # task_id -> completion timestamp

    def compose(self) -> ComposeResult:
        """Build the UI layout."""
        with Horizontal(id="main-container"):
            self.basket_pane = BasketPane(self.todo_data)
            self.basket_pane.id = "basket-pane"
            yield self.basket_pane

            self.task_tree = TaskTree("Inbox", self.todo_data, todo_app=self)
            self.task_tree.id = "task-pane"
            yield self.task_tree

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the app when mounted."""
        if self.task_tree:
            self.task_tree.refresh_tasks()
        self._update_panel_focus()

    def save_to_history(self) -> None:
        """Save current state to undo history."""
        # Store a deep copy of the current state
        state = self.todo_data.to_dict()
        self.history.append(state)

        # Limit history size
        if len(self.history) > self.max_history:
            self.history.pop(0)

    def save_data(self) -> None:
        """Save current data to disk."""
        self.storage.save(self.todo_data)
        if self.basket_pane:
            self.basket_pane.refresh_baskets()

    def action_undo(self) -> None:
        """Undo the last action."""
        if not self.history:
            self.notify("Nothing to undo", severity="warning", timeout=2)
            return

        # Restore the last state
        last_state = self.history.pop()
        self.todo_data = TodoData.from_dict(last_state)

        # Clear recently completed tracking since state has changed
        self.recently_completed.clear()

        self.save_data()
        if self.task_tree:
            self.task_tree.todo_data = self.todo_data
            self.task_tree.refresh_tasks()
        if self.basket_pane:
            self.basket_pane.todo_data = self.todo_data
            self.basket_pane.refresh_baskets()

        # Show remaining undo steps
        remaining = len(self.history)
        if remaining == 0:
            self.notify("Undone (no more history)", timeout=2)
        else:
            self.notify(f"Undone ({remaining} steps remaining)", timeout=2)

    def on_task_tree_task_edited(self, message: TaskTree.TaskEdited) -> None:
        """Handle task edit completion from inline editor."""
        task = self.todo_data.find_task(message.task_id)
        if task and message.new_title != task.title:
            self.save_to_history()
            task.title = message.new_title
            self.save_data()
            if self.task_tree:
                self.task_tree.refresh_tasks()

    def on_task_tree_task_created(self, message: TaskTree.TaskCreated) -> None:
        """Handle task creation completion from inline editor."""
        self.save_to_history()
        task = Task(title=message.title)
        basket = self.basket_pane.selected_basket if self.basket_pane else "Inbox"

        # If basket is empty or no task selected, add to root
        if not self.task_tree or not self.task_tree.flat_list:
            self.todo_data.add_task(basket, task)
        else:
            # Get current task and insert new task below it at same level
            current_idx = self.task_tree.selected_index
            if current_idx < len(self.task_tree.flat_list):
                current_task, current_level = self.task_tree.flat_list[current_idx]
                location = self.todo_data.find_task_location(current_task.id)
                if location:
                    _, parent_id = location

                    if parent_id:
                        # Task is nested - insert in parent's children
                        parent = self.todo_data.find_task(parent_id)
                        if parent:
                            try:
                                idx = parent.children.index(current_task)
                                parent.children.insert(idx + 1, task)
                                self.todo_data._add_to_index(task)
                            except ValueError:
                                parent.add_child(task)
                                self.todo_data._add_to_index(task)
                    else:
                        # Task is at root - insert in basket
                        try:
                            idx = self.todo_data.baskets[basket].index(current_task)
                            self.todo_data.baskets[basket].insert(idx + 1, task)
                            self.todo_data._add_to_index(task)
                        except ValueError:
                            self.todo_data.baskets[basket].append(task)
                            self.todo_data._add_to_index(task)
            else:
                # Add to root
                self.todo_data.add_task(basket, task)

        self.save_data()
        if self.task_tree:
            self.task_tree.refresh_tasks()
            # Focus the newly created task
            self._focus_task_by_id(task.id)

    def action_add_task(self) -> None:
        """Add a new task below the current one at the same nesting level (inline editing)."""
        if self.task_tree:
            # Calculate position and level for new task
            if self.task_tree.flat_list:
                idx = self.task_tree.selected_index + 1
                # Get the level of the current task
                _, current_level = self.task_tree.flat_list[self.task_tree.selected_index]
                level = current_level
            else:
                idx = 0
                level = 0
            self.task_tree.start_create_task(at_index=idx, level=level)

    def action_edit_task(self) -> None:
        """Edit the selected task (inline editing)."""
        if not self.task_tree:
            return

        task = self.task_tree.get_selected_task()
        if not task:
            return

        self.task_tree.start_edit_task(task.id, task.title)

    def action_toggle_complete(self) -> None:
        """Toggle completion of selected task."""
        if self.task_tree:
            task = self.task_tree.get_selected_task()
            if not task:
                return

            self.save_to_history()
            was_completed = task.completed

            # Track completion time BEFORE toggling (so refresh_tasks can see it)
            if not was_completed:
                # About to complete the task - add to tracking NOW
                self.recently_completed[task.id] = time.time()
                # Schedule refresh after 5 seconds
                self.set_timer(5.0, lambda: self._cleanup_completed_task(task.id))
            elif was_completed:
                # About to uncomplete the task - remove from tracking
                self.recently_completed.pop(task.id, None)

            # Now toggle (this calls refresh_tasks internally)
            self.task_tree.toggle_completion()

            self.save_data()

    def action_delete_task(self) -> None:
        """Delete the selected task."""
        if not self.task_tree:
            return

        task = self.task_tree.get_selected_task()
        if task:
            self.save_to_history()
            self.todo_data.delete_task(task.id)
            self.save_data()
            self.task_tree.refresh_tasks()
            # Adjust selection if now out of bounds (deleted last task)
            max_idx = len(self.task_tree.flat_list) - 1
            if self.task_tree.selected_index > max_idx:
                self.task_tree.selected_index = max(0, max_idx)
                self.task_tree._render_tasks()

    def action_move_task(self) -> None:
        """Move task to a different basket."""
        if not self.task_tree:
            return

        task = self.task_tree.get_selected_task()
        if not task:
            return

        def handle_result(basket: str) -> None:
            if basket:
                self.save_to_history()
                self.todo_data.move_task(task.id, basket)
                self.save_data()
                if self.task_tree:
                    # Refresh to rebuild flat_list, then adjust selection if out of bounds
                    self.task_tree.refresh_tasks()
                    max_idx = len(self.task_tree.flat_list) - 1
                    if self.task_tree.selected_index > max_idx:
                        self.task_tree.selected_index = max(0, max_idx)
                        self.task_tree._render_tasks()

        self.push_screen(BasketSelectorDialog(), handle_result)

    def action_navigate_up(self) -> None:
        """Navigate up in current panel."""
        if self.focused_panel == "baskets" and self.basket_pane:
            self.basket_pane.select_previous()
            self._switch_basket()
        elif self.focused_panel == "tasks" and self.task_tree:
            self.task_tree.move_selection(-1)

    def action_navigate_down(self) -> None:
        """Navigate down in current panel."""
        if self.focused_panel == "baskets" and self.basket_pane:
            self.basket_pane.select_next()
            self._switch_basket()
        elif self.focused_panel == "tasks" and self.task_tree:
            self.task_tree.move_selection(1)

    def action_collapse_task(self) -> None:
        """Collapse task."""
        if self.focused_panel == "tasks" and self.task_tree:
            task = self.task_tree.get_selected_task()
            if task and task.children and not task.collapsed:
                self.save_to_history()
                self.task_tree.toggle_collapse()
                self.save_data()

    def action_expand_task(self) -> None:
        """Expand task."""
        if self.focused_panel == "tasks" and self.task_tree:
            task = self.task_tree.get_selected_task()
            if task and task.children and task.collapsed:
                self.save_to_history()
                self.task_tree.toggle_collapse()
                self.save_data()

    def _collapse_recursive(self, task: Task) -> None:
        """Recursively collapse a task and all its children."""
        if task.children:
            task.collapsed = True
            for child in task.children:
                self._collapse_recursive(child)

    def _expand_recursive(self, task: Task) -> None:
        """Recursively expand a task and all its children."""
        if task.children:
            task.collapsed = False
            for child in task.children:
                self._expand_recursive(child)

    def action_collapse_all(self) -> None:
        """Collapse task and all nested children (Shift+A)."""
        if self.focused_panel == "tasks" and self.task_tree:
            task = self.task_tree.get_selected_task()
            if task and task.children:
                self.save_to_history()
                self._collapse_recursive(task)
                self.task_tree.refresh_tasks()
                self.save_data()

    def action_expand_all(self) -> None:
        """Expand task and all nested children (Shift+D)."""
        if self.focused_panel == "tasks" and self.task_tree:
            task = self.task_tree.get_selected_task()
            if task and task.children:
                self.save_to_history()
                self._expand_recursive(task)
                self.task_tree.refresh_tasks()
                self.save_data()

    def action_switch_to_baskets(self) -> None:
        """Switch focus to baskets panel."""
        self.focused_panel = "baskets"
        self._update_panel_focus()

    def action_switch_to_tasks(self) -> None:
        """Switch focus to tasks panel."""
        self.focused_panel = "tasks"
        self._update_panel_focus()

    def _update_panel_focus(self) -> None:
        """Update visual focus state of panels."""
        if self.basket_pane and self.task_tree:
            if self.focused_panel == "baskets":
                self.basket_pane.add_class("focused")
                self.task_tree.remove_class("focused")
            else:
                self.basket_pane.remove_class("focused")
                self.task_tree.add_class("focused")

    def action_toggle_show_completed(self) -> None:
        """Toggle showing completed tasks."""
        if self.task_tree:
            self.task_tree.toggle_show_completed()
            # Toggle CSS class for task pane border color
            if self.task_tree.show_completed:
                self.task_tree.add_class("show-completed-mode")
            else:
                self.task_tree.remove_class("show-completed-mode")
        if self.basket_pane:
            self.basket_pane.show_completed_mode = not self.basket_pane.show_completed_mode
            self.basket_pane.refresh_baskets()

    def action_nest_task(self) -> None:
        """Nest task under previous sibling (Tab key)."""
        if not self.task_tree or not self.task_tree.flat_list or self.focused_panel != "tasks":
            return

        idx = self.task_tree.selected_index
        if idx <= 0:
            return

        current_task, current_level = self.task_tree.flat_list[idx]

        # Find previous sibling (task at same level)
        for i in range(idx - 1, -1, -1):
            prev_task, prev_level = self.task_tree.flat_list[i]
            if prev_level == current_level:
                location = self.todo_data.find_task_location(current_task.id)
                if location:
                    self.save_to_history()
                    basket, parent_id = location

                    # Remove from current location
                    if parent_id:
                        parent = self.todo_data.find_task(parent_id)
                        if parent:
                            parent.remove_child(current_task.id)
                    else:
                        self.todo_data.baskets[basket] = [
                            t for t in self.todo_data.baskets[basket] if t.id != current_task.id
                        ]

                    # Add as child of previous sibling (children move with it)
                    prev_task.add_child(current_task)
                    prev_task.collapsed = False  # Expand to show new child

                    self.save_data()
                    self.task_tree.refresh_tasks()
                break

    def action_unnest_task(self) -> None:
        """Unnest task one level up (Shift+Tab key)."""
        if not self.task_tree or not self.task_tree.flat_list or self.focused_panel != "tasks":
            return

        idx = self.task_tree.selected_index
        if idx < 0 or idx >= len(self.task_tree.flat_list):
            return

        current_task, current_level = self.task_tree.flat_list[idx]

        if current_level == 0:
            return  # Already at root level

        location = self.todo_data.find_task_location(current_task.id)
        if not location:
            return

        basket, parent_id = location
        if not parent_id:
            return  # Already at root

        parent = self.todo_data.find_task(parent_id)
        if not parent:
            return

        self.save_to_history()

        # Remove from parent (children stay with the task)
        parent.remove_child(current_task.id)

        # Find grandparent
        grandparent_location = self.todo_data.find_task_location(parent.id)
        if not grandparent_location:
            return

        gp_basket, gp_parent_id = grandparent_location

        # Add as sibling of parent
        if gp_parent_id:
            grandparent = self.todo_data.find_task(gp_parent_id)
            if grandparent:
                try:
                    parent_idx = grandparent.children.index(parent)
                    grandparent.children.insert(parent_idx + 1, current_task)
                except ValueError:
                    grandparent.add_child(current_task)
        else:
            try:
                parent_idx = self.todo_data.baskets[gp_basket].index(parent)
                self.todo_data.baskets[gp_basket].insert(parent_idx + 1, current_task)
            except ValueError:
                self.todo_data.baskets[gp_basket].append(current_task)

        self.save_data()
        self.task_tree.refresh_tasks()

        # Maintain focus on the unnested task
        self._focus_task_by_id(current_task.id)

    def _focus_task_by_id(self, task_id: str) -> None:
        """Find a task by ID in flat_list and update selection index (without refreshing)."""
        if not self.task_tree:
            return

        for i, (task, level) in enumerate(self.task_tree.flat_list):
            if task.id == task_id:
                self.task_tree.selected_index = i
                self.task_tree._render_tasks()  # Re-render to show selection
                return

    def action_move_task_up(self) -> None:
        """Move task up in the list (w key)."""
        if not self.task_tree or not self.task_tree.flat_list or self.focused_panel != "tasks":
            return

        idx = self.task_tree.selected_index
        if idx <= 0:
            return

        current_task, current_level = self.task_tree.flat_list[idx]
        location = self.todo_data.find_task_location(current_task.id)
        if not location:
            return

        basket, parent_id = location

        if parent_id:
            # Task is nested - swap with previous sibling in parent's children
            parent = self.todo_data.find_task(parent_id)
            if not parent:
                return

            try:
                task_idx = parent.children.index(current_task)
                if task_idx > 0:
                    self.save_to_history()
                    task_id = current_task.id
                    # Swap with previous sibling
                    parent.children[task_idx], parent.children[task_idx - 1] = \
                        parent.children[task_idx - 1], parent.children[task_idx]
                    self.save_data()
                    self.task_tree.refresh_tasks()
                    # Focus the moved task by ID (handles children correctly)
                    self._focus_task_by_id(task_id)
                else:
                    # At top of parent's children - unnest but maintain focus
                    task_id = current_task.id
                    self.action_unnest_task()
                    self._focus_task_by_id(task_id)
            except ValueError:
                return
        else:
            # Task is at root level - swap in basket
            try:
                task_idx = self.todo_data.baskets[basket].index(current_task)
                if task_idx > 0:
                    self.save_to_history()
                    task_id = current_task.id
                    # Swap with previous sibling
                    self.todo_data.baskets[basket][task_idx], self.todo_data.baskets[basket][task_idx - 1] = \
                        self.todo_data.baskets[basket][task_idx - 1], self.todo_data.baskets[basket][task_idx]
                    self.save_data()
                    self.task_tree.refresh_tasks()
                    # Focus the moved task by ID (handles children correctly)
                    self._focus_task_by_id(task_id)
            except (ValueError, IndexError):
                return

    def action_move_task_down(self) -> None:
        """Move task down in the list (s key)."""
        if not self.task_tree or not self.task_tree.flat_list or self.focused_panel != "tasks":
            return

        idx = self.task_tree.selected_index
        if idx >= len(self.task_tree.flat_list) - 1:
            return

        current_task, current_level = self.task_tree.flat_list[idx]
        location = self.todo_data.find_task_location(current_task.id)
        if not location:
            return

        basket, parent_id = location

        if parent_id:
            # Task is nested - swap with next sibling in parent's children
            parent = self.todo_data.find_task(parent_id)
            if not parent:
                return

            try:
                task_idx = parent.children.index(current_task)
                if task_idx < len(parent.children) - 1:
                    self.save_to_history()
                    task_id = current_task.id
                    # Swap with next sibling
                    parent.children[task_idx], parent.children[task_idx + 1] = \
                        parent.children[task_idx + 1], parent.children[task_idx]
                    self.save_data()
                    self.task_tree.refresh_tasks()
                    # Focus the moved task by ID (handles children correctly)
                    self._focus_task_by_id(task_id)
                else:
                    # At bottom of parent's children - unnest but maintain focus
                    task_id = current_task.id
                    self.action_unnest_task()
                    self._focus_task_by_id(task_id)
            except ValueError:
                return
        else:
            # Task is at root level - swap in basket
            try:
                task_idx = self.todo_data.baskets[basket].index(current_task)
                if task_idx < len(self.todo_data.baskets[basket]) - 1:
                    self.save_to_history()
                    task_id = current_task.id
                    # Swap with next sibling
                    self.todo_data.baskets[basket][task_idx], self.todo_data.baskets[basket][task_idx + 1] = \
                        self.todo_data.baskets[basket][task_idx + 1], self.todo_data.baskets[basket][task_idx]
                    self.save_data()
                    self.task_tree.refresh_tasks()
                    # Focus the moved task by ID (handles children correctly)
                    self._focus_task_by_id(task_id)
            except (ValueError, IndexError):
                return

    def action_show_help(self) -> None:
        """Show help screen."""
        help_text = """
[bold]TLTD - Terminal Todo List[/bold]

[bold underline]Panel Switching:[/bold underline]
  ←/→         Switch between baskets and tasks panels

[bold underline]Navigation:[/bold underline]
  ↑/↓         Navigate up/down in current panel
              (In baskets: switch basket; In tasks: move between tasks)

[bold underline]Task Actions:[/bold underline]
  c           Create new task below current (inline editor, same nesting level)
  Enter       Edit selected task (inline editor)
  x           Toggle task completion (✓/☐)
  Backspace   Delete task and all children
  f           Move task to different basket
  z           Toggle show completed tasks
  Esc         Cancel inline editing

[bold underline]Collapsing:[/bold underline]
  a           Collapse task (hide children)
  d           Expand task (show children)
  Shift+a     Collapse task and all nested children
  Shift+d     Expand task and all nested children
  [dim]When collapsed, shows child count like: Task (3)[/dim]

[bold underline]Nesting (children move with task):[/bold underline]
  e           Nest task under previous sibling
  q           Unnest task one level up

[bold underline]Reordering:[/bold underline]
  w           Move task up in list
  s           Move task down in list
  [dim]Maintains nesting level intelligently[/dim]

[bold underline]Undo:[/bold underline]
  \\          Undo last action (up to 50 actions)

[bold underline]Quick Basket Jump:[/bold underline]
  `           Inbox
  1-7         Monday through Sunday
  0           Later

[bold underline]Application:[/bold underline]
  Esc         Quit application
  ?           Show this help

[dim]Data stored in: ~/.tltd/tasks.json[/dim]
"""

        class HelpScreen(ModalScreen[None]):
            def compose(self) -> ComposeResult:
                with Container(id="help-container"):
                    yield Label(help_text, id="help-text")
                    yield Button("Close", variant="primary", id="close-btn")

            def on_button_pressed(self, event: Button.Pressed) -> None:
                self.dismiss()

            def on_key(self, event) -> None:
                """Handle key presses."""
                if event.key == "escape":
                    self.dismiss()
                    event.stop()  # Prevent ESC from reaching TodoApp quit binding

        self.push_screen(HelpScreen())

    def _cleanup_completed_task(self, task_id: str) -> None:
        """Remove a task from recently_completed and refresh the view."""
        self.recently_completed.pop(task_id, None)
        if self.task_tree:
            self.task_tree.refresh_tasks()

    def _switch_basket(self) -> None:
        """Switch to the selected basket."""
        if self.basket_pane and self.task_tree:
            self.task_tree.basket = self.basket_pane.selected_basket
            self.task_tree.border_title = self.basket_pane.selected_basket
            self.task_tree.selected_index = 0
            self.task_tree.refresh_tasks()

    def _jump_to_basket(self, basket_name: str) -> None:
        """Jump directly to a specific basket."""
        if self.basket_pane and self.task_tree:
            self.basket_pane.selected_basket = basket_name
            self.basket_pane.refresh_baskets()
            self._switch_basket()
            # Switch focus to tasks panel
            self.focused_panel = "tasks"
            self._update_panel_focus()

    def action_jump_inbox(self) -> None:
        """Jump to Inbox basket."""
        self._jump_to_basket("Inbox")

    def action_jump_monday(self) -> None:
        """Jump to Monday basket."""
        self._jump_to_basket("Monday")

    def action_jump_tuesday(self) -> None:
        """Jump to Tuesday basket."""
        self._jump_to_basket("Tuesday")

    def action_jump_wednesday(self) -> None:
        """Jump to Wednesday basket."""
        self._jump_to_basket("Wednesday")

    def action_jump_thursday(self) -> None:
        """Jump to Thursday basket."""
        self._jump_to_basket("Thursday")

    def action_jump_friday(self) -> None:
        """Jump to Friday basket."""
        self._jump_to_basket("Friday")

    def action_jump_saturday(self) -> None:
        """Jump to Saturday basket."""
        self._jump_to_basket("Saturday")

    def action_jump_sunday(self) -> None:
        """Jump to Sunday basket."""
        self._jump_to_basket("Sunday")

    def action_jump_later(self) -> None:
        """Jump to Later basket."""
        self._jump_to_basket("Later")
