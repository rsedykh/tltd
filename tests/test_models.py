"""Tests for the data models."""
import pytest
from datetime import datetime, timedelta
from src.models import (
    Task, TodoData, FIXED_BASKETS, DAY_NAMES, LEGACY_DAY_BASKETS,
    get_current_week_dates, get_week_number, date_to_display_name,
    is_date_basket, get_current_week_monday
)


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


class TestWeekFunctions:
    """Tests for week-related helper functions."""

    def test_get_current_week_dates_returns_seven_dates(self):
        """Test that get_current_week_dates returns 7 dates."""
        dates = get_current_week_dates()
        assert len(dates) == 7

    def test_get_current_week_dates_format(self):
        """Test that dates are in YYYY-MM-DD format."""
        dates = get_current_week_dates()
        for date_str in dates:
            # Should be parseable as a date
            datetime.strptime(date_str, '%Y-%m-%d')

    def test_get_current_week_dates_starts_monday(self):
        """Test that the week starts on Monday."""
        dates = get_current_week_dates()
        first_date = datetime.strptime(dates[0], '%Y-%m-%d')
        assert first_date.weekday() == 0  # Monday

    def test_get_current_week_dates_consecutive(self):
        """Test that dates are consecutive."""
        dates = get_current_week_dates()
        for i in range(1, 7):
            prev = datetime.strptime(dates[i-1], '%Y-%m-%d')
            curr = datetime.strptime(dates[i], '%Y-%m-%d')
            assert (curr - prev).days == 1

    def test_get_week_number(self):
        """Test getting week number from a date."""
        # Use a known date
        week_num, year = get_week_number('2026-01-20')  # Should be week 4 of 2026
        assert isinstance(week_num, int)
        assert 1 <= week_num <= 53
        assert isinstance(year, int)

    def test_date_to_display_name(self):
        """Test converting date to day name."""
        # Monday
        dates = get_current_week_dates()
        assert date_to_display_name(dates[0]) == "Monday"
        assert date_to_display_name(dates[6]) == "Sunday"

    def test_is_date_basket(self):
        """Test date basket detection."""
        assert is_date_basket('2026-01-20') is True
        assert is_date_basket('Inbox') is False
        assert is_date_basket('Later') is False
        assert is_date_basket('Monday') is False
        assert is_date_basket('2026-1-20') is False  # Wrong format


class TestTodoData:
    """Tests for the TodoData class."""

    def test_tododata_creation(self):
        """Test creating a new TodoData instance."""
        todo_data = TodoData()
        # Should have Inbox, 7 date baskets, and Later
        assert 'Inbox' in todo_data.baskets
        assert 'Later' in todo_data.baskets
        # Check that current week dates are present
        for date_key in get_current_week_dates():
            assert date_key in todo_data.baskets

    def test_add_task_to_basket(self):
        """Test adding a task to a basket."""
        todo_data = TodoData()
        task = Task(title="Test Task")

        result = todo_data.add_task("Inbox", task)
        assert result is True
        assert len(todo_data.baskets["Inbox"]) == 1
        assert todo_data.baskets["Inbox"][0].title == "Test Task"

    def test_add_task_to_date_basket(self):
        """Test adding a task to a date-based basket."""
        todo_data = TodoData()
        task = Task(title="Test Task")
        date_key = get_current_week_dates()[0]

        result = todo_data.add_task(date_key, task)
        assert result is True
        assert len(todo_data.baskets[date_key]) == 1

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
        date_key = get_current_week_dates()[0]  # Monday
        todo_data.add_task(date_key, task)

        location = todo_data.find_task_location(task.id)
        assert location is not None
        assert location[0] == date_key
        assert location[1] is None  # No parent

    def test_move_task(self):
        """Test moving a task between baskets."""
        todo_data = TodoData()
        task = Task(title="Test Task")
        date_key = get_current_week_dates()[0]
        todo_data.add_task("Inbox", task)

        result = todo_data.move_task(task.id, date_key)
        assert result is True
        assert len(todo_data.baskets["Inbox"]) == 0
        assert len(todo_data.baskets[date_key]) == 1

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

    def test_from_dict_new_format(self):
        """Test deserializing TodoData from new date-based format."""
        date_key = get_current_week_dates()[0]
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
            date_key: []
        }

        todo_data = TodoData.from_dict(data)
        assert len(todo_data.baskets["Inbox"]) == 1
        assert todo_data.baskets["Inbox"][0].title == "Test Task"

    def test_from_dict_legacy_migration(self):
        """Test that legacy day names are migrated to current week dates."""
        data = {
            "Inbox": [],
            "Monday": [
                {
                    'id': 'test-id',
                    'title': 'Monday Task',
                    'completed': False,
                    'collapsed': False,
                    'children': [],
                    'created_at': '2024-01-01T00:00:00'
                }
            ],
            "Tuesday": [],
            "Wednesday": [],
            "Thursday": [],
            "Friday": [],
            "Saturday": [],
            "Sunday": [],
            "Later": []
        }

        todo_data = TodoData.from_dict(data)

        # The Monday task should now be in the current week's Monday date
        current_monday = get_current_week_dates()[0]
        assert current_monday in todo_data.baskets
        assert len(todo_data.baskets[current_monday]) == 1
        assert todo_data.baskets[current_monday][0].title == "Monday Task"

    def test_get_week_task_counts(self):
        """Test getting week task counts."""
        todo_data = TodoData()
        date_key = get_current_week_dates()[0]

        # Add incomplete task
        task1 = Task(title="Open Task")
        todo_data.add_task(date_key, task1)

        # Add completed task
        task2 = Task(title="Done Task", completed=True)
        todo_data.add_task(date_key, task2)

        open_count, completed_count = todo_data.get_week_task_counts()
        assert open_count == 1
        assert completed_count == 1

    def test_week_transition_moves_incomplete_tasks(self):
        """Test that week transition moves incomplete tasks to Inbox."""
        todo_data = TodoData()

        # Create an old week date (not in current week)
        old_date = (get_current_week_monday() - timedelta(days=7)).strftime('%Y-%m-%d')

        # Add tasks to old week
        todo_data._ensure_basket_exists(old_date)
        incomplete_task = Task(title="Incomplete")
        completed_task = Task(title="Completed", completed=True)
        todo_data.baskets[old_date].append(incomplete_task)
        todo_data.baskets[old_date].append(completed_task)
        todo_data._add_to_index(incomplete_task)
        todo_data._add_to_index(completed_task)

        # Perform week transition
        tasks_moved = todo_data.check_and_perform_week_transition()

        # Incomplete task should be in Inbox
        assert tasks_moved == 1
        assert len(todo_data.baskets["Inbox"]) == 1
        assert todo_data.baskets["Inbox"][0].title == "Incomplete"

        # Completed task should stay (or basket removed if empty incomplete)
        if old_date in todo_data.baskets:
            assert len(todo_data.baskets[old_date]) == 1
            assert todo_data.baskets[old_date][0].completed is True


class TestTaskEdgeCases:
    """Edge case tests for Task class."""

    def test_find_task_not_found(self):
        """Test find_task returns None for non-existent ID."""
        task = Task(title="Test")
        result = task.find_task("non-existent-id")
        assert result is None

    def test_find_parent_not_found(self):
        """Test find_parent returns None for non-existent ID."""
        task = Task(title="Test")
        result = task.find_parent("non-existent-id")
        assert result is None

    def test_remove_child_not_found(self):
        """Test remove_child returns False for non-existent ID."""
        task = Task(title="Test")
        result = task.remove_child("non-existent-id")
        assert result is False

    def test_deeply_nested_find(self):
        """Test finding tasks in deeply nested structure."""
        root = Task(title="Root")
        level1 = Task(title="Level 1")
        level2 = Task(title="Level 2")
        level3 = Task(title="Level 3")

        root.add_child(level1)
        level1.add_child(level2)
        level2.add_child(level3)

        found = root.find_task(level3.id)
        assert found is not None
        assert found.title == "Level 3"

    def test_repr(self):
        """Test string representation of Task."""
        task = Task(title="Test Task")
        child = Task(title="Child")
        task.add_child(child)

        repr_str = repr(task)
        assert "Test Task" in repr_str
        assert "children=1" in repr_str


class TestTodoDataEdgeCases:
    """Edge case tests for TodoData class."""

    def test_add_task_invalid_basket(self):
        """Test add_task returns False for invalid basket."""
        todo_data = TodoData()
        task = Task(title="Test")
        result = todo_data.add_task("InvalidBasket", task)
        assert result is False

    def test_add_task_as_child(self):
        """Test adding a task as a child of another task."""
        todo_data = TodoData()
        parent = Task(title="Parent")
        child = Task(title="Child")
        todo_data.add_task("Inbox", parent)

        result = todo_data.add_task("Inbox", child, parent_id=parent.id)
        assert result is True
        assert len(parent.children) == 1
        assert parent.children[0].id == child.id

    def test_add_task_invalid_parent(self):
        """Test add_task returns False for invalid parent_id."""
        todo_data = TodoData()
        task = Task(title="Test")
        result = todo_data.add_task("Inbox", task, parent_id="non-existent")
        assert result is False

    def test_move_task_invalid_basket(self):
        """Test move_task returns False for invalid target basket."""
        todo_data = TodoData()
        task = Task(title="Test")
        todo_data.add_task("Inbox", task)

        result = todo_data.move_task(task.id, "InvalidBasket")
        assert result is False

    def test_move_task_not_found(self):
        """Test move_task returns False for non-existent task."""
        todo_data = TodoData()
        date_key = get_current_week_dates()[0]
        result = todo_data.move_task("non-existent", date_key)
        assert result is False

    def test_move_task_with_children(self):
        """Test that moving a task preserves its children."""
        todo_data = TodoData()
        parent = Task(title="Parent")
        child = Task(title="Child")
        parent.add_child(child)
        todo_data.add_task("Inbox", parent)
        date_key = get_current_week_dates()[0]

        result = todo_data.move_task(parent.id, date_key)
        assert result is True
        moved_parent = todo_data.baskets[date_key][0]
        assert len(moved_parent.children) == 1
        assert moved_parent.children[0].title == "Child"

    def test_move_nested_task_to_new_parent(self):
        """Test moving a task to become a child of another task."""
        todo_data = TodoData()
        task1 = Task(title="Task 1")
        task2 = Task(title="Task 2")
        todo_data.add_task("Inbox", task1)
        todo_data.add_task("Inbox", task2)

        result = todo_data.move_task(task2.id, "Inbox", to_parent_id=task1.id)
        assert result is True
        assert len(task1.children) == 1
        assert task1.children[0].id == task2.id

    def test_delete_nested_task(self):
        """Test deleting a nested task."""
        todo_data = TodoData()
        parent = Task(title="Parent")
        child = Task(title="Child")
        parent.add_child(child)
        todo_data.add_task("Inbox", parent)

        result = todo_data.delete_task(child.id)
        assert result is True
        assert len(parent.children) == 0

    def test_delete_task_not_found(self):
        """Test delete_task returns False for non-existent task."""
        todo_data = TodoData()
        result = todo_data.delete_task("non-existent")
        assert result is False

    def test_find_task_not_found(self):
        """Test find_task returns None for non-existent ID."""
        todo_data = TodoData()
        result = todo_data.find_task("non-existent")
        assert result is None

    def test_find_task_location_not_found(self):
        """Test find_task_location returns None for non-existent task."""
        todo_data = TodoData()
        result = todo_data.find_task_location("non-existent")
        assert result is None

    def test_find_task_location_nested(self):
        """Test find_task_location for nested task."""
        todo_data = TodoData()
        parent = Task(title="Parent")
        child = Task(title="Child")
        parent.add_child(child)
        date_key = get_current_week_dates()[1]  # Tuesday
        todo_data.add_task(date_key, parent)

        location = todo_data.find_task_location(child.id)
        assert location is not None
        assert location[0] == date_key
        assert location[1] == parent.id

    def test_get_basket_count_with_completed(self):
        """Test get_basket_count excludes completed tasks by default."""
        todo_data = TodoData()
        task1 = Task(title="Active")
        task2 = Task(title="Done", completed=True)
        todo_data.add_task("Inbox", task1)
        todo_data.add_task("Inbox", task2)

        # Default: exclude completed
        count = todo_data.get_basket_count("Inbox")
        assert count == 1

        # Include completed
        count_all = todo_data.get_basket_count("Inbox", include_completed=True)
        assert count_all == 2

    def test_get_basket_count_nested(self):
        """Test get_basket_count includes nested tasks."""
        todo_data = TodoData()
        parent = Task(title="Parent")
        child1 = Task(title="Child 1")
        child2 = Task(title="Child 2")
        parent.add_child(child1)
        parent.add_child(child2)
        todo_data.add_task("Inbox", parent)

        count = todo_data.get_basket_count("Inbox")
        assert count == 3  # Parent + 2 children

    def test_get_basket_count_invalid_basket(self):
        """Test get_basket_count returns 0 for invalid basket."""
        todo_data = TodoData()
        count = todo_data.get_basket_count("InvalidBasket")
        assert count == 0

    def test_repr(self):
        """Test string representation of TodoData."""
        todo_data = TodoData()
        task = Task(title="Test")
        todo_data.add_task("Inbox", task)

        repr_str = repr(todo_data)
        assert "TodoData" in repr_str


class TestTaskIndex:
    """Tests for the task indexing functionality (O(1) lookup)."""

    def test_index_populated_on_add(self):
        """Test that adding a task populates the index."""
        todo_data = TodoData()
        task = Task(title="Test")
        todo_data.add_task("Inbox", task)

        # Index should allow O(1) lookup
        found = todo_data.find_task(task.id)
        assert found is task

    def test_index_includes_nested_tasks(self):
        """Test that nested tasks are indexed."""
        todo_data = TodoData()
        parent = Task(title="Parent")
        child = Task(title="Child")
        grandchild = Task(title="Grandchild")

        child.add_child(grandchild)
        parent.add_child(child)
        todo_data.add_task("Inbox", parent)

        # All should be findable via index
        assert todo_data.find_task(parent.id) is parent
        assert todo_data.find_task(child.id) is child
        assert todo_data.find_task(grandchild.id) is grandchild

    def test_index_updated_on_delete(self):
        """Test that deleting a task removes it from the index."""
        todo_data = TodoData()
        task = Task(title="Test")
        todo_data.add_task("Inbox", task)

        todo_data.delete_task(task.id)

        # Should no longer be in index
        assert todo_data.find_task(task.id) is None

    def test_index_rebuilt_on_from_dict(self):
        """Test that index is rebuilt when loading from dict."""
        date_key = get_current_week_dates()[0]
        data = {
            "Inbox": [
                {
                    'id': 'parent-id',
                    'title': 'Parent',
                    'completed': False,
                    'collapsed': False,
                    'children': [
                        {
                            'id': 'child-id',
                            'title': 'Child',
                            'completed': False,
                            'collapsed': False,
                            'children': [],
                            'created_at': '2024-01-01T00:00:00'
                        }
                    ],
                    'created_at': '2024-01-01T00:00:00'
                }
            ],
            date_key: []
        }

        todo_data = TodoData.from_dict(data)

        # Both tasks should be findable
        parent = todo_data.find_task('parent-id')
        child = todo_data.find_task('child-id')

        assert parent is not None
        assert parent.title == "Parent"
        assert child is not None
        assert child.title == "Child"

    def test_index_updated_on_child_add(self):
        """Test that adding a child task updates the index."""
        todo_data = TodoData()
        parent = Task(title="Parent")
        todo_data.add_task("Inbox", parent)

        child = Task(title="Child")
        todo_data.add_task("Inbox", child, parent_id=parent.id)

        # Child should be in index
        assert todo_data.find_task(child.id) is child


class TestTaskDescription:
    """Tests for task description functionality."""

    def test_task_creation_with_description(self):
        """Test creating a task with a description."""
        task = Task(title="Test Task", description="This is a description")
        assert task.title == "Test Task"
        assert task.description == "This is a description"

    def test_task_default_empty_description(self):
        """Test that description defaults to empty string."""
        task = Task(title="Test Task")
        assert task.description == ""

    def test_description_to_dict(self):
        """Test that description is included in serialization."""
        task = Task(title="Test", description="My description")
        data = task.to_dict()
        assert data['description'] == "My description"

    def test_description_from_dict(self):
        """Test deserializing task with description."""
        data = {
            'id': 'test-id',
            'title': 'Test Task',
            'completed': False,
            'collapsed': False,
            'children': [],
            'created_at': '2024-01-01T00:00:00',
            'description': 'Task description here'
        }
        task = Task.from_dict(data)
        assert task.description == 'Task description here'

    def test_description_backward_compatibility(self):
        """Test that old JSON without description field works."""
        data = {
            'id': 'test-id',
            'title': 'Old Task',
            'completed': False,
            'collapsed': False,
            'children': [],
            'created_at': '2024-01-01T00:00:00'
            # Note: no 'description' field
        }
        task = Task.from_dict(data)
        assert task.description == ""

    def test_description_serialization_roundtrip(self):
        """Test that description survives serialization roundtrip."""
        original = Task(title="Test", description="Multi-line\ndescription\nhere")
        data = original.to_dict()
        restored = Task.from_dict(data)
        assert restored.description == original.description

    def test_tododata_preserves_description(self):
        """Test that TodoData serialization preserves descriptions."""
        todo_data = TodoData()
        task = Task(title="Test", description="Important notes")
        todo_data.add_task("Inbox", task)

        data = todo_data.to_dict()
        restored = TodoData.from_dict(data)

        restored_task = restored.baskets["Inbox"][0]
        assert restored_task.description == "Important notes"
