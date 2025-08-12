# ui/panels.py
from PySide6.QtWidgets import QVBoxLayout, QFrame, QLabel

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
