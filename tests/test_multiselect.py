"""Tests for multi-select (mark) functionality."""
from src.models import Task, TodoData, get_current_week_dates


class TestMultiSelectBasics:
    """Basic tests for multi-select state management."""

    def test_marked_task_ids_set_operations(self):
        """Test basic set operations on marked IDs."""
        marked_ids: set = set()

        # Add
        marked_ids.add("task-1")
        assert "task-1" in marked_ids
        assert len(marked_ids) == 1

        # Add more
        marked_ids.add("task-2")
        marked_ids.add("task-3")
        assert len(marked_ids) == 3

        # Toggle (remove if exists)
        if "task-2" in marked_ids:
            marked_ids.remove("task-2")
        assert "task-2" not in marked_ids
        assert len(marked_ids) == 2

        # Toggle (add if not exists)
        if "task-2" not in marked_ids:
            marked_ids.add("task-2")
        assert "task-2" in marked_ids

        # Clear
        marked_ids.clear()
        assert len(marked_ids) == 0

    def test_toggle_mark_logic(self):
        """Test the toggle mark logic (same as used in TaskTree.toggle_mark)."""
        marked_ids: set = set()

        def toggle_mark(task_id: str) -> None:
            if task_id in marked_ids:
                marked_ids.remove(task_id)
            else:
                marked_ids.add(task_id)

        # First toggle adds
        toggle_mark("task-1")
        assert "task-1" in marked_ids

        # Second toggle removes
        toggle_mark("task-1")
        assert "task-1" not in marked_ids

        # Third toggle adds again
        toggle_mark("task-1")
        assert "task-1" in marked_ids

    def test_is_marked(self):
        """Test is_marked check."""
        marked_ids: set = set()

        def is_marked(task_id: str) -> bool:
            return task_id in marked_ids

        assert is_marked("task-1") is False

        marked_ids.add("task-1")
        assert is_marked("task-1") is True
        assert is_marked("task-2") is False


class TestMultiSelectWithTodoData:
    """Tests for multi-select operations with TodoData."""

    def test_get_marked_tasks(self):
        """Test retrieving marked Task objects from TodoData."""
        todo_data = TodoData()
        task1 = Task(title="Task 1")
        task2 = Task(title="Task 2")
        task3 = Task(title="Task 3")
        todo_data.add_task("Inbox", task1)
        todo_data.add_task("Inbox", task2)
        todo_data.add_task("Inbox", task3)

        marked_ids = {task1.id, task3.id}

        # Simulate get_marked_tasks logic
        marked_tasks = []
        for task_id in marked_ids:
            task = todo_data.find_task(task_id)
            if task:
                marked_tasks.append(task)

        assert len(marked_tasks) == 2
        titles = {t.title for t in marked_tasks}
        assert "Task 1" in titles
        assert "Task 3" in titles
        assert "Task 2" not in titles

    def test_bulk_complete(self):
        """Test bulk completion of marked tasks."""
        todo_data = TodoData()
        task1 = Task(title="Task 1")
        task2 = Task(title="Task 2")
        task3 = Task(title="Task 3")
        todo_data.add_task("Inbox", task1)
        todo_data.add_task("Inbox", task2)
        todo_data.add_task("Inbox", task3)

        # Mark tasks 1 and 3
        marked_ids = {task1.id, task3.id}

        # Bulk complete
        for task_id in marked_ids:
            task = todo_data.find_task(task_id)
            if task:
                task.completed = not task.completed

        assert task1.completed is True
        assert task2.completed is False  # Not marked
        assert task3.completed is True

    def test_bulk_delete(self):
        """Test bulk deletion of marked tasks."""
        todo_data = TodoData()
        task1 = Task(title="Task 1")
        task2 = Task(title="Task 2")
        task3 = Task(title="Task 3")
        todo_data.add_task("Inbox", task1)
        todo_data.add_task("Inbox", task2)
        todo_data.add_task("Inbox", task3)

        # Mark tasks 1 and 3
        task_ids_to_delete = [task1.id, task3.id]

        # Bulk delete
        for task_id in task_ids_to_delete:
            todo_data.delete_task(task_id)

        # Only task2 should remain
        assert len(todo_data.baskets["Inbox"]) == 1
        assert todo_data.baskets["Inbox"][0].title == "Task 2"
        assert todo_data.find_task(task1.id) is None
        assert todo_data.find_task(task3.id) is None

    def test_bulk_move(self):
        """Test bulk moving of marked tasks."""
        todo_data = TodoData()
        task1 = Task(title="Task 1")
        task2 = Task(title="Task 2")
        task3 = Task(title="Task 3")
        todo_data.add_task("Inbox", task1)
        todo_data.add_task("Inbox", task2)
        todo_data.add_task("Inbox", task3)

        # Mark tasks 1 and 3
        task_ids_to_move = [task1.id, task3.id]

        # Get the current week's Monday date key
        monday_key = get_current_week_dates()[0]

        # Bulk move to Monday
        for task_id in task_ids_to_move:
            todo_data.move_task(task_id, monday_key)

        # Only task2 should remain in Inbox
        assert len(todo_data.baskets["Inbox"]) == 1
        assert todo_data.baskets["Inbox"][0].title == "Task 2"

        # Tasks 1 and 3 should be in Monday
        assert len(todo_data.baskets[monday_key]) == 2
        monday_titles = {t.title for t in todo_data.baskets[monday_key]}
        assert "Task 1" in monday_titles
        assert "Task 3" in monday_titles


class TestMultiSelectEdgeCases:
    """Edge case tests for multi-select."""

    def test_marks_for_nonexistent_tasks(self):
        """Test that marks for nonexistent tasks are gracefully handled."""
        todo_data = TodoData()
        task1 = Task(title="Task 1")
        todo_data.add_task("Inbox", task1)

        # Mark includes a nonexistent task ID
        marked_ids = {task1.id, "nonexistent-id"}

        # Get marked tasks should only return existing tasks
        marked_tasks = []
        for task_id in marked_ids:
            task = todo_data.find_task(task_id)
            if task:
                marked_tasks.append(task)

        assert len(marked_tasks) == 1
        assert marked_tasks[0].title == "Task 1"

    def test_marks_survive_task_modification(self):
        """Test that marks survive when tasks are modified (not deleted)."""
        todo_data = TodoData()
        task1 = Task(title="Task 1")
        todo_data.add_task("Inbox", task1)

        marked_ids = {task1.id}

        # Modify the task
        task1.title = "Modified Task 1"
        task1.completed = True

        # Mark should still be valid
        assert task1.id in marked_ids
        task = todo_data.find_task(task1.id)
        assert task is not None
        assert task.title == "Modified Task 1"

    def test_marks_cleared_manually(self):
        """Test marks can be cleared explicitly."""
        marked_ids = {"task-1", "task-2", "task-3"}
        assert len(marked_ids) == 3

        marked_ids.clear()
        assert len(marked_ids) == 0

    def test_bulk_operation_on_nested_tasks(self):
        """Test bulk operations on nested tasks."""
        todo_data = TodoData()
        parent = Task(title="Parent")
        child1 = Task(title="Child 1")
        child2 = Task(title="Child 2")
        parent.add_child(child1)
        parent.add_child(child2)
        todo_data.add_task("Inbox", parent)

        # Mark child tasks
        task_ids_to_complete = [child1.id, child2.id]

        # Bulk complete
        for task_id in task_ids_to_complete:
            task = todo_data.find_task(task_id)
            if task:
                task.completed = True

        assert parent.completed is False
        assert child1.completed is True
        assert child2.completed is True

    def test_undo_after_bulk_operation(self):
        """Test that bulk operations can be undone by restoring state."""
        todo_data = TodoData()
        task1 = Task(title="Task 1")
        task2 = Task(title="Task 2")
        todo_data.add_task("Inbox", task1)
        todo_data.add_task("Inbox", task2)

        # Save state before bulk operation
        saved_state = todo_data.to_dict()

        # Bulk delete
        todo_data.delete_task(task1.id)
        todo_data.delete_task(task2.id)

        assert len(todo_data.baskets["Inbox"]) == 0

        # Undo by restoring state
        todo_data = TodoData.from_dict(saved_state)

        assert len(todo_data.baskets["Inbox"]) == 2
        titles = {t.title for t in todo_data.baskets["Inbox"]}
        assert "Task 1" in titles
        assert "Task 2" in titles
