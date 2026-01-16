# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TLTD (Terminal Todo List) is a terminal-based todo application with hierarchical tasks, inspired by Workflowy. Uses Python and Textual for TUI.

**Status**: Fully functional MVP with undo, inline editing, Russian keyboard support.

## Session Start Protocol

**When starting a new session, AUTOMATICALLY perform:**

1. **Pull latest changes**: `git pull` to get any changes from remote
2. **Read HANDOFF.md**: For recent changes and context

## Session End Protocol ⚠️ CRITICAL

**When the user says "session is over" or similar, AUTOMATICALLY perform:**

1. **Sanity Check Sweep**: Review modified files for dead code, unused imports, naming issues, TODO comments
2. **Run Tests**: `source venv/bin/activate && python3 -m pytest tests/ -v` (all must pass)
3. **Update HANDOFF.md**: Summarize accomplishments, note unfinished work
4. **Update CHANGELOG.md**: Add new features, changes, fixes under today's date
5. **Commit**: Descriptive message with `Co-Authored-By: Claude <noreply@anthropic.com>`
6. **Push**: `git push` to sync changes to remote

---

## Architecture

### Core Components

1. **`src/models.py`** - `Task` and `TodoData` classes
   - Hierarchical tasks with UUIDs, infinite nesting
   - `_task_index` dict for O(1) lookups
   - Baskets: Inbox, Monday-Sunday, Later (predefined, not customizable)

2. **`src/storage.py`** - `StorageManager`
   - Persists to `~/.tltd/tasks.json`
   - Atomic writes (temp file + rename)

3. **`src/app.py`** - Main Textual application
   - `TodoApp`: Main app with undo history (50 steps)
   - `BasketPane`: Left sidebar with basket list
   - `TaskTree`: Task display with inline editing
   - `TaskLine`: Individual task with collapse indicators
   - `BasketSelectorDialog`, `HelpScreen`: Modal screens

4. **`src/main.py`** - Entry point

### Key Behaviors

- **Completed tasks**: Show strikethrough for 5 seconds before hiding (toggle visibility with `z`)
- **Collapsed tasks**: Show child count like "Task (3)", count respects show_completed setting
- **Panel focus**: Two panels (baskets/tasks) with heavy border on focused panel
- **Undo**: `save_to_history()` before every data-modifying action

### Data Format

```json
{
  "Inbox": [{"id": "uuid", "title": "Task", "completed": false, "collapsed": false, "children": [], "created_at": "timestamp"}],
  "Monday": [], ...
}
```

## Critical Implementation Gotchas

### Textual Widget Initialization
**CRITICAL**: Always call `super().__init__()` BEFORE setting attributes. Textual's property handling breaks otherwise.

```python
# WRONG - will fail
def __init__(self, task):
    self.task = task
    super().__init__()

# CORRECT
def __init__(self, task):
    super().__init__()
    self.task = task
```

### ESC Key in Modal Dialogs
**CRITICAL**: Must call `event.stop()` after `dismiss()` in modal `on_key()` handlers, otherwise ESC bubbles up and quits the entire app.

```python
def on_key(self, event) -> None:
    if event.key == "escape":
        self.dismiss("")
        event.stop()  # CRITICAL: Prevents bubbling to TodoApp quit binding
```

### Adding Data-Modifying Actions
1. Call `self.save_to_history()` at start
2. Modify `self.todo_data`
3. Call `self.save_data()`
4. Refresh UI widgets
5. If creating tasks: add to `_task_index` via `todo_data._add_to_index(task)`

### Task Creation Index Bug
When creating new tasks, must add them to `_task_index` or subsequent operations (edit, move) will fail to find the task.

### recently_completed Timing
When marking a task complete, must add to `recently_completed` dict BEFORE calling `toggle_completion()` - the toggle calls `refresh_tasks()` which checks the dict to show the 5-second grace period.

### Task Reordering at Boundaries
The w/s keys (move up/down) call `action_unnest_task()` when task reaches top/bottom of its sibling list. Uses `_focus_task_by_id()` to maintain selection after the structural change.

### Adding a New Keybinding
1. Add to `BINDINGS` list in `TodoApp`
2. Implement `action_<name>` method
3. Update `action_show_help()` help text
4. **Add Russian keyboard duplicate** (same physical key position)
5. Update README.md keybindings section

**Russian keyboard mapping** (ЙЦУКЕН layout, same physical keys):
```
c→с  a→ф  d→в  e→у  q→й  w→ц  s→ы  x→ч  z→я  r→к  v→м  `→ё
Shift variants: С Ф В У Й Ц Ы Ч Я А
```

### Inline Editing Pattern
Task creation/editing uses inline Input widgets, not modal dialogs. TaskTree posts `TaskCreated`/`TaskEdited` messages to TodoApp for processing. Use this pattern for new input features.

### Maintaining Selection After Structural Changes
Use `_focus_task_by_id(task_id)` after operations that change task structure (move, unnest, delete). It finds the task in the refreshed tree and selects it.

## Testing

```bash
source venv/bin/activate && python3 -m pytest tests/ -v
```

**Quick launch test** (verify app starts without errors):
```bash
source venv/bin/activate && python src/main.py & sleep 2 && kill $! 2>/dev/null && echo "✓ App launched"
```

- ✅ 67 tests (models, storage, edge cases)
- ⚠️ UI: Manual testing only (see TESTING.md)

Run tests after: new features, refactoring, model/storage changes, session end.

## References

- **HANDOFF.md**: Session context (read at start, update at end)
- **IDEAS.md**: Feature suggestions
- **TESTING.md**: Manual test checklist
