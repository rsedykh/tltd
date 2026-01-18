"""Main UI application using Textual."""
from __future__ import annotations

import time
from typing import Optional, List, Dict, Any, Tuple
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Footer
from textual.binding import Binding

from .models import TodoData, Task
from .storage import StorageManager
from .styles import CSS
from .widgets import TaskTree, BasketPane
from .dialogs import BasketSelectorDialog, DescriptionEditorDialog, HelpScreen


class TodoApp(App):
    """Main todo application."""

    CSS = CSS

    BINDINGS = [
        Binding("c", "add_task", "Create", show=True),
        Binding("C", "add_task_to_inbox", "Create in Inbox", show=False),
        Binding("enter", "edit_task", "Edit", show=True),
        Binding("v", "edit_description", "Description", show=True),
        Binding("x", "toggle_complete", "✓ Done", show=True),
        Binding("backspace", "delete_task", "Delete", show=True),
        Binding("r", "move_task", "Move to Basket", show=True),
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
        Binding("b", "toggle_mark", "Mark", show=True),
        Binding("backslash", "undo", "Undo", show=True),
        Binding("?", "show_help", "Help", show=True),
        Binding("escape", "escape_action", "Clear Marks", show=False),
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
        Binding("м", "edit_description", "Description", show=False),  # v
        Binding("с", "add_task", "Create", show=False),  # c
        Binding("С", "add_task_to_inbox", "Create in Inbox", show=False),  # C (Shift+c)
        Binding("ч", "toggle_complete", "Done", show=False),  # x
        Binding("к", "move_task", "Move", show=False),  # r
        Binding("ф", "collapse_task", "Collapse", show=False),  # a
        Binding("в", "expand_task", "Expand", show=False),  # d
        Binding("Ф", "collapse_all", "Collapse All", show=False),  # A (Shift+a)
        Binding("В", "expand_all", "Expand All", show=False),  # D (Shift+d)
        Binding("ц", "move_task_up", "Up", show=False),  # w
        Binding("ы", "move_task_down", "Down", show=False),  # s
        Binding("у", "nest_task", "Nest", show=False),  # e
        Binding("й", "unnest_task", "Unnest", show=False),  # q
        Binding("я", "toggle_show_completed", "Show Done", show=False),  # z
        Binding("и", "toggle_mark", "Mark", show=False),  # b
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

    def action_add_task_to_inbox(self) -> None:
        """Add a new task to Inbox regardless of current basket."""
        if self.task_tree and self.basket_pane:
            # Switch to Inbox
            self.basket_pane.selected_basket = "Inbox"
            self.basket_pane.refresh_baskets()
            self._switch_basket()
            self.focused_panel = "tasks"
            self._update_panel_focus()
            # Find the last root-level task to insert after it
            last_root_idx = -1
            for i, (task, level) in enumerate(self.task_tree.flat_list):
                if level == 0:
                    last_root_idx = i
            if last_root_idx >= 0:
                # Select the last root task, then create after it
                self.task_tree.selected_index = last_root_idx
                self.task_tree.start_create_task(at_index=last_root_idx + 1, level=0)
            else:
                # Empty basket - just create at root
                self.task_tree.start_create_task(at_index=0, level=0)

    def action_edit_task(self) -> None:
        """Edit the selected task (inline editing)."""
        if not self.task_tree:
            return

        task = self.task_tree.get_selected_task()
        if not task:
            return

        self.task_tree.start_edit_task(task.id, task.title)

    MAX_TITLE_LENGTH = 512
    MAX_DESCRIPTION_LENGTH = 4096
    MAX_NESTING_DEPTH = 8

    def action_edit_description(self) -> None:
        """Edit the title and description of the selected task."""
        if not self.task_tree:
            return

        task = self.task_tree.get_selected_task()
        if not task:
            return

        def handle_result(result: Optional[Tuple[str, str]]) -> None:
            if result is not None:  # None means cancelled
                new_title, new_description = result
                if len(new_description) > self.MAX_DESCRIPTION_LENGTH:
                    self.notify(
                        f"Description too long (max {self.MAX_DESCRIPTION_LENGTH} chars)",
                        severity="warning",
                        timeout=3
                    )
                    return
                # Only save if something changed
                if new_title != task.title or new_description != task.description:
                    self.save_to_history()
                    task.title = new_title
                    task.description = new_description
                    self.save_data()
                    if self.task_tree:
                        self.task_tree.refresh_tasks()

        self.push_screen(
            DescriptionEditorDialog(task.title, task.description),
            handle_result
        )

    def action_toggle_complete(self) -> None:
        """Toggle completion of selected task(s)."""
        if not self.task_tree:
            return

        marked_tasks = self.task_tree.get_marked_tasks()
        if marked_tasks:
            # Bulk complete
            self.save_to_history()
            for task in marked_tasks:
                if not task.completed:
                    self.recently_completed[task.id] = time.time()
                    task_id = task.id
                    self.set_timer(5.0, lambda tid=task_id: self._cleanup_completed_task(tid))
                else:
                    self.recently_completed.pop(task.id, None)
                task.completed = not task.completed
            self.task_tree.clear_marks()
            self.save_data()
            self.task_tree.refresh_tasks()
        else:
            # Single task completion
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
            else:
                # About to uncomplete the task - remove from tracking
                self.recently_completed.pop(task.id, None)

            # Now toggle (this calls refresh_tasks internally)
            self.task_tree.toggle_completion()

            self.save_data()

    def action_delete_task(self) -> None:
        """Delete the selected task(s)."""
        if not self.task_tree:
            return

        marked_tasks = self.task_tree.get_marked_tasks()
        if marked_tasks:
            # Bulk delete
            self.save_to_history()
            task_ids = [t.id for t in marked_tasks]
            for task_id in task_ids:
                self.todo_data.delete_task(task_id)
            self.task_tree.clear_marks()
            self.save_data()
            self.task_tree.refresh_tasks()
            # Handle empty basket
            if not self.task_tree.flat_list:
                self.focused_panel = "baskets"
                self._update_panel_focus()
            # Adjust selection if now out of bounds
            max_idx = len(self.task_tree.flat_list) - 1
            if self.task_tree.selected_index > max_idx:
                self.task_tree.selected_index = max(0, max_idx)
                self.task_tree._render_tasks()
        else:
            # Single task deletion
            task = self.task_tree.get_selected_task()
            if task:
                self.save_to_history()
                self.todo_data.delete_task(task.id)
                self.save_data()
                self.task_tree.refresh_tasks()
                # If basket is now empty, switch focus to baskets panel
                if not self.task_tree.flat_list:
                    self.focused_panel = "baskets"
                    self._update_panel_focus()
                # Adjust selection if now out of bounds (deleted last task)
                max_idx = len(self.task_tree.flat_list) - 1
                if self.task_tree.selected_index > max_idx:
                    self.task_tree.selected_index = max(0, max_idx)
                    self.task_tree._render_tasks()

    def action_move_task(self) -> None:
        """Move task(s) to a different basket."""
        if not self.task_tree:
            return

        marked_tasks = self.task_tree.get_marked_tasks()
        tasks_to_move = marked_tasks if marked_tasks else [self.task_tree.get_selected_task()]

        if not tasks_to_move or not tasks_to_move[0]:
            return

        def handle_result(basket: str) -> None:
            if basket:
                self.save_to_history()
                for task in tasks_to_move:
                    self.todo_data.move_task(task.id, basket)
                if marked_tasks and self.task_tree:
                    self.task_tree.clear_marks()
                self.save_data()
                if self.task_tree:
                    # Refresh to rebuild flat_list, then adjust selection if out of bounds
                    self.task_tree.refresh_tasks()
                    # If basket is now empty, switch focus to baskets panel
                    if not self.task_tree.flat_list:
                        self.focused_panel = "baskets"
                        self._update_panel_focus()
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
        """Collapse task, or if no children/already collapsed, collapse parent and focus on it."""
        if self.focused_panel == "tasks" and self.task_tree:
            task = self.task_tree.get_selected_task()
            if not task:
                return

            # If task has children and is not collapsed, collapse it
            if task.children and not task.collapsed:
                self.save_to_history()
                self.task_tree.toggle_collapse()
                self.save_data()
            else:
                # Task has no children or is already collapsed - collapse parent instead
                location = self.todo_data.find_task_location(task.id)
                if location:
                    _, parent_id = location
                    if parent_id:
                        parent_task = self.todo_data.find_task(parent_id)
                        if parent_task and not parent_task.collapsed:
                            self.save_to_history()
                            parent_task.collapsed = True
                            self.task_tree.refresh_tasks()
                            self._focus_task_by_id(parent_id)
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

    def action_toggle_mark(self) -> None:
        """Toggle mark on current task."""
        if self.focused_panel != "tasks" or not self.task_tree:
            return
        task = self.task_tree.get_selected_task()
        if task:
            self.task_tree.toggle_mark(task.id)

    def action_escape_action(self) -> None:
        """Clear marks if any."""
        if self.task_tree and self.task_tree.marked_task_ids:
            self.task_tree.clear_marks()

    def action_nest_task(self) -> None:
        """Nest task under previous sibling (Tab key)."""
        if not self.task_tree or not self.task_tree.flat_list or self.focused_panel != "tasks":
            return

        idx = self.task_tree.selected_index
        if idx <= 0:
            return

        current_task, current_level = self.task_tree.flat_list[idx]

        # Check nesting depth limit
        if current_level >= self.MAX_NESTING_DEPTH - 1:
            self.notify(f"Maximum nesting depth ({self.MAX_NESTING_DEPTH}) reached", severity="warning", timeout=2)
            return

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
        self.push_screen(HelpScreen())

    def _cleanup_completed_task(self, task_id: str) -> None:
        """Remove a task from recently_completed and refresh the view."""
        self.recently_completed.pop(task_id, None)
        if self.task_tree:
            self.task_tree.refresh_tasks()

    def _switch_basket(self) -> None:
        """Switch to the selected basket."""
        if self.basket_pane and self.task_tree:
            # Clear marks when switching baskets
            self.task_tree.marked_task_ids.clear()
            self.task_tree.basket = self.basket_pane.selected_basket
            self.task_tree.border_title = self.basket_pane.selected_basket
            self.task_tree.selected_index = 0
            self.task_tree.refresh_tasks()

    def _jump_to_basket(self, basket_name: str) -> None:
        """Jump to basket, or move selected/marked tasks if tasks panel is focused."""
        if not self.basket_pane or not self.task_tree:
            return

        # If tasks panel focused, move task(s) to basket
        if self.focused_panel == "tasks":
            marked_tasks = self.task_tree.get_marked_tasks()
            tasks_to_move = marked_tasks if marked_tasks else [self.task_tree.get_selected_task()]

            if tasks_to_move and tasks_to_move[0]:
                current_basket = self.basket_pane.selected_basket
                if current_basket == basket_name:
                    self.notify(f"Already in {basket_name}", timeout=1)
                    return

                self.save_to_history()
                for task in tasks_to_move:
                    self.todo_data.move_task(task.id, basket_name)

                if marked_tasks:
                    self.task_tree.clear_marks()

                self.save_data()
                self.task_tree.refresh_tasks()

                # Handle empty basket after move
                if not self.task_tree.flat_list:
                    self.focused_panel = "baskets"
                    self._update_panel_focus()

                # Adjust selection if out of bounds
                max_idx = len(self.task_tree.flat_list) - 1
                if self.task_tree.selected_index > max_idx:
                    self.task_tree.selected_index = max(0, max_idx)
                    self.task_tree._render_tasks()

                count = len(tasks_to_move)
                if count == 1:
                    self.notify(f"Moved to {basket_name}", timeout=1)
                else:
                    self.notify(f"Moved {count} tasks to {basket_name}", timeout=1)
                return

        # Otherwise, jump to basket (original behavior)
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
