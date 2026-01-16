# Changelog

All notable changes to TLTD (Terminal Todo List) are documented in this file.

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
