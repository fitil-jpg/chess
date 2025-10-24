"""
Enhanced PySide Viewer with Move Evaluation and Pattern Visualization

This enhanced viewer integrates WFC, BSP, guardrails, and pattern matching
systems to provide comprehensive move evaluation and visualization.
"""

import sys
import time
import chess
import logging
from typing import Dict, List, Optional, Any
from PySide6.QtWidgets import (
    QApplication, QWidget, QGridLayout, QVBoxLayout, QHBoxLayout,
    QFrame, QPushButton, QLabel, QCheckBox, QMessageBox, QSizePolicy,
    QListWidget, QScrollArea, QTextEdit, QSplitter, QMainWindow, QTabWidget,
    QProgressBar, QSlider, QSpinBox, QComboBox
)
from PySide6.QtCore import QTimer, QRect, Qt, QSettings, Signal, QThread
from PySide6.QtGui import QPainter, QColor, QPen, QPixmap, QFont, QBrush

# Import our enhanced systems
from chess_ai.move_evaluation import MoveEvaluation, MoveEvaluator, create_move_evaluator
from chess_ai.wfc_engine import create_chess_wfc_engine
from chess_ai.bsp_engine import create_chess_bsp_engine
from chess_ai.guardrails import Guardrails
from chess_ai.pattern_responder import create_pattern_responder
from chess_ai.bot_agent import make_agent

logger = logging.getLogger(__name__)


class MoveEvaluationThread(QThread):
    """Thread for move evaluation to prevent UI blocking."""
    
    evaluation_complete = Signal(object)  # MoveEvaluation object
    
    def __init__(self, evaluator, move, board, color):
        super().__init__()
        self.evaluator = evaluator
        self.move = move
        self.board = board
        self.color = color
    
    def run(self):
        """Run move evaluation in background thread."""
        try:
            evaluation = self.evaluator.evaluate_move(self.move, self.board, self.color)
            self.evaluation_complete.emit(evaluation)
        except Exception as e:
            logger.error(f"Move evaluation failed: {e}")


class MiniChessBoard(QWidget):
    """Mini chess board for pattern visualization."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(200, 200)
        self.board = None
        self.heatmap_data = None
        self.wfc_zones = []
        self.bsp_zones = []
        self.tactical_zones = []
        self.current_move_square = None
        
    def set_board(self, board: chess.Board):
        """Set the chess board to display."""
        self.board = board
        self.update()
    
    def set_visualization_data(self, heatmap_data: Dict[str, Any]):
        """Set visualization data for patterns."""
        self.heatmap_data = heatmap_data
        self.wfc_zones = heatmap_data.get('wfc_zones', [])
        self.bsp_zones = heatmap_data.get('bsp_zones', [])
        self.tactical_zones = heatmap_data.get('tactical_zones', [])
        self.current_move_square = heatmap_data.get('current_move_square')
        self.update()
    
    def paintEvent(self, event):
        """Paint the mini chess board."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Board dimensions
        cell_size = 25
        board_size = 8 * cell_size
        
        # Draw board
        for row in range(8):
            for col in range(8):
                x = col * cell_size
                y = row * cell_size
                
                # Board colors
                is_light = (row + col) % 2 == 0
                base_color = QColor(240, 217, 181) if is_light else QColor(181, 136, 99)
                
                # Draw base square
                painter.fillRect(x, y, cell_size, cell_size, base_color)
                
                # Draw piece
                square = chess.square(col, 7 - row)
                if self.board:
                    piece = self.board.piece_at(square)
                    if piece:
                        self._draw_piece(painter, x, y, cell_size, piece)
                
                # Draw zones
                self._draw_zones(painter, x, y, cell_size, square)
        
        # Draw board border
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.drawRect(0, 0, board_size, board_size)
    
    def _draw_piece(self, painter: QPainter, x: int, y: int, size: int, piece: chess.Piece):
        """Draw a chess piece."""
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.setFont(QFont("Arial", size // 2))
        
        # Piece symbols
        symbols = {
            chess.PAWN: "♟" if piece.color == chess.WHITE else "♙",
            chess.KNIGHT: "♞" if piece.color == chess.WHITE else "♘",
            chess.BISHOP: "♝" if piece.color == chess.WHITE else "♗",
            chess.ROOK: "♜" if piece.color == chess.WHITE else "♖",
            chess.QUEEN: "♛" if piece.color == chess.WHITE else "♕",
            chess.KING: "♚" if piece.color == chess.WHITE else "♔"
        }
        
        symbol = symbols.get(piece.piece_type, "?")
        painter.drawText(x, y, size, size, Qt.AlignCenter, symbol)
    
    def _draw_zones(self, painter: QPainter, x: int, y: int, size: int, square: chess.Square):
        """Draw pattern zones."""
        # WFC zones (blue)
        if square in self.wfc_zones:
            painter.fillRect(x + 2, y + 2, size - 4, size - 4, QColor(0, 100, 255, 100))
        
        # BSP zones (light blue)
        if square in self.bsp_zones:
            painter.fillRect(x + 4, y + 4, size - 8, size - 8, QColor(100, 200, 255, 80))
        
        # Tactical zones (red)
        if square in self.tactical_zones:
            painter.fillRect(x + 6, y + 6, size - 12, size - 12, QColor(255, 100, 100, 120))
        
        # Current move square (green)
        if square == self.current_move_square:
            painter.setPen(QPen(QColor(0, 255, 0), 3))
            painter.drawRect(x + 1, y + 1, size - 2, size - 2)


class EnhancedChessViewer(QMainWindow):
    """Enhanced chess viewer with move evaluation and pattern visualization."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enhanced Chess Viewer — Move Evaluation & Pattern Analysis")
        self.resize(1400, 900)
        
        # Initialize systems
        self.board = chess.Board()
        self.move_evaluator = create_move_evaluator()
        self.current_evaluation = None
        self.evaluation_thread = None
        
        # Move timing
        self.move_delay_ms = 700  # Configurable move delay
        
        # Initialize UI
        self._setup_ui()
        self._setup_timers()
        
        # Initialize board
        self._refresh_board()
        
    def _setup_ui(self):
        """Setup the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Left side - Chess board and mini board
        left_layout = QVBoxLayout()
        
        # Main chess board
        self.board_frame = QFrame()
        self.board_frame.setFixedSize(560, 560)
        self.grid = QGridLayout(self.board_frame)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(0)
        self.cell_grid = [[None for _ in range(8)] for _ in range(8)]
        self._draw_board_widgets()
        
        # Mini board for pattern visualization
        self.mini_board = MiniChessBoard()
        mini_board_label = QLabel("Pattern Visualization:")
        mini_board_label.setAlignment(Qt.AlignCenter)
        
        left_layout.addWidget(self.board_frame)
        left_layout.addWidget(mini_board_label)
        left_layout.addWidget(self.mini_board)
        
        # Right side - Controls and information
        right_layout = QVBoxLayout()
        
        # Control panel
        self._setup_control_panel(right_layout)
        
        # Tab widget for different views
        self.tab_widget = QTabWidget()
        self._setup_tabs()
        right_layout.addWidget(self.tab_widget)
        
        # Add layouts to main layout
        main_layout.addLayout(left_layout, 0)
        main_layout.addLayout(right_layout, 1)
    
    def _setup_control_panel(self, parent_layout):
        """Setup the control panel."""
        control_frame = QFrame()
        control_layout = QVBoxLayout(control_frame)
        
        # Title with ELO ratings
        self.title_label = QLabel("Enhanced Chess Viewer")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        control_layout.addWidget(self.title_label)
        
        # Move delay control
        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel("Move Delay (ms):"))
        self.delay_slider = QSlider(Qt.Horizontal)
        self.delay_slider.setRange(100, 2000)
        self.delay_slider.setValue(self.move_delay_ms)
        self.delay_slider.valueChanged.connect(self._on_delay_changed)
        self.delay_label = QLabel(f"{self.move_delay_ms}ms")
        delay_layout.addWidget(self.delay_slider)
        delay_layout.addWidget(self.delay_label)
        control_layout.addLayout(delay_layout)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.btn_auto = QPushButton("▶ Auto Play")
        self.btn_pause = QPushButton("⏸ Pause")
        self.btn_evaluate = QPushButton("🔍 Evaluate Move")
        self.btn_reset = QPushButton("🔄 Reset")
        
        self.btn_auto.clicked.connect(self.start_auto)
        self.btn_pause.clicked.connect(self.pause_auto)
        self.btn_evaluate.clicked.connect(self.evaluate_current_position)
        self.btn_reset.clicked.connect(self.reset_game)
        
        button_layout.addWidget(self.btn_auto)
        button_layout.addWidget(self.btn_pause)
        button_layout.addWidget(self.btn_evaluate)
        button_layout.addWidget(self.btn_reset)
        
        control_layout.addLayout(button_layout)
        
        # Evaluation status
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("padding: 5px; background-color: #f0f0f0; border-radius: 3px;")
        control_layout.addWidget(self.status_label)
        
        parent_layout.addWidget(control_frame)
    
    def _setup_tabs(self):
        """Setup the tab widget."""
        # Move Evaluation tab
        self.evaluation_tab = QWidget()
        eval_layout = QVBoxLayout(self.evaluation_tab)
        
        # Evaluation results
        self.eval_results = QTextEdit()
        self.eval_results.setReadOnly(True)
        self.eval_results.setMaximumHeight(200)
        eval_layout.addWidget(QLabel("Move Evaluation Results:"))
        eval_layout.addWidget(self.eval_results)
        
        # Pattern matches
        self.pattern_list = QListWidget()
        self.pattern_list.setMaximumHeight(150)
        eval_layout.addWidget(QLabel("Pattern Matches:"))
        eval_layout.addWidget(self.pattern_list)
        
        # Bot tracking
        self.bot_list = QListWidget()
        self.bot_list.setMaximumHeight(150)
        eval_layout.addWidget(QLabel("Bot Analysis:"))
        eval_layout.addWidget(self.bot_list)
        
        eval_layout.addStretch()
        self.tab_widget.addTab(self.evaluation_tab, "🔍 Move Evaluation")
        
        # Heatmaps tab
        self.heatmap_tab = QWidget()
        heatmap_layout = QVBoxLayout(self.heatmap_tab)
        
        # Heatmap controls
        heatmap_control_layout = QHBoxLayout()
        heatmap_control_layout.addWidget(QLabel("Piece:"))
        self.piece_combo = QComboBox()
        self.piece_combo.addItems(["pawn", "knight", "bishop", "rook", "queen", "king"])
        self.piece_combo.currentTextChanged.connect(self._on_piece_changed)
        heatmap_control_layout.addWidget(self.piece_combo)
        
        heatmap_control_layout.addWidget(QLabel("Pattern Type:"))
        self.pattern_combo = QComboBox()
        self.pattern_combo.addItems(["heatmap", "wfc", "bsp", "tactical"])
        self.pattern_combo.currentTextChanged.connect(self._on_pattern_changed)
        heatmap_control_layout.addWidget(self.pattern_combo)
        
        heatmap_layout.addLayout(heatmap_control_layout)
        
        # Heatmap visualization
        self.heatmap_display = QLabel("Heatmap visualization will appear here")
        self.heatmap_display.setAlignment(Qt.AlignCenter)
        self.heatmap_display.setStyleSheet("border: 1px solid #ccc; background-color: #f9f9f9;")
        self.heatmap_display.setMinimumHeight(300)
        heatmap_layout.addWidget(self.heatmap_display)
        
        heatmap_layout.addStretch()
        self.tab_widget.addTab(self.heatmap_tab, "🔥 Heatmaps")
        
        # Usage tab
        self.usage_tab = QWidget()
        usage_layout = QVBoxLayout(self.usage_tab)
        
        # Usage statistics
        self.usage_stats = QTextEdit()
        self.usage_stats.setReadOnly(True)
        usage_layout.addWidget(QLabel("Usage Statistics:"))
        usage_layout.addWidget(self.usage_stats)
        
        usage_layout.addStretch()
        self.tab_widget.addTab(self.usage_tab, "📊 Usage")
    
    def _setup_timers(self):
        """Setup timers for auto-play."""
        self.auto_timer = QTimer()
        self.auto_timer.setInterval(self.move_delay_ms)
        self.auto_timer.timeout.connect(self.auto_step)
        self.auto_running = False
        self.move_in_progress = False
    
    def _draw_board_widgets(self):
        """Draw the chess board widgets."""
        for row in range(8):
            for col in range(8):
                cell = QLabel()
                cell.setFixedSize(70, 70)
                cell.setAlignment(Qt.AlignCenter)
                cell.setStyleSheet("border: 1px solid #ccc;")
                self.grid.addWidget(cell, row, col)
                self.cell_grid[row][col] = cell
    
    def _on_delay_changed(self, value):
        """Handle move delay slider change."""
        self.move_delay_ms = value
        self.delay_label.setText(f"{value}ms")
        self.auto_timer.setInterval(value)
    
    def _on_piece_changed(self, piece_name):
        """Handle piece selection change."""
        self._update_heatmap_display()
    
    def _on_pattern_changed(self, pattern_type):
        """Handle pattern type change."""
        self._update_heatmap_display()
    
    def _update_heatmap_display(self):
        """Update the heatmap display."""
        piece_name = self.piece_combo.currentText()
        pattern_type = self.pattern_combo.currentText()
        
        # Update mini board with current visualization
        if self.current_evaluation and self.current_evaluation.heatmap_data:
            viz_data = self.current_evaluation.get_visualization_data()
            self.mini_board.set_visualization_data(viz_data.get('heatmap', {}))
        
        # Update heatmap display text
        display_text = f"Showing {pattern_type} patterns for {piece_name}"
        self.heatmap_display.setText(display_text)
    
    def start_auto(self):
        """Start automatic play."""
        if not self.auto_running:
            self.auto_running = True
            self.auto_timer.start()
            self.btn_auto.setEnabled(False)
            self.btn_pause.setEnabled(True)
            self.status_label.setText("Auto play running...")
    
    def pause_auto(self):
        """Pause automatic play."""
        self.auto_running = False
        self.auto_timer.stop()
        self.btn_auto.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.status_label.setText("Auto play paused")
    
    def reset_game(self):
        """Reset the game to starting position."""
        self.board = chess.Board()
        self.current_evaluation = None
        self._refresh_board()
        self._clear_evaluation_display()
        self.status_label.setText("Game reset")
    
    def evaluate_current_position(self):
        """Evaluate the current position."""
        if self.move_in_progress:
            return
        
        # Get a random legal move for evaluation
        legal_moves = list(self.board.legal_moves)
        if not legal_moves:
            self.status_label.setText("No legal moves available")
            return
        
        move = legal_moves[0]  # For demo, use first legal move
        self._evaluate_move(move)
    
    def _evaluate_move(self, move: chess.Move):
        """Evaluate a specific move."""
        if self.evaluation_thread and self.evaluation_thread.isRunning():
            return
        
        self.move_in_progress = True
        self.status_label.setText("Evaluating move...")
        
        # Start evaluation in background thread
        self.evaluation_thread = MoveEvaluationThread(
            self.move_evaluator, move, self.board, self.board.turn
        )
        self.evaluation_thread.evaluation_complete.connect(self._on_evaluation_complete)
        self.evaluation_thread.start()
    
    def _on_evaluation_complete(self, evaluation: MoveEvaluation):
        """Handle completed move evaluation."""
        self.current_evaluation = evaluation
        self._update_evaluation_display()
        self._update_heatmap_display()
        self.move_in_progress = False
        self.status_label.setText("Evaluation complete")
    
    def _update_evaluation_display(self):
        """Update the evaluation display."""
        if not self.current_evaluation:
            return
        
        # Update evaluation results
        eval_text = self.current_evaluation.get_detailed_log()
        self.eval_results.setText(eval_text)
        
        # Update pattern matches
        self.pattern_list.clear()
        for pattern in self.current_evaluation.pattern_matches:
            item_text = f"{pattern.pattern_type}: {pattern.pattern_name} (conf: {pattern.confidence:.2f})"
            self.pattern_list.addItem(item_text)
        
        # Update bot results
        self.bot_list.clear()
        for bot_name, result in self.current_evaluation.bot_results.items():
            item_text = f"{bot_name}: {result.status.value} - {result.reason}"
            self.bot_list.addItem(item_text)
    
    def _clear_evaluation_display(self):
        """Clear the evaluation display."""
        self.eval_results.clear()
        self.pattern_list.clear()
        self.bot_list.clear()
        self.mini_board.set_board(None)
    
    def auto_step(self):
        """Perform one step of automatic play."""
        if self.move_in_progress:
            return
        
        if self.board.is_game_over():
            self.pause_auto()
            self.status_label.setText("Game over")
            return
        
        # Get a legal move (for demo, use first available)
        legal_moves = list(self.board.legal_moves)
        if not legal_moves:
            self.pause_auto()
            return
        
        move = legal_moves[0]
        
        # Evaluate the move
        self._evaluate_move(move)
        
        # Apply the move after a short delay
        QTimer.singleShot(100, lambda: self._apply_move(move))
    
    def _apply_move(self, move: chess.Move):
        """Apply a move to the board."""
        try:
            self.board.push(move)
            self._refresh_board()
            self.status_label.setText(f"Move applied: {self.board.san(move)}")
        except Exception as e:
            logger.error(f"Failed to apply move: {e}")
            self.status_label.setText(f"Move failed: {e}")
    
    def _refresh_board(self):
        """Refresh the chess board display."""
        for row in range(8):
            for col in range(8):
                square = chess.square(col, 7 - row)
                piece = self.board.piece_at(square)
                
                cell = self.cell_grid[row][col]
                if piece:
                    cell.setText(piece.symbol())
                    cell.setStyleSheet("border: 1px solid #ccc; background-color: #f0f0f0;")
                else:
                    cell.setText("")
                    cell.setStyleSheet("border: 1px solid #ccc; background-color: white;")
        
        # Update mini board
        self.mini_board.set_board(self.board)


def main():
    """Main function to run the enhanced viewer."""
    app = QApplication(sys.argv)
    app.setApplicationName("Enhanced Chess Viewer")
    
    # Set application style
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f5f5f5;
        }
        QTabWidget::pane {
            border: 1px solid #ccc;
            background-color: white;
        }
        QTabBar::tab {
            background-color: #e0e0e0;
            padding: 8px 16px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background-color: white;
            border-bottom: 2px solid #007bff;
        }
        QPushButton {
            background-color: #007bff;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #0056b3;
        }
        QPushButton:disabled {
            background-color: #ccc;
        }
    """)
    
    viewer = EnhancedChessViewer()
    viewer.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()