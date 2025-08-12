from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QFont, QColor, QPalette, QPainter
from PySide6.QtCore import Qt
from core.constants import SYMBOLS

class Cell(QLabel):
    def __init__(self, row, col, drawer_manager=None):
        super().__init__()
        self.row = row
        self.col = col
        self.drawer_manager = drawer_manager
        self.setFixedSize(60, 60)
        self.setAlignment(Qt.AlignCenter)
        self.setFont(QFont("Arial", 28))
        self.base_color = QColor("#eee") if (row + col) % 2 == 0 else QColor("#999")
        self.setAutoFillBackground(True)
        self.set_highlight(False)
        self._piece_symbol = None
        self.attack_count = 0

    def set_piece(self, piece_symbol):
        self._piece_symbol = piece_symbol
        self.setText(SYMBOLS.get(piece_symbol, "") if piece_symbol else "")

    def set_highlight(self, active):
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("#ffcc00") if active else self.base_color)
        self.setPalette(palette)

    def set_attack_count(self, count):
        self.attack_count = count
        self.update()
def paintEvent(self, event):
    super().paintEvent(event)
    painter = QPainter(self)
    overlays = []
    if self.drawer_manager:
        overlays = self.drawer_manager.get_cell_overlays(self.row, self.col)
    # Якщо є атака
    if self.attack_count > 0:
        if self._piece_symbol:  # є фігура
            painter.setBrush(QColor("#888"))
            painter.setPen(Qt.NoPen)
            painter.drawRect(0, 0, 17, 17)
            painter.setPen(Qt.white)
            painter.setFont(QFont("Arial", 8))
            painter.drawText(0, 0, 17, 17, Qt.AlignCenter, str(self.attack_count))
        else:  # пуста клітинка
            x, y, d = 4, 42, 17  # зліва знизу!
            painter.setBrush(QColor("yellow"))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(x, y, d, d)
            painter.setPen(Qt.black)
            painter.setFont(QFont("Arial", 8))
            painter.drawText(x, y, d, d, Qt.AlignCenter, str(self.attack_count))
    for overlay_type, color in overlays:
        if overlay_type == "king_safe":
            painter.setBrush(QColor("#fff") if color == "white" else QColor("#222"))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(4, 20, 13, 13)
        elif overlay_type == "king_attacked":
            painter.setBrush(QColor("red"))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(4, 20, 13, 13)
        elif overlay_type == "rook_defended":
            painter.setBrush(QColor("blue"))
            painter.setPen(Qt.NoPen)
            painter.drawRect(42, 42, 10, 10)
        elif overlay_type == "knight_fork":
            painter.setBrush(QColor("magenta"))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(24, 22, 13, 13)
        elif overlay_type == "queen_hanging":
            painter.setBrush(QColor("orange"))
            painter.setPen(Qt.NoPen)
            painter.drawRect(4, 42, 10, 10)
        elif overlay_type == "pin":
            painter.setBrush(QColor("cyan"))
            painter.setPen(Qt.NoPen)
            painter.drawRect(42, 4, 10, 10)
        elif overlay_type == "check":
            painter.setBrush(QColor("yellow"))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(42, 4, 10, 10)
