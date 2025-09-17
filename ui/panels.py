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


def create_heatmap_panel(
    piece_callback,
    *,
    set_callback=None,
    sets=None,
    pieces=None,
    current_set=None,
    current_piece=None,
):
    """Return a panel that allows choosing the heatmap set and pattern.

    ``piece_callback`` is invoked with the selected piece name or ``None`` when
    the selection is cleared.  ``set_callback`` (when provided) receives the
    newly selected heatmap set name.
    """

    layout = QVBoxLayout()

    # Heatmap set selector -------------------------------------------------
    layout.addWidget(QLabel("Heatmap set"))
    set_combo = QComboBox()
    set_items = list(sets or [])
    for item in set_items:
        set_combo.addItem(item)
    if current_set and current_set in set_items:
        idx = set_combo.findText(current_set)
        if idx >= 0:
            set_combo.setCurrentIndex(idx)
    if set_callback is not None:
        set_combo.currentTextChanged.connect(set_callback)
    layout.addWidget(set_combo)

    # Heatmap piece/pattern selector --------------------------------------
    layout.addWidget(QLabel("Heatmap piece"))
    piece_combo = QComboBox()
    piece_combo.addItem("none")
    piece_items = list(pieces) if pieces is not None else PIECE_TYPES
    for name in piece_items:
        piece_combo.addItem(name)

    if current_piece:
        idx = piece_combo.findText(current_piece)
        if idx >= 0:
            piece_combo.setCurrentIndex(idx)
    elif current_piece is None:
        piece_combo.setCurrentIndex(0)

    def _on_piece_change(text: str):
        piece_callback(text if text != "none" else None)

    piece_combo.currentTextChanged.connect(_on_piece_change)
    layout.addWidget(piece_combo)
    return layout, set_combo, piece_combo

