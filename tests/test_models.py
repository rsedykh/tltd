"""Tests for the data models."""
import pytest
from src.models import Task, TodoData


class TestTask:
    """Tests for the Task class."""

    def test_task_creation(self):
        """Test creating a new task."""
        task = Task(title="Test Task")
        assert task.title == "Test Task"
        assert task.completed is False
        assert task.collapsed is False
        assert len(task.children) == 0
        assert task.id is not None
        assert task.created_at is not None

    def test_task_with_children(self):
        """Test task with child tasks."""
        parent = Task(title="Parent")
        child = Task(title="Child")
        parent.add_child(child)

        assert len(parent.children) == 1
        assert parent.children[0].title == "Child"

    def test_find_task(self):
        """Test finding a task by ID."""
        parent = Task(title="Parent")
        child = Task(title="Child")
        parent.add_child(child)

        found = parent.find_task(child.id)
        assert found is not None
        assert found.title == "Child"

    def test_find_parent(self):
        """Test finding parent of a task."""
        parent = Task(title="Parent")
        child = Task(title="Child")
        parent.add_child(child)

        found_parent = parent.find_parent(child.id)
        assert found_parent is not None
        assert found_parent.title == "Parent"

    def test_remove_child(self):
        """Test removing a child task."""
        parent = Task(title="Parent")
        child = Task(title="Child")
        parent.add_child(child)

        result = parent.remove_child(child.id)
        assert result is True
        assert len(parent.children) == 0

    def test_to_dict(self):
        """Test serializing task to dictionary."""
        task = Task(title="Test", completed=True)
        data = task.to_dict()

        assert data['title'] == "Test"
        assert data['completed'] is True
        assert 'id' in data
        assert 'children' in data

    def test_from_dict(self):
        """Test deserializing task from dictionary."""
        data = {
            'id': 'test-id',
            'title': 'Test Task',
            'completed': False,
            'collapsed': False,
            'children': [],
            'created_at': '2024-01-01T00:00:00'
        }

        task = Task.from_dict(data)
        assert task.id == 'test-id'
        assert task.title == 'Test Task'
        assert task.completed is False


class TestTodoData:
    """Tests for the TodoData class."""

    def test_tododata_creation(self):
        """Test creating a new TodoData instance."""
        todo_data = TodoData()
        assert len(todo_data.baskets) == len(TodoData.BASKETS)
        for basket in TodoData.BASKETS:
            assert basket in todo_data.baskets
            assert todo_data.baskets[basket] == []

    def test_add_task_to_basket(self):
        """Test adding a task to a basket."""
        todo_data = TodoData()
        task = Task(title="Test Task")

        result = todo_data.add_task("Inbox", task)
        assert result is True
        assert len(todo_data.baskets["Inbox"]) == 1
        assert todo_data.baskets["Inbox"][0].title == "Test Task"

    def test_find_task(self):
        """Test finding a task across all baskets."""
        todo_data = TodoData()
        task = Task(title="Test Task")
        todo_data.add_task("Inbox", task)

        found = todo_data.find_task(task.id)
        assert found is not None
        assert found.title == "Test Task"

    def test_find_task_location(self):
        """Test finding the location of a task."""
        todo_data = TodoData()
        task = Task(title="Test Task")
        todo_data.add_task("Monday", task)

        location = todo_data.find_task_location(task.id)
        assert location is not None
        assert location[0] == "Monday"
        assert location[1] is None  # No parent

    def test_move_task(self):
        """Test moving a task between baskets."""
        todo_data = TodoData()
        task = Task(title="Test Task")
        todo_data.add_task("Inbox", task)

        result = todo_data.move_task(task.id, "Monday")
        assert result is True
        assert len(todo_data.baskets["Inbox"]) == 0
        assert len(todo_data.baskets["Monday"]) == 1

    def test_delete_task(self):
        """Test deleting a task."""
        todo_data = TodoData()
        task = Task(title="Test Task")
        todo_data.add_task("Inbox", task)

        result = todo_data.delete_task(task.id)
        assert result is True
        assert len(todo_data.baskets["Inbox"]) == 0

    def test_get_basket_count(self):
        """Test counting tasks in a basket."""
        todo_data = TodoData()
        task1 = Task(title="Task 1")
        task2 = Task(title="Task 2")
        todo_data.add_task("Inbox", task1)
        todo_data.add_task("Inbox", task2)

        count = todo_data.get_basket_count("Inbox")
        assert count == 2

    def test_to_dict(self):
        """Test serializing TodoData to dictionary."""
        todo_data = TodoData()
        task = Task(title="Test Task")
        todo_data.add_task("Inbox", task)

        data = todo_data.to_dict()
        assert "Inbox" in data
        assert len(data["Inbox"]) == 1
        assert data["Inbox"][0]['title'] == "Test Task"

    def test_from_dict(self):
        """Test deserializing TodoData from dictionary."""
        data = {
            "Inbox": [
                {
                    'id': 'test-id',
                    'title': 'Test Task',
                    'completed': False,
                    'collapsed': False,
                    'children': [],
                    'created_at': '2024-01-01T00:00:00'
                }
            ],
            "Monday": []
        }

        todo_data = TodoData.from_dict(data)
        assert len(todo_data.baskets["Inbox"]) == 1
        assert todo_data.baskets["Inbox"][0].title == "Test Task"
