"""DescriptionEditorDialog for editing task title and description."""
from typing import Tuple, Optional
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Label, Input, TextArea
from textual.screen import ModalScreen


class DescriptionEditorDialog(ModalScreen[Optional[Tuple[str, str]]]):
    """Modal dialog for editing task title and description."""

    def __init__(self, task_title: str, current_description: str):
        super().__init__()
        self.task_title = task_title
        self.current_description = current_description

    MAX_TITLE_LENGTH = 512
    MAX_DESCRIPTION_LENGTH = 4096

    def compose(self) -> ComposeResult:
        with Container(id="description-dialog-container"):
            yield Input(value=self.task_title, id="title-editor", max_length=self.MAX_TITLE_LENGTH)
            yield TextArea(self.current_description, id="description-editor")
            yield Label(f"[dim]TAB to switch, Ctrl+S to save, ESC to cancel (max {self.MAX_DESCRIPTION_LENGTH} chars)[/dim]", id="description-hint")

    def on_mount(self) -> None:
        """Focus the description text area when dialog opens."""
        text_area = self.query_one("#description-editor", TextArea)
        text_area.focus()
        # Move cursor to the very end of text
        if self.current_description:
            lines = self.current_description.split('\n')
            last_line_idx = len(lines) - 1
            last_line_len = len(lines[-1])
            text_area.cursor_location = (last_line_idx, last_line_len)

    def on_key(self, event) -> None:
        """Handle key presses."""
        if event.key == "escape":
            self.dismiss(None)  # None signals cancel
            event.stop()
        elif event.key == "tab":
            # Handle TAB manually to control cursor position
            title_input = self.query_one("#title-editor", Input)
            text_area = self.query_one("#description-editor", TextArea)

            # Check which widget currently has focus and switch
            if text_area.has_focus:
                title_input.focus()
                # Move cursor to end without selection (like inline editing)
                def deselect():
                    try:
                        if title_input.is_mounted:
                            title_input.action_end()
                    except Exception:
                        pass
                self.set_timer(0.01, deselect)
            else:
                text_area.focus()
            event.stop()
        elif event.key == "shift+tab":
            # Handle Shift+TAB (reverse direction)
            title_input = self.query_one("#title-editor", Input)
            text_area = self.query_one("#description-editor", TextArea)

            if title_input.has_focus:
                text_area.focus()
            else:
                title_input.focus()
                def deselect():
                    try:
                        if title_input.is_mounted:
                            title_input.action_end()
                    except Exception:
                        pass
                self.set_timer(0.01, deselect)
            event.stop()
        elif event.key == "ctrl+s":
            title_input = self.query_one("#title-editor", Input)
            text_area = self.query_one("#description-editor", TextArea)
            new_title = title_input.value.strip()
            if not new_title:
                self.notify("Title cannot be empty", severity="warning", timeout=2)
                event.stop()
                return
            if len(text_area.text) > self.MAX_DESCRIPTION_LENGTH:
                self.notify(f"Description too long (max {self.MAX_DESCRIPTION_LENGTH} chars)", severity="warning", timeout=2)
                event.stop()
                return
            self.dismiss((new_title, text_area.text))
            event.stop()
