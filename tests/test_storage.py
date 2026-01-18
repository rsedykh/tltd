"""Tests for the storage layer."""
import pytest
import json
import tempfile
from pathlib import Path
from src.storage import StorageManager
from src.models import TodoData, Task, get_current_week_dates


class TestStorageManager:
    """Tests for the StorageManager class."""

    @pytest.fixture
    def temp_storage(self):
        """Create a temporary storage manager for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir) / "test_tasks.json"
            yield StorageManager(temp_path)

    def test_storage_creation(self, temp_storage):
        """Test creating a storage manager."""
        assert temp_storage.file_path is not None
        assert isinstance(temp_storage.file_path, Path)

    def test_ensure_directory(self, temp_storage):
        """Test directory creation."""
        temp_storage.ensure_directory()
        assert temp_storage.file_path.parent.exists()

    def test_save_and_load(self, temp_storage):
        """Test saving and loading data."""
        # Create test data
        todo_data = TodoData()
        task = Task(title="Test Task")
        todo_data.add_task("Inbox", task)

        # Save
        result = temp_storage.save(todo_data)
        assert result is True
        assert temp_storage.file_path.exists()

        # Load
        loaded_data = temp_storage.load()
        assert len(loaded_data.baskets["Inbox"]) == 1
        assert loaded_data.baskets["Inbox"][0].title == "Test Task"

    def test_load_nonexistent_file(self, temp_storage):
        """Test loading when file doesn't exist."""
        loaded_data = temp_storage.load()
        assert isinstance(loaded_data, TodoData)
        assert len(loaded_data.baskets["Inbox"]) == 0

    def test_load_corrupted_file(self, temp_storage):
        """Test loading a corrupted JSON file."""
        # Write corrupted JSON
        temp_storage.ensure_directory()
        with open(temp_storage.file_path, 'w') as f:
            f.write("{ invalid json }")

        # Should return fresh TodoData
        loaded_data = temp_storage.load()
        assert isinstance(loaded_data, TodoData)

        # Backup should be created
        backup_path = temp_storage.file_path.with_suffix('.json.backup')
        assert backup_path.exists()

    def test_save_nested_tasks(self, temp_storage):
        """Test saving and loading nested tasks."""
        # Create nested structure
        todo_data = TodoData()
        parent = Task(title="Parent Task")
        child1 = Task(title="Child 1")
        child2 = Task(title="Child 2")
        parent.add_child(child1)
        parent.add_child(child2)
        todo_data.add_task("Inbox", parent)

        # Save and load
        temp_storage.save(todo_data)
        loaded_data = temp_storage.load()

        # Verify structure
        assert len(loaded_data.baskets["Inbox"]) == 1
        loaded_parent = loaded_data.baskets["Inbox"][0]
        assert loaded_parent.title == "Parent Task"
        assert len(loaded_parent.children) == 2
        assert loaded_parent.children[0].title == "Child 1"
        assert loaded_parent.children[1].title == "Child 2"

    def test_save_completed_tasks(self, temp_storage):
        """Test saving and loading completed tasks."""
        todo_data = TodoData()
        task = Task(title="Completed Task", completed=True)
        date_key = get_current_week_dates()[0]  # Monday
        todo_data.add_task(date_key, task)

        temp_storage.save(todo_data)
        loaded_data = temp_storage.load()

        assert len(loaded_data.baskets[date_key]) == 1
        assert loaded_data.baskets[date_key][0].completed is True

    def test_save_collapsed_tasks(self, temp_storage):
        """Test saving and loading collapsed state."""
        todo_data = TodoData()
        parent = Task(title="Parent Task", collapsed=True)
        child = Task(title="Child Task")
        parent.add_child(child)
        todo_data.add_task("Inbox", parent)

        temp_storage.save(todo_data)
        loaded_data = temp_storage.load()

        loaded_parent = loaded_data.baskets["Inbox"][0]
        assert loaded_parent.collapsed is True

    def test_backup(self, temp_storage):
        """Test creating a backup."""
        # Create and save test data
        todo_data = TodoData()
        task = Task(title="Test Task")
        todo_data.add_task("Inbox", task)
        temp_storage.save(todo_data)

        # Create backup
        result = temp_storage.backup()
        assert result is True

        backup_path = temp_storage.file_path.with_suffix('.json.backup')
        assert backup_path.exists()

    def test_backup_nonexistent_file(self, temp_storage):
        """Test backup when file doesn't exist."""
        result = temp_storage.backup()
        assert result is False

    def test_atomic_write(self, temp_storage):
        """Test that saves use atomic writes."""
        todo_data = TodoData()
        task = Task(title="Test Task")
        todo_data.add_task("Inbox", task)

        temp_storage.save(todo_data)

        # Temp file should not exist after save
        temp_path = temp_storage.file_path.with_suffix('.json.tmp')
        assert not temp_path.exists()

        # Main file should exist
        assert temp_storage.file_path.exists()

    def test_save_all_baskets(self, temp_storage):
        """Test saving tasks across all baskets."""
        todo_data = TodoData()
        current_week = get_current_week_dates()

        # Add task to Inbox
        todo_data.add_task("Inbox", Task(title="Task in Inbox"))

        # Add task to each day of the week
        for date_key in current_week:
            todo_data.add_task(date_key, Task(title=f"Task in {date_key}"))

        # Add task to Later
        todo_data.add_task("Later", Task(title="Task in Later"))

        temp_storage.save(todo_data)
        loaded_data = temp_storage.load()

        # Verify Inbox
        assert len(loaded_data.baskets["Inbox"]) == 1
        assert loaded_data.baskets["Inbox"][0].title == "Task in Inbox"

        # Verify each day
        for date_key in current_week:
            assert len(loaded_data.baskets[date_key]) == 1
            assert loaded_data.baskets[date_key][0].title == f"Task in {date_key}"

        # Verify Later
        assert len(loaded_data.baskets["Later"]) == 1
        assert loaded_data.baskets["Later"][0].title == "Task in Later"

    def test_json_formatting(self, temp_storage):
        """Test that saved JSON is properly formatted (indented)."""
        todo_data = TodoData()
        task = Task(title="Test Task")
        todo_data.add_task("Inbox", task)

        temp_storage.save(todo_data)

        # Read raw file and verify it's formatted
        with open(temp_storage.file_path, 'r') as f:
            content = f.read()

        # Should contain newlines (formatted JSON)
        assert '\n' in content
        # Should be valid JSON
        parsed = json.loads(content)
        assert "Inbox" in parsed

    def test_unicode_task_titles(self, temp_storage):
        """Test saving and loading unicode characters in task titles."""
        todo_data = TodoData()
        task = Task(title="Test 日本語 emoji 🎉 スケジュール")
        todo_data.add_task("Inbox", task)

        temp_storage.save(todo_data)
        loaded_data = temp_storage.load()

        assert loaded_data.baskets["Inbox"][0].title == "Test 日本語 emoji 🎉 スケジュール"

    def test_deeply_nested_save_load(self, temp_storage):
        """Test saving and loading deeply nested task structure."""
        todo_data = TodoData()

        # Create 5 levels of nesting
        root = Task(title="Level 0")
        current = root
        for i in range(1, 5):
            child = Task(title=f"Level {i}")
            current.add_child(child)
            current = child

        todo_data.add_task("Inbox", root)
        temp_storage.save(todo_data)
        loaded_data = temp_storage.load()

        # Verify nesting structure
        loaded = loaded_data.baskets["Inbox"][0]
        for i in range(5):
            assert loaded.title == f"Level {i}"
            if i < 4:
                assert len(loaded.children) == 1
                loaded = loaded.children[0]

    def test_empty_baskets_preserved(self, temp_storage):
        """Test that empty baskets are preserved in save/load."""
        todo_data = TodoData()
        # Only add to Inbox, leave others empty
        task = Task(title="Test")
        todo_data.add_task("Inbox", task)

        temp_storage.save(todo_data)
        loaded_data = temp_storage.load()

        # Core baskets should exist
        assert "Inbox" in loaded_data.baskets
        assert "Later" in loaded_data.baskets

    def test_multiple_tasks_per_basket(self, temp_storage):
        """Test saving and loading multiple tasks in same basket."""
        todo_data = TodoData()
        for i in range(10):
            task = Task(title=f"Task {i}")
            todo_data.add_task("Inbox", task)

        temp_storage.save(todo_data)
        loaded_data = temp_storage.load()

        assert len(loaded_data.baskets["Inbox"]) == 10
        for i in range(10):
            assert loaded_data.baskets["Inbox"][i].title == f"Task {i}"

    def test_task_index_preserved_after_load(self, temp_storage):
        """Test that task index works after loading from disk."""
        # Create and save
        todo_data = TodoData()
        parent = Task(title="Parent")
        child = Task(title="Child")
        parent.add_child(child)
        todo_data.add_task("Inbox", parent)

        original_parent_id = parent.id
        original_child_id = child.id

        temp_storage.save(todo_data)
        loaded_data = temp_storage.load()

        # Index should work for O(1) lookup
        found_parent = loaded_data.find_task(original_parent_id)
        found_child = loaded_data.find_task(original_child_id)

        assert found_parent is not None
        assert found_child is not None
        assert found_parent.title == "Parent"
        assert found_child.title == "Child"


class TestStorageMigration:
    """Tests for migrating from legacy day-name format to date-based format."""

    @pytest.fixture
    def temp_storage(self):
        """Create a temporary storage manager for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir) / "test_tasks.json"
            yield StorageManager(temp_path)

    def test_needs_migration_detects_legacy_format(self, temp_storage):
        """Test that _needs_migration correctly detects legacy format."""
        legacy_data = {
            "Inbox": [],
            "Monday": [],
            "Tuesday": [],
            "Wednesday": [],
            "Thursday": [],
            "Friday": [],
            "Saturday": [],
            "Sunday": [],
            "Later": []
        }
        assert temp_storage._needs_migration(legacy_data) is True

    def test_needs_migration_returns_false_for_new_format(self, temp_storage):
        """Test that _needs_migration returns False for date-based format."""
        current_week = get_current_week_dates()
        new_data = {
            "Inbox": [],
            current_week[0]: [],
            "Later": []
        }
        assert temp_storage._needs_migration(new_data) is False

    def test_load_migrates_legacy_format(self, temp_storage):
        """Test that loading legacy format migrates to new format."""
        # Write legacy format directly
        temp_storage.ensure_directory()
        legacy_data = {
            "Inbox": [],
            "Monday": [
                {
                    'id': 'task-1',
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
            "Friday": [
                {
                    'id': 'task-2',
                    'title': 'Friday Task',
                    'completed': True,
                    'collapsed': False,
                    'children': [],
                    'created_at': '2024-01-01T00:00:00'
                }
            ],
            "Saturday": [],
            "Sunday": [],
            "Later": []
        }
        with open(temp_storage.file_path, 'w') as f:
            json.dump(legacy_data, f)

        # Load should migrate
        loaded_data = temp_storage.load()

        # Tasks should be in current week's date keys
        current_week = get_current_week_dates()
        monday_key = current_week[0]  # Monday
        friday_key = current_week[4]  # Friday

        assert len(loaded_data.baskets[monday_key]) == 1
        assert loaded_data.baskets[monday_key][0].title == "Monday Task"

        assert len(loaded_data.baskets[friday_key]) == 1
        assert loaded_data.baskets[friday_key][0].title == "Friday Task"

    def test_load_migration_saves_new_format(self, temp_storage):
        """Test that after migration, file is saved in new format."""
        # Write legacy format
        temp_storage.ensure_directory()
        legacy_data = {
            "Inbox": [],
            "Monday": [
                {
                    'id': 'task-1',
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
        with open(temp_storage.file_path, 'w') as f:
            json.dump(legacy_data, f)

        # Load (triggers migration)
        temp_storage.load()

        # Read the file again to check format
        with open(temp_storage.file_path, 'r') as f:
            saved_data = json.load(f)

        # Should no longer have day names
        assert "Monday" not in saved_data
        assert "Tuesday" not in saved_data

        # Should have date keys
        current_week = get_current_week_dates()
        assert current_week[0] in saved_data  # Monday's date

    def test_migration_preserves_task_properties(self, temp_storage):
        """Test that migration preserves all task properties."""
        temp_storage.ensure_directory()
        legacy_data = {
            "Inbox": [],
            "Monday": [
                {
                    'id': 'task-with-all-props',
                    'title': 'Full Task',
                    'completed': True,
                    'collapsed': True,
                    'description': 'Important description',
                    'children': [
                        {
                            'id': 'child-task',
                            'title': 'Child Task',
                            'completed': False,
                            'collapsed': False,
                            'children': [],
                            'created_at': '2024-01-02T00:00:00'
                        }
                    ],
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
        with open(temp_storage.file_path, 'w') as f:
            json.dump(legacy_data, f)

        loaded_data = temp_storage.load()

        current_week = get_current_week_dates()
        monday_key = current_week[0]

        assert len(loaded_data.baskets[monday_key]) == 1
        task = loaded_data.baskets[monday_key][0]

        assert task.title == "Full Task"
        assert task.completed is True
        assert task.collapsed is True
        assert task.description == "Important description"
        assert len(task.children) == 1
        assert task.children[0].title == "Child Task"
