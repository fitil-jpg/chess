"""
Pattern detection system for chess positions.
Identifies critical positions during gameplay for pattern learning.
"""

from __future__ import annotations
import chess
from typing import List, Dict, Any, Optional, Tuple
from core.evaluator import Evaluator
import logging

logger = logging.getLogger(__name__)


class PatternType:
    """Pattern type classifications"""
    TACTICAL_MOMENT = "tactical_moment"
    OPENING_TRICK = "opening_trick"
    FORK = "fork"
    PIN = "pin"
    SKEWER = "skewer"
    DISCOVERED_ATTACK = "discovered_attack"
    HANGING_PIECE = "hanging_piece"
    EXCHANGE = "exchange"
    CRITICAL_DECISION = "critical_decision"
    ENDGAME_TECHNIQUE = "endgame_technique"
    SACRIFICE = "sacrifice"
    DEFENSE = "defense"
    ATTACK = "attack"


class ChessPattern:
    """Represents a detected chess pattern"""
    
    def __init__(
        self,
        fen: str,
        move: str,
        pattern_types: List[str],
        description: str,
        influencing_pieces: List[Dict[str, Any]],
        evaluation: Dict[str, Any],
        metadata: Dict[str, Any] = None
    ):
        self.fen = fen
        self.move = move
        self.pattern_types = pattern_types
        self.description = description
        self.influencing_pieces = influencing_pieces
        self.evaluation = evaluation
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert pattern to dictionary for JSON serialization"""
        return {
            "fen": self.fen,
            "move": self.move,
            "pattern_types": self.pattern_types,
            "description": self.description,
            "influencing_pieces": self.influencing_pieces,
            "evaluation": self.evaluation,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChessPattern':
        """Create pattern from dictionary"""
        return cls(
            fen=data["fen"],
            move=data["move"],
            pattern_types=data["pattern_types"],
            description=data["description"],
            influencing_pieces=data["influencing_pieces"],
            evaluation=data["evaluation"],
            metadata=data.get("metadata", {})
        )
    


class PatternDetector:
    """Detects interesting chess patterns during gameplay"""
    
    def __init__(self):
        self.patterns: List[ChessPattern] = []
        
    def detect_patterns(
        self,
        board: chess.Board,
        move: chess.Move,
        evaluation_before: Dict[str, Any],
        evaluation_after: Dict[str, Any],
        bot_analysis: Dict[str, Any] = None
    ) -> List[ChessPattern]:
        """
        Detect patterns in the current position after a move.
        
        Args:
            board: Current board position (after move)
            move: The move that was played
            evaluation_before: Evaluation before the move
            evaluation_after: Evaluation after the move
            bot_analysis: Optional analysis from multiple bots
            
        Returns:
            List of detected patterns
        """
        detected_patterns = []
        
        # Create a copy to analyze the position before the move
        board_before = board.copy()
        if board_before.move_stack:
            board_before.pop()
        else:
            # If no moves yet, board is already the before state
            board_before = board.copy()
        
        # Get the move in SAN notation
        try:
            move_san = board_before.san(move)
        except:
            # Fallback to UCI if SAN fails
            move_san = move.uci()
        
        # Detect different types of patterns
        pattern_types = []
        descriptions = []
        
        # 1. Tactical moments (sharp evaluation change)
        if self._is_tactical_moment(evaluation_before, evaluation_after):
            pattern_types.append(PatternType.TACTICAL_MOMENT)
            eval_change = abs(evaluation_after.get("total", 0) - evaluation_before.get("total", 0))
            descriptions.append(f"Tactical moment with evaluation change: {eval_change}")
            
        # 2. Fork detection
        fork_info = self._detect_fork(board, move)
        if fork_info:
            pattern_types.append(PatternType.FORK)
            descriptions.append(f"Fork: {fork_info}")
            
        # 3. Pin detection
        pin_info = self._detect_pin(board, move)
        if pin_info:
            pattern_types.append(PatternType.PIN)
            descriptions.append(f"Pin: {pin_info}")
            
        # 4. Hanging piece
        hanging_info = self._detect_hanging_pieces(board)
        if hanging_info:
            pattern_types.append(PatternType.HANGING_PIECE)
            descriptions.append(f"Hanging piece: {hanging_info}")
            
        # 5. Critical decision (many alternatives)
        if bot_analysis and self._is_critical_decision(bot_analysis):
            pattern_types.append(PatternType.CRITICAL_DECISION)
            descriptions.append("Critical position with many alternatives evaluated")
            
        # 6. Opening trick (early game, unusual move)
        if board.fullmove_number <= 10 and self._is_unusual_move(board_before, move):
            pattern_types.append(PatternType.OPENING_TRICK)
            descriptions.append("Unusual opening move")
            
        # 6.5 Exchange sequence (SEE)
        try:
            see_value = Evaluator.static_exchange_eval(board_before, move)
            if board_before.is_capture(move) or abs(see_value) > 0:
                pattern_types.append(PatternType.EXCHANGE)
                sign = "+" if see_value > 0 else "" if see_value == 0 else "-"
                descriptions.append(f"Exchange sequence (SEE={sign}{see_value})")
        except Exception:
            pass

        # 7. Endgame technique
        if self._is_endgame(board) and abs(evaluation_after.get("total", 0)) > 200:
            pattern_types.append(PatternType.ENDGAME_TECHNIQUE)
            descriptions.append("Endgame technique")
            
        # 8. Sacrifice
        if self._is_sacrifice(board_before, move, evaluation_before, evaluation_after):
            pattern_types.append(PatternType.SACRIFICE)
            descriptions.append("Piece sacrifice")
        
        # Only create pattern if we detected something interesting
        if pattern_types:
            # Get influencing pieces (pieces that affect the moved piece's square)
            influencing_pieces = self._get_influencing_pieces(board, move.to_square)
            # Add mover and target roles explicitly
            mover_piece = board_before.piece_at(move.from_square)
            if mover_piece:
                influencing_pieces.append({
                    "square": chess.square_name(move.from_square),
                    "piece": self._piece_name(mover_piece.piece_type),
                    "color": "white" if mover_piece.color == chess.WHITE else "black",
                    "relationship": "mover",
                    "role": "mover"
                })
            captured_piece = board_before.piece_at(move.to_square)
            if captured_piece:
                influencing_pieces.append({
                    "square": chess.square_name(move.to_square),
                    "piece": self._piece_name(captured_piece.piece_type),
                    "color": "white" if captured_piece.color == chess.WHITE else "black",
                    "relationship": "target",
                    "role": "target"
                })
            
            pattern = ChessPattern(
                fen=board_before.fen(),
                move=move_san,
                pattern_types=pattern_types,
                description="; ".join(descriptions),
                influencing_pieces=influencing_pieces,
                evaluation={
                    "before": evaluation_before,
                    "after": evaluation_after,
                    "change": evaluation_after.get("total", 0) - evaluation_before.get("total", 0)
                },
                metadata={
                    "fullmove_number": board.fullmove_number,
                    "turn": "white" if board_before.turn == chess.WHITE else "black",
                    "is_capture": board_before.is_capture(move),
                    "is_check": board.is_check()
                }
            )
            
            detected_patterns.append(pattern)
            
        return detected_patterns
    
    def _is_tactical_moment(self, eval_before: Dict, eval_after: Dict) -> bool:
        """Check if this is a tactical moment (sharp evaluation change)"""
        change = abs(eval_after.get("total", 0) - eval_before.get("total", 0))
        return change > 150  # More than 1.5 pawns
    
    def _detect_fork(self, board: chess.Board, move: chess.Move) -> Optional[str]:
        """Detect if the move creates a fork"""
        piece = board.piece_at(move.to_square)
        if not piece or piece.piece_type not in (chess.KNIGHT, chess.BISHOP):
            return None
            
        # Count valuable pieces attacked
        attacked_pieces = []
        for target_sq in board.attacks(move.to_square):
            target_piece = board.piece_at(target_sq)
            if target_piece and target_piece.color != piece.color:
                if target_piece.piece_type in (chess.KING, chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT):
                    piece_names = {
                        chess.KING: "King",
                        chess.QUEEN: "Queen",
                        chess.ROOK: "Rook",
                        chess.BISHOP: "Bishop",
                        chess.KNIGHT: "Knight"
                    }
                    attacked_pieces.append(piece_names[target_piece.piece_type])
        
        if len(attacked_pieces) >= 2:
            piece_name = "Knight" if piece.piece_type == chess.KNIGHT else "Bishop"
            return f"{piece_name} attacks {', '.join(attacked_pieces[:2])}"
        
        return None
    
    def _detect_pin(self, board: chess.Board, move: chess.Move) -> Optional[str]:
        """Detect if the move creates a pin"""
        # Simplified pin detection - check if a piece is pinned to king
        piece = board.piece_at(move.to_square)
        if not piece or piece.piece_type not in (chess.BISHOP, chess.ROOK, chess.QUEEN):
            return None
        
        # Check if we're creating a pin
        enemy_color = not piece.color
        enemy_king_sq = board.king(enemy_color)
        
        if enemy_king_sq is None:
            return None
        
        # Check if there's a piece between us and the enemy king on the same line
        try:
            between_squares = chess.SquareSet(chess.between(move.to_square, enemy_king_sq))
            if len(between_squares) == 1:
                pinned_sq = list(between_squares)[0]
                pinned_piece = board.piece_at(pinned_sq)
                if pinned_piece and pinned_piece.color == enemy_color:
                    piece_names = {
                        chess.QUEEN: "Queen",
                        chess.ROOK: "Rook",
                        chess.BISHOP: "Bishop",
                        chess.KNIGHT: "Knight",
                        chess.PAWN: "Pawn"
                    }
                    return f"{piece_names.get(pinned_piece.piece_type, 'Piece')} pinned to King"
        except:
            # If there's any error with between calculation, just skip pin detection
            pass
        
        return None
    
    def _detect_hanging_pieces(self, board: chess.Board) -> Optional[str]:
        """Detect hanging pieces (attacked but not defended)"""
        hanging = []
        for sq, piece in board.piece_map().items():
            # Check enemy pieces that are attacked but not defended
            if piece.color == board.turn:
                continue
                
            attackers = len(board.attackers(board.turn, sq))
            defenders = len(board.attackers(not board.turn, sq))
            
            if attackers > 0 and defenders == 0 and piece.piece_type != chess.PAWN:
                piece_names = {
                    chess.KING: "King",
                    chess.QUEEN: "Queen",
                    chess.ROOK: "Rook",
                    chess.BISHOP: "Bishop",
                    chess.KNIGHT: "Knight"
                }
                hanging.append(piece_names.get(piece.piece_type, "Piece"))
        
        if hanging:
            return f"{hanging[0]} hanging"
        return None
    
    def _is_critical_decision(self, bot_analysis: Dict[str, Any]) -> bool:
        """Check if this position had many evaluated alternatives"""
        # If multiple bots were consulted or many moves evaluated
        return bot_analysis.get("alternatives_count", 0) > 5
    
    def _is_unusual_move(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if this is an unusual opening move"""
        # Simplified: consider moves that are not typical developing moves
        piece = board.piece_at(move.from_square)
        if not piece:
            return False
            
        # Unusual if moving same piece twice in opening
        move_history = [m.from_square for m in board.move_stack[-3:] if board.move_stack]
        return move.from_square in move_history
    
    def _is_endgame(self, board: chess.Board) -> bool:
        """Check if position is in endgame"""
        # Count non-pawn, non-king pieces
        piece_count = 0
        for piece_type in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]:
            piece_count += len(board.pieces(piece_type, chess.WHITE))
            piece_count += len(board.pieces(piece_type, chess.BLACK))
        return piece_count <= 6
    
    def _is_sacrifice(
        self,
        board_before: chess.Board,
        move: chess.Move,
        eval_before: Dict,
        eval_after: Dict
    ) -> bool:
        """Check if this is a piece sacrifice"""
        # A sacrifice: material goes down but evaluation improves
        if not board_before.is_capture(move):
            # Check if piece is hanging after move
            board_after = board_before.copy()
            board_after.push(move)
            
            attackers = len(board_after.attackers(not board_before.turn, move.to_square))
            defenders = len(board_after.attackers(board_before.turn, move.to_square))
            
            if attackers > defenders:
                eval_change = eval_after.get("total", 0) - eval_before.get("total", 0)
                # If we're improving evaluation despite hanging piece
                if board_before.turn == chess.WHITE:
                    return eval_change > 0
                else:
                    return eval_change < 0
        
        return False
    
    def _get_influencing_pieces(self, board: chess.Board, square: int) -> List[Dict[str, Any]]:
        """
        Get pieces that influence the given square (for heatmap analysis).
        Returns list of pieces with their positions and relationships.
        """
        influencing = []
        
        # Get all attackers and defenders of this square
        for color in [chess.WHITE, chess.BLACK]:
            attackers = board.attackers(color, square)
            for attacker_sq in attackers:
                piece = board.piece_at(attacker_sq)
                if piece:
                    influencing.append({
                        "square": chess.square_name(attacker_sq),
                        "piece": self._piece_name(piece.piece_type),
                        "color": "white" if piece.color == chess.WHITE else "black",
                        "relationship": "attacker" if color == board.turn else "defender",
                        "role": "attacker" if color == board.turn else "defender"
                    })
        
        return influencing

    @staticmethod
    def _piece_name(piece_type: chess.PieceType) -> str:
        piece_names = {
            chess.KING: "King",
            chess.QUEEN: "Queen",
            chess.ROOK: "Rook",
            chess.BISHOP: "Bishop",
            chess.KNIGHT: "Knight",
            chess.PAWN: "Pawn",
        }
        return piece_names.get(piece_type, "Unknown")
    
    def add_pattern(self, pattern: ChessPattern):
        """Add a detected pattern to the collection"""
        self.patterns.append(pattern)
        
    def get_patterns(self, filter_types: List[str] = None) -> List[ChessPattern]:
        """Get patterns, optionally filtered by type"""
        if not filter_types:
            return self.patterns
        
        return [p for p in self.patterns if any(pt in p.pattern_types for pt in filter_types)]
    
    def clear_patterns(self):
        """Clear all detected patterns"""
        self.patterns.clear()
