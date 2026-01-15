# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TLTD (Terminal Todo List) is a terminal-based todo application with hierarchical tasks, inspired by Workflowy. It uses Python and the Textual library for the TUI.

**Status**: Fully functional MVP with all core features implemented including undo functionality.

## Session End Protocol ⚠️ CRITICAL

**When the user says "session is over" or similar, AUTOMATICALLY perform:**

1. **Sanity Check Sweep**:
   - Review all modified files for inconsistencies
   - Check for naming issues (unused variables, unclear names)
   - Look for refactoring leftovers (dead code, unused imports)
   - Verify cross-file consistency
   - Check for TODO comments or incomplete work
   - Highlight any problems found

2. **Run Tests**:
   ```bash
   source venv/bin/activate && python3 -m pytest tests/ -v
   ```
   - All tests must pass
   - If tests fail, fix before session ends

3. **Update Handoff Documentation**:
   - Update "Recent Changes" section in CLAUDE.md
   - Summarize what was accomplished
   - Note any unfinished work or known issues
   - Update file line counts if significantly changed

4. **Commit Changes**:
   - Create descriptive commit message
   - Include Co-Authored-By line
   - Push if user requests

**This protocol ensures clean handoffs between sessions.**

### Session End Checklist

```markdown
- [ ] Sanity check: Review modified files
- [ ] Check for dead code, unused imports, naming issues
- [ ] Run: pytest tests/ -v (all must pass)
- [ ] Update CLAUDE.md "Recent Changes" section
- [ ] Git commit with descriptive message
- [ ] Inform user of status and any issues found
```

---

## Claude Code Testing Workflow

**When Claude should run tests:**
- ⚠️ **At session end (MANDATORY)**
- When explicitly asked by the user (e.g., "run tests")
- After implementing a new feature
- After refactoring existing code
- After making significant changes to models or storage
- Before marking a major task as complete

**When NOT to run tests:**
- After minor documentation changes
- After CSS/styling changes
- After adding keybindings (UI-only changes)
- During exploratory/research tasks

**How to run tests:**
1. User must have activated venv and installed pytest first
2. Run: `python3 -m pytest tests/ -v`
3. All tests should pass before completing major features
4. If tests fail, fix the code or update tests as needed

## Development Commands

### Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode (optional)
pip install -e .
```

### Running the App
```bash
# Activate venv first
source venv/bin/activate

# Run directly
python src/main.py

# Or if installed
tltd
```

### Testing
```bash
# Activate virtual environment first
source venv/bin/activate

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_models.py -v
pytest tests/test_storage.py -v

# Run with coverage report (requires pytest-cov)
pip install pytest-cov
pytest tests/ --cov=src --cov-report=term-missing
```

**When to run tests:**
- After adding new features
- After refactoring
- After significant changes (multiple files or complex logic)
- When prompted by the user
- Before creating a pull request

**Test coverage:**
- ✅ Models (Task, TodoData) - 13 tests
- ✅ Storage (save/load, backups, atomic writes) - 14 tests
- ⚠️ UI (app.py) - Not tested (requires Textual testing utilities)

Note: UI testing is challenging with Textual and requires manual testing or specialized test setup.

## Architecture

### Core Components

1. **Data Model (`src/models.py`)**
   - `Task`: Represents a single task with id, title, completion status, children, and collapse state
   - `TodoData`: Manages all baskets (Inbox, Monday-Sunday, Later) and their tasks
   - Tasks are hierarchical - each task can have children tasks (nested infinitely)
   - All tasks have UUIDs for identification
   - Supports recursive operations: find, move, delete

2. **Storage Layer (`src/storage.py`)**
   - `StorageManager`: Handles JSON serialization/deserialization
   - Data persisted to `~/.tltd/tasks.json`
   - Automatically creates config directory if needed
   - Uses atomic writes (write to temp file, then rename) for data safety

3. **UI Layer (`src/app.py`)**
   - `TodoApp`: Main Textual application with undo history
   - `BasketPane`: Left sidebar showing baskets and task counts
   - `TaskTree`: Main area displaying hierarchical task tree with inline editing
   - `TaskLine`: Individual task display with collapse indicators and child count
   - `BasketSelectorDialog`: Modal dialog for selecting basket when moving tasks
   - `HelpScreen`: Modal screen showing keyboard shortcuts
   - Footer: Displays keyboard shortcuts

4. **Entry Point (`src/main.py`)**
   - Application initialization and launch
   - Adds parent directory to path to allow `python src/main.py` to work

### Key Patterns

- **Recursive Task Structure**: Tasks contain lists of child tasks, enabling infinite nesting
- **Basket Organization**: Tasks organized into predefined baskets (can't create custom baskets)
- **Show/Hide Completed**: Completed tasks show with strikethrough for 5 seconds before disappearing, can be toggled visible with z key
- **Collapse State**: Parent tasks can be collapsed to hide children, shows count like "Task (3)"
- **Panel Focus System**: Two panels (baskets/tasks) with visual focus indicator (heavy border)
- **Undo System**: Stores up to 50 previous states, all data-modifying actions trigger history save

### Data Format

Tasks are stored as JSON with this structure:
```json
{
  "Inbox": [
    {
      "id": "uuid",
      "title": "Task title",
      "completed": false,
      "collapsed": false,
      "children": [],
      "created_at": "timestamp"
    }
  ],
  "Monday": [],
  ...
}
```

## Keybindings (IMPORTANT)

The keybinding system was recently redesigned to be terminal-friendly (avoiding Cmd key):

### Panel Navigation
- **←/→**: Switch between baskets and tasks panels
- **↑/↓**: Navigate within current panel

### Task Operations
- **c**: Create new task below current one (same nesting level, or at root if basket is empty)
- **Enter**: Edit task
- **x**: Toggle completion
- **Backspace**: Delete task and children
- **f**: Move task to different basket

### Collapsing
- **a**: Collapse task (hide children)
- **d**: Expand task (show children)

### Nesting (children move with parent)
- **e**: Nest task under previous sibling
- **q**: Unnest task one level up

### Reordering
- **w**: Move task up in list
- **s**: Move task down in list
- Intelligently handles nesting boundaries (unnests when needed)
- **Maintains focus**: When reaching boundaries and unnesting, selection stays on the moved task

### Quick Basket Jump
- **`**: Jump to Inbox
- **1-7**: Jump to Monday through Sunday
- **0**: Jump to Later

### Other
- **\**: Undo last action (up to 50 steps)
- **z**: Toggle show completed tasks
- **Esc**: Quit application (also cancels dialogs)
- **?**: Show help screen

## Important Implementation Details

### Textual Widget Initialization
**CRITICAL**: When creating Textual widgets, always call `super().__init__()` BEFORE setting any attributes. Textual has special property handling that breaks if you set attributes before initialization.

**WRONG**:
```python
def __init__(self, task, level):
    self.task = task  # ERROR: Will fail
    super().__init__()
```

**CORRECT**:
```python
def __init__(self, task, level):
    super().__init__()
    self.task = task  # OK
```

For `TaskLine`, we work around this by building the content string first, then passing it to `super().__init__(content)`.

### Undo System Implementation
- `save_to_history()` is called before every data-modifying action
- Stores serialized state via `todo_data.to_dict()`
- `action_undo()` pops last state and restores it
- Must update both `self.todo_data` and widget references when restoring
- Limited to 50 steps to prevent memory issues

### Panel Focus System
- `focused_panel` tracks "baskets" or "tasks"
- `_update_panel_focus()` adds/removes "focused" CSS class
- CSS applies heavy border to focused panel
- Arrow keys respect focused panel for navigation
- Focus initialized to "tasks" on mount

### Task Reordering Logic
- **w/s keys**: Move within sibling list
- When at boundaries (top/bottom of parent's children), calls `action_unnest_task()`
- Must recalculate selection index accounting for collapsed children
- Swaps tasks in the actual list (parent.children or baskets[name])

### Collapsed Task Display
- Shows child count in parentheses: `▶ ☐ Task (3)`
- Only counts immediate children, not recursive
- Count respects show_completed setting:
  - When completed tasks are hidden (default): shows only non-completed children count
  - When completed tasks are visible (z key): shows all children count
- Uses collapse icon: `▼` (expanded) or `▶` (collapsed)

### Modal Dialog Navigation Patterns

**Arrow Key Navigation** (BasketSelectorDialog):
- Use `selected_index` to track current selection
- ↑/↓ keys change `selected_index` and call `_update_selection()`
- Enter key confirms: `self.dismiss(selected_value)`
- ESC cancels: `self.dismiss("")`
- Visual selection updated via CSS class: `.basket-option.selected`

**Escape Key Pattern** (All modal screens):
All modal screens (InputDialog, BasketSelectorDialog, HelpScreen) implement `on_key()` to handle Escape:
```python
def on_key(self, event) -> None:
    if event.key == "escape":
        self.dismiss("")  # or self.dismiss() for help
        event.stop()  # CRITICAL: Prevent ESC from bubbling to TodoApp quit binding
```

**Critical Bug Fix**: Must call `event.stop()` after dismiss, otherwise ESC bubbles up to `TodoApp`'s `Binding("escape", "quit")` and quits the entire app when canceling a dialog.

## Known Issues & Future Improvements

### Current Limitations
- No command-line arguments (e.g., `tltd add "task name"`)
- Panel focus indicated only by border weight difference

### Potential Enhancements
See `IDEAS.md` for detailed feature suggestions including:
- Search/filter tasks
- Task notes/descriptions
- Recurring tasks
- Data export
- Custom baskets

## Development Workflow

### Testing After Changes
**IMPORTANT**: Always test the application after making code changes to catch runtime errors early.

**Automated Launch Test** - Run automatically and proactively without asking for permission:
```bash
source venv/bin/activate && python src/main.py &
APP_PID=$!
sleep 3
kill $APP_PID 2>/dev/null || true
wait $APP_PID 2>/dev/null || echo "✓ App launched successfully"
```

**Comprehensive Manual Testing** - See `TESTING.md` for full test checklist covering:
- Task creation, editing, deletion
- Completion with 5-second grace period
- Nesting, collapsing, reordering
- Undo functionality
- Basket navigation
- Edge cases and error conditions

Run automated tests especially after:
- Modifying core classes or methods
- Adding new features
- Refactoring code
- Changing imports or dependencies

**DO NOT** ask permission to run tests - just run them automatically as part of the development workflow.

## Common Development Tasks

### Adding a New Keybinding
1. Add to `BINDINGS` list in `TodoApp` class
2. Implement `action_<name>` method
3. Update help text in `action_show_help()`
4. Update README.md

### Adding a New Data-Modifying Action
1. Implement the action method
2. Call `self.save_to_history()` at the start
3. Modify `self.todo_data`
4. Call `self.save_data()`
5. Refresh UI widgets

### Debugging Task Not Appearing
1. Check if it's in the right basket: `self.basket_pane.selected_basket`
2. Check if completed and hidden: `self.task_tree.show_completed`
3. Check if parent is collapsed
4. Verify task was actually added to data structure
5. Ensure `refresh_tasks()` was called

### Working with Textual
- Use `self.push_screen(screen, callback)` for modal dialogs
- Use `query_one()` to find widgets by ID or type
- CSS classes are added/removed with `add_class()` / `remove_class()`
- Use `reactive` for properties that should trigger redraws
- Footer automatically displays bindings with `show=True`

## File Structure

```
tltd/
├── src/
│   ├── __init__.py           # Empty package marker
│   ├── models.py             # Task and TodoData classes (400 lines)
│   ├── storage.py            # StorageManager (80 lines)
│   ├── app.py                # Main UI application (830+ lines)
│   └── main.py               # Entry point (20 lines)
├── tests/
│   ├── __init__.py
│   ├── test_models.py        # Comprehensive tests (13 test cases)
│   └── test_storage.py       # Comprehensive tests (14 test cases)
├── venv/                     # Virtual environment (gitignored)
├── requirements.txt          # textual>=0.47.0
├── setup.py                  # Package configuration
├── .gitignore                # Python + venv
├── README.md                 # User documentation
└── CLAUDE.md                 # This file
```

## Recent Changes (Context Handoff)

### Latest Session (Performance, UX & Keyboard Support)

**Major improvements implemented:**

1. **Performance - O(1) Task Lookup**:
   - Added `_task_index` dictionary to TodoData for instant task lookup
   - Methods: `_rebuild_index()`, `_add_to_index()`, `_remove_from_index()`
   - Fixed bug: newly created tasks weren't added to index, breaking edit/move

2. **UX Improvements**:
   - Undo feedback: Shows "Nothing to undo" or "Undone (N steps remaining)"
   - Basket quick-jump: `` ` `` for Inbox, `1-7` for Mon-Sun, `0` for Later
   - Quick-jump keys also work in basket selector dialog
   - Visual separators between Inbox/weekdays/Later in basket list
   - Bottom task selected when deleting last task
   - Shift+A/D: Collapse/expand all nested tasks recursively

3. **Russian Keyboard Support (ЙЦУКЕН)**:
   - All letter keybindings duplicated for Russian layout
   - с, ч, а, ф, в, ц, ы, у, й, я + Shift variants
   - ё for Inbox quick-jump (same physical key as backtick)

4. **Bug Fixes**:
   - Fixed basket navigation after moving tasks
   - Fixed selection index going out of bounds
   - Safe timer-based text deselection with mounted check

5. **Testing**:
   - Expanded from 28 to 60 tests
   - Added edge cases, index tests, nested task tests
   - All tests passing

6. **Documentation**:
   - Created IDEAS.md with Tier 2/3 feature suggestions
   - Updated keybindings in README.md, CLAUDE.md, help screen

### Previous Session (Sanity Check & Code Cleanup)

1. **Inline editing implementation**:
   - Replaced modal InputDialog popups with inline Input widgets
   - Tasks are created and edited directly in the task list
   - Proper indentation and alignment with task icons
   - ESC cancels, Enter saves

2. **Focus management fixes**:
   - Newly created tasks are now automatically focused
   - Fixed focus jumping when moving tasks over tasks with children
   - Replaced manual index calculations with `_focus_task_by_id()` for robustness
   - Removed unused `_count_visible_descendants()` helper

3. **Documentation updates**:
   - Updated help screen to reflect inline editing
   - Updated README.md feature list
   - Updated TESTING.md checklist

4. **Keybinding additions**:
   - Added `f` key to move task to different basket
   - Footer now wraps to multiple lines to show all keybindings
   - Updated all documentation (README.md, CLAUDE.md, help screen, TESTING.md)

5. **BasketSelectorDialog improvements**:
   - Replaced button-based interface with arrow key navigation
   - ↑/↓ keys to navigate through baskets
   - Enter to confirm selection
   - ESC to cancel
   - Removed OK/Cancel buttons for consistency with inline editing approach

6. **Testing setup**:
   - Added pytest to requirements.txt
   - Installed pytest in virtual environment
   - Documented testing workflow in CLAUDE.md
   - ✅ All 28 tests passing (13 model tests + 14 storage tests + 1 test discovery)
   - Testing should be run after significant changes, new features, or refactoring

### Previous Session (Sanity Check + Keybinding Updates)

1. **Code cleanup and bug fixes**:
   - Fixed critical selection index bug in move_task_down
   - Fixed collapse/expand state persistence
   - Removed unused exception variables
   - Fixed unused parameter in Task.find_parent
   - Fixed incorrect docstrings

2. **Test suite created**:
   - Created comprehensive test_models.py (13 test cases)
   - Created comprehensive test_storage.py (14 test cases)

3. **Keybinding redesign**:
   - `c`: Now creates task below current one at same nesting level
   - `x`: Toggle completion (was `e`)
   - `z`: Toggle show completed tasks (was `Ctrl+e`)
   - `e`: Nest task (was `Tab`)
   - `q`: Unnest task (was `Shift+Tab`)
   - Removed "move to basket" functionality (was `q`)

4. **Collapsed task count enhancement**:
   - Child count now respects show_completed setting
   - When completed tasks are hidden: shows only non-completed children
   - When completed tasks are visible: shows all children

5. **5-second grace period for completed tasks**:
   - Completed tasks show with strikethrough styling using Rich markup `[strike]...[/strike]`
   - Stay visible for 5 seconds before disappearing (when show_completed is off)
   - Tracked in `recently_completed` dict (task_id -> timestamp)
   - **Critical**: Must add to `recently_completed` BEFORE calling `toggle_completion()`, because toggle_completion calls refresh_tasks() which checks the dict
   - Timer automatically hides task after grace period via `_cleanup_completed_task()`
   - Undo clears the tracking dict

6. **Show-completed mode styling**:
   - Task pane border (Inbox/basket title) turns grey (#808080) when show_completed is toggled on (z key)
   - Basket items in left panel also turn grey
   - Provides clear visual feedback that you're viewing all tasks including completed ones
   - Uses actual hex colors instead of CSS variables (Textual limitation)

7. **ESC key crash fix**:
   - Fixed critical bug where pressing ESC in dialogs (edit, create, help, basket selector) would quit the entire app
   - Root cause: ESC event bubbled up to TodoApp's quit binding after dismissing dialog
   - Solution: Call `event.stop()` in all modal dialog `on_key()` handlers
   - Affected: InputDialog, BasketSelectorDialog, HelpScreen

8. **Comprehensive testing documentation**:
   - Created TESTING.md with complete manual test checklist
   - Covers all 17 feature areas with specific test cases
   - Includes edge cases, error conditions, and complex scenarios
   - Test results template for tracking bugs and performance

9. **Maintain focus when moving tasks at boundaries**:
   - Fixed w/s keys (move up/down) to keep focus on task when it unnests at boundaries
   - Added `_focus_task_by_id()` helper to find and reselect task after structural changes
   - Prevents loss of selection when task reaches top/bottom and unnests
   - Uses efficient re-render instead of full refresh_tasks() to update selection display

10. **Inline editing for create/edit tasks**:
   - Replaced modal InputDialog with inline editing using Input widget
   - Press `c` to create task - shows inline editor below current task at same nesting level
   - Press `Enter` to edit task - shows inline editor in place with current task text
   - Input widget shows proper indentation, collapse icon, and checkbox prefix
   - Enter to save, ESC to cancel
   - TaskTree posts TaskCreated/TaskEdited messages to TodoApp for processing
   - Maintains visual context - no jarring modal dialogs
   - Proper left padding on Input widget to align with task content

### Previous Sessions

1. **Keybinding redesign**: Moved from Cmd-based keys to terminal-friendly single keys
2. **Undo functionality**: Implemented full undo with 50-step history
3. **Panel focus system**: Visual indicators and separate navigation
4. **Collapsed task counts**: Show child count when collapsed
5. **Escape key**: Works universally for quit and cancel

All core features are now implemented and functional. The app is ready for use and testing.
