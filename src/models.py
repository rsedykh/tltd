"""Data models for the todo application."""
import uuid
import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple

# Input validation limits (enforced on load for defense-in-depth)
MAX_TITLE_LENGTH = 512
MAX_DESCRIPTION_LENGTH = 4096
MAX_NESTING_DEPTH = 8

# Fixed baskets that don't change
FIXED_BASKETS = ['Inbox', 'Later']

# Day names for display (Monday=0, Sunday=6)
DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

# Legacy day names for migration detection
LEGACY_DAY_BASKETS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

# Week transition hour (4am Monday local time)
WEEK_TRANSITION_HOUR = 4


def get_current_week_monday() -> datetime:
    """Get the Monday of the current week at midnight."""
    now = datetime.now()
    # If it's Monday before 4am, we're still in the previous week
    if now.weekday() == 0 and now.hour < WEEK_TRANSITION_HOUR:
        # Go back to previous Monday
        monday = now - timedelta(days=7)
    else:
        # Normal case: go back to this week's Monday
        monday = now - timedelta(days=now.weekday())
    return monday.replace(hour=0, minute=0, second=0, microsecond=0)


def get_current_week_dates() -> List[str]:
    """Get the 7 date strings (YYYY-MM-DD) for the current week (Mon-Sun)."""
    monday = get_current_week_monday()
    return [(monday + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]


def get_week_number(date_str: str) -> Tuple[int, int]:
    """
    Get the ISO week number and year for a date string.
    Returns (week_number, year).
    Uses the Monday's week number for the entire week (handles year boundary).
    """
    date = datetime.strptime(date_str, '%Y-%m-%d')
    # Find the Monday of this date's week
    monday = date - timedelta(days=date.weekday())
    iso_cal = monday.isocalendar()
    return (iso_cal[1], iso_cal[0])


def date_to_display_name(date_str: str) -> str:
    """Convert a date string (YYYY-MM-DD) to a day name (e.g., 'Monday')."""
    date = datetime.strptime(date_str, '%Y-%m-%d')
    return DAY_NAMES[date.weekday()]


def is_date_basket(key: str) -> bool:
    """Check if a basket key is in date format (YYYY-MM-DD)."""
    return bool(re.match(r'^\d{4}-\d{2}-\d{2}$', key))


def get_ordered_baskets(all_basket_keys: List[str]) -> List[str]:
    """
    Get baskets in display order: Inbox, current week dates, Later.
    Only includes baskets that exist in all_basket_keys.
    """
    current_week = get_current_week_dates()
    result = ['Inbox']
    # Add current week dates that exist
    for date_key in current_week:
        if date_key in all_basket_keys:
            result.append(date_key)
    result.append('Later')
    return result


def is_in_current_week(date_str: str) -> bool:
    """Check if a date string is in the current week."""
    return date_str in get_current_week_dates()


class Task:
    """Represents a single task with hierarchical children."""

    def __init__(
        self,
        title: str,
        task_id: Optional[str] = None,
        completed: bool = False,
        collapsed: bool = False,
        children: Optional[List['Task']] = None,
        created_at: Optional[str] = None,
        description: str = ""
    ):
        self.id = task_id or str(uuid.uuid4())
        self.title = title
        self.completed = completed
        self.collapsed = collapsed
        self.children = children or []
        self.created_at = created_at or datetime.now().isoformat()
        self.description = description

    def add_child(self, task: 'Task') -> None:
        """Add a child task."""
        self.children.append(task)

    def remove_child(self, task_id: str) -> bool:
        """Remove a child task by ID. Returns True if found and removed."""
        for i, child in enumerate(self.children):
            if child.id == task_id:
                self.children.pop(i)
                return True
        return False

    def find_task(self, task_id: str) -> Optional['Task']:
        """Recursively find a task by ID in this task and its children."""
        if self.id == task_id:
            return self

        for child in self.children:
            result = child.find_task(task_id)
            if result:
                return result

        return None

    def find_parent(self, task_id: str) -> Optional['Task']:
        """Find the parent task of a given task ID."""
        for child in self.children:
            if child.id == task_id:
                return self
            result = child.find_parent(task_id)
            if result:
                return result
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'completed': self.completed,
            'collapsed': self.collapsed,
            'children': [child.to_dict() for child in self.children],
            'created_at': self.created_at,
            'description': self.description
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create a Task from a dictionary."""
        children = [cls.from_dict(child) for child in data.get('children', [])]
        # Enforce length limits on load (defense-in-depth for manually edited files)
        title = data.get('title', '')[:MAX_TITLE_LENGTH]
        description = data.get('description', '')[:MAX_DESCRIPTION_LENGTH]
        return cls(
            title=title,
            task_id=data.get('id'),
            completed=data.get('completed', False),
            collapsed=data.get('collapsed', False),
            children=children,
            created_at=data.get('created_at'),
            description=description
        )

    def __repr__(self) -> str:
        return f"Task(id={self.id[:8]}, title='{self.title}', completed={self.completed}, children={len(self.children)})"


class TodoData:
    """Manages all baskets and their tasks."""

    # For backwards compatibility, keep BASKETS as a property that returns current week
    @classmethod
    def get_baskets(cls) -> List[str]:
        """Get the list of active baskets (Inbox + current week + Later)."""
        return ['Inbox'] + get_current_week_dates() + ['Later']

    # Legacy constant for backwards compatibility (redirects to dynamic)
    BASKETS = property(lambda self: self.get_baskets())

    def __init__(self):
        # Initialize with fixed baskets + current week dates
        current_baskets = ['Inbox'] + get_current_week_dates() + ['Later']
        self.baskets: Dict[str, List[Task]] = {basket: [] for basket in current_baskets}
        self._task_index: Dict[str, Task] = {}  # task_id -> Task for O(1) lookup

    def _rebuild_index(self) -> None:
        """Rebuild the task index from all baskets."""
        self._task_index.clear()
        for basket_tasks in self.baskets.values():
            for task in basket_tasks:
                self._index_task_recursive(task)

    def _index_task_recursive(self, task: Task) -> None:
        """Add a task and all its children to the index."""
        self._task_index[task.id] = task
        for child in task.children:
            self._index_task_recursive(child)

    def _add_to_index(self, task: Task) -> None:
        """Add a single task and its children to the index."""
        self._index_task_recursive(task)

    def _remove_from_index(self, task: Task) -> None:
        """Remove a task and its children from the index."""
        self._task_index.pop(task.id, None)
        for child in task.children:
            self._remove_from_index(child)

    def _is_valid_basket(self, basket: str) -> bool:
        """Check if a basket name is valid (fixed basket or date format)."""
        return basket in FIXED_BASKETS or is_date_basket(basket)

    def _ensure_basket_exists(self, basket: str) -> None:
        """Ensure a basket exists in the data structure."""
        if basket not in self.baskets:
            self.baskets[basket] = []

    def add_task(self, basket: str, task: Task, parent_id: Optional[str] = None) -> bool:
        """
        Add a task to a basket. If parent_id is provided, add as a child of that task.
        Returns True if successful.
        """
        if not self._is_valid_basket(basket):
            return False

        self._ensure_basket_exists(basket)

        if parent_id:
            # Find parent and add as child
            parent = self.find_task(parent_id)
            if parent:
                parent.add_child(task)
                self._add_to_index(task)
                return True
            return False
        else:
            # Add to basket root
            self.baskets[basket].append(task)
            self._add_to_index(task)
            return True

    def find_task(self, task_id: str) -> Optional[Task]:
        """Find a task by ID across all baskets. O(1) lookup via index."""
        return self._task_index.get(task_id)

    def find_task_location(self, task_id: str) -> Optional[Tuple[str, Optional[str]]]:
        """
        Find which basket and parent (if any) contains the task.
        Returns (basket_name, parent_id) or None if not found.
        """
        for basket_name, basket_tasks in self.baskets.items():
            for task in basket_tasks:
                if task.id == task_id:
                    return (basket_name, None)

                parent = task.find_parent(task_id)
                if parent:
                    return (basket_name, parent.id)
        return None

    def move_task(self, task_id: str, to_basket: str, to_parent_id: Optional[str] = None) -> bool:
        """
        Move a task from its current location to a new basket/parent.
        Returns True if successful.
        """
        if not self._is_valid_basket(to_basket):
            return False

        self._ensure_basket_exists(to_basket)

        # Find current location
        location = self.find_task_location(task_id)
        if not location:
            return False

        from_basket, from_parent_id = location

        # Get the task
        task = self.find_task(task_id)
        if not task:
            return False

        # Remove from current location
        if from_parent_id:
            parent = self.find_task(from_parent_id)
            if parent:
                parent.remove_child(task_id)
        else:
            self.baskets[from_basket] = [t for t in self.baskets[from_basket] if t.id != task_id]

        # Add to new location
        if to_parent_id:
            new_parent = self.find_task(to_parent_id)
            if new_parent:
                new_parent.add_child(task)
                return True
            return False
        else:
            self.baskets[to_basket].append(task)
            return True

    def delete_task(self, task_id: str) -> bool:
        """Delete a task and all its children. Returns True if successful."""
        task = self.find_task(task_id)
        if not task:
            return False

        location = self.find_task_location(task_id)
        if not location:
            return False

        basket_name, parent_id = location

        # Remove from index before removing from data structure
        self._remove_from_index(task)

        if parent_id:
            parent = self.find_task(parent_id)
            if parent:
                return parent.remove_child(task_id)
        else:
            self.baskets[basket_name] = [t for t in self.baskets[basket_name] if t.id != task_id]
            return True

        return False

    def get_basket_count(self, basket: str, include_completed: bool = False) -> int:
        """Get the count of tasks in a basket (including nested tasks)."""
        if basket not in self.baskets:
            return 0

        def count_tasks(tasks: List[Task]) -> int:
            count = 0
            for task in tasks:
                if include_completed or not task.completed:
                    count += 1
                    count += count_tasks(task.children)
            return count

        return count_tasks(self.baskets[basket])

    def to_dict(self) -> Dict[str, Any]:
        """Convert all data to dictionary for JSON serialization."""
        return {
            basket: [task.to_dict() for task in tasks]
            for basket, tasks in self.baskets.items()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], migrate_legacy: bool = True) -> 'TodoData':
        """
        Create TodoData from a dictionary.
        If migrate_legacy is True, converts old day-name baskets to current week dates.
        """
        todo_data = cls()

        # Detect legacy format (has day names like "Monday")
        has_legacy = any(key in LEGACY_DAY_BASKETS for key in data.keys())

        if has_legacy and migrate_legacy:
            # Migrate legacy day names to current week dates
            current_week = get_current_week_dates()
            for i, day_name in enumerate(LEGACY_DAY_BASKETS):
                if day_name in data and data[day_name]:
                    date_key = current_week[i]
                    todo_data._ensure_basket_exists(date_key)
                    todo_data.baskets[date_key] = [Task.from_dict(task_data) for task_data in data[day_name]]

        # Load fixed baskets and date-based baskets
        for basket, tasks_data in data.items():
            if basket in FIXED_BASKETS:
                todo_data.baskets[basket] = [Task.from_dict(task_data) for task_data in tasks_data]
            elif is_date_basket(basket):
                # Date-based basket - load it (may be current or old week)
                todo_data._ensure_basket_exists(basket)
                todo_data.baskets[basket] = [Task.from_dict(task_data) for task_data in tasks_data]

        todo_data._rebuild_index()
        return todo_data

    def get_week_task_counts(self) -> Tuple[int, int]:
        """
        Get task counts for the current week.
        Returns (open_count, completed_count).
        """
        open_count = 0
        completed_count = 0

        def count_recursive(tasks: List[Task]) -> Tuple[int, int]:
            open_c, done_c = 0, 0
            for task in tasks:
                if task.completed:
                    done_c += 1
                else:
                    open_c += 1
                child_open, child_done = count_recursive(task.children)
                open_c += child_open
                done_c += child_done
            return open_c, done_c

        for date_key in get_current_week_dates():
            if date_key in self.baskets:
                o, c = count_recursive(self.baskets[date_key])
                open_count += o
                completed_count += c

        return open_count, completed_count

    def check_and_perform_week_transition(self) -> int:
        """
        Check if week transition is needed and move incomplete tasks from old weeks to Inbox.
        Returns the number of tasks moved.
        """
        current_week = set(get_current_week_dates())
        tasks_moved = 0

        # Find all date-based baskets that are NOT in the current week
        old_week_baskets = [
            key for key in list(self.baskets.keys())
            if is_date_basket(key) and key not in current_week
        ]

        for basket_key in old_week_baskets:
            tasks = self.baskets.get(basket_key, [])
            # Move incomplete tasks to Inbox
            incomplete_tasks = [t for t in tasks if not t.completed]
            completed_tasks = [t for t in tasks if t.completed]

            for task in incomplete_tasks:
                self._ensure_basket_exists('Inbox')
                self.baskets['Inbox'].append(task)
                tasks_moved += 1

            # Keep completed tasks in place (archived) or remove basket if empty
            if completed_tasks:
                self.baskets[basket_key] = completed_tasks
            else:
                # No completed tasks left, remove the old basket
                del self.baskets[basket_key]

        return tasks_moved

    def get_display_baskets(self) -> List[str]:
        """Get the list of baskets to display: Inbox, current week, Later."""
        return ['Inbox'] + get_current_week_dates() + ['Later']

    def __repr__(self) -> str:
        counts = {basket: len(tasks) for basket, tasks in self.baskets.items()}
        return f"TodoData(baskets={counts})"
