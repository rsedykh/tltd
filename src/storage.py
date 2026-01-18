"""Storage management for persisting todo data."""
import json
import os
from pathlib import Path
from typing import Optional

from .models import TodoData, LEGACY_DAY_BASKETS


class StorageManager:
    """Manages loading and saving todo data to disk."""

    DEFAULT_DIR = Path.home() / '.tltd'
    DEFAULT_FILE = DEFAULT_DIR / 'tasks.json'

    def __init__(self, file_path: Optional[Path] = None):
        self.file_path = file_path or self.DEFAULT_FILE

    def ensure_directory(self) -> None:
        """Create the storage directory if it doesn't exist."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)

    def load(self) -> TodoData:
        """
        Load todo data from disk.
        Returns a new TodoData instance if file doesn't exist or is corrupted.
        Automatically migrates legacy day-name format to date-based format.
        """
        if not self.file_path.exists():
            return TodoData()

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Detect if migration is needed
            needs_migration = self._needs_migration(data)

            todo_data = TodoData.from_dict(data, migrate_legacy=True)

            # If we migrated, save the new format immediately
            if needs_migration:
                self.save(todo_data)

            return todo_data
        except (json.JSONDecodeError, KeyError, OSError):
            # If file is corrupted, backup and return fresh data
            backup_path = self.file_path.with_suffix('.json.backup')
            try:
                if self.file_path.exists():
                    self.file_path.rename(backup_path)
            except OSError:
                pass
            return TodoData()

    def _needs_migration(self, data: dict) -> bool:
        """Check if the data contains legacy day-name baskets that need migration."""
        return any(key in LEGACY_DAY_BASKETS for key in data.keys())

    def save(self, todo_data: TodoData) -> bool:
        """
        Save todo data to disk.
        Returns True if successful, False otherwise.
        """
        try:
            self.ensure_directory()

            # Write to a temporary file first
            temp_path = self.file_path.with_suffix('.json.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(todo_data.to_dict(), f, indent=2, ensure_ascii=False)

            # Set restrictive permissions before rename
            os.chmod(temp_path, 0o600)

            # Atomic rename
            temp_path.replace(self.file_path)
            return True

        except (OSError, TypeError):
            return False

    def backup(self) -> bool:
        """
        Create a backup of the current data file.
        Returns True if successful.
        """
        if not self.file_path.exists():
            return False

        try:
            backup_path = self.file_path.with_suffix('.json.backup')
            with open(self.file_path, 'r') as src:
                with open(backup_path, 'w') as dst:
                    dst.write(src.read())
            # Set restrictive permissions on backup file
            os.chmod(backup_path, 0o600)
            return True
        except OSError:
            return False
