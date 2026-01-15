# TLTD - Terminal Todo List

A terminal-based todo application with hierarchical tasks, inspired by Workflowy.

## Features

- **Multiple Baskets**: Organize tasks into Inbox, Monday-Sunday, and Later
- **Hierarchical Tasks**: Nest tasks infinitely for better organization
- **Inline Editing**: Create and edit tasks directly in the list without popups
- **Collapsible Trees**: Collapse/expand task groups
- **Task Completion**: Complete tasks with 5-second strikethrough grace period
- **Undo**: Full undo support (up to 50 actions)
- **Persistent Storage**: Data saved to `~/.tltd/tasks.json`

## Installation

1. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run tests (optional):
```bash
pytest tests/ -v
```

## Usage

Run the application:
```bash
python src/main.py
```

Or install and run as a command:
```bash
pip install -e .
tltd
```

## Keyboard Shortcuts

### Panel Switching
- `←/→`: Switch between baskets and tasks panels

### Navigation
- `↑/↓`: Navigate in current panel (baskets or tasks)

### Task Actions
- `c`: Create new task below current (inline editor, same nesting level)
- `Enter`: Edit selected task (inline editor)
- `x`: Toggle task completion
- `Backspace`: Delete task and all children
- `f`: Move task to different basket
- `z`: Toggle "show completed tasks"
- `Esc`: Cancel inline editing

### Collapsing
- `a`: Collapse task (hide children)
- `d`: Expand task (show children)

### Nesting (children move with task)
- `e`: Nest task under previous sibling
- `q`: Unnest task one level up

### Reordering
- `w`: Move task up in list
- `s`: Move task down in list

### Undo
- `\`: Undo last action (up to 50 actions)

### Quick Basket Jump
- `` ` ``: Jump to Inbox
- `1-7`: Jump to Monday through Sunday
- `=`: Jump to Later

### Application
- `Esc`: Quit application
- `?`: Show help screen

## License

MIT
