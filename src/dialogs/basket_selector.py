"""BasketSelectorDialog for moving tasks between baskets."""
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Label
from textual.screen import ModalScreen

from ..models import TodoData


class BasketSelectorDialog(ModalScreen[str]):
    """Modal dialog for selecting a basket."""

    def __init__(self):
        super().__init__()
        self.selected_index = 0

    def compose(self) -> ComposeResult:
        with Container(id="dialog-container"):
            yield Label("Move to basket (↑/↓ to select, Enter to confirm, ESC to cancel):", id="dialog-title")
            with Vertical(id="basket-list"):
                for i, basket in enumerate(TodoData.BASKETS):
                    label = Label(basket, classes="basket-option")
                    if i == self.selected_index:
                        label.add_class("selected")
                    yield label

    def _update_selection(self) -> None:
        """Update visual selection of basket items."""
        basket_list = self.query_one("#basket-list")
        labels = basket_list.query(".basket-option")
        for i, label in enumerate(labels):
            if i == self.selected_index:
                label.add_class("selected")
            else:
                label.remove_class("selected")

    # Quick-jump key mapping: key -> basket name
    QUICK_JUMP_KEYS = {
        "grave_accent": "Inbox",
        "1": "Monday",
        "2": "Tuesday",
        "3": "Wednesday",
        "4": "Thursday",
        "5": "Friday",
        "6": "Saturday",
        "7": "Sunday",
        "0": "Later",
    }

    def on_key(self, event) -> None:
        """Handle key presses."""
        if event.key == "escape":
            self.dismiss("")
            event.stop()  # Prevent ESC from reaching TodoApp quit binding
        elif event.key == "enter":
            self.dismiss(TodoData.BASKETS[self.selected_index])
            event.stop()
        elif event.key == "up":
            if self.selected_index > 0:
                self.selected_index -= 1
                self._update_selection()
            event.stop()
        elif event.key == "down":
            if self.selected_index < len(TodoData.BASKETS) - 1:
                self.selected_index += 1
                self._update_selection()
            event.stop()
        elif event.key in self.QUICK_JUMP_KEYS:
            # Quick-jump to basket and confirm
            self.dismiss(self.QUICK_JUMP_KEYS[event.key])
            event.stop()
