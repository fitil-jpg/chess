#!/usr/bin/env python3
"""
Enhanced PySide Viewer with Pattern Management and Display
Integrates pattern detection, filtering, and management during gameplay.
"""

from utils.usage_logger import record_usage
record_usage(__file__)

import sys
import chess
import logging
import time
from typing import List, Dict, Optional, Any
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QWidget, QGridLayout, QVBoxLayout, QHBoxLayout,
    QFrame, QPushButton, QLabel, QMessageBox, QSizePolicy,
    QListWidget, QScrollArea, QTabWidget, QSpinBox, QComboBox,
    QTextEdit, QMainWindow, QCheckBox, QGroupBox, QSplitter,
    QListWidgetItem, QProgressBar, QSlider
)
from PySide6.QtCore import QTimer, Qt, QSettings, Signal, QThread
from PySide6.QtGui import QPainter, QColor, QFont, QPen

from chess_ai.bot_agent import make_agent
from chess_ai.pattern_detector import PatternDetector, ChessPattern, PatternType
from chess_ai.pattern_manager import PatternManager
from chess_ai.pattern_filter import PatternFilter
from ui.cell import Cell
from ui.drawer_manager import DrawerManager
from evaluation import evaluate

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set Stockfish path if available
import os
if not os.environ.get("STOCKFISH_PATH"):
    stockfish_path = "/workspace/bin/stockfish-bin"
    if os.path.exists(stockfish_path):
        os.environ["STOCKFISH_PATH"] = stockfish_path

# Bot configuration
WHITE_AGENT = "StockfishBot"
BLACK_AGENT = "DynamicBot"


class PatternDetectionWorker(QThread):
    """Worker thread for pattern detection during games"""
    patternDetected = Signal(object)  # ChessPattern
    patternFiltered = Signal(object)  # Filtered pattern data
    
    def __init__(self, board, move, evaluation_before, evaluation_after, bot_analysis=None):
        super().__init__()
        self.board = board
        self.move = move
        self.evaluation_before = evaluation_before
        self.evaluation_after = evaluation_after
        self.bot_analysis = bot_analysis or {}
        self.pattern_detector = PatternDetector()
        self.pattern_filter = PatternFilter()
    
    def run(self):
        """Detect patterns and apply filtering"""
        try:
            # Detect patterns
            patterns = self.pattern_detector.detect_patterns(
                self.board,
                self.move,
                self.evaluation_before,
                self.evaluation_after,
                self.bot_analysis
            )
            
            for pattern in patterns:
                if self.isInterruptionRequested():
                    return
                # Emit the pattern
                self.patternDetected.emit(pattern)
                
                # Apply filtering and emit filtered data
                filter_result = self.pattern_filter.analyze_pattern_relevance(
                    self.board,
                    self.move,
                    pattern.pattern_types
                )
                
                # Check for exchange patterns
                exchange_info = self.pattern_filter.detect_exchange_pattern(self.board, self.move)
                if exchange_info:
                    filter_result["exchange_info"] = exchange_info
                
                if self.isInterruptionRequested():
                    return
                self.patternFiltered.emit({
                    "pattern": pattern,
                    "filter_result": filter_result
                })
                
        except Exception as e:
            logger.error(f"Pattern detection failed: {e}")


class PatternDisplayWidget(QWidget):
    """Widget for displaying detected patterns during gameplay"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.patterns = []
        self.current_pattern = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Pattern list
        self.pattern_list = QListWidget()
        self.pattern_list.itemClicked.connect(self.on_pattern_selected)
        layout.addWidget(QLabel("Detected Patterns:"))
        layout.addWidget(self.pattern_list)
        
        # Pattern details
        self.pattern_details = QTextEdit()
        self.pattern_details.setMaximumHeight(200)
        self.pattern_details.setReadOnly(True)
        layout.addWidget(QLabel("Pattern Details:"))
        layout.addWidget(self.pattern_details)
        
        # Filter controls
        filter_group = QGroupBox("Pattern Filter")
        filter_layout = QVBoxLayout(filter_group)
        
        self.show_filtered_checkbox = QCheckBox("Show Filtered View")
        self.show_filtered_checkbox.setChecked(True)
        self.show_filtered_checkbox.toggled.connect(self.on_filter_toggled)
        filter_layout.addWidget(self.show_filtered_checkbox)
        
        self.complexity_slider = QSlider(Qt.Horizontal)
        self.complexity_slider.setRange(0, 2)
        self.complexity_slider.setValue(1)
        self.complexity_slider.valueChanged.connect(self.on_complexity_changed)
        filter_layout.addWidget(QLabel("Complexity Filter:"))
        filter_layout.addWidget(self.complexity_slider)
        
        layout.addWidget(filter_group)
    
    def add_pattern(self, pattern: ChessPattern, filter_result: Dict[str, Any]):
        """Add a detected pattern to the display"""
        self.patterns.append({
            "pattern": pattern,
            "filter_result": filter_result,
            "timestamp": time.time()
        })
        
        # Add to list
        item_text = f"{pattern.move} - {', '.join(pattern.pattern_types[:2])}"
        if len(pattern.pattern_types) > 2:
            item_text += f" (+{len(pattern.pattern_types)-2} more)"
        
        item = QListWidgetItem(item_text)
        item.setData(Qt.UserRole, len(self.patterns) - 1)
        self.pattern_list.addItem(item)
        
        # Auto-select if this is the first pattern
        if len(self.patterns) == 1:
            self.pattern_list.setCurrentItem(item)
            self.on_pattern_selected(item)
    
    def on_pattern_selected(self, item: QListWidgetItem):
        """Handle pattern selection"""
        pattern_index = item.data(Qt.UserRole)
        if 0 <= pattern_index < len(self.patterns):
            pattern_data = self.patterns[pattern_index]
            self.current_pattern = pattern_data
            self.update_pattern_details()
    
    def update_pattern_details(self):
        """Update the pattern details display"""
        if not self.current_pattern:
            return
        
        pattern = self.current_pattern["pattern"]
        filter_result = self.current_pattern["filter_result"]
        
        details = f"Move: {pattern.move}\n"
        details += f"Types: {', '.join(pattern.pattern_types)}\n"
        details += f"Description: {pattern.description}\n"
        details += f"Evaluation Change: {pattern.evaluation.get('change', 0):.1f}\n\n"
        
        # Add filtering information
        relevant_count = len(filter_result.get("relevant_pieces", set()))
        irrelevant_count = len(filter_result.get("irrelevant_pieces", set()))
        details += f"Relevant Pieces: {relevant_count}\n"
        details += f"Irrelevant Pieces: {irrelevant_count}\n"
        details += f"Relevance Score: {filter_result.get('relevance_score', 0):.2f}\n\n"
        
        # Add exchange information if available
        if "exchange_info" in filter_result:
            exchange = filter_result["exchange_info"]
            details += f"Exchange Pattern Detected:\n"
            details += f"  Value: {exchange.get('exchange_value', 0)}\n"
            details += f"  Forced: {exchange.get('is_forced', False)}\n\n"
        
        # Add pattern analysis details
        pattern_analysis = filter_result.get("pattern_analysis", {})
        for pattern_type, analysis in pattern_analysis.items():
            details += f"{pattern_type.upper()} Analysis:\n"
            for key, value in analysis.items():
                if key != "relevant_squares":
                    details += f"  {key}: {value}\n"
            details += "\n"
        
        self.pattern_details.setPlainText(details)
    
    def on_filter_toggled(self, checked: bool):
        """Handle filter toggle"""
        # This would be connected to the main board display
        pass
    
    def on_complexity_changed(self, value: int):
        """Handle complexity filter change"""
        complexity_levels = ["simple", "moderate", "complex"]
        # This would filter the displayed patterns
        pass
    
    def clear_patterns(self):
        """Clear all patterns"""
        self.patterns.clear()
        self.current_pattern = None
        self.pattern_list.clear()
        self.pattern_details.clear()


class EnhancedChessViewer(QMainWindow):
    """Enhanced chess viewer with pattern management and display"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enhanced Chess Viewer — Pattern Management")
        self.resize(1400, 900)
        
        # Initialize components
        self.board = chess.Board()
        self.piece_objects = {}
        self.pattern_manager = PatternManager()
        self.pattern_filter = PatternFilter()
        self.drawer_manager = DrawerManager()
        # Track background workers to ensure clean shutdown
        self._workers: List[QThread] = []
        
        # Game state
        self.auto_running = False
        self.move_in_progress = False
        self.detected_patterns = []
        
        # Initialize agents
        self._init_agents()
        
        # Initialize UI
        self._init_ui()
        
        # Initialize board
        self._init_board()
    
    def _init_agents(self):
        """Initialize chess agents"""
        try:
            self.white_agent = make_agent(WHITE_AGENT, chess.WHITE)
            self.black_agent = make_agent(BLACK_AGENT, chess.BLACK)
        except Exception as exc:
            logger.error(f"Failed to initialize agents: {exc}")
            self._show_error("AI Agent Initialization Failed", str(exc))
    
    def _init_ui(self):
        """Initialize user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel - chess board
        left_panel = self._create_board_panel()
        main_layout.addWidget(left_panel, 2)
        
        # Right panel - controls and patterns
        right_panel = self._create_control_panel()
        main_layout.addWidget(right_panel, 1)
    
    def _create_board_panel(self) -> QWidget:
        """Create the chess board panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Board frame
        self.board_frame = QFrame()
        self.board_frame.setFixedSize(560, 560)
        self.board_frame.setStyleSheet("border: 2px solid #333;")
        
        self.grid = QGridLayout(self.board_frame)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(0)
        self.cell_grid = [[None for _ in range(8)] for _ in range(8)]
        
        layout.addWidget(self.board_frame, alignment=Qt.AlignCenter)
        
        # Game controls
        controls_layout = QHBoxLayout()
        
        self.btn_start = QPushButton("▶ Start")
        self.btn_pause = QPushButton("⏸ Pause")
        self.btn_stop = QPushButton("⏹ Stop")
        self.btn_reset = QPushButton("🔄 Reset")
        self.btn_new_game = QPushButton("🆕 New Game")
        
        self.btn_start.clicked.connect(self.start_auto)
        self.btn_pause.clicked.connect(self.pause_auto)
        self.btn_stop.clicked.connect(self.stop_auto)
        self.btn_reset.clicked.connect(self.reset_game)
        self.btn_new_game.clicked.connect(self.new_game)
        
        controls_layout.addWidget(self.btn_start)
        controls_layout.addWidget(self.btn_pause)
        controls_layout.addWidget(self.btn_stop)
        controls_layout.addWidget(self.btn_reset)
        controls_layout.addWidget(self.btn_new_game)
        
        layout.addLayout(controls_layout)
        
        # Game status
        self.status_label = QLabel("Ready to play")
        layout.addWidget(self.status_label)
        
        return panel
    
    def _create_control_panel(self) -> QWidget:
        """Create the control panel with tabs"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Tab widget
        tab_widget = QTabWidget()
        
        # Pattern display tab
        self.pattern_display = PatternDisplayWidget()
        tab_widget.addTab(self.pattern_display, "🎯 Patterns")
        
        # Pattern management tab
        pattern_mgmt_tab = self._create_pattern_management_tab()
        tab_widget.addTab(pattern_mgmt_tab, "📚 Pattern Library")
        
        # Settings tab
        settings_tab = self._create_settings_tab()
        tab_widget.addTab(settings_tab, "⚙️ Settings")
        
        layout.addWidget(tab_widget)
        
        return panel
    
    def _create_pattern_management_tab(self) -> QWidget:
        """Create pattern management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Search controls
        search_group = QGroupBox("Search Patterns")
        search_layout = QVBoxLayout(search_group)
        
        # Pattern type filter
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Types:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["All", "Fork", "Pin", "Tactical", "Hanging", "Sacrifice"])
        type_layout.addWidget(self.type_combo)
        search_layout.addLayout(type_layout)
        
        # Piece type filter
        piece_layout = QHBoxLayout()
        piece_layout.addWidget(QLabel("Piece:"))
        self.piece_combo = QComboBox()
        self.piece_combo.addItems(["All", "Pawn", "Knight", "Bishop", "Rook", "Queen", "King"])
        piece_layout.addWidget(self.piece_combo)
        search_layout.addLayout(piece_layout)
        
        # Search button
        self.search_btn = QPushButton("🔍 Search")
        self.search_btn.clicked.connect(self.search_patterns)
        search_layout.addWidget(self.search_btn)
        
        layout.addWidget(search_group)
        
        # Pattern list
        self.pattern_library_list = QListWidget()
        self.pattern_library_list.itemClicked.connect(self.on_library_pattern_selected)
        layout.addWidget(QLabel("Pattern Library:"))
        layout.addWidget(self.pattern_library_list)
        
        # Pattern actions
        actions_layout = QHBoxLayout()
        
        self.btn_add_pattern = QPushButton("➕ Add Pattern")
        self.btn_edit_pattern = QPushButton("✏️ Edit")
        self.btn_delete_pattern = QPushButton("🗑️ Delete")
        self.btn_export_patterns = QPushButton("📤 Export")
        
        self.btn_add_pattern.clicked.connect(self.add_custom_pattern)
        self.btn_edit_pattern.clicked.connect(self.edit_pattern)
        self.btn_delete_pattern.clicked.connect(self.delete_pattern)
        self.btn_export_patterns.clicked.connect(self.export_patterns)
        
        actions_layout.addWidget(self.btn_add_pattern)
        actions_layout.addWidget(self.btn_edit_pattern)
        actions_layout.addWidget(self.btn_delete_pattern)
        actions_layout.addWidget(self.btn_export_patterns)
        
        layout.addLayout(actions_layout)
        
        return widget
    
    def _create_settings_tab(self) -> QWidget:
        """Create settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Bot settings
        bot_group = QGroupBox("Bot Configuration")
        bot_layout = QVBoxLayout(bot_group)
        
        # White agent
        white_layout = QHBoxLayout()
        white_layout.addWidget(QLabel("White:"))
        self.white_agent_combo = QComboBox()
        self.white_agent_combo.addItems(["StockfishBot", "DynamicBot", "RandomBot", "AggressiveBot"])
        self.white_agent_combo.setCurrentText(WHITE_AGENT)
        white_layout.addWidget(self.white_agent_combo)
        bot_layout.addLayout(white_layout)
        
        # Black agent
        black_layout = QHBoxLayout()
        black_layout.addWidget(QLabel("Black:"))
        self.black_agent_combo = QComboBox()
        self.black_agent_combo.addItems(["StockfishBot", "DynamicBot", "RandomBot", "AggressiveBot"])
        self.black_agent_combo.setCurrentText(BLACK_AGENT)
        black_layout.addWidget(self.black_agent_combo)
        bot_layout.addLayout(black_layout)
        
        layout.addWidget(bot_group)
        
        # Pattern detection settings
        pattern_group = QGroupBox("Pattern Detection")
        pattern_layout = QVBoxLayout(pattern_group)
        
        self.auto_detect_checkbox = QCheckBox("Auto-detect patterns during play")
        self.auto_detect_checkbox.setChecked(True)
        pattern_layout.addWidget(self.auto_detect_checkbox)
        
        self.filter_pieces_checkbox = QCheckBox("Filter irrelevant pieces")
        self.filter_pieces_checkbox.setChecked(True)
        pattern_layout.addWidget(self.filter_pieces_checkbox)
        
        layout.addWidget(pattern_group)
        
        # Timing settings
        timing_group = QGroupBox("Timing")
        timing_layout = QVBoxLayout(timing_group)
        
        timing_layout.addWidget(QLabel("Move Delay (ms):"))
        self.move_delay_spinbox = QSpinBox()
        self.move_delay_spinbox.setRange(100, 5000)
        self.move_delay_spinbox.setValue(1000)
        timing_layout.addWidget(self.move_delay_spinbox)
        
        layout.addWidget(timing_group)
        
        return widget
    
    def _init_board(self):
        """Initialize the chess board"""
        for row in range(8):
            for col in range(8):
                cell = Cell(row, col, self.drawer_manager)
                self.grid.addWidget(cell, row, col)
                self.cell_grid[row][col] = cell
        
        self._update_board()
    
    def _update_board(self):
        """Update the board display"""
        for row in range(8):
            for col in range(8):
                square = chess.square(col, 7 - row)
                piece = self.board.piece_at(square)
                cell = self.cell_grid[row][col]
                cell.set_piece(piece.symbol() if piece else None)
                cell.update()
    
    def start_auto(self):
        """Start automatic play"""
        if not self.auto_running:
            self.auto_running = True
            self.auto_timer = QTimer()
            self.auto_timer.timeout.connect(self.auto_step)
            self.auto_timer.start(self.move_delay_spinbox.value())
            self.status_label.setText("Auto play running...")
    
    def pause_auto(self):
        """Pause automatic play"""
        if hasattr(self, 'auto_timer'):
            self.auto_timer.stop()
        self.auto_running = False
        self.status_label.setText("Paused")
    
    def stop_auto(self):
        """Stop automatic play"""
        self.pause_auto()
        self.status_label.setText("Stopped")
    
    def reset_game(self):
        """Reset the current game"""
        self.board = chess.Board()
        self.piece_objects = {}
        self.detected_patterns.clear()
        self.pattern_display.clear_patterns()
        self._update_board()
        self.status_label.setText("Game reset")
    
    def new_game(self):
        """Start a new game"""
        self.reset_game()
        self.start_auto()
    
    def auto_step(self):
        """Perform one automatic move"""
        if self.move_in_progress or self.board.is_game_over():
            if self.board.is_game_over():
                self.pause_auto()
                self._show_game_over()
            return
        
        self.move_in_progress = True
        
        try:
            # Choose move
            mover_color = self.board.turn
            agent = self.white_agent if mover_color == chess.WHITE else self.black_agent
            
            # Get evaluation before move
            eval_before, _ = evaluate(self.board)
            eval_before_dict = {"total": eval_before}
            
            # Choose move
            move = agent.choose_move(self.board)
            if move is None or not self.board.is_legal(move):
                self.pause_auto()
                return
            
            # Apply move
            self.board.push(move)
            
            # Get evaluation after move
            eval_after, _ = evaluate(self.board)
            eval_after_dict = {"total": eval_after}
            
            # Update board display
            self._update_board()
            
            # Detect patterns if enabled
            if self.auto_detect_checkbox.isChecked():
                self._detect_patterns_async(move, eval_before_dict, eval_after_dict)
            
            # Update status
            move_san = self.board.san(move)
            self.status_label.setText(f"Last move: {move_san}")
            
        except Exception as e:
            logger.error(f"Error in auto_step: {e}")
            self.pause_auto()
        finally:
            self.move_in_progress = False
    
    def _detect_patterns_async(self, move, eval_before, eval_after):
        """Detect patterns asynchronously"""
        worker = PatternDetectionWorker(
            self.board, move, eval_before, eval_after
        )
        # Parent the thread to the viewer so Qt manages lifetime
        worker.setParent(self)
        worker.patternDetected.connect(self.on_pattern_detected)
        worker.patternFiltered.connect(self.on_pattern_filtered)
        worker.finished.connect(self._on_worker_finished)
        # Keep a strong reference so the thread isn't destroyed prematurely
        self._workers.append(worker)
        worker.start()

    def _on_worker_finished(self):
        """Clean up finished worker threads"""
        sender = self.sender()
        if isinstance(sender, QThread):
            try:
                # Remove from tracking list if present
                self._workers = [w for w in self._workers if w is not sender]
            finally:
                try:
                    sender.deleteLater()
                except Exception:
                    pass
    
    def on_pattern_detected(self, pattern: ChessPattern):
        """Handle detected pattern"""
        logger.info(f"Pattern detected: {pattern.move} - {pattern.pattern_types}")
    
    def on_pattern_filtered(self, data: Dict[str, Any]):
        """Handle filtered pattern data"""
        pattern = data["pattern"]
        filter_result = data["filter_result"]
        
        # Add to pattern display
        self.pattern_display.add_pattern(pattern, filter_result)
        
        # Save to pattern manager
        pattern_id = self.pattern_manager.add_pattern(pattern)
        logger.info(f"Pattern saved with ID: {pattern_id}")
    
    def search_patterns(self):
        """Search patterns in the library"""
        # Get search criteria
        pattern_type = self.type_combo.currentText()
        piece_type = self.piece_combo.currentText()
        
        # Build search parameters
        search_params = {}
        if pattern_type != "All":
            search_params["pattern_types"] = [pattern_type.lower()]
        if piece_type != "All":
            search_params["piece_types"] = [piece_type.lower()]
        
        # Search patterns
        results = self.pattern_manager.search_patterns(**search_params)
        
        # Update list
        self.pattern_library_list.clear()
        for pattern in results:
            item_text = f"{pattern.move} - {', '.join(pattern.pattern_types)}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, pattern)
            self.pattern_library_list.addItem(item)
    
    def on_library_pattern_selected(self, item: QListWidgetItem):
        """Handle library pattern selection"""
        pattern = item.data(Qt.UserRole)
        if pattern:
            # Load pattern on board
            try:
                self.board = chess.Board(pattern.fen)
                self._update_board()
                self.status_label.setText(f"Loaded pattern: {pattern.move}")
            except Exception as e:
                logger.error(f"Failed to load pattern: {e}")
    
    def add_custom_pattern(self):
        """Add a custom pattern"""
        # This would open a dialog to create a custom pattern
        QMessageBox.information(self, "Add Pattern", "Custom pattern creation not implemented yet")
    
    def edit_pattern(self):
        """Edit selected pattern"""
        current_item = self.pattern_library_list.currentItem()
        if current_item:
            QMessageBox.information(self, "Edit Pattern", "Pattern editing not implemented yet")
    
    def delete_pattern(self):
        """Delete selected pattern"""
        current_item = self.pattern_library_list.currentItem()
        if current_item:
            pattern = current_item.data(Qt.UserRole)
            if pattern and pattern.metadata.get("id"):
                if self.pattern_manager.delete_pattern(pattern.metadata["id"]):
                    self.search_patterns()  # Refresh list
                    QMessageBox.information(self, "Success", "Pattern deleted")
                else:
                    QMessageBox.warning(self, "Error", "Failed to delete pattern")
    
    def export_patterns(self):
        """Export patterns"""
        QMessageBox.information(self, "Export", "Pattern export not implemented yet")
    
    def _show_game_over(self):
        """Show game over message"""
        result = self.board.result()
        QMessageBox.information(self, "Game Over", f"Game result: {result}")
    
    def _show_error(self, title: str, message: str):
        """Show error message"""
        QMessageBox.critical(self, title, message)

    def closeEvent(self, event):
        """Ensure all background threads are stopped before closing"""
        try:
            # Stop timers/auto-play to avoid spawning new workers
            self.auto_running = False
            if hasattr(self, 'auto_timer'):
                try:
                    self.auto_timer.stop()
                except Exception:
                    pass

            # Wait for any running worker threads to finish
            for worker in list(self._workers):
                try:
                    if worker.isRunning():
                        # Wait up to 2 seconds per worker to finish gracefully
                        worker.wait(2000)
                except Exception:
                    pass
                try:
                    worker.deleteLater()
                except Exception:
                    pass
            self._workers.clear()
        finally:
            event.accept()


def main():
    """Main function"""
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("Enhanced Chess Viewer")
        app.setApplicationVersion("2.0")
        
        # Apply styling
        app.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
            }
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #e9ecef;
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
                background-color: #6c757d;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        viewer = EnhancedChessViewer()
        viewer.show()
        
        sys.exit(app.exec())
        
    except Exception as exc:
        print(f"Application failed to start: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()