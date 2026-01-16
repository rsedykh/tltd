"""Data models for the todo application."""
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple


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
        return cls(
            title=data['title'],
            task_id=data['id'],
            completed=data.get('completed', False),
            collapsed=data.get('collapsed', False),
            children=children,
            created_at=data.get('created_at'),
            description=data.get('description', '')
        )

    def __repr__(self) -> str:
        return f"Task(id={self.id[:8]}, title='{self.title}', completed={self.completed}, children={len(self.children)})"


class TodoData:
    """Manages all baskets and their tasks."""

    BASKETS = ['Inbox', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday', 'Later']

    def __init__(self):
        self.baskets: Dict[str, List[Task]] = {basket: [] for basket in self.BASKETS}
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

    def add_task(self, basket: str, task: Task, parent_id: Optional[str] = None) -> bool:
        """
        Add a task to a basket. If parent_id is provided, add as a child of that task.
        Returns True if successful.
        """
        if basket not in self.BASKETS:
            return False

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
        if to_basket not in self.BASKETS:
            return False

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
        if basket not in self.BASKETS:
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
    def from_dict(cls, data: Dict[str, Any]) -> 'TodoData':
        """Create TodoData from a dictionary."""
        todo_data = cls()
        for basket, tasks_data in data.items():
            if basket in cls.BASKETS:
                todo_data.baskets[basket] = [Task.from_dict(task_data) for task_data in tasks_data]
        todo_data._rebuild_index()
        return todo_data

    def __repr__(self) -> str:
        counts = {basket: len(tasks) for basket, tasks in self.baskets.items()}
        return f"TodoData(baskets={counts})"
