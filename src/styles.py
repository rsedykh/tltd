"""CSS styles for the TLTD application."""

CSS = """
Screen {
    background: $surface;
}

#main-container {
    width: 100%;
    height: 100%;
}

#basket-pane {
    width: 20;
    border: solid $primary;
    padding: 1;
}

#basket-pane.focused {
    border: heavy $accent;
}

#task-pane {
    width: 1fr;
    border: solid $primary;
    padding: 1;
}

#task-pane.focused {
    border: heavy $accent;
}

#task-pane.show-completed-mode {
    border: solid #808080;
}

#task-pane.focused.show-completed-mode {
    border: heavy #808080;
}

.selected {
    background: $primary;
    color: $text;
}

.basket-item {
    padding: 0 1;
}

.basket-item.show-completed-mode {
    color: #808080;
}

.basket-item.selected.show-completed-mode {
    background: #1a1a1a;
    color: #808080;
}

.basket-separator {
    color: #555555;
    padding: 0 1;
}

.basket-separator.show-completed-mode {
    color: #404040;
}

#dialog-container {
    width: 60;
    height: auto;
    background: $surface;
    border: thick $primary;
    padding: 1 2;
}

#dialog-title {
    margin-bottom: 1;
    text-style: bold;
}

#basket-list {
    width: 100%;
    height: auto;
    margin-bottom: 1;
}

.basket-option {
    padding: 0 1;
}

#help-container {
    width: 80;
    height: auto;
    background: $surface;
    border: thick $primary;
    padding: 1 2;
}

#help-text {
    width: 100%;
    height: auto;
    margin-bottom: 1;
}

#description-dialog-container {
    width: 70;
    height: auto;
    max-height: 20;
    background: $surface;
    border: thick $primary;
    padding: 1 2;
}

#title-editor {
    width: 100%;
    margin-bottom: 1;
}

#description-editor {
    width: 100%;
    height: 10;
    margin-bottom: 1;
}

#description-hint {
    width: 100%;
}

Footer {
    height: auto;
}
"""
