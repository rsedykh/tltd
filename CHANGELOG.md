# Changelog

All notable changes to TLTD (Terminal Todo List) are documented in this file.

## 2026-01-18

### Added
- **Dynamic week-aware baskets**: Replaced static weekday names with date-based storage
  - Week header shows "W: 03/26 (5/2)" format (week number, year, open/completed counts)
  - Days display as "Monday (2)", "Tuesday (0)", etc. under the week header
  - Automatic migration from old day-name format on first load
  - Week transition: incomplete tasks from old weeks move to Inbox at Monday 4am
  - Completed tasks stay archived (hidden from UI)
  - Hourly timer checks for week transition during long-running sessions
- 16 new tests for week functions and storage migration (95 total)
- **Quick move with number keys**: Move tasks directly to baskets without dialog
  - When tasks panel focused: `` ` ``, `1-7`, `0` move selected task(s) to basket
  - When baskets panel focused: same keys jump to basket (original behavior)
  - Works with multi-select (marked tasks move together)
  - Shows notification feedback ("Moved to Monday", etc.)
- **Crash logging**: Application errors now logged to `~/.tltd/crash.log`
  - Full tracebacks with timestamps
  - Log rotation at 1MB with 2 backup files
  - User notified of log file location on crash
- **Multi-select operations**: Mark tasks for bulk actions
  - `r` key marks/unmarks current task (Russian: `к`)
  - `Esc` clears all marks
  - Blue background highlight for marked tasks
  - Bulk operations apply to all marked: `x` (complete), number keys (move), `Backspace` (delete)
  - Marks auto-clear when switching baskets
- **Quick-add CLI command (`td`)**: Add tasks to Inbox from terminal
  - `td "Task title"` - add task with title
  - `td "Task title \\ description"` - add task with description
- **Raycast integration**: Script commands for macOS Raycast launcher
  - `td` - quick-add task to Inbox
  - `tltd` - open app in Terminal
  - Examples for iTerm2, Warp, and Kitty terminals
- New `raycast/` directory with script commands

### Changed
- **Data format**: Baskets now use date keys (YYYY-MM-DD) instead of day names
- `Esc` key now clears marks instead of quitting (use `Ctrl+C` to quit)
- Removed basket selector dialog (`r` key) - use number keys to move tasks directly
- Mark keybind changed: `b` → `r`
- **Modular code structure**: Split app.py (~1460 lines) into:
  - `src/widgets/` package (TaskLine, TaskTree, BasketPane)
  - `src/dialogs/` package (DescriptionEditorDialog, HelpScreen)
  - `src/styles.py` (CSS styles)
  - `src/app.py` now ~770 lines (orchestration only)

### Removed
- `src/dialogs/basket_selector.py` - no longer needed with quick-move feature

### Security
- Input validation limits:
  - Task titles: max 512 characters (enforced in UI and on load)
  - Task descriptions: max 4096 characters (validated on save and on load)
  - Nesting depth: max 8 levels (prevents recursion issues)
- Model-level input truncation in `Task.from_dict()` for defense-in-depth
- Log files now created with restrictive permissions (`0o600`)
- Backup files now created with restrictive permissions (`0o600`)

### Documentation
- Updated CLAUDE.md to reflect modular code structure
- Fixed test count (67 → 95) and added description field to data format example

## 2026-01-17

### Added
- **Task descriptions**: Optional description field for tasks
  - Press `v` (or `м` for Russian keyboard) to open editor modal
  - Descriptions display below task title (dimmed, truncated with "...")
  - TAB switches between title and description fields
  - Ctrl+S saves, ESC cancels
  - 4096 character limit
  - Backward compatible with existing data files
- 7 new description tests (67 total)

### Changed
- Collapse behavior: Collapsing a task now collapses its parent when no children remain visible

### Security
- Added `rich.markup.escape()` to prevent Rich markup injection in user content

### Fixed
- Added missing `Tuple` import to app.py
- README keybinding documentation: `f` → `r` for move task

## 2026-01-16

### Added
- Initial release of TLTD - Terminal Todo List
- Core hierarchical task management with infinite nesting
- Task persistence to `~/.tltd/tasks.json`
- Inline task editing (no modal dialogs)
- Task completion with 5-second grace period before hiding
- Collapsible tasks with child count indicators
- Eight basket categories: Inbox, Monday-Sunday, Later
- Undo history (50 steps) with visual feedback
- Help screen with keybinding reference
- Russian keyboard layout support (ЙЦУКЕН)
  - с, ч, к, ф, в, ц, ы, у, й, я and Shift variants
  - ё for Inbox quick-jump
- Basket quick-jump keybindings:
  - ` (backtick): Inbox
  - 1-7: Monday through Sunday
  - 0: Later
- Shift+C to create task in Inbox from any basket
- Shift+A/D to collapse/expand all nested tasks recursively
- Task index for O(1) lookup performance
- Visual separators between basket groups
- Comprehensive test suite (60 tests)

### Changed
- Move task keybind: `f` → `r`
- Auto-focus baskets panel when basket becomes empty
- Cursor placed at end of text when editing (not select all)

### Fixed
- Shift+C adds task at bottom of Inbox (not top)
- Newly created tasks added to index for edit/move operations
- Selection index bounds after moving/deleting tasks
- Safe timer-based widget operations with mounted check

### Security
- Restrictive file permissions: 0o700 for directory, 0o600 for data file
