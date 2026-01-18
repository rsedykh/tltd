"""BasketPane widget for the left sidebar."""
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Label
from textual.reactive import reactive

from ..models import TodoData


class BasketPane(Vertical):
    """Left sidebar showing available baskets."""

    selected_basket: reactive[str] = reactive("Inbox")
    show_completed_mode: reactive[bool] = reactive(False)

    def __init__(self, todo_data: TodoData):
        super().__init__()
        self.todo_data = todo_data
        self.border_title = "Baskets"

    def compose(self) -> ComposeResult:
        """Build the basket list."""
        for basket in TodoData.BASKETS:
            # Add separator after Inbox and before Later
            if basket == "Monday":
                yield Label("───────────", classes="basket-separator")
            count = self.todo_data.get_basket_count(basket)
            label = f"{basket} ({count})"
            widget = Label(label, classes="basket-item")
            if basket == self.selected_basket:
                widget.add_class("selected")
            yield widget
            if basket == "Sunday":
                yield Label("───────────", classes="basket-separator")

    def refresh_baskets(self) -> None:
        """Refresh basket counts and selection."""
        self.remove_children()
        for basket in TodoData.BASKETS:
            # Add separator after Inbox and before Later
            if basket == "Monday":
                sep = Label("───────────", classes="basket-separator")
                if self.show_completed_mode:
                    sep.add_class("show-completed-mode")
                self.mount(sep)
            count = self.todo_data.get_basket_count(basket)
            label = f"{basket} ({count})"
            widget = Label(label, classes="basket-item")
            if basket == self.selected_basket:
                widget.add_class("selected")
            if self.show_completed_mode:
                widget.add_class("show-completed-mode")
            self.mount(widget)
            if basket == "Sunday":
                sep = Label("───────────", classes="basket-separator")
                if self.show_completed_mode:
                    sep.add_class("show-completed-mode")
                self.mount(sep)

    def select_next(self) -> None:
        """Select next basket."""
        baskets = TodoData.BASKETS
        idx = baskets.index(self.selected_basket)
        self.selected_basket = baskets[(idx + 1) % len(baskets)]
        self.refresh_baskets()

    def select_previous(self) -> None:
        """Select previous basket."""
        baskets = TodoData.BASKETS
        idx = baskets.index(self.selected_basket)
        self.selected_basket = baskets[(idx - 1) % len(baskets)]
        self.refresh_baskets()
