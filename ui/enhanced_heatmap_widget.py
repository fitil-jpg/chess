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
from chess_ai.risk_analyzer import MoveAnalysisStats, MoveAnalysisSummary
from chess_ai.guardrails import Guardrails


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
            'guardrails_violation': QColor(255, 0, 255, 150), # Magenta with transparency
            'tactical_pattern': QColor(0, 100, 255, 120), # Blue gradient for tactical
            'high_value_move': QColor(128, 0, 128, 120), # Purple gradient for high-value
            'cow_opening': QColor(255, 165, 0, 120) # Orange for COW opening
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
        
        # Guardrails statistics data
        self.guardrails_stats: Optional[MoveAnalysisSummary] = None
        self.move_risk_stats: Dict[str, MoveAnalysisStats] = {}
        self.guardrails_enabled = True
        
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
        
        # Guardrails statistics toggle
        self.show_guardrails = QCheckBox("Guardrails Stats")
        self.show_guardrails.setChecked(True)
        self.show_guardrails.toggled.connect(self._on_guardrails_toggled)
        controls_layout.addWidget(self.show_guardrails)
        
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
        self._update_statistics_display()  # Update statistics to show formula and coefficients
    
    def set_bsp_zones(self, bsp_zones: Dict[str, Any]) -> None:
        """Set BSP zone data."""
        self.bsp_zones = bsp_zones
        self._update_bsp_display()
    
    def set_guardrails_stats(self, stats: MoveAnalysisSummary) -> None:
        """Set guardrails analysis statistics."""
        self.guardrails_stats = stats
        self._update_statistics_display()
    
    def set_move_risk_stats(self, move_stats: Dict[str, MoveAnalysisStats]) -> None:
        """Set individual move risk statistics."""
        self.move_risk_stats = move_stats.copy()
        self._update_guardrails_visualization()
    
    def set_guardrails_enabled(self, enabled: bool) -> None:
        """Enable or disable guardrails visualization."""
        self.guardrails_enabled = enabled
        self._update_guardrails_visualization()
        self._update_statistics_display()
    
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
        """Update the statistics display with comprehensive guardrails information."""
        stats_text = ""
        
        # Show guardrails statistics if available and enabled
        if self.guardrails_stats and self.show_guardrails.isChecked():
            stats_text = f"🛡️ Guardrails Analysis\n"
            stats_text += f"{'=' * 40}\n"
            
            gs = self.guardrails_stats
            stats_text += f"Total Moves Evaluated: {gs.total_moves_evaluated}\n"
            stats_text += f"Safe Moves Found: {gs.safe_moves_found}\n"
            stats_text += f"Risky Moves Rejected: {gs.risky_moves_rejected}\n"
            
            if gs.total_moves_evaluated > 0:
                safe_ratio = (gs.safe_moves_found / gs.total_moves_evaluated) * 100
                risk_ratio = (gs.risky_moves_rejected / gs.total_moves_evaluated) * 100
                stats_text += f"Safety Rate: {safe_ratio:.1f}% | Risk Rate: {risk_ratio:.1f}%\n"
            
            stats_text += f"Analysis Depth: {gs.analysis_depth} plies\n"
            stats_text += f"Total Search Nodes: {gs.total_search_nodes:,}\n"
            stats_text += f"Analysis Time: {gs.analysis_time_total_ms:.2f}ms\n"
            
            if gs.chosen_move:
                decision_type = "Bot" if gs.chosen_by_bot else "Manual"
                stats_text += f"Selected Move: {gs.chosen_move} ({decision_type})\n"
            
            # Show rejection reasons
            if gs.rejection_reasons:
                stats_text += f"\n🚫 Rejection Reasons:\n"
                for reason, count in sorted(gs.rejection_reasons.items(), key=lambda x: x[1], reverse=True):
                    stats_text += f"  • {reason}: {count} moves\n"
            
            # Pattern description
            if gs.pattern_description:
                stats_text += f"\n📊 Pattern Analysis:\n{gs.pattern_description}\n"
            
            stats_text += f"\n{'=' * 40}\n\n"
        
        # Show heatmap formula and coefficients when heatmap is active
        if self.active_heatmap != "none" and self.active_heatmap in self.heatmap_data:
            if not stats_text:
                stats_text = f"Heatmap Calculation Info\n"
            else:
                stats_text += f"🔥 Heatmap Calculation Info\n"
            stats_text += f"{'=' * 30}\n"
            stats_text += f"Active Heatmap: {self.active_heatmap}\n"
            
            # Formula for heatmap calculation
            stats_text += f"\nFormula:\n"
            stats_text += f"heatmap[7-rank, file] += 1\n"
            stats_text += f"intensity = heatmap[row][col] / max_intensity\n"
            
            # Current coefficients
            if self.active_heatmap in self.heatmap_data:
                heatmap = self.heatmap_data[self.active_heatmap]
                max_intensity = max(max(row) for row in heatmap) if heatmap else 1.0
                total_moves = sum(sum(row) for row in heatmap)
                
                stats_text += f"\nCurrent Coefficients:\n"
                stats_text += f"Max Intensity: {max_intensity:.1f}\n"
                stats_text += f"Total Movements: {total_moves}\n"
                stats_text += f"Normalization Factor: {max_intensity if max_intensity > 0 else 1.0}\n"
                
                # Show piece-specific info if it's a pawn heatmap
                if self.active_heatmap == "pawn":
                    stats_text += f"\nPawn Heatmap Specifics:\n"
                    stats_text += f"Piece Symbols: ['P', 'p']\n"
                    stats_text += f"Movement Counting: All pawn moves\n"
            
            stats_text += f"\n{'=' * 30}\n\n"
        
        if not self.current_move_eval:
            if not stats_text:
                self.stats_label.setText("No move evaluation data")
            else:
                stats_text += "No move evaluation data"
                self.stats_label.setText(stats_text)
            return
        
        if not stats_text:
            stats_text = f"Move Evaluation Statistics\n"
            stats_text += f"{'=' * 30}\n"
        
        # Move evaluation information
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
        
        # Guardrails - Enhanced display
        if not self.current_move_eval.guardrails_passed:
            stats_text += f"\n⚠️ Guardrails VIOLATIONS:\n"
            for violation in self.current_move_eval.guardrails_violations:
                stats_text += f"  ❌ {violation}\n"
        else:
            stats_text += f"\n✅ Guardrails: PASSED\n"
        
        if self.current_move_eval.guardrails_warnings:
            stats_text += f"\n⚠️ Guardrails WARNINGS:\n"
            for warning in self.current_move_eval.guardrails_warnings:
                stats_text += f"  ⚠️ {warning}\n"
        
        # Show individual move risk stats if available
        if self.move_risk_stats and hasattr(self.current_move_eval, 'move'):
            move_uci = self.current_move_eval.move.uci()
            if move_uci in self.move_risk_stats:
                risk_stat = self.move_risk_stats[move_uci]
                stats_text += f"\n🔍 Risk Analysis for Current Move:\n"
                stats_text += f"  Risk Status: {'❌ RISKY' if risk_stat.is_risky else '✅ SAFE'}\n"
                stats_text += f"  Material Change: {risk_stat.material_after - risk_stat.material_before:+d}\n"
                stats_text += f"  Attackers: {risk_stat.attackers_count} | Defenders: {risk_stat.defenders_count}\n"
                stats_text += f"  Search Nodes: {risk_stat.search_nodes:,}\n"
                stats_text += f"  Analysis Time: {risk_stat.analysis_time_ms:.2f}ms\n"
                if risk_stat.rejection_reason:
                    stats_text += f"  Reason: {risk_stat.rejection_reason}\n"
        
        self.stats_label.setText(stats_text)
    
    def _on_heatmap_changed(self, heatmap_name: str) -> None:
        """Handle heatmap selection change."""
        self.active_heatmap = heatmap_name
        self._update_heatmap_display()
        self._update_statistics_display()  # Update statistics to show formula and coefficients
        self.heatmap_changed.emit(heatmap_name)
    
    def _on_bsp_zones_toggled(self, checked: bool) -> None:
        """Handle BSP zones toggle."""
        self._update_bsp_display()
    
    def _on_real_time_toggled(self, checked: bool) -> None:
        """Handle real-time visualization toggle."""
        if not checked:
            self.visualization_timer.stop()
    
    def _on_guardrails_toggled(self, checked: bool) -> None:
        """Handle guardrails statistics toggle."""
        self._update_statistics_display()
        self._update_guardrails_visualization()
    
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
    
    def _update_guardrails_visualization(self) -> None:
        """Update guardrails visualization on the mini-board."""
        if not self.guardrails_enabled or not self.show_guardrails.isChecked():
            # Clear guardrails overlays
            for row in range(8):
                for col in range(8):
                    cell = self.mini_board_cells[row][col]
                    # Reset guardrails visualization (keep other layers)
                    if hasattr(cell, 'guardrails_violation'):
                        cell.guardrails_violation = False
            return
        
        # Apply guardrails violation overlay for risky moves
        if self.move_risk_stats:
            for move_uci, risk_stat in self.move_risk_stats.items():
                if risk_stat.is_risky:
                    try:
                        move = chess.Move.from_uci(move_uci)
                        to_row, to_col = 7 - chess.square_rank(move.to_square), chess.square_file(move.to_square)
                        
                        if 0 <= to_row < 8 and 0 <= to_col < 8:
                            cell = self.mini_board_cells[to_row][to_col]
                            cell.guardrails_violation = True
                            # Apply magenta overlay for guardrails violations
                            cell.setStyleSheet(f"border: 2px solid magenta; background-color: rgba(255, 0, 255, 0.2);")
                    except ValueError:
                        # Invalid UCI, skip
                        continue
        
        self.update()
    
    def clear_visualization(self) -> None:
        """Clear all visualization overlays."""
        for row in range(8):
            for col in range(8):
                cell = self.mini_board_cells[row][col]
                cell.set_heatmap_intensity(0.0)
                cell.set_bsp_zone_type("")
                cell.set_highlighted(False)
                cell.set_current_move(False)
                # Clear guardrails visualization
                if hasattr(cell, 'guardrails_violation'):
                    cell.guardrails_violation = False
                    cell.setStyleSheet("border: 1px solid #888;")
        
        self.visualization_timer.stop()
        self.current_move_eval = None
        self.guardrails_stats = None
        self.move_risk_stats.clear()
        self.stats_label.setText("Visualization cleared")
    
    def export_visualization_state(self) -> Dict[str, Any]:
        """Export current visualization state."""
        return {
            'active_heatmap': self.active_heatmap,
            'show_bsp_zones': self.show_bsp_zones.isChecked(),
            'show_real_time': self.show_real_time.isChecked(),
            'show_guardrails': self.show_guardrails.isChecked(),
            'guardrails_enabled': self.guardrails_enabled,
            'visualization_speed_ms': self.speed_spinbox.value(),
            'board_fen': self.board.fen(),
            'current_move_eval': self.current_move_eval.get_evaluation_summary() if self.current_move_eval else None,
            'guardrails_stats': self.guardrails_stats.__dict__ if self.guardrails_stats else None,
            'move_risk_stats_count': len(self.move_risk_stats)
        }
    
    def update_for_current_piece(self, piece_type: str) -> None:
        """Update heatmap display for the current moving piece."""
        if piece_type in self.heatmap_data:
            self.active_heatmap = piece_type
            self.heatmap_combo.setCurrentText(piece_type)
            self._update_heatmap_display()
            logger.info(f"Updated heatmap for current piece: {piece_type}")
    
    def highlight_current_move_squares(self, move: chess.Move, delay_ms: int = 50) -> None:
        """Highlight the current move squares with green indicator."""
        # Clear previous highlights
        for row in range(8):
            for col in range(8):
                self.mini_board_cells[row][col].set_current_move(False)
        
        # Highlight new move squares
        from_row, from_col = 7 - chess.square_rank(move.from_square), chess.square_file(move.from_square)
        to_row, to_col = 7 - chess.square_rank(move.to_square), chess.square_file(move.to_square)
        
        if 0 <= from_row < 8 and 0 <= from_col < 8:
            self.mini_board_cells[from_row][from_col].set_current_move(True)
        if 0 <= to_row < 8 and 0 <= to_col < 8:
            self.mini_board_cells[to_row][to_col].set_current_move(True)
        
        # Apply delay for visualization
        if delay_ms > 0:
            QTimer.singleShot(delay_ms, self.update)
        else:
            self.update()
    
    def show_tactical_pattern_overlay(self, tactical_squares: Set[chess.Square], confidence: float = 0.6) -> None:
        """Show blue gradient overlay for tactical pattern squares."""
        if not timing_manager.meets_tactical_pattern_threshold(confidence):
            return
        
        # Clear previous tactical overlays
        for row in range(8):
            for col in range(8):
                cell = self.mini_board_cells[row][col]
                # Reset tactical visualization (keep other layers)
                if hasattr(cell, 'tactical_intensity'):
                    cell.tactical_intensity = 0.0
        
        # Apply new tactical overlay
        for square in tactical_squares:
            row, col = 7 - chess.square_rank(square), chess.square_file(square)
            if 0 <= row < 8 and 0 <= col < 8:
                cell = self.mini_board_cells[row][col]
                # Set tactical intensity based on confidence
                cell.tactical_intensity = confidence
                
                # Blue gradient visualization
                blue_color = QColor(0, 100, 255, int(confidence * 150))
                cell.setStyleSheet(f"border: 1px solid #888; background-color: rgba(0, 100, 255, {confidence * 0.3});")
        
        self.update()
        logger.info(f"Applied tactical pattern overlay to {len(tactical_squares)} squares (confidence: {confidence:.2f})")
    
    def show_minimax_threshold_overlay(self, minimax_squares: Dict[chess.Square, float]) -> None:
        """Show purple gradient overlay for minimax threshold moves (>10% from neutral)."""
        for square, value in minimax_squares.items():
            if timing_manager.meets_minimax_threshold(value):
                row, col = 7 - chess.square_rank(square), chess.square_file(square)
                if 0 <= row < 8 and 0 <= col < 8:
                    cell = self.mini_board_cells[row][col]
                    # Purple gradient based on value intensity
                    intensity = min(abs(value), 1.0)
                    purple_color = QColor(128, 0, 128, int(intensity * 120))
                    cell.setStyleSheet(f"border: 2px solid purple; background-color: rgba(128, 0, 128, {intensity * 0.4});")
        
        self.update()
        logger.info(f"Applied minimax threshold overlay to {len(minimax_squares)} squares")
    
    def animate_green_cell_pulse(self, square: chess.Square) -> None:
        """Animate green cell pulsing for current evaluation."""
        row, col = 7 - chess.square_rank(square), chess.square_file(square)
        if 0 <= row < 8 and 0 <= col < 8:
            cell = self.mini_board_cells[row][col]
            cell.set_current_move(True)
            
            # Start pulsing animation
            pulse_timer = QTimer()
            pulse_alpha = 1.0
            pulse_direction = -1
            
            def pulse_step():
                nonlocal pulse_alpha, pulse_direction
                pulse_alpha += 0.1 * pulse_direction
                
                if pulse_alpha <= 0.3:
                    pulse_alpha = 0.3
                    pulse_direction = 1
                elif pulse_alpha >= 1.0:
                    pulse_alpha = 1.0
                    pulse_direction = -1
                
                # Update cell opacity
                green_color = QColor(0, 255, 0, int(pulse_alpha * 180))
                cell.setStyleSheet(f"border: 2px solid green; background-color: rgba(0, 255, 0, {pulse_alpha * 0.5});")
                cell.update()
            
            pulse_timer.timeout.connect(pulse_step)
            pulse_timer.start(timing_manager.get_green_cell_pulse_delay_ms())
            
            # Store timer reference to prevent garbage collection
            cell.pulse_timer = pulse_timer
    
    def stop_green_cell_animation(self) -> None:
        """Stop all green cell animations."""
        for row in range(8):
            for col in range(8):
                cell = self.mini_board_cells[row][col]
                if hasattr(cell, 'pulse_timer'):
                    cell.pulse_timer.stop()
                    del cell.pulse_timer
                cell.set_current_move(False)
        self.update()
    
    def update_visualization_for_move_evaluation(self, move_eval: MoveEvaluation) -> None:
        """Comprehensive update for move evaluation with all visualization layers."""
        if not move_eval:
            return
        
        # Set current move evaluation
        self.set_move_evaluation(move_eval)
        
        # Update for current piece if available
        if hasattr(move_eval, 'active_piece_type'):
            self.update_for_current_piece(move_eval.active_piece_type)
        
        # Highlight current move squares
        if hasattr(move_eval, 'move'):
            self.highlight_current_move_squares(move_eval.move, timing_manager.get_visualization_delay_ms())
        
        # Show tactical patterns if available
        if hasattr(move_eval, 'tactical_squares') and move_eval.tactical_squares:
            confidence = getattr(move_eval, 'tactical_confidence', 0.6)
            self.show_tactical_pattern_overlay(move_eval.tactical_squares, confidence)
        
        # Show minimax threshold overlay
        if hasattr(move_eval, 'minimax_values') and move_eval.minimax_values:
            self.show_minimax_threshold_overlay(move_eval.minimax_values)
        
        # Start green cell animation for current evaluation
        if hasattr(move_eval, 'current_eval_square'):
            self.animate_green_cell_pulse(move_eval.current_eval_square)
        
        # Update statistics display
        self._update_statistics_display()
        
        logger.info(f"Updated comprehensive visualization for move evaluation: {getattr(move_eval, 'move', None)}")