"""
Enhanced Heatmap Widget with Mini-Board Visualization.

This widget provides an enhanced heatmap visualization with:
- Mini-board display showing current position
- Different colored zones (red for heatmaps, blue for BSP zones, green for current move)
- Real-time move evaluation visualization
- Integration with WFC/BSP analysis
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional, Set, Tuple, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QPushButton, QComboBox, QCheckBox, QSpinBox
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont
import chess
from chess import Board, Square, Move

from core.timing_config import timing_manager
from core.move_object import MoveEvaluation, VisualizationState


class MiniBoardCell(QWidget):
    """A single cell in the mini-board visualization."""
    
    def __init__(self, row: int, col: int, parent=None):
        super().__init__(parent)
        self.row = row
        self.col = col
        self.square = chess.square(col, 7 - row)
        
        # Visual state
        self.piece_symbol = ""
        self.heatmap_intensity = 0.0
        self.zone_color = QColor(240, 240, 240)  # Default light gray
        self.is_highlighted = False
        self.is_current_move = False
        self.bsp_zone_type = ""
        
        # Colors for different visualization layers
        self.colors = {
            'heatmap': QColor(255, 0, 0, 100),      # Red with transparency
            'bsp_zone': QColor(0, 0, 255, 100),     # Blue with transparency
            'current_move': QColor(0, 255, 0, 150), # Green with transparency
            'pattern_match': QColor(255, 255, 0, 100), # Yellow with transparency
            'guardrails_violation': QColor(255, 0, 255, 150) # Magenta with transparency
        }
        
        self.setFixedSize(40, 40)
        self.setStyleSheet("border: 1px solid #888;")
    
    def set_piece(self, symbol: str) -> None:
        """Set the piece symbol for this cell."""
        self.piece_symbol = symbol
        self.update()
    
    def set_heatmap_intensity(self, intensity: float) -> None:
        """Set heatmap intensity (0.0 to 1.0)."""
        self.heatmap_intensity = max(0.0, min(1.0, intensity))
        self.update()
    
    def set_zone_color(self, color: QColor) -> None:
        """Set the BSP zone color."""
        self.zone_color = color
        self.update()
    
    def set_bsp_zone_type(self, zone_type: str) -> None:
        """Set the BSP zone type."""
        self.bsp_zone_type = zone_type
        # Set zone color based on type
        zone_colors = {
            'center': QColor(0, 100, 255, 80),    # Blue for center
            'edge': QColor(100, 100, 100, 60),    # Gray for edge
            'corner': QColor(150, 75, 0, 60),     # Brown for corner
            'flank': QColor(0, 150, 100, 60),     # Teal for flank
            'general': QColor(200, 200, 200, 40)  # Light gray for general
        }
        self.zone_color = zone_colors.get(zone_type, QColor(240, 240, 240, 40))
        self.update()
    
    def set_highlighted(self, highlighted: bool) -> None:
        """Set highlight state."""
        self.is_highlighted = highlighted
        self.update()
    
    def set_current_move(self, is_current: bool) -> None:
        """Set current move state."""
        self.is_current_move = is_current
        self.update()
    
    def paintEvent(self, event):
        """Custom paint event for the cell."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Base background (checkerboard pattern)
        is_light_square = (self.row + self.col) % 2 == 0
        base_color = QColor(240, 217, 181) if is_light_square else QColor(181, 136, 99)
        painter.fillRect(self.rect(), base_color)
        
        # BSP zone overlay
        if self.bsp_zone_type:
            painter.fillRect(self.rect(), self.zone_color)
        
        # Heatmap overlay
        if self.heatmap_intensity > 0:
            heatmap_color = QColor(self.colors['heatmap'])
            heatmap_color.setAlpha(int(self.heatmap_intensity * 200))
            painter.fillRect(self.rect(), heatmap_color)
        
        # Current move highlight
        if self.is_current_move:
            painter.fillRect(self.rect(), self.colors['current_move'])
        
        # General highlight
        if self.is_highlighted:
            painter.setPen(QPen(QColor(255, 255, 0), 3))
            painter.drawRect(self.rect().adjusted(1, 1, -1, -1))
        
        # Draw piece symbol
        if self.piece_symbol:
            painter.setPen(QPen(QColor(0, 0, 0)))
            painter.setFont(QFont("Arial", 16, QFont.Bold))
            painter.drawText(self.rect(), Qt.AlignCenter, self.piece_symbol)
        
        # Draw square coordinate (small text in corner)
        square_name = chess.square_name(self.square)
        painter.setPen(QPen(QColor(100, 100, 100)))
        painter.setFont(QFont("Arial", 8))
        painter.drawText(2, 12, square_name)


class EnhancedHeatmapWidget(QWidget):
    """Enhanced heatmap widget with mini-board and real-time visualization."""
    
    # Signals
    heatmap_changed = Signal(str)  # Emitted when heatmap selection changes
    visualization_updated = Signal(dict)  # Emitted when visualization updates
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.board = Board()
        self.current_move_eval: Optional[MoveEvaluation] = None
        
        # Mini-board grid
        self.mini_board_cells: List[List[MiniBoardCell]] = []
        
        # Heatmap data
        self.heatmap_data: Dict[str, List[List[float]]] = {}
        self.active_heatmap = "none"
        
        # BSP data
        self.bsp_zones: Dict[str, Any] = {}
        
        # Real-time visualization
        self.visualization_timer = QTimer()
        self.visualization_timer.timeout.connect(self._update_real_time_visualization)
        self.current_evaluation_step = 0
        
        self._setup_ui()
        self._setup_mini_board()
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Enhanced Heatmap Visualization")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title_label)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        # Heatmap selection
        controls_layout.addWidget(QLabel("Heatmap:"))
        self.heatmap_combo = QComboBox()
        self.heatmap_combo.addItems(["none", "pawn", "knight", "bishop", "rook", "queen", "king"])
        self.heatmap_combo.currentTextChanged.connect(self._on_heatmap_changed)
        controls_layout.addWidget(self.heatmap_combo)
        
        # BSP zones toggle
        self.show_bsp_zones = QCheckBox("BSP Zones")
        self.show_bsp_zones.setChecked(True)
        self.show_bsp_zones.toggled.connect(self._on_bsp_zones_toggled)
        controls_layout.addWidget(self.show_bsp_zones)
        
        # Real-time visualization toggle
        self.show_real_time = QCheckBox("Real-time")
        self.show_real_time.setChecked(True)
        self.show_real_time.toggled.connect(self._on_real_time_toggled)
        controls_layout.addWidget(self.show_real_time)
        
        # Visualization speed
        controls_layout.addWidget(QLabel("Speed:"))
        self.speed_spinbox = QSpinBox()
        self.speed_spinbox.setRange(10, 500)
        self.speed_spinbox.setValue(timing_manager.get_visualization_delay_ms())
        self.speed_spinbox.setSuffix(" ms")
        self.speed_spinbox.valueChanged.connect(self._on_speed_changed)
        controls_layout.addWidget(self.speed_spinbox)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Mini-board frame
        self.board_frame = QFrame()
        self.board_frame.setFrameStyle(QFrame.Box)
        self.board_frame.setFixedSize(340, 340)
        layout.addWidget(self.board_frame)
        
        # Statistics display
        self.stats_label = QLabel("Statistics will appear here")
        self.stats_label.setWordWrap(True)
        self.stats_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
                font-family: monospace;
            }
        """)
        layout.addWidget(self.stats_label)
        
        layout.addStretch()
    
    def _setup_mini_board(self) -> None:
        """Set up the mini-board grid."""
        grid_layout = QGridLayout(self.board_frame)
        grid_layout.setContentsMargins(5, 5, 5, 5)
        grid_layout.setSpacing(1)
        
        self.mini_board_cells = []
        for row in range(8):
            cell_row = []
            for col in range(8):
                cell = MiniBoardCell(row, col)
                grid_layout.addWidget(cell, row, col)
                cell_row.append(cell)
            self.mini_board_cells.append(cell_row)
    
    def set_board(self, board: Board) -> None:
        """Set the current board position."""
        self.board = board.copy()
        self._update_board_display()
    
    def set_heatmap_data(self, heatmap_data: Dict[str, List[List[float]]]) -> None:
        """Set heatmap data."""
        self.heatmap_data = heatmap_data
        self._update_heatmap_display()
    
    def set_bsp_zones(self, bsp_zones: Dict[str, Any]) -> None:
        """Set BSP zone data."""
        self.bsp_zones = bsp_zones
        self._update_bsp_display()
    
    def set_move_evaluation(self, move_eval: MoveEvaluation) -> None:
        """Set current move evaluation for real-time visualization."""
        self.current_move_eval = move_eval
        if self.show_real_time.isChecked():
            self._start_real_time_visualization()
    
    def _update_board_display(self) -> None:
        """Update the board display with current pieces."""
        for row in range(8):
            for col in range(8):
                cell = self.mini_board_cells[row][col]
                square = chess.square(col, 7 - row)
                piece = self.board.piece_at(square)
                
                if piece:
                    cell.set_piece(piece.symbol())
                else:
                    cell.set_piece("")
    
    def _update_heatmap_display(self) -> None:
        """Update heatmap visualization."""
        if self.active_heatmap == "none" or self.active_heatmap not in self.heatmap_data:
            # Clear heatmap
            for row in range(8):
                for col in range(8):
                    self.mini_board_cells[row][col].set_heatmap_intensity(0.0)
            return
        
        heatmap = self.heatmap_data[self.active_heatmap]
        max_intensity = max(max(row) for row in heatmap) if heatmap else 1.0
        
        for row in range(8):
            for col in range(8):
                if row < len(heatmap) and col < len(heatmap[row]):
                    intensity = heatmap[row][col] / max_intensity if max_intensity > 0 else 0.0
                    self.mini_board_cells[row][col].set_heatmap_intensity(intensity)
    
    def _update_bsp_display(self) -> None:
        """Update BSP zone visualization."""
        if not self.show_bsp_zones.isChecked() or not self.bsp_zones:
            # Clear BSP zones
            for row in range(8):
                for col in range(8):
                    self.mini_board_cells[row][col].set_bsp_zone_type("")
            return
        
        # This is a simplified implementation
        # In a real implementation, you would use the actual BSP engine results
        zone_types = ['center', 'edge', 'corner', 'flank', 'general']
        for row in range(8):
            for col in range(8):
                # Simple zone classification based on position
                if 2 <= row <= 5 and 2 <= col <= 5:
                    zone_type = 'center'
                elif row in [0, 7] or col in [0, 7]:
                    if (row in [0, 7] and col in [0, 7]):
                        zone_type = 'corner'
                    else:
                        zone_type = 'edge'
                elif row in [1, 6] or col in [1, 6]:
                    zone_type = 'flank'
                else:
                    zone_type = 'general'
                
                self.mini_board_cells[row][col].set_bsp_zone_type(zone_type)
    
    def _start_real_time_visualization(self) -> None:
        """Start real-time visualization of move evaluation."""
        if not self.current_move_eval:
            return
        
        self.current_evaluation_step = 0
        self.visualization_timer.start(self.speed_spinbox.value())
    
    def _update_real_time_visualization(self) -> None:
        """Update real-time visualization step by step."""
        if not self.current_move_eval or not self.show_real_time.isChecked():
            self.visualization_timer.stop()
            return
        
        # Simulate step-by-step evaluation visualization
        steps = self.current_move_eval.evaluation_steps
        if self.current_evaluation_step >= len(steps):
            self.visualization_timer.stop()
            return
        
        current_step = steps[self.current_evaluation_step]
        
        # Update current move cell
        if hasattr(self.current_move_eval, 'move'):
            move = self.current_move_eval.move
            from_row, from_col = 7 - chess.square_rank(move.from_square), chess.square_file(move.from_square)
            to_row, to_col = 7 - chess.square_rank(move.to_square), chess.square_file(move.to_square)
            
            # Clear previous current move highlights
            for row in range(8):
                for col in range(8):
                    self.mini_board_cells[row][col].set_current_move(False)
            
            # Highlight current move squares
            self.mini_board_cells[from_row][from_col].set_current_move(True)
            self.mini_board_cells[to_row][to_col].set_current_move(True)
        
        # Update statistics display
        self._update_statistics_display(current_step)
        
        self.current_evaluation_step += 1
    
    def _update_statistics_display(self, current_step=None) -> None:
        """Update the statistics display."""
        if not self.current_move_eval:
            self.stats_label.setText("No move evaluation data")
            return
        
        stats_text = f"Move Evaluation Statistics\n"
        stats_text += f"{'=' * 30}\n"
        
        if hasattr(self.current_move_eval, 'move'):
            stats_text += f"Move: {self.current_move_eval.san_notation}\n"
        
        stats_text += f"Phase: {self.current_move_eval.phase.value}\n"
        stats_text += f"Status: {self.current_move_eval.status.value}\n"
        stats_text += f"Total Duration: {self.current_move_eval.total_duration_ms:.1f}ms\n"
        stats_text += f"Final Score: {self.current_move_eval.final_score:.1f}\n"
        stats_text += f"Confidence: {self.current_move_eval.confidence:.2f}\n"
        stats_text += f"Primary Reason: {self.current_move_eval.primary_reason}\n"
        
        if current_step:
            stats_text += f"\nCurrent Step: {current_step.method_name}\n"
            stats_text += f"Bot: {current_step.bot_name or 'N/A'}\n"
            stats_text += f"Duration: {current_step.duration_ms:.1f}ms\n"
            stats_text += f"Status: {current_step.status.value}\n"
            stats_text += f"Reason: {current_step.reason}\n"
        
        # Pattern matches
        if self.current_move_eval.pattern_matches:
            stats_text += f"\nPattern Matches: {len(self.current_move_eval.pattern_matches)}\n"
            for i, match in enumerate(self.current_move_eval.pattern_matches[:3]):  # Show first 3
                stats_text += f"  {i+1}. {match.get('type', 'Unknown')} (conf: {match.get('confidence', 0):.2f})\n"
        
        # Guardrails
        if not self.current_move_eval.guardrails_passed:
            stats_text += f"\nGuardrails Violations:\n"
            for violation in self.current_move_eval.guardrails_violations:
                stats_text += f"  • {violation}\n"
        
        self.stats_label.setText(stats_text)
    
    def _on_heatmap_changed(self, heatmap_name: str) -> None:
        """Handle heatmap selection change."""
        self.active_heatmap = heatmap_name
        self._update_heatmap_display()
        self.heatmap_changed.emit(heatmap_name)
    
    def _on_bsp_zones_toggled(self, checked: bool) -> None:
        """Handle BSP zones toggle."""
        self._update_bsp_display()
    
    def _on_real_time_toggled(self, checked: bool) -> None:
        """Handle real-time visualization toggle."""
        if not checked:
            self.visualization_timer.stop()
    
    def _on_speed_changed(self, value: int) -> None:
        """Handle visualization speed change."""
        if self.visualization_timer.isActive():
            self.visualization_timer.setInterval(value)
    
    def highlight_squares(self, squares: Set[Square]) -> None:
        """Highlight specific squares."""
        # Clear all highlights first
        for row in range(8):
            for col in range(8):
                self.mini_board_cells[row][col].set_highlighted(False)
        
        # Set new highlights
        for square in squares:
            row, col = 7 - chess.square_rank(square), chess.square_file(square)
            if 0 <= row < 8 and 0 <= col < 8:
                self.mini_board_cells[row][col].set_highlighted(True)
    
    def clear_visualization(self) -> None:
        """Clear all visualization overlays."""
        for row in range(8):
            for col in range(8):
                cell = self.mini_board_cells[row][col]
                cell.set_heatmap_intensity(0.0)
                cell.set_bsp_zone_type("")
                cell.set_highlighted(False)
                cell.set_current_move(False)
        
        self.visualization_timer.stop()
        self.current_move_eval = None
        self.stats_label.setText("Visualization cleared")
    
    def export_visualization_state(self) -> Dict[str, Any]:
        """Export current visualization state."""
        return {
            'active_heatmap': self.active_heatmap,
            'show_bsp_zones': self.show_bsp_zones.isChecked(),
            'show_real_time': self.show_real_time.isChecked(),
            'visualization_speed_ms': self.speed_spinbox.value(),
            'board_fen': self.board.fen(),
            'current_move_eval': self.current_move_eval.get_evaluation_summary() if self.current_move_eval else None
        }