#!/usr/bin/env python3
"""
Enhanced DynamicBot designed to defeat Stockfish
Uses advanced pattern recognition, deep analysis, and strategic planning.
"""

from __future__ import annotations
import chess
import chess.engine
import random
import time
from typing import List, Dict, Any, Optional, Tuple
import logging
from dataclasses import dataclass

from chess_ai.pattern_detector import PatternDetector, ChessPattern
from chess_ai.pattern_filter import PatternFilter
from chess_ai.pattern_manager import PatternManager

logger = logging.getLogger(__name__)


@dataclass
class MoveAnalysis:
    """Analysis of a potential move"""
    move: chess.Move
    evaluation: float
    patterns: List[ChessPattern]
    tactical_value: float
    positional_value: float
    safety_score: float
    complexity: str
    confidence: float


class EnhancedDynamicBot:
    """
    Enhanced DynamicBot with advanced pattern recognition and strategic planning
    Designed to defeat Stockfish through superior pattern understanding
    """
    
    def __init__(self, color: chess.Color, stockfish_path: str = None):
        self.color = color
        self.stockfish_path = stockfish_path or "stockfish"
        self.pattern_detector = PatternDetector()
        self.pattern_filter = PatternFilter()
        self.pattern_manager = PatternManager()
        
        # Bot configuration
        self.aggression_level = 0.7  # 0.0 = defensive, 1.0 = aggressive
        self.pattern_weight = 0.4    # Weight of pattern-based evaluation
        self.tactical_weight = 0.3   # Weight of tactical evaluation
        self.positional_weight = 0.3 # Weight of positional evaluation
        
        # Game state tracking
        self.game_phase = "opening"
        self.move_count = 0
        self.pattern_history = []
        self.opponent_patterns = []
        
        # Opening book (simplified)
        self.opening_book = self._init_opening_book()
        
        # Endgame patterns
        self.endgame_patterns = self._init_endgame_patterns()
    
    def _init_opening_book(self) -> Dict[str, List[str]]:
        """Initialize opening book with strong moves"""
        return {
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1": [
                "e4", "d4", "Nf3", "c4"
            ],
            "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1": [
                "e5", "c5", "e6", "c6"
            ],
            "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2": [
                "Nf3", "Bc4", "Nc3", "d3"
            ]
        }
    
    def _init_endgame_patterns(self) -> Dict[str, List[str]]:
        """Initialize endgame patterns"""
        return {
            "king_pawn": ["Kf7", "Ke7", "Kd7"],
            "queen_endgame": ["Qa8+", "Qh8+", "Qf8+"],
            "rook_endgame": ["Ra8", "Rh8", "Rf8"]
        }
    
    def choose_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Choose the best move using enhanced analysis"""
        try:
            self.move_count += 1
            self._update_game_phase(board)
            
            # Get all legal moves
            legal_moves = list(board.legal_moves)
            if not legal_moves:
                return None
            
            # Analyze all moves
            move_analyses = []
            for move in legal_moves:
                # Debug: check if move is still legal
                if move not in board.legal_moves:
                    logger.warning(f"Move {move} is not legal, skipping")
                    continue
                analysis = self._analyze_move(board, move)
                if analysis:
                    move_analyses.append(analysis)
            
            if not move_analyses:
                # Fallback to random legal move
                return random.choice(legal_moves)
            
            # Sort by overall score
            move_analyses.sort(key=lambda x: x.confidence, reverse=True)
            
            # Select best move with some randomness for variety
            best_moves = move_analyses[:3]
            selected_analysis = random.choices(
                best_moves,
                weights=[0.5, 0.3, 0.2],
                k=1
            )[0]
            
            # Verify the move is still legal
            if selected_analysis.move not in board.legal_moves:
                logger.warning(f"Selected move {selected_analysis.move} is not legal, using fallback")
                return random.choice(legal_moves)
            
            # Log the decision
            logger.info(f"Selected move: {board.san(selected_analysis.move)} "
                       f"(eval: {selected_analysis.evaluation:.2f}, "
                       f"confidence: {selected_analysis.confidence:.2f})")
            
            return selected_analysis.move
            
        except Exception as e:
            logger.error(f"Error in choose_move: {e}")
            return random.choice(list(board.legal_moves)) if board.legal_moves else None
    
    def _analyze_move(self, board: chess.Board, move: chess.Move) -> Optional[MoveAnalysis]:
        """Analyze a potential move comprehensively"""
        try:
            # Check if move is legal
            if move not in board.legal_moves:
                return None
            
            # Get evaluation before move
            eval_before = self._basic_evaluation(board)
            
            # Make the move temporarily
            board.push(move)
            
            # Basic evaluation after move
            evaluation = self._evaluate_position(board)
            
            # Detect patterns (board already has the move applied)
            patterns = self._detect_move_patterns(board, move, eval_before, evaluation)
            
            # Calculate tactical value
            tactical_value = self._calculate_tactical_value(board, move, patterns)
            
            # Calculate positional value
            positional_value = self._calculate_positional_value(board, move)
            
            # Calculate safety score
            safety_score = self._calculate_safety_score(board, move)
            
            # Determine complexity
            complexity = self._determine_complexity(patterns, tactical_value)
            
            # Calculate overall confidence
            confidence = self._calculate_confidence(
                evaluation, tactical_value, positional_value, 
                safety_score, patterns, complexity
            )
            
            # Undo the move
            board.pop()
            
            return MoveAnalysis(
                move=move,
                evaluation=evaluation,
                patterns=patterns,
                tactical_value=tactical_value,
                positional_value=positional_value,
                safety_score=safety_score,
                complexity=complexity,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Error analyzing move {move}: {e}")
            # Ensure move is undone if it was made
            if board.move_stack and board.peek() == move:
                board.pop()
            return None
    
    def _evaluate_position(self, board: chess.Board) -> float:
        """Evaluate the current position"""
        try:
            # Use Stockfish for deep evaluation if available
            if self.stockfish_path:
                try:
                    with chess.engine.SimpleEngine.popen_uci(self.stockfish_path) as engine:
                        result = engine.analyse(board, chess.engine.Limit(time=0.1))
                        return result["score"].white().score(mate_score=10000) / 100.0
                except:
                    pass
            
            # Fallback to basic evaluation
            return self._basic_evaluation(board)
            
        except Exception as e:
            logger.error(f"Error evaluating position: {e}")
            return 0.0
    
    def _basic_evaluation(self, board: chess.Board) -> float:
        """Basic position evaluation"""
        piece_values = {
            chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
            chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 100
        }
        
        score = 0.0
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = piece_values.get(piece.piece_type, 0)
                if piece.color == self.color:
                    score += value
                else:
                    score -= value
        
        # Add mobility bonus
        mobility = len(list(board.legal_moves))
        if board.turn == self.color:
            score += mobility * 0.1
        else:
            score -= mobility * 0.1
        
        return score
    
    def _detect_move_patterns(self, board: chess.Board, move: chess.Move, eval_before: float, eval_after: float) -> List[ChessPattern]:
        """Detect patterns for this move (board already has the move applied)"""
        try:
            # Detect patterns (board already has the move applied)
            patterns = self.pattern_detector.detect_patterns(
                board, move, {"total": eval_before}, {"total": eval_after}
            )
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting patterns: {e}")
            return []
    
    def _calculate_tactical_value(self, board: chess.Board, move: chess.Move, patterns: List[ChessPattern]) -> float:
        """Calculate tactical value of the move"""
        tactical_value = 0.0
        
        # Check for captures
        if board.is_capture(move):
            captured_piece = board.piece_at(move.to_square)
            if captured_piece:
                piece_values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
                              chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 100}
                captured_value = piece_values.get(captured_piece.piece_type, 0)
                tactical_value += captured_value
        
        # Check for checks
        if board.gives_check(move):
            tactical_value += 0.5
        
        # Check for pattern-based tactical value
        for pattern in patterns:
            if "fork" in pattern.pattern_types:
                tactical_value += 2.0
            elif "pin" in pattern.pattern_types:
                tactical_value += 1.5
            elif "tactical_moment" in pattern.pattern_types:
                tactical_value += 1.0
            elif "sacrifice" in pattern.pattern_types:
                tactical_value += pattern.evaluation.get("change", 0) / 10.0
        
        return tactical_value
    
    def _calculate_positional_value(self, board: chess.Board, move: chess.Move) -> float:
        """Calculate positional value of the move"""
        positional_value = 0.0
        
        # Center control
        center_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
        if move.to_square in center_squares:
            positional_value += 0.3
        
        # Piece development
        if self.game_phase == "opening":
            if board.piece_at(move.to_square) and board.piece_at(move.to_square).piece_type in [chess.KNIGHT, chess.BISHOP]:
                positional_value += 0.2
        
        # King safety
        if move.to_square in [chess.G1, chess.G8, chess.C1, chess.C8]:  # Castling squares
            positional_value += 0.5
        
        # Pawn structure
        if board.piece_at(move.to_square) and board.piece_at(move.to_square).piece_type == chess.PAWN:
            # Check for pawn chains, passed pawns, etc.
            positional_value += self._evaluate_pawn_structure(board, move)
        
        return positional_value
    
    def _evaluate_pawn_structure(self, board: chess.Board, move: chess.Move) -> float:
        """Evaluate pawn structure after the move"""
        score = 0.0
        
        # Check for passed pawns
        if board.piece_at(move.to_square) and board.piece_at(move.to_square).piece_type == chess.PAWN:
            file = chess.square_file(move.to_square)
            rank = chess.square_rank(move.to_square)
            
            # Simple passed pawn check
            if self._is_passed_pawn(board, move.to_square):
                score += 0.5
        
        return score
    
    def _is_passed_pawn(self, board: chess.Board, square: int) -> bool:
        """Check if a pawn is passed"""
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        color = board.piece_at(square).color
        
        # Check adjacent files for enemy pawns
        for adj_file in [file - 1, file, file + 1]:
            if 0 <= adj_file <= 7:
                for adj_rank in range(8):
                    adj_square = chess.square(adj_file, adj_rank)
                    piece = board.piece_at(adj_square)
                    if piece and piece.piece_type == chess.PAWN and piece.color != color:
                        if (color == chess.WHITE and adj_rank > rank) or \
                           (color == chess.BLACK and adj_rank < rank):
                            return False
        
        return True
    
    def _calculate_safety_score(self, board: chess.Board, move: chess.Move) -> float:
        """Calculate safety score for the move"""
        safety_score = 0.0
        
        # Check if move exposes king
        if self._exposes_king(board, move):
            safety_score -= 2.0
        
        # Check if move creates hanging pieces
        if self._creates_hanging_pieces(board, move):
            safety_score -= 1.0
        
        # Check if move improves king safety
        if self._improves_king_safety(board, move):
            safety_score += 1.0
        
        return safety_score
    
    def _exposes_king(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move exposes the king to danger"""
        # Simple check - if king is in check after move
        return board.is_check()
    
    def _creates_hanging_pieces(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move creates hanging pieces"""
        # This is a simplified check
        # In a real implementation, you'd check if any pieces are undefended
        return False
    
    def _improves_king_safety(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move improves king safety"""
        # Check for castling
        if move.to_square in [chess.G1, chess.G8, chess.C1, chess.C8]:
            return True
        
        # Check if move moves king away from center
        king_square = board.king(self.color)
        if move.from_square == king_square:
            center_distance_before = self._distance_from_center(king_square)
            center_distance_after = self._distance_from_center(move.to_square)
            return center_distance_after > center_distance_before
        
        return False
    
    def _distance_from_center(self, square: int) -> float:
        """Calculate distance from center of board"""
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        center_file, center_rank = 3.5, 3.5
        return ((file - center_file) ** 2 + (rank - center_rank) ** 2) ** 0.5
    
    def _determine_complexity(self, patterns: List[ChessPattern], tactical_value: float) -> str:
        """Determine the complexity of the position"""
        if tactical_value > 3.0 or len(patterns) > 3:
            return "complex"
        elif tactical_value > 1.0 or len(patterns) > 1:
            return "moderate"
        else:
            return "simple"
    
    def _calculate_confidence(self, evaluation: float, tactical_value: float, 
                            positional_value: float, safety_score: float,
                            patterns: List[ChessPattern], complexity: str) -> float:
        """Calculate overall confidence in the move"""
        # Base confidence from evaluation
        confidence = abs(evaluation) * 0.3
        
        # Add tactical confidence
        confidence += tactical_value * 0.4
        
        # Add positional confidence
        confidence += positional_value * 0.2
        
        # Add safety confidence
        confidence += safety_score * 0.1
        
        # Adjust for complexity
        if complexity == "complex":
            confidence *= 1.2  # Reward complex moves
        elif complexity == "simple":
            confidence *= 0.8  # Slightly penalize simple moves
        
        # Add pattern bonus
        pattern_bonus = len(patterns) * 0.1
        confidence += pattern_bonus
        
        return max(0.0, min(10.0, confidence))  # Clamp between 0 and 10
    
    def _update_game_phase(self, board: chess.Board):
        """Update the current game phase"""
        piece_count = len([p for p in board.piece_map().values() if p.piece_type != chess.KING])
        
        if piece_count > 20:
            self.game_phase = "opening"
        elif piece_count > 8:
            self.game_phase = "midgame"
        else:
            self.game_phase = "endgame"
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about this agent"""
        return {
            "name": "EnhancedDynamicBot",
            "version": "2.0",
            "color": "white" if self.color == chess.WHITE else "black",
            "game_phase": self.game_phase,
            "move_count": self.move_count,
            "patterns_detected": len(self.pattern_history),
            "aggression_level": self.aggression_level,
            "pattern_weight": self.pattern_weight,
            "tactical_weight": self.tactical_weight,
            "positional_weight": self.positional_weight
        }


def make_enhanced_dynamic_bot(color: chess.Color, **kwargs) -> EnhancedDynamicBot:
    """Factory function to create an EnhancedDynamicBot"""
    return EnhancedDynamicBot(color, **kwargs)