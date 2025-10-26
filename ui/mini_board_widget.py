"""
Mini Board Widget for Heatmap Tab

Displays a small chess board with overlays for:
- Heatmap intensities (red gradient)
- BSP zones (blue gradient)
- Tactical patterns (purple gradient for minimax > 10%)
- Current move evaluation (green cell)
- Guardrails statistics
"""

import time
import logging
from typing import Optional, Dict, List, Tuple, Any
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt, QTimer, QRect, QSize
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont
import chess

from core.move_object import MoveObject
from utils.timing_config import get_timing_config

logger = logging.getLogger(__name__)


class MiniBoardWidget(QWidget):
    """
    Mini chess board widget with multiple overlays.

    Displays:
    - Chess pieces (simplified)
    - Heatmap overlay (red gradient)
    - BSP zones overlay (blue gradient)
    - Tactical squares (purple gradient for minimax > 10%)
    - Current evaluation cell (green highlight with animation)
    - Guardrails statistics
    """

    def __init__(self, parent=None, cell_size: int = 40):
        super().__init__(parent)
        self.cell_size = cell_size
        self.board_size = 8
        self.config = get_timing_config()

        # Board state
        self.board: Optional[chess.Board] = None
        self.current_move: Optional[MoveObject] = None

        # Overlay data
        self.heatmap_data: Dict[chess.Square, float] = {}  # 0.0 to 1.0
        self.bsp_zones: Dict[chess.Square, Tuple[str, float]] = {}  # (zone_type, control)
        self.tactical_squares: Dict[chess.Square, float] = {}  # minimax value
        self.current_eval_square: Optional[chess.Square] = None
        self.guardrails_stats: Dict[str, Any] = {}

        # Animation state
        self.green_cell_alpha = 1.0
        self.animation_direction = -1  # -1 for fading out, 1 for fading in

        # Setup UI
        self._setup_ui()

        # Setup animation timer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._animate_green_cell)
        if self.config.animate_transitions:
            self.animation_timer.start(self.config.cell_animation_delay_ms)

    def _setup_ui(self):
        """Setup the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Title
        title = QLabel("🔬 Move Evaluation Board")
        title.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(title)

        # Info panel
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 3px;
                padding: 5px;
                font-size: 10px;
            }
        """)
        layout.addWidget(self.info_label)

        # Board frame
        self.board_frame = QFrame()
        self.board_frame.setFixedSize(
            self.cell_size * self.board_size + 2,
            self.cell_size * self.board_size + 2
        )
        self.board_frame.setFrameStyle(QFrame.Box | QFrame.Plain)
        layout.addWidget(self.board_frame)

        # Legend
        legend_layout = QHBoxLayout()
        legend_items = [
            ("🔴", "Heatmap"),
            ("🔵", "BSP Zones"),
            ("🟣", "Tactical (>10%)"),
            ("🟢", "Current Eval")
        ]
        for color, label_text in legend_items:
            label = QLabel(f"{color} {label_text}")
            label.setStyleSheet("font-size: 9px;")
            legend_layout.addWidget(label)
        layout.addLayout(legend_layout)

        # Guardrails stats
        self.guardrails_label = QLabel()
        self.guardrails_label.setWordWrap(True)
        self.guardrails_label.setStyleSheet("""
            QLabel {
                background-color: #fff3cd;
                border: 1px solid #ffc107;
                border-radius: 3px;
                padding: 5px;
                font-size: 9px;
            }
        """)
        layout.addWidget(self.guardrails_label)

        layout.addStretch()

        self._update_info_label()

    def set_board(self, board: chess.Board):
        """Set the chess board to display."""
        self.board = board
        self.update()

    def set_current_move(self, move_obj: MoveObject):
        """Set the current move being evaluated."""
        self.current_move = move_obj

        # Update heatmap data
        if move_obj.active_heatmap_piece and move_obj.heatmap_intensity:
            self.heatmap_data[move_obj.move.to_square] = move_obj.heatmap_intensity

        # Update BSP zones
        if move_obj.bsp_zone_type and move_obj.bsp_zone_control:
            for square in move_obj.bsp_zone_cells:
                self.bsp_zones[square] = (move_obj.bsp_zone_type, move_obj.bsp_zone_control)

        # Update tactical squares (minimax > 10%)
        if move_obj.meets_minimax_threshold and move_obj.minimax_value:
            self.tactical_squares[move_obj.move.to_square] = move_obj.minimax_value

        # Set current evaluation square
        self.current_eval_square = move_obj.move.to_square

        # Update guardrails
        self.guardrails_stats = {
            'passed': move_obj.guardrails_passed,
            'warnings': move_obj.guardrails_warnings,
            'active_methods': len(move_obj.get_active_methods())
        }

        self._update_info_label()
        self._update_guardrails_label()
        self.update()

    def set_heatmap_data(self, heatmap: Dict[chess.Square, float]):
        """Set heatmap overlay data."""
        self.heatmap_data = heatmap.copy()
        self.update()

    def set_bsp_zones(self, zones: Dict[chess.Square, Tuple[str, float]]):
        """Set BSP zone overlay data."""
        self.bsp_zones = zones.copy()
        self.update()

    def set_tactical_squares(self, tactical: Dict[chess.Square, float]):
        """Set tactical squares overlay data."""
        self.tactical_squares = tactical.copy()
        self.update()

    def set_current_eval_square(self, square: Optional[chess.Square]):
        """Set the square currently being evaluated (green highlight)."""
        self.current_eval_square = square
        self.update()

    def clear_overlays(self):
        """Clear all overlay data."""
        self.heatmap_data.clear()
        self.bsp_zones.clear()
        self.tactical_squares.clear()
        self.current_eval_square = None
        self.guardrails_stats.clear()
        self._update_info_label()
        self._update_guardrails_label()
        self.update()

    def _animate_green_cell(self):
        """Animate the green cell highlight (pulsing effect)."""
        if not self.config.animate_transitions or self.current_eval_square is None:
            return

        # Pulse animation
        delta = 0.05 * self.animation_direction
        self.green_cell_alpha += delta

        if self.green_cell_alpha <= 0.3:
            self.green_cell_alpha = 0.3
            self.animation_direction = 1
        elif self.green_cell_alpha >= 1.0:
            self.green_cell_alpha = 1.0
            self.animation_direction = -1

        self.update()

    def _update_info_label(self):
        """Update the information label."""
        if not self.current_move:
            self.info_label.setText("No move being evaluated")
            return

        info_parts = []
        info_parts.append(f"<b>Move:</b> {self.current_move.move.uci()}")
        info_parts.append(f"<b>Stage:</b> {self.current_move.current_stage.value}")
        info_parts.append(f"<b>Score:</b> {self.current_move.final_score:.2f}")

        if self.current_move.active_heatmap_piece:
            info_parts.append(f"<b>Heatmap:</b> {self.current_move.active_heatmap_piece}")

        if self.current_move.bsp_zone_type:
            info_parts.append(f"<b>BSP Zone:</b> {self.current_move.bsp_zone_type}")

        if self.current_move.tactical_motifs:
            info_parts.append(f"<b>Tactics:</b> {', '.join(self.current_move.tactical_motifs)}")

        self.info_label.setText("<br>".join(info_parts))

    def _update_guardrails_label(self):
        """Update the guardrails statistics label."""
        if not self.guardrails_stats:
            self.guardrails_label.setText("No guardrails data")
            return

        parts = []
        if self.guardrails_stats.get('passed'):
            parts.append("✅ <b>Guardrails:</b> PASSED")
        else:
            parts.append("⚠️ <b>Guardrails:</b> FAILED")
            warnings = self.guardrails_stats.get('warnings', [])
            if warnings:
                parts.append(f"<b>Warnings:</b> {', '.join(warnings)}")

        active_methods = self.guardrails_stats.get('active_methods', 0)
        parts.append(f"<b>Active Methods:</b> {active_methods}")

        self.guardrails_label.setText("<br>".join(parts))

    def paintEvent(self, event):
        """Paint the mini board with overlays."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw board background
        for rank in range(8):
            for file in range(8):
                square = chess.square(file, 7 - rank)
                x = file * self.cell_size
                y = rank * self.cell_size

                # Base square color
                is_light = (rank + file) % 2 == 0
                base_color = QColor(240, 217, 181) if is_light else QColor(181, 136, 99)
                painter.fillRect(x, y, self.cell_size, self.cell_size, base_color)

        # Draw overlays in order (bottom to top)
        self._draw_heatmap_overlay(painter)
        self._draw_bsp_zones_overlay(painter)
        self._draw_tactical_overlay(painter)
        self._draw_current_eval_overlay(painter)

        # Draw pieces
        if self.board:
            self._draw_pieces(painter)

        # Draw grid lines
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        for i in range(9):
            painter.drawLine(i * self.cell_size, 0, i * self.cell_size, 8 * self.cell_size)
            painter.drawLine(0, i * self.cell_size, 8 * self.cell_size, i * self.cell_size)

    def _draw_heatmap_overlay(self, painter: QPainter):
        """Draw heatmap overlay (red gradient)."""
        for square, intensity in self.heatmap_data.items():
            file = chess.square_file(square)
            rank = 7 - chess.square_rank(square)
            x = file * self.cell_size
            y = rank * self.cell_size

            # Red gradient based on intensity
            alpha = int(intensity * 150)  # Max 150 for visibility
            color = QColor(255, 0, 0, alpha)
            painter.fillRect(x, y, self.cell_size, self.cell_size, color)

    def _draw_bsp_zones_overlay(self, painter: QPainter):
        """Draw BSP zones overlay (blue gradient)."""
        for square, (zone_type, control) in self.bsp_zones.items():
            file = chess.square_file(square)
            rank = 7 - chess.square_rank(square)
            x = file * self.cell_size
            y = rank * self.cell_size

            # Blue gradient based on control value
            alpha = int(control * 100)  # Lighter than heatmap
            color = QColor(0, 100, 255, alpha)
            painter.fillRect(x, y, self.cell_size, self.cell_size, color)

    def _draw_tactical_overlay(self, painter: QPainter):
        """Draw tactical squares overlay (purple gradient for minimax > 10%)."""
        for square, value in self.tactical_squares.items():
            file = chess.square_file(square)
            rank = 7 - chess.square_rank(square)
            x = file * self.cell_size
            y = rank * self.cell_size

            # Purple gradient based on minimax value
            alpha = int(min(abs(value) * 10, 1.0) * 120)
            color = QColor(128, 0, 128, alpha)
            painter.fillRect(x, y, self.cell_size, self.cell_size, color)

    def _draw_current_eval_overlay(self, painter: QPainter):
        """Draw current evaluation cell (green highlight with animation)."""
        if self.current_eval_square is None:
            return

        file = chess.square_file(self.current_eval_square)
        rank = 7 - chess.square_rank(self.current_eval_square)
        x = file * self.cell_size
        y = rank * self.cell_size

        # Green highlight with animated alpha
        alpha = int(self.green_cell_alpha * 180)
        color = QColor(0, 255, 0, alpha)
        painter.fillRect(x, y, self.cell_size, self.cell_size, color)

        # Draw border
        pen = QPen(QColor(0, 200, 0), 2)
        painter.setPen(pen)
        painter.drawRect(x + 1, y + 1, self.cell_size - 2, self.cell_size - 2)

    def _draw_pieces(self, painter: QPainter):
        """Draw chess pieces (simplified)."""
        font = QFont("Arial", max(8, self.cell_size // 4))
        painter.setFont(font)

        piece_symbols = {
            chess.PAWN: '♟',
            chess.KNIGHT: '♞',
            chess.BISHOP: '♝',
            chess.ROOK: '♜',
            chess.QUEEN: '♛',
            chess.KING: '♚',
        }

        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece is None:
                continue

            file = chess.square_file(square)
            rank = 7 - chess.square_rank(square)
            x = file * self.cell_size
            y = rank * self.cell_size

            # Get piece symbol
            symbol = piece_symbols.get(piece.piece_type, '?')

            # Color based on piece color
            if piece.color == chess.WHITE:
                painter.setPen(QPen(QColor(255, 255, 255)))
                # Draw shadow for visibility
                painter.drawText(x + 2, y + 2, self.cell_size, self.cell_size,
                                Qt.AlignCenter, symbol)
                painter.setPen(QPen(QColor(0, 0, 0)))
            else:
                painter.setPen(QPen(QColor(0, 0, 0)))

            # Draw piece
            painter.drawText(x, y, self.cell_size, self.cell_size,
                            Qt.AlignCenter, symbol)

    def sizeHint(self):
        """Suggest a size for the widget."""
        return QSize(
            self.cell_size * self.board_size + 20,
            self.cell_size * self.board_size + 150
        )


__all__ = ["MiniBoardWidget"]
