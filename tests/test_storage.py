"""Tests for the storage layer."""
import pytest
import json
import tempfile
from pathlib import Path
from src.storage import StorageManager
from src.models import TodoData, Task


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
        todo_data.add_task("Monday", task)

        temp_storage.save(todo_data)
        loaded_data = temp_storage.load()

        assert len(loaded_data.baskets["Monday"]) == 1
        assert loaded_data.baskets["Monday"][0].completed is True

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

        for i, basket in enumerate(TodoData.BASKETS):
            task = Task(title=f"Task in {basket}")
            todo_data.add_task(basket, task)

        temp_storage.save(todo_data)
        loaded_data = temp_storage.load()

        # Verify all baskets have their tasks
        for basket in TodoData.BASKETS:
            assert len(loaded_data.baskets[basket]) == 1
            assert loaded_data.baskets[basket][0].title == f"Task in {basket}"
