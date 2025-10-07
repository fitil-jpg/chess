from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QFont, QColor, QPalette, QPainter, QPen
from PySide6.QtCore import Qt
from core.constants import SYMBOLS


class Cell(QLabel):
    def __init__(self, row, col, drawer_manager=None, scale: float = 1.0):
        super().__init__()
        self.row = row
        self.col = col
        self.drawer_manager = drawer_manager
        self.scale = scale
        size = int(60 * scale)
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignCenter)
        self.setFont(QFont("Arial", max(1, int(28 * scale))))
        self.base_color = QColor("#eee") if (row + col) % 2 == 0 else QColor("#999")
        self.setAutoFillBackground(True)
        self.set_highlight(False)
        self._piece_symbol = None
        self.attack_count = 0
        self._border_highlight = False

    def set_piece(self, piece_symbol):
        self._piece_symbol = piece_symbol
        self.setText(SYMBOLS.get(piece_symbol, "") if piece_symbol else "")

    def set_highlight(self, active):
        palette = self.palette()
        # Use a greener highlight with higher opacity (less transparent)
        palette.setColor(
            QPalette.Window,
            QColor(46, 204, 113) if active else self.base_color,  # #2ecc71, fully opaque
        )
        palette.setColor(QPalette.WindowText, QColor("red") if active else QColor("black"))
        self.setPalette(palette)

    def set_attack_count(self, count):
        self.attack_count = count
        self.update()

    def set_border_highlight(self, active: bool):
        self._border_highlight = bool(active)
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
                d = int(17 * self.scale)
                painter.setBrush(QColor("#888"))
                painter.setPen(Qt.NoPen)
                painter.drawRect(0, 0, d, d)
                painter.setPen(Qt.white)
                painter.setFont(QFont("Arial", max(1, int(8 * self.scale))))
                painter.drawText(0, 0, d, d, Qt.AlignCenter, str(self.attack_count))
            else:  # пуста клітинка
                x, y, d = int(4 * self.scale), int(42 * self.scale), int(17 * self.scale)
                painter.setBrush(QColor("yellow"))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(x, y, d, d)
                painter.setPen(Qt.black)
                painter.setFont(QFont("Arial", max(1, int(8 * self.scale))))
                painter.drawText(x, y, d, d, Qt.AlignCenter, str(self.attack_count))

        for overlay_type, color in overlays:
            if overlay_type == "king_safe":
                painter.setBrush(QColor("#fff") if color == "white" else QColor("#222"))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(int(4 * self.scale), int(20 * self.scale), int(13 * self.scale), int(13 * self.scale))
            elif overlay_type == "king_attacked":
                painter.setBrush(QColor("red"))
                painter.setPen(Qt.NoPen)
                painter.setOpacity(0.6)  # Reduce transparency from full opacity to 60%
                painter.drawEllipse(int(4 * self.scale), int(20 * self.scale), int(13 * self.scale), int(13 * self.scale))
                painter.setOpacity(1.0)  # Reset opacity for other drawings
            elif overlay_type == "rook_defended":
                painter.setBrush(QColor("blue"))
                painter.setPen(Qt.NoPen)
                painter.drawRect(int(42 * self.scale), int(42 * self.scale), int(10 * self.scale), int(10 * self.scale))
            elif overlay_type == "knight_fork":
                painter.setBrush(QColor("magenta"))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(int(24 * self.scale), int(22 * self.scale), int(13 * self.scale), int(13 * self.scale))
            elif overlay_type == "queen_hanging":
                painter.setBrush(QColor("orange"))
                painter.setPen(Qt.NoPen)
                painter.drawRect(int(4 * self.scale), int(42 * self.scale), int(10 * self.scale), int(10 * self.scale))
            elif overlay_type == "pin":
                painter.setBrush(QColor("cyan"))
                painter.setPen(Qt.NoPen)
                painter.drawRect(int(42 * self.scale), int(4 * self.scale), int(10 * self.scale), int(10 * self.scale))
            elif overlay_type == "check":
                painter.setBrush(QColor("yellow"))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(int(42 * self.scale), int(4 * self.scale), int(10 * self.scale), int(10 * self.scale))
            elif overlay_type == "gradient":
                painter.setBrush(QColor(color))
                painter.setPen(Qt.NoPen)
                painter.setOpacity(0.4)
                painter.drawRect(0, 0, self.width(), self.height())
                painter.setOpacity(1.0)

        if self._border_highlight:
            pen = QPen(QColor("#ff8800"))
            pen.setWidth(max(2, int(3 * self.scale)))
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            inset = pen.width() // 2
            painter.drawRect(
                inset,
                inset,
                self.width() - inset * 2,
                self.height() - inset * 2,
            )
