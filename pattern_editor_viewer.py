#!/usr/bin/env python3
"""
<<<<<<< HEAD
Chess Pattern Editor/Viewer - Enhanced Interactive Chess Analysis Tool

This tool transforms the basic interactive viewer into a comprehensive pattern
analysis system that detects, categorizes, and stores chess patterns during
bot games for future analysis and learning.
"""

import sys
import time
import json
import logging
import hashlib
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

# Import enhanced pattern system with fallbacks
try:
    from enhanced_pattern_system import (
        EnhancedPatternDetector, EnhancedPatternStorage, EnhancedChessPattern,
        PatternRole, ExchangeType, ParticipatingPiece, ExchangeSequence
    )
    ENHANCED_PATTERNS_AVAILABLE = True
except ImportError:
    ENHANCED_PATTERNS_AVAILABLE = False
    # Create dummy classes
    class EnhancedPatternDetector:
        def __init__(self):
            pass
        def analyze_position_enhanced(self, *args):
            return None
    
    class EnhancedPatternStorage:
        def __init__(self, *args):
            self.patterns_index = {}
        def get_all_pattern_ids(self):
            return []
        def load_pattern(self, pattern_id):
            return None
        def save_pattern(self, pattern):
            pass
    
    class EnhancedChessPattern:
        pass

try:
    from chess_ai.threat_map import ThreatMap
except ImportError:
    ThreatMap = None

try:
    from utils.error_handler import ErrorHandler
except ImportError:
    class ErrorHandler:
        @staticmethod
        def handle_agent_error(exc, agent_name):
            print(f"Agent error for {agent_name}: {exc}")
=======
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
from ui.cell import Cell
from ui.drawer_manager import DrawerManager
from evaluation import evaluate
>>>>>>> main

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

<<<<<<< HEAD
# Simplified chess implementation when python-chess is not available
if not CHESS_AVAILABLE:
    class SimpleChess:
        WHITE = True
        BLACK = False
        
        PAWN = 1
        KNIGHT = 2
        BISHOP = 3
        ROOK = 4
        QUEEN = 5
        KING = 6
        
        class Board:
            def __init__(self, fen=None):
                self.turn = self.WHITE
                self.fullmove_number = 1
                self.castling_rights = 15  # KQkq
                self._setup_initial_position()
            
            def _setup_initial_position(self):
                self.pieces = {}
                # Set up initial position
                for i in range(8):
                    self.pieces[i + 8] = SimpleChess.Piece(SimpleChess.PAWN, SimpleChess.WHITE)  # White pawns
                    self.pieces[i + 48] = SimpleChess.Piece(SimpleChess.PAWN, SimpleChess.BLACK)  # Black pawns
                
                # White pieces
                self.pieces[0] = SimpleChess.Piece(SimpleChess.ROOK, SimpleChess.WHITE)
                self.pieces[7] = SimpleChess.Piece(SimpleChess.ROOK, SimpleChess.WHITE)
                self.pieces[1] = SimpleChess.Piece(SimpleChess.KNIGHT, SimpleChess.WHITE)
                self.pieces[6] = SimpleChess.Piece(SimpleChess.KNIGHT, SimpleChess.WHITE)
                self.pieces[2] = SimpleChess.Piece(SimpleChess.BISHOP, SimpleChess.WHITE)
                self.pieces[5] = SimpleChess.Piece(SimpleChess.BISHOP, SimpleChess.WHITE)
                self.pieces[3] = SimpleChess.Piece(SimpleChess.QUEEN, SimpleChess.WHITE)
                self.pieces[4] = SimpleChess.Piece(SimpleChess.KING, SimpleChess.WHITE)
                
                # Black pieces
                self.pieces[56] = SimpleChess.Piece(SimpleChess.ROOK, SimpleChess.BLACK)
                self.pieces[63] = SimpleChess.Piece(SimpleChess.ROOK, SimpleChess.BLACK)
                self.pieces[57] = SimpleChess.Piece(SimpleChess.KNIGHT, SimpleChess.BLACK)
                self.pieces[62] = SimpleChess.Piece(SimpleChess.KNIGHT, SimpleChess.BLACK)
                self.pieces[58] = SimpleChess.Piece(SimpleChess.BISHOP, SimpleChess.BLACK)
                self.pieces[61] = SimpleChess.Piece(SimpleChess.BISHOP, SimpleChess.BLACK)
                self.pieces[59] = SimpleChess.Piece(SimpleChess.QUEEN, SimpleChess.BLACK)
                self.pieces[60] = SimpleChess.Piece(SimpleChess.KING, SimpleChess.BLACK)
            
            def fen(self):
                return "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
            
            def piece_at(self, square):
                return self.pieces.get(square)
            
            def piece_map(self):
                return self.pieces
            
            def is_game_over(self):
                return False  # Simplified
            
            def legal_moves(self):
                # Return some dummy moves
                return [SimpleChess.Move(8, 16), SimpleChess.Move(9, 17), SimpleChess.Move(10, 18)]
            
            def is_legal(self, move):
                return True  # Simplified
            
            def push(self, move):
                # Move piece
                if move.from_square in self.pieces:
                    piece = self.pieces[move.from_square]
                    del self.pieces[move.from_square]
                    self.pieces[move.to_square] = piece
                self.turn = not self.turn
                if self.turn == self.WHITE:
                    self.fullmove_number += 1
            
            def san(self, move):
                return f"Move{move.from_square}-{move.to_square}"
            
            def copy(self):
                new_board = SimpleChess.Board()
                new_board.pieces = self.pieces.copy()
                new_board.turn = self.turn
                new_board.fullmove_number = self.fullmove_number
                return new_board
            
            def is_capture(self, move):
                return move.to_square in self.pieces
            
            def is_check(self):
                return False  # Simplified
            
            def result(self):
                return "*"  # Game in progress
        
        class Piece:
            def __init__(self, piece_type, color):
                self.piece_type = piece_type
                self.color = color
            
            def symbol(self):
                symbols = {
                    SimpleChess.PAWN: 'P' if self.color == SimpleChess.WHITE else 'p',
                    SimpleChess.KNIGHT: 'N' if self.color == SimpleChess.WHITE else 'n',
                    SimpleChess.BISHOP: 'B' if self.color == SimpleChess.WHITE else 'b',
                    SimpleChess.ROOK: 'R' if self.color == SimpleChess.WHITE else 'r',
                    SimpleChess.QUEEN: 'Q' if self.color == SimpleChess.WHITE else 'q',
                    SimpleChess.KING: 'K' if self.color == SimpleChess.WHITE else 'k'
                }
                return symbols.get(self.piece_type, '?')
        
        class Move:
            def __init__(self, from_square, to_square):
                self.from_square = from_square
                self.to_square = to_square
            
            def uci(self):
                return f"{self.square_name(self.from_square)}{self.square_name(self.to_square)}"
            
            @staticmethod
            def square_name(square):
                file = chr(ord('a') + (square % 8))
                rank = str((square // 8) + 1)
                return file + rank
            
            @staticmethod
            def from_uci(uci_str):
                # Parse UCI string like "e2e4"
                from_file = ord(uci_str[0]) - ord('a')
                from_rank = int(uci_str[1]) - 1
                to_file = ord(uci_str[2]) - ord('a')
                to_rank = int(uci_str[3]) - 1
                
                from_square = from_rank * 8 + from_file
                to_square = to_rank * 8 + to_file
                
                return SimpleChess.Move(from_square, to_square)
        
        @staticmethod
        def square(file, rank):
            return rank * 8 + file
        
        @staticmethod
        def square_name(square):
            file = chr(ord('a') + (square % 8))
            rank = str((square // 8) + 1)
            return file + rank
        
        SQUARES = list(range(64))
    
    # Replace chess module with our simple implementation
    chess = SimpleChess

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

@dataclass
class ChessPattern:
    """Represents a detected chess pattern"""
    id: str
    position_fen: str
    move_san: str
    move_uci: str
    categories: List[str]
    confidence: float
    piece_positions: Dict[str, List[str]]  # piece_type -> [square_names]
    heatmap_influences: Dict[str, float]   # square -> influence_value
    bot_evaluations: Dict[str, Dict[str, Any]]  # bot_name -> evaluation_data
    alternative_moves: List[Dict[str, Any]]  # other considered moves
    game_context: Dict[str, Any]
    timestamp: float
    description: str = ""
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChessPattern':
        """Create from dictionary"""
        return cls(**data)

class PatternDetector:
    """Detects interesting patterns during chess games"""
    
    def __init__(self):
        self.min_alternatives = 3  # Minimum alternative moves to consider pattern
        self.confidence_threshold = 0.6
        self.evaluation_threshold = 0.5  # Minimum evaluation difference
        
    def analyze_position(self, board: chess.Board, chosen_move: chess.Move, 
                        bot_name: str, bot_evaluation: Dict[str, Any],
                        all_bot_results: Dict[str, Dict[str, Any]]) -> Optional[ChessPattern]:
        """Analyze a position and detect if it contains an interesting pattern"""
        
        # Get all legal moves
        legal_moves = list(board.legal_moves)
        if len(legal_moves) < self.min_alternatives:
            return None
        
        # Calculate move complexity (number of viable alternatives)
        move_complexity = self._calculate_move_complexity(board, legal_moves)
        
        # Detect pattern categories
        categories = self._detect_pattern_categories(board, chosen_move, bot_evaluation)
        
        if not categories or move_complexity < 0.3:
            return None
        
        # Extract piece positions
        piece_positions = self._extract_piece_positions(board)
        
        # Calculate heatmap influences
        heatmap_influences = self._calculate_heatmap_influences(board, chosen_move)
        
        # Get alternative moves analysis
        alternative_moves = self._analyze_alternative_moves(board, legal_moves, chosen_move)
        
        # Calculate confidence
        confidence = self._calculate_pattern_confidence(
            move_complexity, len(categories), bot_evaluation, alternative_moves
        )
        
        if confidence < self.confidence_threshold:
            return None
        
        # Generate unique pattern ID
        pattern_id = self._generate_pattern_id(board, chosen_move)
        
        # Create game context
        game_context = {
            'move_number': board.fullmove_number,
            'turn': 'white' if board.turn == chess.WHITE else 'black',
            'castling_rights': str(board.castling_rights),
            'material_balance': self._calculate_material_balance(board),
            'game_phase': self._detect_game_phase(board)
        }
        
        return ChessPattern(
            id=pattern_id,
            position_fen=board.fen(),
            move_san=board.san(chosen_move),
            move_uci=chosen_move.uci(),
            categories=[cat.value for cat in categories],
            confidence=confidence,
            piece_positions=piece_positions,
            heatmap_influences=heatmap_influences,
            bot_evaluations={bot_name: bot_evaluation, **all_bot_results},
            alternative_moves=alternative_moves,
            game_context=game_context,
            timestamp=time.time()
        )
    
    def _calculate_move_complexity(self, board: chess.Board, legal_moves: List[chess.Move]) -> float:
        """Calculate how complex the move decision is"""
        # Simple heuristic based on number of moves and piece activity
        num_moves = len(legal_moves)
        
        # Count different piece types that can move
        moving_pieces = set()
        for move in legal_moves:
            piece = board.piece_at(move.from_square)
            if piece:
                moving_pieces.add(piece.piece_type)
        
        # Normalize complexity score
        complexity = min(1.0, (num_moves / 20.0) * (len(moving_pieces) / 6.0))
        return complexity
    
    def _detect_pattern_categories(self, board: chess.Board, move: chess.Move, 
                                 bot_evaluation: Dict[str, Any]) -> List[PatternCategory]:
        """Detect what categories this pattern belongs to"""
        categories = []
        
        # Game phase detection
        if board.fullmove_number <= 10:
            categories.append(PatternCategory.OPENING)
        elif board.fullmove_number <= 25:
            categories.append(PatternCategory.MIDDLEGAME)
        else:
            categories.append(PatternCategory.ENDGAME)
        
        # Tactical pattern detection
        if self._is_capture_move(board, move):
            categories.append(PatternCategory.TACTICAL)
        
        if self._is_check_move(board, move):
            categories.append(PatternCategory.ATTACKING)
        
        # Fork detection
        if self._is_fork_move(board, move):
            categories.append(PatternCategory.FORK)
        
        # Defensive patterns
        if self._is_defensive_move(board, move):
            categories.append(PatternCategory.DEFENSIVE)
        
        # Positional patterns
        if self._is_positional_move(board, move):
            categories.append(PatternCategory.POSITIONAL)
        
        return categories
    
    def _is_capture_move(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move is a capture"""
        return board.is_capture(move)
    
    def _is_check_move(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move gives check"""
        board_copy = board.copy()
        board_copy.push(move)
        return board_copy.is_check()
    
    def _is_fork_move(self, board: chess.Board, move: chess.Move) -> bool:
        """Detect if move creates a fork"""
        # Simple fork detection - piece attacks multiple valuable pieces
        board_copy = board.copy()
        board_copy.push(move)
        
        attacking_piece = board_copy.piece_at(move.to_square)
        if not attacking_piece:
            return False
        
        # Count valuable pieces attacked
        attacked_squares = board_copy.attacks(move.to_square)
        valuable_attacks = 0
        
        for square in attacked_squares:
            piece = board_copy.piece_at(square)
            if piece and piece.color != attacking_piece.color:
                if piece.piece_type in [chess.QUEEN, chess.ROOK, chess.KING]:
                    valuable_attacks += 1
        
        return valuable_attacks >= 2
    
    def _is_defensive_move(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move is defensive"""
        # Check if move blocks a check or defends a piece
        if board.is_check():
            return True
        
        # Check if piece was under attack and moved to safety
        piece = board.piece_at(move.from_square)
        if piece and board.is_attacked_by(not piece.color, move.from_square):
            return True
        
        return False
    
    def _is_positional_move(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move is positional (improves position without immediate tactics)"""
        # Simple heuristic - non-capture, non-check moves
        return not self._is_capture_move(board, move) and not self._is_check_move(board, move)
    
    def _extract_piece_positions(self, board: chess.Board) -> Dict[str, List[str]]:
        """Extract positions of all pieces"""
        positions = defaultdict(list)
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                piece_key = f"{piece.symbol()}"
                positions[piece_key].append(chess.square_name(square))
        
        return dict(positions)
    
    def _calculate_heatmap_influences(self, board: chess.Board, move: chess.Move) -> Dict[str, float]:
        """Calculate heatmap influences for the position"""
        influences = {}
        
        # Simple influence calculation based on piece attacks and defenses
        for square in chess.SQUARES:
            square_name = chess.square_name(square)
            influence = 0.0
            
            # Count attackers and defenders
            white_attackers = len(board.attackers(chess.WHITE, square))
            black_attackers = len(board.attackers(chess.BLACK, square))
            
            # Calculate net influence
            influence = (white_attackers - black_attackers) / 8.0  # Normalize
            influences[square_name] = influence
        
        return influences
    
    def _analyze_alternative_moves(self, board: chess.Board, legal_moves: List[chess.Move], 
                                 chosen_move: chess.Move) -> List[Dict[str, Any]]:
        """Analyze alternative moves that could have been played"""
        alternatives = []
        
        for move in legal_moves[:5]:  # Limit to top 5 alternatives
            if move == chosen_move:
                continue
            
            # Simple evaluation of alternative
            board_copy = board.copy()
            board_copy.push(move)
            
            alternative = {
                'move_san': board.san(move),
                'move_uci': move.uci(),
                'is_capture': board.is_capture(move),
                'is_check': board_copy.is_check(),
                'evaluation_score': 0.0  # Placeholder for actual evaluation
            }
            alternatives.append(alternative)
        
        return alternatives
    
    def _calculate_pattern_confidence(self, move_complexity: float, num_categories: int,
                                    bot_evaluation: Dict[str, Any], 
                                    alternatives: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for the pattern"""
        # Combine multiple factors
        complexity_score = move_complexity
        category_score = min(1.0, num_categories / 3.0)
        alternative_score = min(1.0, len(alternatives) / 5.0)
        
        # Weight the factors
        confidence = (complexity_score * 0.4 + category_score * 0.3 + alternative_score * 0.3)
        return confidence
    
    def _generate_pattern_id(self, board: chess.Board, move: chess.Move) -> str:
        """Generate unique ID for the pattern"""
        # Use FEN + move to create unique hash
        pattern_string = f"{board.fen()}_{move.uci()}"
        return hashlib.md5(pattern_string.encode()).hexdigest()[:12]
    
    def _calculate_material_balance(self, board: chess.Board) -> int:
        """Calculate material balance (positive = white advantage)"""
        piece_values = {
            chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
            chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0
        }
        
        balance = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = piece_values[piece.piece_type]
                balance += value if piece.color == chess.WHITE else -value
        
        return balance
    
    def _detect_game_phase(self, board: chess.Board) -> str:
        """Detect current game phase"""
        # Count pieces to determine phase
        piece_count = len([p for p in board.piece_map().values() if p.piece_type != chess.KING])
        
        if piece_count >= 20:
            return "opening"
        elif piece_count >= 12:
            return "middlegame"
        else:
            return "endgame"

class PatternStorage:
    """Manages storage and retrieval of chess patterns"""
    
    def __init__(self, storage_path: str = "patterns"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.patterns: Dict[str, ChessPattern] = {}
        self.load_patterns()
    
    def save_pattern(self, pattern: ChessPattern):
        """Save a pattern to storage"""
        self.patterns[pattern.id] = pattern
        self._save_to_file()
    
    def get_pattern(self, pattern_id: str) -> Optional[ChessPattern]:
        """Get a pattern by ID"""
        return self.patterns.get(pattern_id)
    
    def get_patterns_by_category(self, category: str) -> List[ChessPattern]:
        """Get all patterns in a category"""
        return [p for p in self.patterns.values() if category in p.categories]
    
    def search_patterns(self, query: str) -> List[ChessPattern]:
        """Search patterns by description or tags"""
        query_lower = query.lower()
        results = []
        
        for pattern in self.patterns.values():
            if (query_lower in pattern.description.lower() or 
                any(query_lower in tag.lower() for tag in pattern.tags)):
                results.append(pattern)
        
        return results
    
    def get_all_patterns(self) -> List[ChessPattern]:
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
                        pattern = ChessPattern.from_dict(pattern_data)
                        self.patterns[pattern.id] = pattern
                logger.info(f"Loaded {len(self.patterns)} patterns")
            except Exception as e:
                logger.error(f"Failed to load patterns: {e}")
    
    def _save_to_file(self):
        """Save patterns to file"""
        patterns_file = self.storage_path / "patterns.json"
        try:
            with open(patterns_file, 'w') as f:
                pattern_list = [pattern.to_dict() for pattern in self.patterns.values()]
                json.dump(pattern_list, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save patterns: {e}")

class GameWorker(QThread):
    """Worker thread for playing games and detecting patterns"""
    
    gameCompleted = pyqtSignal(object)  # GameResult
    patternDetected = pyqtSignal(object)  # ChessPattern
    progressUpdated = pyqtSignal(int)   # progress percentage
    statusUpdated = pyqtSignal(str)     # status message
=======
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
>>>>>>> main
    
    def __init__(self, white_agent, black_agent, num_games=10):
        super().__init__()
        self.white_agent = white_agent
        self.black_agent = black_agent
        self.num_games = num_games
        self._stop_requested = False
<<<<<<< HEAD
        
        if ENHANCED_PATTERNS_AVAILABLE:
            self.pattern_detector = EnhancedPatternDetector()
        else:
            self.pattern_detector = PatternDetector()
=======
        self.pattern_detector = PatternDetector()
>>>>>>> main
        
    def run(self):
        """Run games and detect patterns"""
        for game_id in range(self.num_games):
            if self._stop_requested:
                break
                
            self.statusUpdated.emit(f"Playing game {game_id + 1}/{self.num_games}")
            
<<<<<<< HEAD
            # Play one game
            self._play_game_with_pattern_detection(game_id)
=======
            # Play one game and detect patterns
            self._play_and_detect(game_id)
            self.gameCompleted.emit(game_id + 1)
>>>>>>> main
            
            # Update progress
            progress = int((game_id + 1) / self.num_games * 100)
            self.progressUpdated.emit(progress)
            
<<<<<<< HEAD
        self.statusUpdated.emit("All games completed!")
    
    def _play_game_with_pattern_detection(self, game_id: int):
        """Play a game while detecting patterns"""
        board = chess.Board()
        move_count = 0
        
        while not board.is_game_over() and move_count < 100:  # Limit moves
            if self._stop_requested:
                break
            
            # Determine current player
            current_agent = self.white_agent if board.turn == chess.WHITE else self.black_agent
            other_agent = self.black_agent if board.turn == chess.WHITE else self.white_agent
            
            try:
                # Get move from current agent
                move = current_agent.choose_move(board)
                if move is None or not board.is_legal(move):
                    break
                
                # Get evaluations from multiple bots for pattern analysis
                bot_evaluations = self._get_multi_bot_evaluations(board, move)
                
                # Detect pattern
                if ENHANCED_PATTERNS_AVAILABLE:
                    pattern = self.pattern_detector.analyze_position_enhanced(
                        board, move, 
                        current_agent.__class__.__name__,
                        bot_evaluations.get(current_agent.__class__.__name__, {}),
                        bot_evaluations
                    )
                else:
                    pattern = self.pattern_detector.analyze_position(
                        board, move, 
                        current_agent.__class__.__name__,
                        bot_evaluations.get(current_agent.__class__.__name__, {}),
                        bot_evaluations
                    )
                
                if pattern:
                    self.patternDetected.emit(pattern)
                
                # Apply move
                board.push(move)
                move_count += 1
                
=======
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
                    
>>>>>>> main
            except Exception as e:
                logger.error(f"Error in game {game_id}, move {move_count}: {e}")
                break
    
<<<<<<< HEAD
    def _get_multi_bot_evaluations(self, board: chess.Board, move: chess.Move) -> Dict[str, Dict[str, Any]]:
        """Get evaluations from multiple bots for comparison"""
        evaluations = {}
        
        # For now, return simple evaluation structure
        # In a full implementation, this would query multiple bots
        evaluations["primary"] = {
            "confidence": 0.8,
            "evaluation_score": 0.0,
            "reason": "Selected move",
            "alternatives_considered": len(list(board.legal_moves))
        }
        
        return evaluations
    
=======
>>>>>>> main
    def stop(self):
        """Stop the worker"""
        self._stop_requested = True

<<<<<<< HEAD
class ManualPatternDialog(QDialog):
    """Dialog for creating manual patterns"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Manual Pattern")
        self.setModal(True)
        self.resize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Pattern name
        layout.addWidget(QLabel("Pattern Name:"))
        self.name_edit = QLineEdit()
        layout.addWidget(self.name_edit)
        
        # Pattern description
        layout.addWidget(QLabel("Description:"))
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        layout.addWidget(self.description_edit)
        
        # FEN position
        layout.addWidget(QLabel("FEN Position:"))
        self.fen_edit = QLineEdit()
        self.fen_edit.setPlaceholderText("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        layout.addWidget(self.fen_edit)
        
        # Key move
        layout.addWidget(QLabel("Key Move (UCI):"))
        self.move_edit = QLineEdit()
        self.move_edit.setPlaceholderText("e2e4")
        layout.addWidget(self.move_edit)
        
        # Categories
        layout.addWidget(QLabel("Categories:"))
        categories_widget = QWidget()
        categories_layout = QVBoxLayout(categories_widget)
        
        self.category_checkboxes = {}
        categories = ["tactical", "opening", "middlegame", "endgame", "fork", "pin", 
                     "sacrifice", "exchange_pattern", "positional", "defensive"]
        
        for category in categories:
            checkbox = QCheckBox(category.title())
            self.category_checkboxes[category] = checkbox
            categories_layout.addWidget(checkbox)
        
        layout.addWidget(categories_widget)
        
        # Tags
        layout.addWidget(QLabel("Tags (comma-separated):"))
        self.tags_edit = QLineEdit()
        layout.addWidget(self.tags_edit)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_pattern_data(self) -> Dict[str, Any]:
        """Get pattern data from dialog"""
        categories = [category for category, checkbox in self.category_checkboxes.items()
                     if checkbox.isChecked()]
        
        tags_text = self.tags_edit.text().strip()
        tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
        
        return {
            "name": self.name_edit.text(),
            "description": self.description_edit.toPlainText(),
            "fen": self.fen_edit.text(),
            "move": self.move_edit.text(),
            "categories": categories,
            "tags": tags
        }

class PatternEditDialog(QDialog):
    """Dialog for editing pattern details"""
    
    def __init__(self, pattern: ChessPattern, parent=None):
        super().__init__(parent)
        self.pattern = pattern
        self.setWindowTitle("Edit Pattern")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Description
        layout.addWidget(QLabel("Description:"))
        self.description_edit = QTextEdit()
        self.description_edit.setPlainText(pattern.description)
        layout.addWidget(self.description_edit)
        
        # Tags
        layout.addWidget(QLabel("Tags (comma-separated):"))
        self.tags_edit = QLineEdit()
        self.tags_edit.setText(", ".join(pattern.tags))
        layout.addWidget(self.tags_edit)
        
        # Categories
        layout.addWidget(QLabel("Categories:"))
        self.categories_widget = QWidget()
        categories_layout = QVBoxLayout(self.categories_widget)
        
        self.category_checkboxes = {}
        for category in PatternCategory:
            checkbox = QCheckBox(category.value.title())
            checkbox.setChecked(category.value in pattern.categories)
            self.category_checkboxes[category.value] = checkbox
            categories_layout.addWidget(checkbox)
        
        layout.addWidget(self.categories_widget)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_updated_pattern(self) -> ChessPattern:
        """Get the updated pattern"""
        # Update description
        self.pattern.description = self.description_edit.toPlainText()
        
        # Update tags
        tags_text = self.tags_edit.text().strip()
        self.pattern.tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
        
        # Update categories
        self.pattern.categories = [
            category for category, checkbox in self.category_checkboxes.items()
            if checkbox.isChecked()
        ]
        
        return self.pattern

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

class PatternEditorViewer(QMainWindow):
    """Main pattern editor/viewer application"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chess Pattern Editor/Viewer")
        self.resize(1400, 900)
        
        # Initialize components
        if ENHANCED_PATTERNS_AVAILABLE:
            self.pattern_storage = EnhancedPatternStorage()
            self.pattern_detector = EnhancedPatternDetector()
        else:
            self.pattern_storage = PatternStorage()
            self.pattern_detector = PatternDetector()
        
        self.current_pattern = None
        self.game_worker = None
        self.pattern_selection_filters = {
            'min_confidence': 0.5,
            'categories': [],
            'complexity': 'all',
            'include_exchanges': True
        }
=======

class PatternEditorViewer(QMainWindow):
    """Main pattern editor/viewer window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chess Pattern Editor & Viewer")
        self.resize(1400, 800)
        
        # Pattern management
        self.pattern_catalog = PatternCatalog()
        self.pattern_catalog.load_patterns()
        self.current_patterns: List[ChessPattern] = list(self.pattern_catalog.patterns)
        self.current_pattern_index = -1
        
        # Chess board state
        self.board = chess.Board()
        self.piece_objects = {}
>>>>>>> main
        
        # Initialize agents
        self._init_agents()
        
<<<<<<< HEAD
        # Setup UI
        self._setup_ui()
        
        # Load existing patterns
        self._refresh_pattern_list()
    
    def _init_agents(self):
        """Initialize chess agents"""
        try:
            self.white_agent = make_agent("StockfishBot", chess.WHITE)
            self.black_agent = make_agent("DynamicBot", chess.BLACK)
        except Exception as e:
            logger.error(f"Failed to initialize agents: {e}")
            # Fallback to simpler agents
            try:
                self.white_agent = make_agent("RandomBot", chess.WHITE)
                self.black_agent = make_agent("RandomBot", chess.BLACK)
            except Exception as e2:
                logger.error(f"Failed to initialize fallback agents: {e2}")
                self._show_error("Agent Initialization Failed", 
                               "Could not initialize chess agents. Please check your configuration.")
    
    def _setup_ui(self):
        """Setup the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel - Game control and board
        left_panel = self._create_left_panel()
        main_layout.addWidget(left_panel, 1)
        
        # Right panel - Pattern management
        right_panel = self._create_right_panel()
        main_layout.addWidget(right_panel, 2)
    
    def _create_left_panel(self) -> QWidget:
        """Create left panel with game controls and board"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Game control group
        control_group = QGroupBox("Game Control")
        control_layout = QVBoxLayout(control_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.btn_start = QPushButton("▶ Start Auto Play")
        self.btn_pause = QPushButton("⏸ Pause")
        self.btn_stop = QPushButton("⏹ Stop")
        self.btn_reset = QPushButton("🔄 Reset")
        
        self.btn_start.clicked.connect(self._start_auto_play)
        self.btn_pause.clicked.connect(self._pause_auto_play)
        self.btn_stop.clicked.connect(self._stop_auto_play)
        self.btn_reset.clicked.connect(self._reset_games)
        
        # Initial button states
        self.btn_pause.setEnabled(False)
        self.btn_stop.setEnabled(False)
        
        button_layout.addWidget(self.btn_start)
        button_layout.addWidget(self.btn_pause)
        button_layout.addWidget(self.btn_stop)
        button_layout.addWidget(self.btn_reset)
        
        control_layout.addLayout(button_layout)
        
        # Settings
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(QLabel("Games:"))
        self.games_spinbox = QSpinBox()
        self.games_spinbox.setRange(1, 100)
        self.games_spinbox.setValue(10)
        settings_layout.addWidget(self.games_spinbox)
        settings_layout.addStretch()
        
        control_layout.addLayout(settings_layout)
        
        # Progress and status
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        control_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready to start pattern detection")
        control_layout.addWidget(self.status_label)
        
        layout.addWidget(control_group)
        
        # Chess board
        board_group = QGroupBox("Current Position")
        board_layout = QVBoxLayout(board_group)
        
        self.chess_board = ChessBoardWidget()
        board_layout.addWidget(self.chess_board, alignment=Qt.AlignCenter)
        
        layout.addWidget(board_group)
        
        return panel
    
    def _create_right_panel(self) -> QWidget:
        """Create right panel with pattern management"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Pattern selection controls
        selection_group = QGroupBox("Pattern Selection Controls")
        selection_layout = QVBoxLayout(selection_group)
        
        # Pattern filters
        filters_layout = QHBoxLayout()
        
        # Confidence filter
        filters_layout.addWidget(QLabel("Min Confidence:"))
        self.confidence_slider = QSlider(Qt.Horizontal)
        self.confidence_slider.setRange(0, 100)
        self.confidence_slider.setValue(50)
        self.confidence_slider.valueChanged.connect(self._on_confidence_changed)
        filters_layout.addWidget(self.confidence_slider)
        
        self.confidence_label = QLabel("0.5")
        filters_layout.addWidget(self.confidence_label)
        
        selection_layout.addLayout(filters_layout)
        
        # Category filters
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("Categories:"))
        
        self.tactical_check = QCheckBox("Tactical")
        self.exchange_check = QCheckBox("Exchanges")
        self.positional_check = QCheckBox("Positional")
        
        self.tactical_check.stateChanged.connect(self._on_filter_changed)
        self.exchange_check.stateChanged.connect(self._on_filter_changed)
        self.positional_check.stateChanged.connect(self._on_filter_changed)
        
        category_layout.addWidget(self.tactical_check)
        category_layout.addWidget(self.exchange_check)
        category_layout.addWidget(self.positional_check)
        
        selection_layout.addLayout(category_layout)
        
        # Complexity filter
        complexity_layout = QHBoxLayout()
        complexity_layout.addWidget(QLabel("Complexity:"))
        self.complexity_combo = QComboBox()
        self.complexity_combo.addItems(["All", "Simple", "Intermediate", "Complex"])
        self.complexity_combo.currentTextChanged.connect(self._on_filter_changed)
        complexity_layout.addWidget(self.complexity_combo)
        complexity_layout.addStretch()
        
        selection_layout.addLayout(complexity_layout)
        
        # Manual pattern creation
        manual_layout = QHBoxLayout()
        self.btn_create_pattern = QPushButton("➕ Create Manual Pattern")
        self.btn_import_pattern = QPushButton("📁 Import Pattern")
        
        self.btn_create_pattern.clicked.connect(self._create_manual_pattern)
        self.btn_import_pattern.clicked.connect(self._import_pattern)
        
        manual_layout.addWidget(self.btn_create_pattern)
        manual_layout.addWidget(self.btn_import_pattern)
        
        selection_layout.addLayout(manual_layout)
        
        layout.addWidget(selection_group)
        
        # Pattern list group
        list_group = QGroupBox("Detected Patterns")
        list_layout = QVBoxLayout(list_group)
        
        # Search and filter
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self._filter_patterns)
        search_layout.addWidget(self.search_edit)
        
        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories")
        for category in PatternCategory:
            self.category_filter.addItem(category.value.title())
        self.category_filter.currentTextChanged.connect(self._filter_patterns)
        search_layout.addWidget(self.category_filter)
        
        list_layout.addLayout(search_layout)
        
        # Pattern list
        self.pattern_list = QListWidget()
        self.pattern_list.itemClicked.connect(self._on_pattern_selected)
        list_layout.addWidget(self.pattern_list)
        
        # Pattern actions
        actions_layout = QHBoxLayout()
        
        self.btn_save_pattern = QPushButton("💾 Save Pattern")
        self.btn_edit_pattern = QPushButton("✏️ Edit Pattern")
        self.btn_delete_pattern = QPushButton("🗑️ Delete Pattern")
        
        self.btn_save_pattern.clicked.connect(self._save_current_pattern)
        self.btn_edit_pattern.clicked.connect(self._edit_current_pattern)
        self.btn_delete_pattern.clicked.connect(self._delete_current_pattern)
        
        # Initially disabled
        self.btn_edit_pattern.setEnabled(False)
        self.btn_delete_pattern.setEnabled(False)
        
        actions_layout.addWidget(self.btn_save_pattern)
        actions_layout.addWidget(self.btn_edit_pattern)
        actions_layout.addWidget(self.btn_delete_pattern)
        
        list_layout.addLayout(actions_layout)
        
        layout.addWidget(list_group)
        
        # Pattern details group
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
        
        return panel
    
    def _start_auto_play(self):
        """Start automatic game playing with pattern detection"""
        if self.game_worker and self.game_worker.isRunning():
            return
        
        # Update UI
        self.btn_start.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.btn_stop.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Start worker
        self.game_worker = GameWorker(
            self.white_agent, 
            self.black_agent, 
            self.games_spinbox.value()
        )
        
        self.game_worker.patternDetected.connect(self._on_pattern_detected)
        self.game_worker.progressUpdated.connect(self._on_progress_updated)
        self.game_worker.statusUpdated.connect(self._on_status_updated)
        self.game_worker.finished.connect(self._on_games_finished)
        
        self.game_worker.start()
        
        self.status_label.setText("Starting pattern detection...")
    
    def _pause_auto_play(self):
        """Pause automatic play"""
        if self.game_worker:
            self.game_worker.stop()
=======
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
>>>>>>> main
        
        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.status_label.setText("Paused")
<<<<<<< HEAD
    
    def _stop_auto_play(self):
        """Stop automatic play"""
        if self.game_worker:
            self.game_worker.stop()
            self.game_worker.wait()
        
        self._reset_ui_after_games()
        self.status_label.setText("Stopped")
    
    def _reset_games(self):
        """Reset everything"""
        self._stop_auto_play()
        self.current_pattern = None
        self.chess_board.set_board(chess.Board())
        self._clear_pattern_details()
        self.status_label.setText("Reset completed")
    
    def _reset_ui_after_games(self):
        """Reset UI state after games complete"""
=======
        
    def _stop_detection(self):
        """Stop pattern detection"""
        if hasattr(self, 'pattern_worker'):
            self.pattern_worker.stop()
            self.pattern_worker.wait()
        
>>>>>>> main
        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_stop.setEnabled(False)
        self.progress_bar.setVisible(False)
<<<<<<< HEAD
    
    def _on_pattern_detected(self, pattern: ChessPattern):
        """Handle detected pattern"""
        # Add to temporary storage
        self.pattern_storage.save_pattern(pattern)
        
        # Update UI
        self._add_pattern_to_list(pattern)
        
        # Update board if this is the first/current pattern
        if not self.current_pattern:
            self.current_pattern = pattern
            self._display_pattern(pattern)
    
    def _on_progress_updated(self, progress: int):
        """Handle progress update"""
        self.progress_bar.setValue(progress)
    
    def _on_status_updated(self, status: str):
        """Handle status update"""
        self.status_label.setText(status)
    
    def _on_games_finished(self):
        """Handle games completion"""
        self._reset_ui_after_games()
        self.status_label.setText(f"Completed! Detected {len(self.pattern_storage.patterns)} patterns")
    
    def _on_pattern_selected(self, item: QListWidgetItem):
        """Handle pattern selection"""
        pattern_id = item.data(Qt.UserRole)
        pattern = self.pattern_storage.get_pattern(pattern_id)
        
        if pattern:
            self.current_pattern = pattern
            self._display_pattern(pattern)
            
            # Enable edit/delete buttons
            self.btn_edit_pattern.setEnabled(True)
            self.btn_delete_pattern.setEnabled(True)
    
    def _display_pattern(self, pattern: ChessPattern):
        """Display pattern details"""
        # Update board
        board = chess.Board(pattern.position_fen)
        self.chess_board.set_board(board)
        
        # Highlight relevant squares (example: squares involved in the move)
        move = chess.Move.from_uci(pattern.move_uci)
        highlighted = {move.from_square, move.to_square}
        self.chess_board.set_highlighted_squares(highlighted)
        
        # Update pattern details table
        self._update_pattern_table(pattern)
        
        # Update description
        self.pattern_description.setPlainText(pattern.description)
    
    def _update_pattern_table(self, pattern: ChessPattern):
        """Update pattern details table"""
        details = [
            ("ID", pattern.id),
            ("Move", f"{pattern.move_san} ({pattern.move_uci})"),
            ("Categories", ", ".join(pattern.categories)),
            ("Confidence", f"{pattern.confidence:.2f}"),
            ("Game Context", f"Move {pattern.game_context.get('move_number', '?')} ({pattern.game_context.get('turn', '?')})"),
            ("Material Balance", str(pattern.game_context.get('material_balance', '?'))),
            ("Game Phase", pattern.game_context.get('game_phase', '?')),
            ("Alternatives", str(len(pattern.alternative_moves))),
            ("Tags", ", ".join(pattern.tags)),
            ("Timestamp", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(pattern.timestamp)))
        ]
        
        self.pattern_table.setRowCount(len(details))
        for i, (prop, value) in enumerate(details):
            self.pattern_table.setItem(i, 0, QTableWidgetItem(prop))
            self.pattern_table.setItem(i, 1, QTableWidgetItem(str(value)))
    
    def _clear_pattern_details(self):
        """Clear pattern details display"""
        self.pattern_table.setRowCount(0)
        self.pattern_description.clear()
        self.btn_edit_pattern.setEnabled(False)
        self.btn_delete_pattern.setEnabled(False)
    
    def _add_pattern_to_list(self, pattern: ChessPattern):
        """Add pattern to the list widget"""
        # Create display text
        categories_str = ", ".join(pattern.categories[:2])  # Show first 2 categories
        if len(pattern.categories) > 2:
            categories_str += "..."
        
        display_text = f"{pattern.move_san} - {categories_str} (conf: {pattern.confidence:.2f})"
        
        # Create list item
        item = QListWidgetItem(display_text)
        item.setData(Qt.UserRole, pattern.id)
        
        # Add to list
        self.pattern_list.addItem(item)
    
    def _refresh_pattern_list(self):
        """Refresh the pattern list from storage"""
        self.pattern_list.clear()
        
        for pattern in self.pattern_storage.get_all_patterns():
            self._add_pattern_to_list(pattern)
    
    def _filter_patterns(self):
        """Filter patterns based on search and category"""
        search_text = self.search_edit.text().lower()
        category_filter = self.category_filter.currentText()
        
        # Hide/show items based on filters
        for i in range(self.pattern_list.count()):
            item = self.pattern_list.item(i)
            pattern_id = item.data(Qt.UserRole)
            pattern = self.pattern_storage.get_pattern(pattern_id)
            
            if not pattern:
                continue
            
            # Check search filter
            search_match = (not search_text or 
                          search_text in pattern.move_san.lower() or
                          search_text in pattern.description.lower() or
                          any(search_text in tag.lower() for tag in pattern.tags))
            
            # Check category filter
            category_match = (category_filter == "All Categories" or
                            category_filter.lower() in pattern.categories)
            
            # Show/hide item
            item.setHidden(not (search_match and category_match))
    
    def _save_current_pattern(self):
        """Save current pattern (if any)"""
        if self.current_pattern:
            # Update description from UI
            self.current_pattern.description = self.pattern_description.toPlainText()
            self.pattern_storage.save_pattern(self.current_pattern)
            self.status_label.setText("Pattern saved")
        else:
            self.status_label.setText("No pattern to save")
    
    def _edit_current_pattern(self):
        """Edit current pattern"""
        if not self.current_pattern:
            return
        
        dialog = PatternEditDialog(self.current_pattern, self)
        if dialog.exec() == QDialog.Accepted:
            updated_pattern = dialog.get_updated_pattern()
            self.pattern_storage.save_pattern(updated_pattern)
            self.current_pattern = updated_pattern
            
            # Refresh display
            self._display_pattern(updated_pattern)
            self._refresh_pattern_list()
            
            self.status_label.setText("Pattern updated")
    
    def _delete_current_pattern(self):
        """Delete current pattern"""
        if not self.current_pattern:
            return
        
        reply = QMessageBox.question(
            self, "Delete Pattern",
            f"Are you sure you want to delete pattern {self.current_pattern.id}?",
=======
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
>>>>>>> main
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
<<<<<<< HEAD
            self.pattern_storage.delete_pattern(self.current_pattern.id)
            self.current_pattern = None
            
            # Refresh UI
            self._refresh_pattern_list()
            self._clear_pattern_details()
            self.chess_board.set_board(chess.Board())
            
            self.status_label.setText("Pattern deleted")
    
    def _show_error(self, title: str, message: str):
        """Show error message"""
        if PYSIDE_AVAILABLE:
            QMessageBox.critical(self, title, message)
        else:
            print(f"Error - {title}: {message}")
    
    def _on_confidence_changed(self, value):
        """Handle confidence slider change"""
        confidence = value / 100.0
        self.confidence_label.setText(f"{confidence:.2f}")
        self.pattern_selection_filters['min_confidence'] = confidence
        self._apply_pattern_filters()
    
    def _on_filter_changed(self):
        """Handle filter changes"""
        categories = []
        if self.tactical_check.isChecked():
            categories.append("tactical")
        if self.exchange_check.isChecked():
            categories.append("exchange_pattern")
        if self.positional_check.isChecked():
            categories.append("positional")
        
        self.pattern_selection_filters['categories'] = categories
        self.pattern_selection_filters['complexity'] = self.complexity_combo.currentText().lower()
        
        self._apply_pattern_filters()
    
    def _apply_pattern_filters(self):
        """Apply current filters to pattern list"""
        # Hide/show patterns based on current filters
        for i in range(self.pattern_list.count()):
            item = self.pattern_list.item(i)
            if hasattr(item, 'data') and item.data(Qt.UserRole):
                pattern_id = item.data(Qt.UserRole)
                should_show = self._pattern_matches_filters(pattern_id)
                item.setHidden(not should_show)
    
    def _pattern_matches_filters(self, pattern_id: str) -> bool:
        """Check if pattern matches current filters"""
        if ENHANCED_PATTERNS_AVAILABLE:
            pattern = self.pattern_storage.load_pattern(pattern_id)
            if not pattern:
                return False
            
            # Check confidence
            if pattern.detection_confidence < self.pattern_selection_filters['min_confidence']:
                return False
            
            # Check categories
            filter_categories = self.pattern_selection_filters['categories']
            if filter_categories:
                pattern_categories = [pattern.primary_category] + pattern.secondary_categories
                if not any(cat in pattern_categories for cat in filter_categories):
                    return False
            
            # Check complexity
            complexity_filter = self.pattern_selection_filters['complexity']
            if complexity_filter != 'all' and pattern.complexity != complexity_filter:
                return False
            
            return True
        else:
            # Fallback for basic patterns
            return True
    
    def _create_manual_pattern(self):
        """Create a manual pattern"""
        if not PYSIDE_AVAILABLE:
            print("Manual pattern creation requires GUI")
            return
        
        dialog = ManualPatternDialog(self)
        if dialog.exec() == QDialog.Accepted:
            pattern_data = dialog.get_pattern_data()
            
            if ENHANCED_PATTERNS_AVAILABLE:
                # Create enhanced pattern
                pattern = self._create_enhanced_pattern_from_data(pattern_data)
                self.pattern_storage.save_pattern(pattern)
            else:
                # Create basic pattern
                pattern = self._create_basic_pattern_from_data(pattern_data)
                self.pattern_storage.save_pattern(pattern)
            
            self._refresh_pattern_list()
            self.status_label.setText("Manual pattern created")
    
    def _import_pattern(self):
        """Import pattern from file"""
        if not PYSIDE_AVAILABLE:
            print("Pattern import requires GUI")
            return
        
        from PySide6.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getOpenFileName(
            self, "Import Pattern", "", "JSON Files (*.json)"
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if ENHANCED_PATTERNS_AVAILABLE:
                    pattern = EnhancedChessPattern.from_dict(data)
                    self.pattern_storage.save_pattern(pattern)
                else:
                    pattern = ChessPattern.from_dict(data)
                    self.pattern_storage.save_pattern(pattern)
                
                self._refresh_pattern_list()
                self.status_label.setText(f"Pattern imported from {filename}")
                
            except Exception as e:
                self._show_error("Import Error", f"Failed to import pattern: {e}")
    
    def _create_enhanced_pattern_from_data(self, data: Dict[str, Any]):
        """Create enhanced pattern from manual data"""
        # This would be implemented based on the manual pattern dialog
        # For now, return a placeholder
        pass
    
    def _create_basic_pattern_from_data(self, data: Dict[str, Any]):
        """Create basic pattern from manual data"""
        # This would be implemented based on the manual pattern dialog
        # For now, return a placeholder
        pass

def main():
    """Main function"""
    if not PYSIDE_AVAILABLE:
        print("PySide6 not available. Running in command-line mode.")
        print("To use the GUI version, install PySide6: pip install PySide6")
        
        # Simple command-line interface
        pattern_storage = PatternStorage()
        detector = PatternDetector()
        
        print(f"Loaded {len(pattern_storage.patterns)} existing patterns")
        print("Pattern detection system initialized.")
        print("Use the GUI version for interactive pattern analysis.")
        return
    
    app = QApplication(sys.argv)
    app.setApplicationName("Chess Pattern Editor/Viewer")
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
        viewer = PatternEditorViewer()
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
=======
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
>>>>>>> main
