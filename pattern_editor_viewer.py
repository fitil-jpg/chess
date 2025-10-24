#!/usr/bin/env python3
"""
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

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
            
            # Play one game
            self._play_game_with_pattern_detection(game_id)
            
            # Update progress
            progress = int((game_id + 1) / self.num_games * 100)
            self.progressUpdated.emit(progress)
            
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
                
            except Exception as e:
                logger.error(f"Error in game {game_id}, move {move_count}: {e}")
                break
    
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
    
    def stop(self):
        """Stop the worker"""
        self._stop_requested = True

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
        self.pattern_storage = PatternStorage()
        self.current_pattern = None
        self.game_worker = None
        
        # Initialize agents
        self._init_agents()
        
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
        
        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.status_label.setText("Paused")
    
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
        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_stop.setEnabled(False)
        self.progress_bar.setVisible(False)
    
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
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.pattern_storage.delete_pattern(self.current_pattern.id)
            self.current_pattern = None
            
            # Refresh UI
            self._refresh_pattern_list()
            self._clear_pattern_details()
            self.chess_board.set_board(chess.Board())
            
            self.status_label.setText("Pattern deleted")
    
    def _show_error(self, title: str, message: str):
        """Show error message"""
        QMessageBox.critical(self, title, message)

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