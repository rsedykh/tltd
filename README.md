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

### Using pipx (recommended)

```bash
pipx install git+https://github.com/rsedykh/tltd.git
```

Then run with:
```bash
tltd
```

### Development setup

1. Clone and create a virtual environment:
```bash
git clone https://github.com/rsedykh/tltd.git
cd tltd
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install in editable mode:
```bash
pip install -e ".[dev]"
```

3. Run tests:
```bash
pytest tests/ -v
```

## Usage

```bash
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
- `0`: Jump to Later

### Application
- `Esc`: Quit application
- `?`: Show help screen

## License

MIT
