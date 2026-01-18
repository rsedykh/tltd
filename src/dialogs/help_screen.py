"""HelpScreen dialog for displaying keyboard shortcuts."""
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Label, Button
from textual.screen import ModalScreen


HELP_TEXT = """
[bold]TLTD - Terminal Todo List[/bold]

[bold underline]Panel Switching:[/bold underline]
  ←/→         Switch between baskets and tasks panels

[bold underline]Navigation:[/bold underline]
  ↑/↓         Navigate up/down in current panel
              (In baskets: switch basket; In tasks: move between tasks)

[bold underline]Task Actions:[/bold underline]
  c           Create new task below current (inline editor, same nesting level)
  Shift+c     Create new task in Inbox (from any basket)
  Enter       Edit selected task (inline editor)
  v           Edit task (Ctrl+S to save, ESC to cancel)
  x           Toggle task completion (✓/☐)
  Backspace   Delete task and all children
  r           Move task to different basket
  z           Toggle show completed tasks
  Esc         Cancel inline editing

[bold underline]Collapsing:[/bold underline]
  a           Collapse task (hide children)
  d           Expand task (show children)
  Shift+a     Collapse task and all nested children
  Shift+d     Expand task and all nested children
  [dim]When collapsed, shows child count like: Task (3)[/dim]

[bold underline]Nesting (children move with task):[/bold underline]
  e           Nest task under previous sibling
  q           Unnest task one level up

[bold underline]Reordering:[/bold underline]
  w           Move task up in list
  s           Move task down in list
  [dim]Maintains nesting level intelligently[/dim]

[bold underline]Undo:[/bold underline]
  \\          Undo last action (up to 50 actions)

[bold underline]Multi-Select:[/bold underline]
  b           Mark/unmark task
  Esc         Clear all marks
  [dim]When marked: x/r/Backspace apply to all[/dim]

[bold underline]Quick Move / Basket Jump:[/bold underline]
  `           Inbox
  1-7         Monday through Sunday
  0           Later
  [dim]Tasks panel: moves task(s) to basket[/dim]
  [dim]Baskets panel: jumps to basket[/dim]

[bold underline]Application:[/bold underline]
  ?           Show this help
  Ctrl+c      Quit application

[dim]Data stored in: ~/.tltd/tasks.json[/dim]
"""


class HelpScreen(ModalScreen[None]):
    """Modal screen displaying help text."""

    def compose(self) -> ComposeResult:
        with Container(id="help-container"):
            yield Label(HELP_TEXT, id="help-text")
            yield Button("Close", variant="primary", id="close-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()

    def on_key(self, event) -> None:
        """Handle key presses."""
        if event.key == "escape":
            self.dismiss()
            event.stop()  # Prevent ESC from reaching TodoApp quit binding
