# Changelog

All notable changes to TLTD (Terminal Todo List) are documented in this file.

## 2026-01-18

### Added
- **Quick-add CLI command (`td`)**: Add tasks to Inbox from terminal
  - `td "Task title"` - add task with title
  - `td "Task title \\ description"` - add task with description
- **Raycast integration**: Script commands for macOS Raycast launcher
  - `td` - quick-add task to Inbox
  - `tltd` - open app in Terminal
  - Examples for iTerm2, Warp, and Kitty terminals
- New `raycast/` directory with script commands

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
