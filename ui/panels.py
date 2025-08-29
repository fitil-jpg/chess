# ui/panels.py
from PySide6.QtWidgets import QVBoxLayout, QFrame, QLabel, QComboBox

def create_metrics_panel(side: str, output_labels, left=False, endgame_label=None):
    layout = QVBoxLayout()
    if endgame_label:
        endgame_label.setText("")
        endgame_label.setVisible(False)
        layout.addWidget(endgame_label)
    layout.addWidget(QLabel(f"♟ {side} Army Metrics"))
    for lbl in output_labels:
        lbl.setText("-")
        layout.addWidget(lbl)
    layout.addSpacing(10)
    layout.addWidget(QLabel(f"🧠 {side} Strategy Balance"))
    for text in [
        "Center ████████░░░░ 80%",
        "King    ██████░░░░░░ 60%",
        "Mob     █████░░░░░░░ 50%"
    ]:
        layout.addWidget(QLabel(text))
    layout.addSpacing(10)
    box = QVBoxLayout()
    box_frame = QFrame()
    box_frame.setLayout(box)
    box_frame.setStyleSheet("border: 1px solid black; padding: 4px;")
    layout.addWidget(box_frame)
    return layout


PIECE_TYPES = ["pawn", "knight", "bishop", "rook", "queen", "king"]


def create_heatmap_panel(callback):
    """Return a panel with a combo box to toggle heatmaps by piece type.

    ``callback`` is invoked with the selected piece name or ``None`` when the
    selection is cleared.
    """

    layout = QVBoxLayout()
    layout.addWidget(QLabel("Heatmap piece"))
    combo = QComboBox()
    combo.addItem("none")
    for p in PIECE_TYPES:
        combo.addItem(p)

    def _on_change(text: str):
        callback(text if text != "none" else None)

    combo.currentTextChanged.connect(_on_change)
    layout.addWidget(combo)
    return layout, combo

