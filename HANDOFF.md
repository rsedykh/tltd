# Session Handoff

This file tracks recent changes for context handoff between Claude Code sessions.

## Latest Session (Code Sanitization & Bug Fixes)

**Changes made:**

1. **Code sanitization review** (using custom code-sanitizer agent):
   - Reviewed entire codebase for dead code, unused imports, naming consistency
   - Found zero dead code or unused imports - codebase is very clean
   - Identified 2 issues that needed fixing

2. **Fixed incorrect help text** (critical bug):
   - Help screen had wrong keybinding documentation: showed 'b' for marking tasks, actually 'r'
   - Removed incorrect "r moves tasks" line (it's number keys that move marked tasks)
   - Updated multi-select section to accurately describe behavior

3. **Consolidated duplicate constants** (DRY principle):
   - `MAX_TITLE_LENGTH`, `MAX_DESCRIPTION_LENGTH`, `MAX_NESTING_DEPTH` were defined in 3 places
   - Moved all to `models.py` as single source of truth
   - Updated `app.py` and `description_editor.py` to import from models

4. **Added custom agents to project**:
   - Moved 5 custom agents from user config to `.claude/agents/`:
     - code-sanitizer.md (for code quality reviews)
     - security-researcher.md (for security audits)
     - code-merge-architect.md (for complex merges)
     - quick-task-executor.md (for quick tasks)
     - middle-dev.md (for mid-level development)
   - Updated `.gitignore` to exclude local Claude Code settings

**Files changed:**
- `src/dialogs/help_screen.py` (fixed keybinding documentation)
- `src/models.py` (added MAX_NESTING_DEPTH constant)
- `src/app.py` (removed duplicate constants, import from models)
- `src/dialogs/description_editor.py` (removed duplicate constants, import from models)
- `.claude/agents/` (added 5 agent files)
- `.gitignore` (added Claude Code local settings)

**Tests:** 95 passing

**Code quality:** Excellent - no dead code, no unused imports, consistent naming, proper architecture

---

## Previous Session (Dynamic Weeks Feature)

**Major feature implemented:**

1. **Dynamic week-aware baskets**:
   - Replaced static weekday baskets (Monday-Sunday) with date-based keys (YYYY-MM-DD format)
   - Week header shows "W: 03/26 (5/2)" format (week number, open/completed counts)
   - Days display as "Monday (2)", "Tuesday (0)", etc. under the week header
   - Automatic migration from old day-name format to new date-based format on first load

2. **Week transition logic**:
   - At Monday 4am (or on app startup), incomplete tasks from old weeks move to Inbox
   - Completed tasks stay archived in old week data (hidden from UI)
   - Hourly timer checks for week transition during long-running sessions
   - User notification when tasks are moved

3. **Keybinding changes**:
   - Removed `r` keybind for basket selector dialog (no longer needed)
   - Changed `b` → `r` for mark/toggle action
   - Russian keyboard: `и` → `к` for mark action
   - Move tasks by selecting them and pressing basket number keys (` 1-7 0)

4. **Removed BasketSelectorDialog**:
   - Deleted `src/dialogs/basket_selector.py`
   - Updated `src/dialogs/__init__.py`
   - Removed import and `action_move_task` from app.py

**Files changed:**
- `src/models.py` (new week/date functions, dynamic baskets, week transition)
- `src/storage.py` (migration detection and auto-save)
- `src/widgets/basket_pane.py` (week header, date-to-day-name display)
- `src/app.py` (week transition on mount, hourly timer, updated jump actions)
- `src/styles.py` (week-header CSS class)
- `src/dialogs/basket_selector.py` (DELETED)
- `src/dialogs/__init__.py` (removed BasketSelectorDialog)
- `tests/test_models.py` (TestWeekFunctions class, updated tests for date baskets)
- `tests/test_storage.py` (TestStorageMigration class)
- `tests/test_multiselect.py` (updated to use date keys)

**Tests:** 95 passing

---

## Previous Session (Documentation & Security Hardening)

**Changes made:**

1. **Updated CLAUDE.md** (was outdated after modular refactoring):
   - Core Components section now reflects modular structure (`src/widgets/`, `src/dialogs/`, `src/styles.py`, `src/quick_add.py`)
   - Test count updated from 67 to 79
   - Data format example now includes `description` field
   - Keybinding instructions reference `src/dialogs/help_screen.py` instead of `action_show_help()`

2. **Security hardening** (defense-in-depth):
   - `src/models.py`: Added `MAX_TITLE_LENGTH` and `MAX_DESCRIPTION_LENGTH` constants; `Task.from_dict()` now truncates on load to protect against manually edited JSON files
   - `src/main.py`: Log directory created with `0o700`, log file set to `0o600` permissions
   - `src/storage.py`: Backup files now get `0o600` permissions (consistent with data files)

**Files changed:**
- `CLAUDE.md` (documentation updates)
- `src/models.py` (input validation on load)
- `src/main.py` (log file permissions)
- `src/storage.py` (backup file permissions)

**Tests:** 79 passing

---

## Previous Session (Quick Move Feature)

**Feature implemented:**

1. **Quick move tasks with number keys**:
   - When tasks panel is focused: `` ` ``, `1-7`, `0` now move selected task(s) to that basket
   - When baskets panel is focused: same keys jump to basket (original behavior)
   - Supports multi-select (marked tasks move together)
   - Shows notification: "Moved to Monday", "Already in Inbox", etc.
   - Handles empty basket after move (auto-focuses baskets panel)

**Files changed:**
- `src/app.py` (modified `_jump_to_basket()` method)
- `src/dialogs/help_screen.py` (updated help text)

**Tests:** 79 passing

---

## Previous Session (Crash Logging)

**Feature implemented:**

1. **Crash logging to file**:
   - Crashes now write full tracebacks to `~/.tltd/crash.log`
   - Includes timestamps via Python's logging module
   - Log rotation: 1MB max size, keeps 2 backup files (crash.log.1, crash.log.2)
   - User sees error message + log file path on crash

**Files changed:**
- `src/main.py` (added logging setup, traceback capture)

**Tests:** 79 passing

---

## Previous Session (Multi-Select Operations)

**Major feature implemented:**

1. **Multi-select for bulk operations**:
   - `r` key marks/unmarks tasks (Russian: `к`)
   - `Esc` clears all marks
   - Marked tasks show blue background highlight (`.marked` CSS class)
   - When tasks are marked, bulk operations apply to all:
     - `x` - complete/uncomplete all marked
     - Number keys - move all marked to selected basket
     - `Backspace` - delete all marked
   - Marks automatically clear when switching baskets
   - Single undo restores all tasks from bulk operation

2. **Keybinding changes**:
   - `Esc` no longer quits app (now clears marks only)
   - Use `Ctrl+C` to quit

3. **Tests**:
   - Added `tests/test_multiselect.py` with 12 tests
   - Total: 95 tests passing

**Files changed:**
- `src/app.py` (new keybindings, bulk operation logic)
- `src/widgets/task_tree.py` (marked_task_ids state, mark methods)
- `src/styles.py` (`.marked` CSS classes)
- `src/dialogs/help_screen.py` (multi-select section)
- `README.md` (multi-select keybindings)
- `tests/test_multiselect.py` (new)

---

## Previous Session (Modular Refactoring & Security Hardening)

**Major refactoring:**

1. **Split app.py into modular structure**:
   - `src/styles.py` - CSS styles extracted (~130 lines)
   - `src/widgets/` - UI components package
     - `task_line.py` - TaskLine widget
     - `task_tree.py` - TaskTree widget with Messages
     - `basket_pane.py` - BasketPane widget
   - `src/dialogs/` - Modal screens package
     - `description_editor.py` - DescriptionEditorDialog
     - `help_screen.py` - HelpScreen + HELP_TEXT constant
   - `src/app.py` reduced from ~1460 to ~770 lines

2. **Security hardening (based on security audit)**:
   - `MAX_TITLE_LENGTH = 512` - enforced in UI via Input max_length
   - `MAX_DESCRIPTION_LENGTH = 4096` - validated on save with user feedback
   - `MAX_NESTING_DEPTH = 8` - prevents stack overflow from deep recursion

**Files changed:**
- `src/app.py` (refactored, added constants)
- `src/styles.py` (new)
- `src/widgets/__init__.py` (new)
- `src/widgets/task_line.py` (new)
- `src/widgets/task_tree.py` (new)
- `src/widgets/basket_pane.py` (new)
- `src/dialogs/__init__.py` (new)
- `src/dialogs/description_editor.py` (new)
- `src/dialogs/help_screen.py` (new)

**Code quality:** Ran code-sanitizer and security-researcher agents - codebase is clean.

---

## Previous Sessions (Summary)

- **Raycast Quick-Add Integration**: CLI command `td "Task"` and Raycast scripts
- **Task Descriptions**: `v` key opens description editor modal
- **pipx Packaging**: Modern Python packaging with pyproject.toml
- **Performance O(1) Lookup**: Task index for instant lookups
- **UX Improvements**: Undo feedback, basket quick-jump, visual separators
- **Russian Keyboard Support**: Full ЙЦУКЕН layout support
- **Inline Editing**: No modal dialogs for create/edit

All core features are now implemented and functional. The app is ready for use and testing.
