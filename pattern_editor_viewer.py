#!/usr/bin/env python3
"""
Pattern Editor/Viewer for Chess
Detects and catalogs interesting chess patterns during bot games.
"""

from utils.usage_logger import record_usage
record_usage(__file__)

import sys
import chess
import logging
from typing import List, Dict, Optional
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QWidget, QGridLayout, QVBoxLayout, QHBoxLayout,
    QFrame, QPushButton, QLabel, QMessageBox, QSizePolicy,
    QListWidget, QScrollArea, QTabWidget, QProgressBar,
    QSpinBox, QComboBox, QGroupBox, QSplitter, QTextEdit, QMainWindow,
    QCheckBox, QListWidgetItem
)
from PySide6.QtCore import QTimer, Qt, QSettings, Signal, QThread
from PySide6.QtGui import QPainter, QColor, QFont

from chess_ai.bot_agent import make_agent
from chess_ai.pattern_detector import PatternDetector, ChessPattern, PatternType
from chess_ai.pattern_storage import PatternCatalog
from pathlib import Path
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

# Default bot configuration
WHITE_AGENT = "StockfishBot"
BLACK_AGENT = "DynamicBot"


class PatternWorker(QThread):
    """Worker thread for detecting patterns during games"""
    patternDetected = Signal(object)  # ChessPattern
    gameCompleted = Signal(int)       # game number
    progressUpdated = Signal(int)     # progress percentage
    statusUpdated = Signal(str)       # status message
    
    def __init__(self, white_agent, black_agent, num_games=10):
        super().__init__()
        self.white_agent = white_agent
        self.black_agent = black_agent
        self.num_games = num_games
        self._stop_requested = False
        self.pattern_detector = PatternDetector()
        
    def run(self):
        """Run games and detect patterns"""
        for game_id in range(self.num_games):
            if self._stop_requested:
                break
                
            self.statusUpdated.emit(f"Playing game {game_id + 1}/{self.num_games}")
            
            # Play one game and detect patterns
            self._play_and_detect(game_id)
            self.gameCompleted.emit(game_id + 1)
            
            # Update progress
            progress = int((game_id + 1) / self.num_games * 100)
            self.progressUpdated.emit(progress)
            
        self.statusUpdated.emit(f"Completed! Found {len(self.pattern_detector.patterns)} patterns")
        
    def _play_and_detect(self, game_id: int):
        """Play a game and detect patterns"""
        board = chess.Board()
        move_count = 0
        max_moves = 100  # Limit moves per game
        
        # Store evaluation history
        eval_history = []
        
        while not board.is_game_over() and move_count < max_moves:
            if self._stop_requested:
                break
                
            # Get evaluation before move
            eval_before, _ = evaluate(board)
            eval_before_dict = {"total": eval_before}
            
            # Choose move
            mover_color = board.turn
            agent = self.white_agent if mover_color == chess.WHITE else self.black_agent
            
            try:
                move = agent.choose_move(board)
                if move is None or not board.is_legal(move):
                    break
                
                # Create bot analysis data
                bot_analysis = {}
                if hasattr(agent, "get_last_reason"):
                    reason = agent.get_last_reason()
                    if "alternatives" in str(reason).lower():
                        bot_analysis["alternatives_count"] = 6  # Indicate multiple alternatives
                
                # Push move
                board.push(move)
                move_count += 1
                
                # Get evaluation after move
                eval_after, _ = evaluate(board)
                eval_after_dict = {"total": eval_after}
                
                # Detect patterns
                patterns = self.pattern_detector.detect_patterns(
                    board,
                    move,
                    eval_before_dict,
                    eval_after_dict,
                    bot_analysis
                )
                
                # Emit detected patterns
                for pattern in patterns:
                    pattern.metadata["game_id"] = game_id
                    self.patternDetected.emit(pattern)
                    
            except Exception as e:
                logger.error(f"Error in game {game_id}, move {move_count}: {e}")
                break
    
    def stop(self):
        """Stop the worker"""
        self._stop_requested = True


class PatternEditorViewer(QMainWindow):
    """Main pattern editor/viewer window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chess Pattern Editor & Viewer")
        self.resize(1400, 800)
        
        # Pattern management
        self.pattern_catalog = PatternCatalog()
        self.tournament_patterns_path: Optional[Path] = None
        self.pattern_catalog.load_patterns()
        self.current_patterns: List[ChessPattern] = list(self.pattern_catalog.patterns)
        self.current_pattern_index = -1
        
        # Chess board state
        self.board = chess.Board()
        self.piece_objects = {}
        
        # Initialize agents
        self._init_agents()
        
        # Initialize UI
        self._init_ui()
        
        # Load existing patterns
        self._update_pattern_list()
        
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
        # Main widget with scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.setCentralWidget(scroll_area)
        
        content_widget = QWidget()
        main_layout = QVBoxLayout(content_widget)
        
        # Splitter for board and controls
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - chess board
        left_panel = self._create_board_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - pattern controls
        right_panel = self._create_control_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([600, 800])
        
        main_layout.addWidget(splitter)
        scroll_area.setWidget(content_widget)
        
    def _create_board_panel(self) -> QWidget:
        """Create panel with chess board"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Title
        title = QLabel("Pattern Board")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Chess board
        self.board_frame = QFrame()
        self.board_frame.setFixedSize(560, 560)
        self.board_frame.setStyleSheet("border: 2px solid #333;")
        
        self.grid = QGridLayout(self.board_frame)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(0)
        self.cell_grid = [[None for _ in range(8)] for _ in range(8)]
        
        # Initialize board cells
        self._init_board_cells()
        
        layout.addWidget(self.board_frame, alignment=Qt.AlignCenter)
        
        # Pattern info display
        self.pattern_info = QTextEdit()
        self.pattern_info.setMaximumHeight(150)
        self.pattern_info.setPlainText("Select a pattern to view details...")
        layout.addWidget(self.pattern_info)
        
        return panel
        
    def _create_control_panel(self) -> QWidget:
        """Create control panel with tabs"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Tab widget
        tab_widget = QTabWidget()
        
        # Tab 1: Pattern Detection
        detection_tab = self._create_detection_tab()
        tab_widget.addTab(detection_tab, "Pattern Detection")
        
        # Tab 2: Pattern Library
        library_tab = self._create_library_tab()
        tab_widget.addTab(library_tab, "Pattern Library")
        
        # Tab 3: Statistics
        stats_tab = self._create_stats_tab()
        tab_widget.addTab(stats_tab, "Statistics")
        
        layout.addWidget(tab_widget)
        
        return panel
        
    def _create_detection_tab(self) -> QWidget:
        """Create pattern detection tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Control group
        control_group = QGroupBox("Game Control")
        control_layout = QVBoxLayout(control_group)
        
        # Buttons
        self.btn_start = QPushButton("▶ Start Auto Play")
        self.btn_pause = QPushButton("⏸ Pause")
        self.btn_stop = QPushButton("⏹ Stop")
        
        self.btn_start.setStyleSheet("background-color: #28a745; color: white; padding: 10px; font-size: 14px;")
        self.btn_pause.setStyleSheet("background-color: #007bff; color: white; padding: 10px; font-size: 14px;")
        self.btn_stop.setStyleSheet("background-color: #dc3545; color: white; padding: 10px; font-size: 14px;")
        
        self.btn_pause.setEnabled(False)
        self.btn_stop.setEnabled(False)
        
        self.btn_start.clicked.connect(self._start_pattern_detection)
        self.btn_pause.clicked.connect(self._pause_detection)
        self.btn_stop.clicked.connect(self._stop_detection)
        
        control_layout.addWidget(self.btn_start)
        control_layout.addWidget(self.btn_pause)
        control_layout.addWidget(self.btn_stop)
        
        # Settings
        settings_group = QGroupBox("Settings")
        settings_layout = QVBoxLayout(settings_group)
        
        # Number of games
        games_layout = QHBoxLayout()
        games_layout.addWidget(QLabel("Number of games:"))
        self.games_spinbox = QSpinBox()
        self.games_spinbox.setRange(1, 50)
        self.games_spinbox.setValue(10)
        games_layout.addWidget(self.games_spinbox)
        games_layout.addStretch()
        settings_layout.addLayout(games_layout)
        
        # Bot selection
        bots_layout = QHBoxLayout()
        bots_layout.addWidget(QLabel("White:"))
        self.white_combo = QComboBox()
        self.white_combo.addItems(["StockfishBot", "DynamicBot", "RandomBot", "AggressiveBot"])
        self.white_combo.setCurrentText(WHITE_AGENT)
        bots_layout.addWidget(self.white_combo)
        
        bots_layout.addWidget(QLabel("Black:"))
        self.black_combo = QComboBox()
        self.black_combo.addItems(["StockfishBot", "DynamicBot", "RandomBot", "AggressiveBot"])
        self.black_combo.setCurrentText(BLACK_AGENT)
        bots_layout.addWidget(self.black_combo)
        settings_layout.addLayout(bots_layout)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        settings_layout.addWidget(self.progress_bar)
        
        # Status
        self.status_label = QLabel("Ready to detect patterns")
        settings_layout.addWidget(self.status_label)
        
        layout.addWidget(control_group)
        layout.addWidget(settings_group)
        
        # Detected patterns list
        patterns_group = QGroupBox("Detected Patterns (This Session)")
        patterns_layout = QVBoxLayout(patterns_group)
        
        self.detected_list = QListWidget()
        self.detected_list.itemClicked.connect(self._on_detected_pattern_clicked)
        patterns_layout.addWidget(self.detected_list)
        
        # Save detected patterns button
        self.btn_save_detected = QPushButton("💾 Save Detected Patterns to Library")
        self.btn_save_detected.clicked.connect(self._save_detected_patterns)
        patterns_layout.addWidget(self.btn_save_detected)
        
        layout.addWidget(patterns_group)
        layout.addStretch()
        
        return widget
        
    def _create_library_tab(self) -> QWidget:
        """Create pattern library tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Filter group
        filter_group = QGroupBox("Pattern Filters")
        filter_layout = QVBoxLayout(filter_group)
        
        # Pattern type checkboxes
        self.filter_checkboxes = {}
        pattern_types = [
            ("Tactical Moment", PatternType.TACTICAL_MOMENT),
            ("Fork", PatternType.FORK),
            ("Pin", PatternType.PIN),
            ("Hanging Piece", PatternType.HANGING_PIECE),
            ("Opening Trick", PatternType.OPENING_TRICK),
            ("Endgame Technique", PatternType.ENDGAME_TECHNIQUE),
            ("Sacrifice", PatternType.SACRIFICE),
            ("Critical Decision", PatternType.CRITICAL_DECISION),
        ]
        
        for label, pattern_type in pattern_types:
            checkbox = QCheckBox(label)
            checkbox.stateChanged.connect(self._apply_filters)
            self.filter_checkboxes[pattern_type] = checkbox
            filter_layout.addWidget(checkbox)
        
        # Filter buttons
        filter_btn_layout = QHBoxLayout()
        btn_select_all = QPushButton("Select All")
        btn_clear_all = QPushButton("Clear All")
        btn_select_all.clicked.connect(self._select_all_filters)
        btn_clear_all.clicked.connect(self._clear_all_filters)
        filter_btn_layout.addWidget(btn_select_all)
        filter_btn_layout.addWidget(btn_clear_all)
        filter_layout.addLayout(filter_btn_layout)
        
        layout.addWidget(filter_group)
        
        # Source selection
        source_group = QGroupBox("Source")
        source_layout = QHBoxLayout(source_group)
        self.source_combo = QComboBox()
        self.source_combo.addItems(["Catalog", "Tournament (latest)"])
        self.source_combo.currentIndexChanged.connect(self._on_source_changed)
        source_layout.addWidget(QLabel("Load from:"))
        source_layout.addWidget(self.source_combo)
        source_layout.addStretch()
        layout.addWidget(source_group)

        # Pattern list
        patterns_group = QGroupBox("Pattern Library")
        patterns_layout = QVBoxLayout(patterns_group)
        
        self.library_list = QListWidget()
        self.library_list.itemClicked.connect(self._on_library_pattern_clicked)
        patterns_layout.addWidget(self.library_list)
        
        # Pattern management buttons
        mgmt_layout = QHBoxLayout()
        
        self.btn_delete_pattern = QPushButton("🗑 Delete Pattern")
        self.btn_export_patterns = QPushButton("📤 Export to PGN")
        self.btn_clear_library = QPushButton("🗑 Clear Library")
        
        self.btn_delete_pattern.clicked.connect(self._delete_pattern)
        self.btn_export_patterns.clicked.connect(self._export_patterns)
        self.btn_clear_library.clicked.connect(self._clear_library)
        
        mgmt_layout.addWidget(self.btn_delete_pattern)
        mgmt_layout.addWidget(self.btn_export_patterns)
        mgmt_layout.addWidget(self.btn_clear_library)
        
        patterns_layout.addLayout(mgmt_layout)
        
        layout.addWidget(patterns_group)
        
        return widget
        
    def _create_stats_tab(self) -> QWidget:
        """Create statistics tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Statistics display
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        layout.addWidget(self.stats_text)
        
        # Refresh button
        btn_refresh = QPushButton("🔄 Refresh Statistics")
        btn_refresh.clicked.connect(self._update_statistics)
        layout.addWidget(btn_refresh)
        
        # Initial statistics
        self._update_statistics()
        
        return widget
        
    def _init_board_cells(self):
        """Initialize chess board cells"""
        for row in range(8):
            for col in range(8):
                cell = Cell(row, col, DrawerManager())
                self.grid.addWidget(cell, row, col)
                self.cell_grid[row][col] = cell
                
    def _start_pattern_detection(self):
        """Start pattern detection in games"""
        self.btn_start.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.btn_stop.setEnabled(True)
        
        # Clear detected patterns
        self.detected_list.clear()
        
        # Create and start worker
        self.pattern_worker = PatternWorker(
            self.white_agent,
            self.black_agent,
            self.games_spinbox.value()
        )
        self.pattern_worker.patternDetected.connect(self._on_pattern_detected)
        self.pattern_worker.gameCompleted.connect(self._on_game_completed)
        self.pattern_worker.progressUpdated.connect(self._on_progress_updated)
        self.pattern_worker.statusUpdated.connect(self._on_status_updated)
        self.pattern_worker.start()
        
        self.status_label.setText("Detecting patterns...")
        self.progress_bar.setVisible(True)
        
    def _pause_detection(self):
        """Pause pattern detection"""
        if hasattr(self, 'pattern_worker'):
            self.pattern_worker.stop()
        
        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.status_label.setText("Paused")
        
    def _stop_detection(self):
        """Stop pattern detection"""
        if hasattr(self, 'pattern_worker'):
            self.pattern_worker.stop()
            self.pattern_worker.wait()
        
        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_stop.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Stopped")
        
    def _on_pattern_detected(self, pattern: ChessPattern):
        """Handle detected pattern"""
        # Add to detected list
        item_text = f"{pattern.move} - {', '.join(pattern.pattern_types[:2])}"
        self.detected_list.addItem(item_text)
        
        # Store pattern reference
        item = self.detected_list.item(self.detected_list.count() - 1)
        item.setData(Qt.UserRole, pattern)
        
    def _on_game_completed(self, game_num: int):
        """Handle game completion"""
        self.status_label.setText(f"Completed game {game_num}")
        
    def _on_progress_updated(self, progress: int):
        """Handle progress update"""
        self.progress_bar.setValue(progress)
        
    def _on_status_updated(self, status: str):
        """Handle status update"""
        self.status_label.setText(status)
        
        # Re-enable start button when complete
        if "Completed" in status:
            self.btn_start.setEnabled(True)
            self.btn_pause.setEnabled(False)
            self.btn_stop.setEnabled(False)
        
    def _on_detected_pattern_clicked(self, item: QListWidgetItem):
        """Handle click on detected pattern"""
        pattern = item.data(Qt.UserRole)
        if pattern:
            self._display_pattern(pattern)
        
    def _on_library_pattern_clicked(self, item: QListWidgetItem):
        """Handle click on library pattern"""
        index = self.library_list.row(item)
        if 0 <= index < len(self.current_patterns):
            pattern = self.current_patterns[index]
            self._display_pattern(pattern)
            self.current_pattern_index = index
        
    def _display_pattern(self, pattern: ChessPattern):
        """Display pattern on board and show info"""
        # Load FEN on board
        try:
            self.board = chess.Board(pattern.fen)
            self._update_board()
        except Exception as e:
            logger.error(f"Failed to load pattern FEN: {e}")
            
        # Display pattern info
        info_text = f"Pattern: {pattern.move}\n\n"
        info_text += f"Types: {', '.join(pattern.pattern_types)}\n\n"
        info_text += f"Description: {pattern.description}\n\n"
        info_text += f"Evaluation Change: {pattern.evaluation.get('change', 0):.1f}\n\n"
        info_text += f"Influencing Pieces:\n"
        for piece_info in pattern.influencing_pieces:
            info_text += f"  - {piece_info['color']} {piece_info['piece']} at {piece_info['square']} ({piece_info['relationship']})\n"
        
        if pattern.metadata:
            info_text += f"\nMetadata:\n"
            for key, value in pattern.metadata.items():
                info_text += f"  {key}: {value}\n"
        
        self.pattern_info.setPlainText(info_text)
        
    def _update_board(self):
        """Update board display"""
        for row in range(8):
            for col in range(8):
                square = chess.square(col, 7 - row)
                piece = self.board.piece_at(square)
                cell = self.cell_grid[row][col]
                cell.set_piece(piece.symbol() if piece else None)
                cell.update()
                
    def _save_detected_patterns(self):
        """Save detected patterns to library"""
        # Get all detected patterns
        detected_patterns = []
        for i in range(self.detected_list.count()):
            item = self.detected_list.item(i)
            pattern = item.data(Qt.UserRole)
            if pattern:
                detected_patterns.append(pattern)
        
        if not detected_patterns:
            QMessageBox.information(self, "No Patterns", "No patterns to save.")
            return
        
        # Add to catalog
        self.pattern_catalog.add_patterns(detected_patterns)
        self.pattern_catalog.save_patterns()
        
        # Update library list
        self.current_patterns = list(self.pattern_catalog.patterns)
        self._update_pattern_list()
        
        QMessageBox.information(
            self,
            "Patterns Saved",
            f"Saved {len(detected_patterns)} patterns to library."
        )
        
    def _update_pattern_list(self):
        """Update pattern library list"""
        self.library_list.clear()
        
        for pattern in self.current_patterns:
            item_text = f"{pattern.move} - {', '.join(pattern.pattern_types[:2])}"
            self.library_list.addItem(item_text)
        
    def _apply_filters(self):
        """Apply pattern filters"""
        # Get selected filter types
        selected_types = [
            pt for pt, checkbox in self.filter_checkboxes.items()
            if checkbox.isChecked()
        ]
        
        # Filter patterns
        if selected_types:
            self.current_patterns = self.pattern_catalog.get_patterns(pattern_types=selected_types)
        else:
            self.current_patterns = list(self.pattern_catalog.patterns)
        
        self._update_pattern_list()
        
    def _select_all_filters(self):
        """Select all filter checkboxes"""
        for checkbox in self.filter_checkboxes.values():
            checkbox.setChecked(True)
        
    def _clear_all_filters(self):
        """Clear all filter checkboxes"""
        for checkbox in self.filter_checkboxes.values():
            checkbox.setChecked(False)
        self.current_patterns = list(self.pattern_catalog.patterns)
        self._update_pattern_list()
        
    def _delete_pattern(self):
        """Delete selected pattern from library"""
        if self.current_pattern_index < 0:
            QMessageBox.warning(self, "No Selection", "Please select a pattern to delete.")
            return
        
        reply = QMessageBox.question(
            self,
            "Delete Pattern",
            "Are you sure you want to delete this pattern?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Find the pattern in the main catalog
            pattern_to_delete = self.current_patterns[self.current_pattern_index]
            try:
                catalog_index = self.pattern_catalog.patterns.index(pattern_to_delete)
                self.pattern_catalog.remove_pattern(catalog_index)
                self.pattern_catalog.save_patterns()
                
                # Update display
                self.current_patterns = list(self.pattern_catalog.patterns)
                self._update_pattern_list()
                self.current_pattern_index = -1
                
                QMessageBox.information(self, "Success", "Pattern deleted.")
            except ValueError:
                QMessageBox.warning(self, "Error", "Pattern not found in catalog.")
        
    def _export_patterns(self):
        """Export patterns to PGN"""
        if not self.current_patterns:
            QMessageBox.warning(self, "No Patterns", "No patterns to export.")
            return
        
        output_path = "patterns/export.pgn"
        self.pattern_catalog.export_to_pgn(output_path, self.current_patterns)
        
        QMessageBox.information(
            self,
            "Export Complete",
            f"Exported {len(self.current_patterns)} patterns to {output_path}"
        )
        
    def _clear_library(self):
        """Clear pattern library"""
        reply = QMessageBox.question(
            self,
            "Clear Library",
            "Are you sure you want to delete ALL patterns from the library?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.pattern_catalog.clear_patterns()
            self.pattern_catalog.save_patterns()
            self.current_patterns = []
            self._update_pattern_list()
            self._update_statistics()
            
            QMessageBox.information(self, "Success", "Pattern library cleared.")
        
    def _update_statistics(self):
        """Update statistics display"""
        stats = self.pattern_catalog.get_statistics()
        
        stats_text = "Pattern Library Statistics\n"
        stats_text += "=" * 40 + "\n\n"
        stats_text += f"Total Patterns: {stats.get('total', 0)}\n\n"
        
        if stats.get('by_type'):
            stats_text += "Patterns by Type:\n"
            for pattern_type, count in sorted(stats['by_type'].items(), key=lambda x: -x[1]):
                stats_text += f"  {pattern_type}: {count}\n"
            stats_text += "\n"
        
        stats_text += f"Average Evaluation Change: {stats.get('avg_eval_change', 0):.2f}\n"
        stats_text += f"Opening Patterns: {stats.get('opening_patterns', 0)}\n"
        stats_text += f"Endgame Patterns: {stats.get('endgame_patterns', 0)}\n"
        
        self.stats_text.setPlainText(stats_text)

    def _on_source_changed(self, idx: int):
        """Switch between main catalog and latest tournament patterns."""
        label = self.source_combo.currentText()
        if label.startswith("Tournament"):
            self._load_latest_tournament_patterns()
        else:
            self.pattern_catalog = PatternCatalog()
            self.pattern_catalog.load_patterns()
            self.current_patterns = list(self.pattern_catalog.patterns)
            self._update_pattern_list()
            self._update_statistics()

    def _load_latest_tournament_patterns(self):
        """Load patterns from output/tournaments/<latest>/patterns/patterns.jsonl if present."""
        try:
            root = Path("output/tournaments")
            if not root.exists():
                return
            # Choose latest by directory name (timestamped)
            dirs = sorted([p for p in root.iterdir() if p.is_dir()], key=lambda p: p.name)
            if not dirs:
                return
            latest = dirs[-1]
            patterns_jsonl = latest / "patterns" / "patterns.jsonl"
            if not patterns_jsonl.exists():
                return
            # Build a transient catalog from JSONL
            records = []
            with patterns_jsonl.open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        import json
                        rec = json.loads(line)
                        pat = rec.get("pattern")
                        if isinstance(pat, dict):
                            records.append(pat)
                    except Exception:
                        continue
            # Convert
            from chess_ai.pattern_detector import ChessPattern as DetectedPattern  # local import
            self.pattern_catalog = PatternCatalog()  # temporary holder
            self.pattern_catalog.patterns = [DetectedPattern.from_dict(p) for p in records]
            self.current_patterns = list(self.pattern_catalog.patterns)
            self._update_pattern_list()
            self._update_statistics()
        except Exception as e:
            logger.error(f"Failed to load tournament patterns: {e}")
        
    def _show_error(self, title: str, message: str):
        """Show error message"""
        QMessageBox.critical(self, title, message)


def main():
    """Main function"""
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("Chess Pattern Editor & Viewer")
        app.setApplicationVersion("1.0")
        
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
        
        viewer = PatternEditorViewer()
        viewer.show()
        
        sys.exit(app.exec())
        
    except Exception as exc:
        print(f"Application failed to start: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
