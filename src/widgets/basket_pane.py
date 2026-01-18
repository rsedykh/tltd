"""BasketPane widget for the left sidebar."""
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Label
from textual.reactive import reactive

from ..models import (
    TodoData, get_current_week_dates, get_week_number,
    date_to_display_name
)


class BasketPane(Vertical):
    """Left sidebar showing available baskets."""

    selected_basket: reactive[str] = reactive("Inbox")
    show_completed_mode: reactive[bool] = reactive(False)

    def __init__(self, todo_data: TodoData):
        super().__init__()
        self.todo_data = todo_data
        self.border_title = "Baskets"
        # Mapping of selectable baskets in display order
        self._selectable_baskets: list[str] = []

    def _build_selectable_list(self) -> list[str]:
        """Build the list of selectable baskets in order."""
        baskets = ['Inbox']
        baskets.extend(get_current_week_dates())
        baskets.append('Later')
        return baskets

    def _get_week_header(self) -> str:
        """Get the week header string like 'W: 03/26 (5/2)'."""
        current_dates = get_current_week_dates()
        if current_dates:
            week_num, year = get_week_number(current_dates[0])
            open_count, completed_count = self.todo_data.get_week_task_counts()
            return f"W: {week_num:02d}/{year % 100} ({open_count}/{completed_count})"
        return ""

    def compose(self) -> ComposeResult:
        """Build the basket list."""
        self._selectable_baskets = self._build_selectable_list()
        current_week_dates = get_current_week_dates()

        # Inbox
        count = self.todo_data.get_basket_count('Inbox')
        label = f"Inbox ({count})"
        widget = Label(label, classes="basket-item")
        if 'Inbox' == self.selected_basket:
            widget.add_class("selected")
        yield widget

        # Separator before week
        yield Label("───────────", classes="basket-separator")

        # Week header (non-selectable)
        week_header = self._get_week_header()
        yield Label(week_header, classes="week-header")

        # Current week days
        for date_key in current_week_dates:
            day_name = date_to_display_name(date_key)
            count = self.todo_data.get_basket_count(date_key)
            label = f"{day_name} ({count})"
            widget = Label(label, classes="basket-item")
            if date_key == self.selected_basket:
                widget.add_class("selected")
            yield widget

        # Separator after week
        yield Label("───────────", classes="basket-separator")

        # Later
        count = self.todo_data.get_basket_count('Later')
        label = f"Later ({count})"
        widget = Label(label, classes="basket-item")
        if 'Later' == self.selected_basket:
            widget.add_class("selected")
        yield widget

    def refresh_baskets(self) -> None:
        """Refresh basket counts and selection."""
        self.remove_children()
        self._selectable_baskets = self._build_selectable_list()
        current_week_dates = get_current_week_dates()

        # Inbox
        count = self.todo_data.get_basket_count('Inbox')
        label = f"Inbox ({count})"
        widget = Label(label, classes="basket-item")
        if 'Inbox' == self.selected_basket:
            widget.add_class("selected")
        if self.show_completed_mode:
            widget.add_class("show-completed-mode")
        self.mount(widget)

        # Separator before week
        sep = Label("───────────", classes="basket-separator")
        if self.show_completed_mode:
            sep.add_class("show-completed-mode")
        self.mount(sep)

        # Week header (non-selectable)
        week_header = self._get_week_header()
        header_widget = Label(week_header, classes="week-header")
        if self.show_completed_mode:
            header_widget.add_class("show-completed-mode")
        self.mount(header_widget)

        # Current week days
        for date_key in current_week_dates:
            day_name = date_to_display_name(date_key)
            count = self.todo_data.get_basket_count(date_key)
            label = f"{day_name} ({count})"
            widget = Label(label, classes="basket-item")
            if date_key == self.selected_basket:
                widget.add_class("selected")
            if self.show_completed_mode:
                widget.add_class("show-completed-mode")
            self.mount(widget)

        # Separator after week
        sep = Label("───────────", classes="basket-separator")
        if self.show_completed_mode:
            sep.add_class("show-completed-mode")
        self.mount(sep)

        # Later
        count = self.todo_data.get_basket_count('Later')
        label = f"Later ({count})"
        widget = Label(label, classes="basket-item")
        if 'Later' == self.selected_basket:
            widget.add_class("selected")
        if self.show_completed_mode:
            widget.add_class("show-completed-mode")
        self.mount(widget)

    def select_next(self) -> None:
        """Select next basket."""
        baskets = self._selectable_baskets
        if not baskets:
            return
        try:
            idx = baskets.index(self.selected_basket)
            self.selected_basket = baskets[(idx + 1) % len(baskets)]
        except ValueError:
            self.selected_basket = baskets[0]
        self.refresh_baskets()

    def select_previous(self) -> None:
        """Select previous basket."""
        baskets = self._selectable_baskets
        if not baskets:
            return
        try:
            idx = baskets.index(self.selected_basket)
            self.selected_basket = baskets[(idx - 1) % len(baskets)]
        except ValueError:
            self.selected_basket = baskets[0]
        self.refresh_baskets()
