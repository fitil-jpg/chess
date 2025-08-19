from PySide6.QtWidgets import QWidget, QListWidget, QVBoxLayout, QLabel


class RunSelectorWindow(QWidget):
    """Window that displays available recorded runs."""

    def __init__(self, runs):
        super().__init__()
        self.setWindowTitle("Run Selector")
        self.runs = list(runs)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Available runs"))

        self.list_widget = QListWidget()
        for run in self.runs:
            game_id = run.get("game_id", "<unknown>")
            self.list_widget.addItem(game_id)
        layout.addWidget(self.list_widget)
