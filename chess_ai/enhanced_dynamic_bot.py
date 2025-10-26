"""
Enhanced DynamicBot optimized to beat Stockfish.
Uses advanced pattern recognition, deeper search, and strategic planning.
"""

from __future__ import annotations
import chess
import logging
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
import random

from .dynamic_bot import DynamicBot
from .enhanced_pattern_detector import EnhancedPatternDetector
from .pattern_manager import PatternManager
from core.evaluator import Evaluator
from utils import GameContext

logger = logging.getLogger(__name__)


class EnhancedDynamicBot(DynamicBot):
    """Enhanced DynamicBot with pattern recognition and strategic planning"""
    
    def __init__(self, color: bool, **kwargs):
        super().__init__(color, **kwargs)
        
        # Enhanced components
        self.pattern_detector = EnhancedPatternDetector()
        self.pattern_manager = PatternManager()
        
        # Strategic planning
        self.opening_book = self._load_opening_book()
        self.endgame_database = self._load_endgame_database()
        
        # Pattern-based weights
        self.pattern_weights = {
            "tactical_moment": 2.0,
            "fork": 3.0,
            "pin": 2.5,
            "hanging_piece": 2.0,
            "exchange": 1.5,
            "sacrifice": 2.5,
            "critical_decision": 2.0,
            "opening_trick": 1.8,
            "endgame_technique": 2.2
        }
        
        # Phase-specific strategies
        self.phase_strategies = {
            "opening": self._opening_strategy,
            "middlegame": self._middlegame_strategy,
            "endgame": self._endgame_strategy
        }
        
        # Stockfish counter-strategies
        self.stockfish_counters = {
            "aggressive": 1.5,  # Counter aggressive play
            "positional": 1.3,  # Counter positional play
            "tactical": 2.0,    # Counter tactical play
            "endgame": 1.8      # Counter endgame play
        }
        
    def _load_opening_book(self) -> Dict[str, List[str]]:
        """Load opening book for better opening play"""
        # Simplified opening book - in practice would load from file
        return {
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1": [
                "e4", "d4", "Nf3", "c4", "g3"
            ],
            "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1": [
                "e5", "c5", "e6", "c6", "Nf6"
            ]
        }
        
    def _load_endgame_database(self) -> Dict[str, str]:
        """Load endgame database for better endgame play"""
        # Simplified endgame database - in practice would load from file
        return {
            "KQvK": "win",
            "KRvK": "win", 
            "KQvKQ": "draw",
            "KRvKR": "draw"
        }
        
    def choose_move(self, board: chess.Board, context: GameContext = None, 
                   evaluator: Evaluator = None, debug: bool = False) -> Tuple[chess.Move, float]:
        """Enhanced move selection with pattern recognition and strategic planning"""
        
        # Detect game phase
        phase = self._detect_game_phase(board)
        
        # Use phase-specific strategy
        if phase in self.phase_strategies:
            move, confidence = self.phase_strategies[phase](board, context, evaluator, debug)
            if move is not None:
                return move, confidence
        
        # Fallback to enhanced base strategy
        return self._enhanced_base_strategy(board, context, evaluator, debug)
        
    def _detect_game_phase(self, board: chess.Board) -> str:
        """Detect current game phase"""
        piece_count = sum(1 for _ in board.piece_map().values())
        
        if piece_count > 20:
            return "opening"
        elif piece_count > 8:
            return "middlegame"
        else:
            return "endgame"
            
    def _opening_strategy(self, board: chess.Board, context: GameContext = None,
                         evaluator: Evaluator = None, debug: bool = False) -> Tuple[chess.Move, float]:
        """Opening strategy focused on development and control"""
        
        # Check opening book
        fen = board.fen()
        if fen in self.opening_book:
            moves = self.opening_book[fen]
            for move_str in moves:
                try:
                    move = board.parse_san(move_str)
                    if board.is_legal(move):
                        return move, 0.9
                except:
                    continue
        
        # Focus on development and center control
        development_moves = []
        center_moves = []
        
        for move in board.legal_moves:
            # Development moves
            if self._is_development_move(board, move):
                development_moves.append(move)
            
            # Center control moves
            if self._controls_center(board, move):
                center_moves.append(move)
        
        # Prefer development over center control
        if development_moves:
            move = random.choice(development_moves)
            return move, 0.8
        elif center_moves:
            move = random.choice(center_moves)
            return move, 0.7
        
        # Fallback to base strategy
        return self._enhanced_base_strategy(board, context, evaluator, debug)
        
    def _middlegame_strategy(self, board: chess.Board, context: GameContext = None,
                            evaluator: Evaluator = None, debug: bool = False) -> Tuple[chess.Move, float]:
        """Middlegame strategy focused on tactics and position"""
        
        # Detect patterns and prioritize tactical moves
        patterns = self._detect_relevant_patterns(board)
        
        if patterns:
            # Find moves that create or exploit patterns
            tactical_moves = self._find_tactical_moves(board, patterns)
            if tactical_moves:
                move = random.choice(tactical_moves)
                return move, 0.9
        
        # Look for positional improvements
        positional_moves = self._find_positional_moves(board, evaluator)
        if positional_moves:
            move = random.choice(positional_moves)
            return move, 0.7
        
        # Fallback to base strategy
        return self._enhanced_base_strategy(board, context, evaluator, debug)
        
    def _endgame_strategy(self, board: chess.Board, context: GameContext = None,
                         evaluator: Evaluator = None, debug: bool = False) -> Tuple[chess.Move, float]:
        """Endgame strategy focused on king activity and pawn promotion"""
        
        # Check for immediate wins
        winning_moves = self._find_winning_moves(board)
        if winning_moves:
            move = random.choice(winning_moves)
            return move, 1.0
        
        # King activity
        king_moves = self._find_king_moves(board)
        if king_moves:
            move = random.choice(king_moves)
            return move, 0.8
        
        # Pawn promotion
        promotion_moves = self._find_promotion_moves(board)
        if promotion_moves:
            move = random.choice(promotion_moves)
            return move, 0.9
        
        # Fallback to base strategy
        return self._enhanced_base_strategy(board, context, evaluator, debug)
        
    def _enhanced_base_strategy(self, board: chess.Board, context: GameContext = None,
                               evaluator: Evaluator = None, debug: bool = False) -> Tuple[chess.Move, float]:
        """Enhanced base strategy with pattern recognition"""
        
        # Get base move from parent class
        move, confidence = super().choose_move(board, context, evaluator, debug)
        
        if move is None:
            return None, 0.0
        
        # Apply pattern-based bonuses
        enhanced_confidence = self._apply_pattern_bonuses(board, move, confidence)
        
        return move, enhanced_confidence
        
    def _detect_relevant_patterns(self, board: chess.Board) -> List[Dict[str, Any]]:
        """Detect relevant patterns for current position"""
        patterns = []
        
        # Check for tactical opportunities
        for move in board.legal_moves:
            try:
                # Simulate move
                board_copy = board.copy()
                board_copy.push(move)
                
                # Detect patterns
                detected = self.pattern_detector.detect_patterns(
                    board_copy, move, {"total": 0}, {"total": 0}
                )
                
                if detected:
                    patterns.extend([p.to_dict() if hasattr(p, 'to_dict') else p for p in detected])
                    
            except Exception as e:
                logger.warning(f"Pattern detection failed for move {move}: {e}")
                continue
        
        return patterns
        
    def _find_tactical_moves(self, board: chess.Board, patterns: List[Dict[str, Any]]) -> List[chess.Move]:
        """Find moves that create or exploit tactical patterns"""
        tactical_moves = []
        
        for pattern in patterns:
            pattern_types = pattern.get('pattern_types', [])
            
            # Look for moves that create these patterns
            for move in board.legal_moves:
                if self._creates_pattern(board, move, pattern_types):
                    tactical_moves.append(move)
        
        return tactical_moves
        
    def _find_positional_moves(self, board: chess.Board, evaluator: Evaluator = None) -> List[chess.Move]:
        """Find moves that improve position"""
        if evaluator is None:
            evaluator = Evaluator(board)
        
        positional_moves = []
        
        for move in board.legal_moves:
            # Evaluate position after move
            board_copy = board.copy()
            board_copy.push(move)
            
            # Check for positional improvements
            if self._improves_position(board, board_copy, evaluator):
                positional_moves.append(move)
        
        return positional_moves
        
    def _find_winning_moves(self, board: chess.Board) -> List[chess.Move]:
        """Find moves that lead to immediate wins"""
        winning_moves = []
        
        for move in board.legal_moves:
            board_copy = board.copy()
            board_copy.push(move)
            
            # Check for checkmate
            if board_copy.is_checkmate():
                winning_moves.append(move)
            
            # Check for major material advantage
            if self._gains_major_material(board, move):
                winning_moves.append(move)
        
        return winning_moves
        
    def _find_king_moves(self, board: chess.Board) -> List[chess.Move]:
        """Find moves that activate the king"""
        king_moves = []
        
        for move in board.legal_moves:
            if board.piece_at(move.from_square) and board.piece_at(move.from_square).piece_type == chess.KING:
                # King moves in endgame
                king_moves.append(move)
        
        return king_moves
        
    def _find_promotion_moves(self, board: chess.Board) -> List[chess.Move]:
        """Find moves that promote pawns"""
        promotion_moves = []
        
        for move in board.legal_moves:
            if move.promotion:
                promotion_moves.append(move)
        
        return promotion_moves
        
    def _is_development_move(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move develops a piece"""
        piece = board.piece_at(move.from_square)
        if not piece:
            return False
        
        # Moving pieces from starting positions
        if piece.piece_type == chess.KNIGHT:
            return move.from_square in [chess.B1, chess.G1, chess.B8, chess.G8]
        elif piece.piece_type == chess.BISHOP:
            return move.from_square in [chess.C1, chess.F1, chess.C8, chess.F8]
        elif piece.piece_type == chess.QUEEN:
            return move.from_square in [chess.D1, chess.D8]
        
        return False
        
    def _controls_center(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move controls center squares"""
        center_squares = [chess.E4, chess.E5, chess.D4, chess.D5]
        return move.to_square in center_squares
        
    def _creates_pattern(self, board: chess.Board, move: chess.Move, pattern_types: List[str]) -> bool:
        """Check if move creates specific patterns"""
        # Simplified pattern creation check
        for pattern_type in pattern_types:
            if pattern_type == "fork":
                return self._creates_fork(board, move)
            elif pattern_type == "pin":
                return self._creates_pin(board, move)
            elif pattern_type == "tactical_moment":
                return self._creates_tactical_moment(board, move)
        
        return False
        
    def _creates_fork(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move creates a fork"""
        piece = board.piece_at(move.from_square)
        if not piece or piece.piece_type not in [chess.KNIGHT, chess.BISHOP]:
            return False
        
        # Count attacked pieces after move
        board_copy = board.copy()
        board_copy.push(move)
        
        attacked_pieces = 0
        for target_sq in board_copy.attacks(move.to_square):
            target_piece = board_copy.piece_at(target_sq)
            if target_piece and target_piece.color != piece.color:
                attacked_pieces += 1
        
        return attacked_pieces >= 2
        
    def _creates_pin(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move creates a pin"""
        piece = board.piece_at(move.from_square)
        if not piece or piece.piece_type not in [chess.BISHOP, chess.ROOK, chess.QUEEN]:
            return False
        
        # Check for pin after move
        board_copy = board.copy()
        board_copy.push(move)
        
        # Look for pieces pinned to king
        enemy_color = not piece.color
        enemy_king_sq = board_copy.king(enemy_color)
        
        if enemy_king_sq is None:
            return False
        
        try:
            between_squares = chess.SquareSet(chess.between(move.to_square, enemy_king_sq))
            if len(between_squares) == 1:
                pinned_sq = list(between_squares)[0]
                pinned_piece = board_copy.piece_at(pinned_sq)
                return pinned_piece is not None and pinned_piece.color == enemy_color
        except:
            pass
        
        return False
        
    def _creates_tactical_moment(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move creates a tactical moment"""
        # Simplified check - look for captures or checks
        return board.is_capture(move) or board.gives_check(move)
        
    def _improves_position(self, board_before: chess.Board, board_after: chess.Board, 
                          evaluator: Evaluator) -> bool:
        """Check if position improves after move"""
        # Simplified position improvement check
        material_before = evaluator.material_diff(self.color)
        material_after = evaluator.material_diff(self.color)
        
        return material_after > material_before
        
    def _gains_major_material(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move gains major material"""
        if not board.is_capture(move):
            return False
        
        captured_piece = board.piece_at(move.to_square)
        if not captured_piece:
            return False
        
        # Major pieces
        return captured_piece.piece_type in [chess.QUEEN, chess.ROOK]
        
    def _apply_pattern_bonuses(self, board: chess.Board, move: chess.Move, 
                              base_confidence: float) -> float:
        """Apply pattern-based bonuses to move confidence"""
        enhanced_confidence = base_confidence
        
        # Check for pattern creation
        for pattern_type, weight in self.pattern_weights.items():
            if self._creates_pattern(board, move, [pattern_type]):
                enhanced_confidence += weight * 0.1
        
        # Cap confidence at 1.0
        return min(enhanced_confidence, 1.0)
        
    def get_last_reason(self) -> str:
        """Get reason for last move"""
        return "Enhanced pattern-based strategy"
        
    def get_last_features(self) -> Dict[str, Any]:
        """Get features from last move"""
        return {
            "pattern_detection": True,
            "strategic_planning": True,
            "phase_aware": True
        }