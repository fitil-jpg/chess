#!/usr/bin/env python3
"""
Tournament Pattern Viewer - Enhanced Pattern Viewer with Tournament Support

This tool extends the pattern viewer to support tournament patterns
with separate sections for regular patterns and tournament patterns.
"""

import sys
import time
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, Counter

# Try to import chess, fall back to None if not available
try:
    import chess
    CHESS_AVAILABLE = True
except ImportError:
    chess = None
    CHESS_AVAILABLE = False
    print("Warning: python-chess not available, using simplified chess logic")

# Try to import PySide6, fall back to basic implementation if not available
try:
    from PySide6.QtWidgets import (
        QApplication, QWidget, QGridLayout, QVBoxLayout, QHBoxLayout,
        QFrame, QPushButton, QLabel, QCheckBox, QMessageBox, QSizePolicy,
        QListWidget, QScrollArea, QTextEdit, QSplitter, QMainWindow, QTabWidget,
        QProgressBar, QSlider, QSpinBox, QComboBox, QGroupBox, QListWidgetItem,
        QTreeWidget, QTreeWidgetItem, QDialog, QDialogButtonBox, QLineEdit,
        QTableWidget, QTableWidgetItem, QHeaderView
    )
    from PySide6.QtCore import QTimer, QRect, Qt, QSettings, Signal, QThread, pyqtSignal
    from PySide6.QtGui import QPainter, QColor, QPen, QPixmap, QFont, QBrush, QIcon
    PYSIDE_AVAILABLE = True
except ImportError:
    PYSIDE_AVAILABLE = False
    print("Warning: PySide6 not available, GUI will not work")
    
    # Create dummy classes for when PySide6 is not available
    class QThread:
        def __init__(self):
            pass
        def start(self):
            pass
        def stop(self):
            pass
        def wait(self):
            pass
        def isRunning(self):
            return False
    
    class Signal:
        def __init__(self, *args):
            pass
        def emit(self, *args):
            pass
        def connect(self, func):
            pass
    
    pyqtSignal = Signal
    
    class QWidget:
        def __init__(self, parent=None):
            pass
    
    class QMainWindow(QWidget):
        pass
    
    class QDialog(QWidget):
        pass
    
    class QListWidgetItem:
        def __init__(self, text=""):
            self.text_val = text
            self.data_val = None
        def text(self):
            return self.text_val
        def data(self, role):
            return self.data_val
        def setData(self, role, value):
            self.data_val = value
    
    class Qt:
        UserRole = 0
        AlignCenter = 0
        Horizontal = 0
    
    class QPainter:
        def __init__(self, *args):
            pass
        def setRenderHint(self, hint):
            pass
        def fillRect(self, *args):
            pass
        def setPen(self, pen):
            pass
        def setFont(self, font):
            pass
        def drawText(self, *args):
            pass
        def drawRect(self, *args):
            pass
    
    class QColor:
        def __init__(self, *args):
            pass
    
    class QPen:
        def __init__(self, *args):
            pass
    
    class QFont:
        def __init__(self, *args):
            pass
    
    class QApplication:
        def __init__(self, argv):
            pass
        def setApplicationName(self, name):
            pass
        def setApplicationVersion(self, version):
            pass
        def setStyleSheet(self, style):
            pass
        def exec(self):
            return 0

# Import chess AI components with fallbacks
try:
    from chess_ai.bot_agent import make_agent
except ImportError:
    def make_agent(name, color):
        return None

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pattern categories
class PatternCategory(Enum):
    TACTICAL = "tactical"
    OPENING = "opening"
    MIDDLEGAME = "middlegame"
    ENDGAME = "endgame"
    FORK = "fork"
    PIN = "pin"
    SKEWER = "skewer"
    SACRIFICE = "sacrifice"
    TRAP = "trap"
    POSITIONAL = "positional"
    DEFENSIVE = "defensive"
    ATTACKING = "attacking"
    TOURNAMENT = "tournament"

@dataclass
class TournamentPattern:
    """Represents a pattern from tournament games"""
    id: str
    bot1: str
    bot2: str
    result: str
    moves: List[str]
    final_fen: str
    move_count: int
    timestamp: str
    game_context: Dict[str, Any]
    pattern_type: str = "tournament"
    description: str = ""
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TournamentPattern':
        """Create from dictionary"""
        return cls(**data)

class TournamentPatternStorage:
    """Manages storage and retrieval of tournament patterns"""
    
    def __init__(self, storage_path: str = "tournament_patterns"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.patterns: Dict[str, TournamentPattern] = {}
        self.load_patterns()
    
    def save_pattern(self, pattern: TournamentPattern):
        """Save a pattern to storage"""
        self.patterns[pattern.id] = pattern
        self._save_to_file()
    
    def get_pattern(self, pattern_id: str) -> Optional[TournamentPattern]:
        """Get a pattern by ID"""
        return self.patterns.get(pattern_id)
    
    def get_patterns_by_bot(self, bot_name: str) -> List[TournamentPattern]:
        """Get all patterns involving a specific bot"""
        return [p for p in self.patterns.values() if bot_name in [p.bot1, p.bot2]]
    
    def get_patterns_by_result(self, result: str) -> List[TournamentPattern]:
        """Get all patterns with a specific result"""
        return [p for p in self.patterns.values() if p.result == result]
    
    def search_patterns(self, query: str) -> List[TournamentPattern]:
        """Search patterns by description or tags"""
        query_lower = query.lower()
        results = []
        
        for pattern in self.patterns.values():
            if (query_lower in pattern.description.lower() or 
                query_lower in pattern.bot1.lower() or
                query_lower in pattern.bot2.lower() or
                any(query_lower in tag.lower() for tag in pattern.tags)):
                results.append(pattern)
        
        return results
    
    def get_all_patterns(self) -> List[TournamentPattern]:
        """Get all stored patterns"""
        return list(self.patterns.values())
    
    def delete_pattern(self, pattern_id: str):
        """Delete a pattern"""
        if pattern_id in self.patterns:
            del self.patterns[pattern_id]
            self._save_to_file()
    
    def load_patterns(self):
        """Load patterns from storage"""
        patterns_file = self.storage_path / "patterns.json"
        if patterns_file.exists():
            try:
                with open(patterns_file, 'r') as f:
                    data = json.load(f)
                    for pattern_data in data:
                        pattern = TournamentPattern.from_dict(pattern_data)
                        self.patterns[pattern.id] = pattern
                logger.info(f"Loaded {len(self.patterns)} tournament patterns")
            except Exception as e:
                logger.error(f"Failed to load tournament patterns: {e}")
    
    def _save_to_file(self):
        """Save patterns to file"""
        patterns_file = self.storage_path / "patterns.json"
        try:
            with open(patterns_file, 'w') as f:
                pattern_list = [pattern.to_dict() for pattern in self.patterns.values()]
                json.dump(pattern_list, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save tournament patterns: {e}")

class TournamentStatsViewer(QWidget):
    """Widget for viewing tournament statistics"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tournament_stats = {}
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI for tournament stats"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Tournament Statistics")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Stats table
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(4)
        self.stats_table.setHorizontalHeaderLabels(["Bot", "Wins", "Losses", "Draws"])
        self.stats_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.stats_table)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Stats")
        refresh_btn.clicked.connect(self.refresh_stats)
        layout.addWidget(refresh_btn)
    
    def load_tournament_stats(self, stats_file: str):
        """Load tournament statistics from file"""
        try:
            with open(stats_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.tournament_stats = data.get('tournament_stats', {})
                self.update_stats_display()
        except Exception as e:
            logger.error(f"Failed to load tournament stats: {e}")
    
    def update_stats_display(self):
        """Update the stats display"""
        if not self.tournament_stats.get('bot_rankings'):
            return
        
        rankings = self.tournament_stats['bot_rankings']
        self.stats_table.setRowCount(len(rankings))
        
        for i, (bot_name, stats) in enumerate(rankings):
            self.stats_table.setItem(i, 0, QTableWidgetItem(bot_name))
            self.stats_table.setItem(i, 1, QTableWidgetItem(str(stats['wins'])))
            self.stats_table.setItem(i, 2, QTableWidgetItem(str(stats['losses'])))
            self.stats_table.setItem(i, 3, QTableWidgetItem(str(stats['draws'])))
    
    def refresh_stats(self):
        """Refresh the statistics display"""
        # Look for latest tournament stats file
        stats_dir = Path("tournament_stats")
        if stats_dir.exists():
            stats_files = list(stats_dir.glob("final_results_*.json"))
            if stats_files:
                latest_file = max(stats_files, key=lambda f: f.stat().st_mtime)
                self.load_tournament_stats(str(latest_file))

class TournamentPatternViewer(QMainWindow):
    """Main tournament pattern viewer application"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tournament Pattern Viewer")
        self.resize(1400, 900)
        
        # Initialize components
        self.tournament_storage = TournamentPatternStorage()
        self.current_pattern = None
        
        # Setup UI
        self._setup_ui()
        
        # Load existing patterns
        self._refresh_pattern_list()
    
    def _setup_ui(self):
        """Setup the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel - Pattern list and controls
        left_panel = self._create_left_panel()
        main_layout.addWidget(left_panel, 1)
        
        # Right panel - Pattern details and board
        right_panel = self._create_right_panel()
        main_layout.addWidget(right_panel, 2)
    
    def _create_left_panel(self) -> QWidget:
        """Create left panel with pattern list and controls"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Pattern selection controls
        selection_group = QGroupBox("Pattern Selection")
        selection_layout = QVBoxLayout(selection_group)
        
        # Bot filter
        bot_layout = QHBoxLayout()
        bot_layout.addWidget(QLabel("Bot Filter:"))
        self.bot_filter = QComboBox()
        self.bot_filter.addItem("All Bots")
        self.bot_filter.currentTextChanged.connect(self._filter_patterns)
        bot_layout.addWidget(self.bot_filter)
        selection_layout.addLayout(bot_layout)
        
        # Result filter
        result_layout = QHBoxLayout()
        result_layout.addWidget(QLabel("Result Filter:"))
        self.result_filter = QComboBox()
        self.result_filter.addItem("All Results")
        self.result_filter.addItem("1-0")
        self.result_filter.addItem("0-1")
        self.result_filter.addItem("1/2-1/2")
        self.result_filter.currentTextChanged.connect(self._filter_patterns)
        result_layout.addWidget(self.result_filter)
        selection_layout.addLayout(result_layout)
        
        # Search
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self._filter_patterns)
        search_layout.addWidget(self.search_edit)
        selection_layout.addLayout(search_layout)
        
        layout.addWidget(selection_group)
        
        # Pattern list
        list_group = QGroupBox("Tournament Patterns")
        list_layout = QVBoxLayout(list_group)
        
        self.pattern_list = QListWidget()
        self.pattern_list.itemClicked.connect(self._on_pattern_selected)
        list_layout.addWidget(self.pattern_list)
        
        # Pattern actions
        actions_layout = QHBoxLayout()
        
        self.btn_refresh = QPushButton("🔄 Refresh")
        self.btn_delete = QPushButton("🗑️ Delete")
        self.btn_export = QPushButton("📤 Export")
        
        self.btn_refresh.clicked.connect(self._refresh_pattern_list)
        self.btn_delete.clicked.connect(self._delete_current_pattern)
        self.btn_export.clicked.connect(self._export_patterns)
        
        actions_layout.addWidget(self.btn_refresh)
        actions_layout.addWidget(self.btn_delete)
        actions_layout.addWidget(self.btn_export)
        
        list_layout.addLayout(actions_layout)
        
        layout.addWidget(list_group)
        
        # Tournament stats
        stats_group = QGroupBox("Tournament Statistics")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_viewer = TournamentStatsViewer()
        stats_layout.addWidget(self.stats_viewer)
        
        layout.addWidget(stats_group)
        
        return panel
    
    def _create_right_panel(self) -> QWidget:
        """Create right panel with pattern details and board"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Pattern details
        details_group = QGroupBox("Pattern Details")
        details_layout = QVBoxLayout(details_group)
        
        # Pattern info table
        self.pattern_table = QTableWidget()
        self.pattern_table.setColumnCount(2)
        self.pattern_table.setHorizontalHeaderLabels(["Property", "Value"])
        self.pattern_table.horizontalHeader().setStretchLastSection(True)
        details_layout.addWidget(self.pattern_table)
        
        # Pattern description
        details_layout.addWidget(QLabel("Description:"))
        self.pattern_description = QTextEdit()
        self.pattern_description.setMaximumHeight(100)
        details_layout.addWidget(self.pattern_description)
        
        layout.addWidget(details_group)
        
        # Chess board
        board_group = QGroupBox("Chess Position")
        board_layout = QVBoxLayout(board_group)
        
        self.chess_board = ChessBoardWidget()
        board_layout.addWidget(self.chess_board, alignment=Qt.AlignCenter)
        
        layout.addWidget(board_group)
        
        # Move list
        moves_group = QGroupBox("Game Moves")
        moves_layout = QVBoxLayout(moves_group)
        
        self.moves_list = QListWidget()
        moves_layout.addWidget(self.moves_list)
        
        layout.addWidget(moves_group)
        
        return panel
    
    def _refresh_pattern_list(self):
        """Refresh the pattern list from storage"""
        self.pattern_list.clear()
        
        # Update bot filter
        current_bot_filter = self.bot_filter.currentText()
        self.bot_filter.clear()
        self.bot_filter.addItem("All Bots")
        
        bots = set()
        for pattern in self.tournament_storage.get_all_patterns():
            bots.add(pattern.bot1)
            bots.add(pattern.bot2)
        
        for bot in sorted(bots):
            self.bot_filter.addItem(bot)
        
        # Restore selection
        if current_bot_filter in [self.bot_filter.itemText(i) for i in range(self.bot_filter.count())]:
            self.bot_filter.setCurrentText(current_bot_filter)
        
        # Add patterns to list
        for pattern in self.tournament_storage.get_all_patterns():
            self._add_pattern_to_list(pattern)
        
        # Apply current filters
        self._filter_patterns()
    
    def _add_pattern_to_list(self, pattern: TournamentPattern):
        """Add pattern to the list widget"""
        # Create display text
        display_text = f"{pattern.bot1} vs {pattern.bot2} - {pattern.result} ({pattern.move_count} moves)"
        
        # Create list item
        item = QListWidgetItem(display_text)
        item.setData(Qt.UserRole, pattern.id)
        
        # Add to list
        self.pattern_list.addItem(item)
    
    def _filter_patterns(self):
        """Filter patterns based on current filters"""
        bot_filter = self.bot_filter.currentText()
        result_filter = self.result_filter.currentText()
        search_text = self.search_edit.text().lower()
        
        # Hide/show items based on filters
        for i in range(self.pattern_list.count()):
            item = self.pattern_list.item(i)
            pattern_id = item.data(Qt.UserRole)
            pattern = self.tournament_storage.get_pattern(pattern_id)
            
            if not pattern:
                continue
            
            # Check bot filter
            bot_match = (bot_filter == "All Bots" or 
                        bot_filter in [pattern.bot1, pattern.bot2])
            
            # Check result filter
            result_match = (result_filter == "All Results" or 
                          result_filter == pattern.result)
            
            # Check search filter
            search_match = (not search_text or 
                          search_text in pattern.bot1.lower() or
                          search_text in pattern.bot2.lower() or
                          search_text in pattern.description.lower() or
                          any(search_text in tag.lower() for tag in pattern.tags))
            
            # Show/hide item
            item.setHidden(not (bot_match and result_match and search_match))
    
    def _on_pattern_selected(self, item: QListWidgetItem):
        """Handle pattern selection"""
        pattern_id = item.data(Qt.UserRole)
        pattern = self.tournament_storage.get_pattern(pattern_id)
        
        if pattern:
            self.current_pattern = pattern
            self._display_pattern(pattern)
    
    def _display_pattern(self, pattern: TournamentPattern):
        """Display pattern details"""
        # Update pattern details table
        self._update_pattern_table(pattern)
        
        # Update description
        self.pattern_description.setPlainText(pattern.description)
        
        # Update board
        try:
            board = chess.Board(pattern.final_fen)
            self.chess_board.set_board(board)
        except Exception as e:
            logger.error(f"Failed to load board position: {e}")
        
        # Update moves list
        self.moves_list.clear()
        for i, move in enumerate(pattern.moves, 1):
            move_item = QListWidgetItem(f"{i}. {move}")
            self.moves_list.addItem(move_item)
    
    def _update_pattern_table(self, pattern: TournamentPattern):
        """Update pattern details table"""
        details = [
            ("ID", pattern.id),
            ("Bot 1", pattern.bot1),
            ("Bot 2", pattern.bot2),
            ("Result", pattern.result),
            ("Move Count", str(pattern.move_count)),
            ("Timestamp", pattern.timestamp),
            ("Pattern Type", pattern.pattern_type),
            ("Tags", ", ".join(pattern.tags)),
        ]
        
        self.pattern_table.setRowCount(len(details))
        for i, (prop, value) in enumerate(details):
            self.pattern_table.setItem(i, 0, QTableWidgetItem(prop))
            self.pattern_table.setItem(i, 1, QTableWidgetItem(str(value)))
    
    def _delete_current_pattern(self):
        """Delete current pattern"""
        if not self.current_pattern:
            return
        
        reply = QMessageBox.question(
            self, "Delete Pattern",
            f"Are you sure you want to delete pattern {self.current_pattern.id}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.tournament_storage.delete_pattern(self.current_pattern.id)
            self.current_pattern = None
            self._refresh_pattern_list()
            self._clear_pattern_details()
    
    def _export_patterns(self):
        """Export patterns to file"""
        if not PYSIDE_AVAILABLE:
            print("Export requires GUI")
            return
        
        from PySide6.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Tournament Patterns", "", "JSON Files (*.json)"
        )
        
        if filename:
            try:
                patterns = self.tournament_storage.get_all_patterns()
                data = [pattern.to_dict() for pattern in patterns]
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                QMessageBox.information(self, "Export Complete", f"Exported {len(patterns)} patterns to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export patterns: {e}")
    
    def _clear_pattern_details(self):
        """Clear pattern details display"""
        self.pattern_table.setRowCount(0)
        self.pattern_description.clear()
        self.moves_list.clear()
        self.chess_board.set_board(chess.Board())

class ChessBoardWidget(QWidget):
    """Chess board widget for displaying positions"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(400, 400)
        self.board = chess.Board()
        self.highlighted_squares = set()
        
    def set_board(self, board: chess.Board):
        """Set the board position"""
        self.board = board
        self.update()
    
    def set_highlighted_squares(self, squares: Set[int]):
        """Set squares to highlight"""
        self.highlighted_squares = squares
        self.update()
    
    def paintEvent(self, event):
        """Paint the chess board"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        cell_size = 50
        
        # Draw squares
        for row in range(8):
            for col in range(8):
                x = col * cell_size
                y = row * cell_size
                
                # Square color
                is_light = (row + col) % 2 == 0
                square = chess.square(col, 7 - row)
                
                if square in self.highlighted_squares:
                    color = QColor(255, 255, 0, 100)  # Yellow highlight
                elif is_light:
                    color = QColor(240, 217, 181)
                else:
                    color = QColor(181, 136, 99)
                
                painter.fillRect(x, y, cell_size, cell_size, color)
                
                # Draw piece
                piece = self.board.piece_at(square)
                if piece:
                    self._draw_piece(painter, x, y, cell_size, piece)
        
        # Draw border
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.drawRect(0, 0, 8 * cell_size, 8 * cell_size)
    
    def _draw_piece(self, painter: QPainter, x: int, y: int, size: int, piece: chess.Piece):
        """Draw a chess piece"""
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.setFont(QFont("Arial", size // 2))
        
        # Unicode chess symbols
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

def main():
    """Main function"""
    if not PYSIDE_AVAILABLE:
        print("PySide6 not available. Running in command-line mode.")
        print("To use the GUI version, install PySide6: pip install PySide6")
        
        # Simple command-line interface
        storage = TournamentPatternStorage()
        print(f"Loaded {len(storage.patterns)} tournament patterns")
        print("Tournament pattern viewer initialized.")
        print("Use the GUI version for interactive pattern analysis.")
        return
    
    app = QApplication(sys.argv)
    app.setApplicationName("Tournament Pattern Viewer")
    app.setApplicationVersion("1.0")
    
    # Set application style
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f5f5f5;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #ccc;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
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
        QListWidget {
            border: 1px solid #ccc;
            background-color: white;
        }
        QListWidget::item {
            padding: 5px;
            border-bottom: 1px solid #eee;
        }
        QListWidget::item:selected {
            background-color: #007bff;
            color: white;
        }
        QTableWidget {
            border: 1px solid #ccc;
            background-color: white;
            gridline-color: #eee;
        }
    """)
    
    try:
        viewer = TournamentPatternViewer()
        viewer.show()
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        if PYSIDE_AVAILABLE:
            QMessageBox.critical(None, "Startup Error", f"Failed to start application:\n{str(e)}")
        else:
            print(f"Startup Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()