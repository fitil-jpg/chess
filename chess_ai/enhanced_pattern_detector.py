"""
Enhanced Pattern Detection System with Exchange Analysis
=========================================================

This module provides advanced pattern detection including:
1. Piece participation tracking (only pieces involved in pattern)
2. Exchange detection and evaluation (2-3 moves ahead)
3. Individual JSON storage for each pattern
4. Pattern filtering and management
"""

from __future__ import annotations
import chess
import json
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class PieceParticipation:
    """Tracks a piece's participation in a pattern."""
    square: str  # e.g., "e4"
    piece_type: str  # "pawn", "knight", "bishop", "rook", "queen", "king"
    color: str  # "white" or "black"
    role: str  # "attacker", "defender", "target", "moved", "support"
    moved_in_pattern: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExchangeSequence:
    """Represents a forced exchange sequence."""
    moves: List[str]  # UCI moves in sequence
    material_balance: int  # Final material change (positive = advantage)
    forced: bool  # Whether the exchange is forced
    evaluation_change: float  # Evaluation change through sequence
    participating_squares: List[str]  # Squares involved in exchange
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EnhancedPattern:
    """Enhanced chess pattern with participation tracking."""
    pattern_id: str  # Unique identifier
    fen: str  # Position before the pattern
    triggering_move: str  # Move that creates/reveals the pattern
    pattern_type: str  # "fork", "pin", "skewer", "exchange", "tactical", etc.
    participating_pieces: List[PieceParticipation]
    exchange_sequence: Optional[ExchangeSequence]
    evaluation: Dict[str, Any]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "pattern_id": self.pattern_id,
            "fen": self.fen,
            "triggering_move": self.triggering_move,
            "pattern_type": self.pattern_type,
            "participating_pieces": [p.to_dict() for p in self.participating_pieces],
            "exchange_sequence": self.exchange_sequence.to_dict() if self.exchange_sequence else None,
            "evaluation": self.evaluation,
            "metadata": self.metadata
        }
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EnhancedPattern:
        """Create pattern from dictionary."""
        participating_pieces = [
            PieceParticipation(**p) for p in data.get("participating_pieces", [])
        ]
        
        exchange_data = data.get("exchange_sequence")
        exchange_sequence = None
        if exchange_data:
            exchange_sequence = ExchangeSequence(**exchange_data)
        
        return cls(
            pattern_id=data["pattern_id"],
            fen=data["fen"],
            triggering_move=data["triggering_move"],
            pattern_type=data["pattern_type"],
            participating_pieces=participating_pieces,
            exchange_sequence=exchange_sequence,
            evaluation=data["evaluation"],
            metadata=data.get("metadata", {})
        )


class EnhancedPatternDetector:
    """
    Advanced pattern detector that:
    1. Identifies only pieces participating in the pattern
    2. Detects exchange sequences (2-3 moves ahead)
    3. Saves patterns as individual JSON files
    """
    
    def __init__(self, patterns_dir: str = "patterns/detected"):
        self.patterns_dir = Path(patterns_dir)
        self.patterns_dir.mkdir(parents=True, exist_ok=True)
        self.detected_patterns: List[EnhancedPattern] = []
        
        # Piece values for exchange calculation
        self.piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 0  # King is invaluable
        }
    
    def detect_pattern(
        self,
        board: chess.Board,
        move: chess.Move,
        depth: int = 3
    ) -> Optional[EnhancedPattern]:
        """
        Detect pattern after a move, identifying only participating pieces.
        
        Args:
            board: Current board position (after move)
            move: Move that was just played
            depth: How many moves ahead to analyze for exchanges
            
        Returns:
            EnhancedPattern if pattern detected, None otherwise
        """
        # Create board before move
        board_before = board.copy()
        if board_before.move_stack:
            board_before.pop()
        
        pattern_type = self._identify_pattern_type(board, move)
        if not pattern_type:
            return None
        
        # Identify participating pieces
        participating_pieces = self._get_participating_pieces(board, move, pattern_type)
        
        # Check for exchange sequences
        exchange_sequence = self._detect_exchange_sequence(board, move, depth)
        
        # Generate unique pattern ID
        pattern_id = f"{pattern_type}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Create evaluation
        evaluation = {
            "material_balance": self._calculate_material_balance(board),
            "piece_count": len(board.piece_map()),
            "game_phase": self._get_game_phase(board),
            "is_check": board.is_check(),
            "is_capture": board_before.is_capture(move)
        }
        
        # Create metadata
        metadata = {
            "detected_at": datetime.now().isoformat(),
            "move_number": board.fullmove_number,
            "turn": "white" if board_before.turn == chess.WHITE else "black",
            "pieces_in_pattern": len(participating_pieces),
            "has_exchange": exchange_sequence is not None
        }
        
        pattern = EnhancedPattern(
            pattern_id=pattern_id,
            fen=board_before.fen(),
            triggering_move=move.uci(),
            pattern_type=pattern_type,
            participating_pieces=participating_pieces,
            exchange_sequence=exchange_sequence,
            evaluation=evaluation,
            metadata=metadata
        )
        
        self.detected_patterns.append(pattern)
        return pattern
    
    def _identify_pattern_type(self, board: chess.Board, move: chess.Move) -> Optional[str]:
        """Identify the type of pattern."""
        # Check for various pattern types
        if self._is_fork(board, move):
            return "fork"
        elif self._is_pin(board, move):
            return "pin"
        elif self._is_skewer(board, move):
            return "skewer"
        elif self._is_discovered_attack(board, move):
            return "discovered_attack"
        elif board.is_capture(move):
            return "capture"
        elif board.is_check():
            return "check"
        elif self._is_centralization(board, move):
            return "centralization"
        
        return None
    
    def _get_participating_pieces(
        self,
        board: chess.Board,
        move: chess.Move,
        pattern_type: str
    ) -> List[PieceParticipation]:
        """
        Identify ONLY pieces that participate in creating the pattern.
        Excludes pieces that didn't move and aren't involved.
        """
        participating = []
        moved_piece = board.piece_at(move.to_square)
        
        # Always include the moved piece
        if moved_piece:
            participating.append(PieceParticipation(
                square=chess.square_name(move.to_square),
                piece_type=self._piece_type_name(moved_piece.piece_type),
                color="white" if moved_piece.color == chess.WHITE else "black",
                role="moved",
                moved_in_pattern=True
            ))
        
        # Pattern-specific participating pieces
        if pattern_type == "fork":
            # Include pieces being attacked in the fork
            participating.extend(self._get_fork_participants(board, move))
        elif pattern_type == "pin":
            # Include pinned piece and piece behind it
            participating.extend(self._get_pin_participants(board, move))
        elif pattern_type == "capture":
            # Include captured piece's position
            participating.extend(self._get_capture_participants(board, move))
        elif pattern_type in ["discovered_attack", "skewer"]:
            # Include pieces in the attack line
            participating.extend(self._get_attack_line_participants(board, move))
        
        # Add defenders and attackers of key squares
        participating.extend(self._get_key_defenders_attackers(board, move))
        
        return participating
    
    def _get_fork_participants(self, board: chess.Board, move: chess.Move) -> List[PieceParticipation]:
        """Get pieces involved in a fork."""
        participants = []
        attacks = board.attacks(move.to_square)
        
        for target_sq in attacks:
            piece = board.piece_at(target_sq)
            if piece and piece.color != board.piece_at(move.to_square).color:
                # Only include valuable pieces in fork
                if piece.piece_type in [chess.QUEEN, chess.ROOK, chess.KING, chess.BISHOP, chess.KNIGHT]:
                    participants.append(PieceParticipation(
                        square=chess.square_name(target_sq),
                        piece_type=self._piece_type_name(piece.piece_type),
                        color="white" if piece.color == chess.WHITE else "black",
                        role="target",
                        moved_in_pattern=False
                    ))
        
        return participants
    
    def _get_pin_participants(self, board: chess.Board, move: chess.Move) -> List[PieceParticipation]:
        """Get pieces involved in a pin."""
        participants = []
        piece = board.piece_at(move.to_square)
        
        if not piece or piece.piece_type not in [chess.BISHOP, chess.ROOK, chess.QUEEN]:
            return participants
        
        # Find pinned piece and piece behind it
        enemy_color = not piece.color
        enemy_king_sq = board.king(enemy_color)
        
        if enemy_king_sq is None:
            return participants
        
        try:
            between_squares = list(chess.SquareSet(chess.between(move.to_square, enemy_king_sq)))
            if len(between_squares) == 1:
                pinned_sq = between_squares[0]
                pinned_piece = board.piece_at(pinned_sq)
                
                if pinned_piece and pinned_piece.color == enemy_color:
                    # Pinned piece
                    participants.append(PieceParticipation(
                        square=chess.square_name(pinned_sq),
                        piece_type=self._piece_type_name(pinned_piece.piece_type),
                        color="white" if pinned_piece.color == chess.WHITE else "black",
                        role="target",
                        moved_in_pattern=False
                    ))
                    
                    # King (piece behind)
                    king_piece = board.piece_at(enemy_king_sq)
                    if king_piece:
                        participants.append(PieceParticipation(
                            square=chess.square_name(enemy_king_sq),
                            piece_type="king",
                            color="white" if king_piece.color == chess.WHITE else "black",
                            role="support",
                            moved_in_pattern=False
                        ))
        except:
            pass
        
        return participants
    
    def _get_capture_participants(self, board: chess.Board, move: chess.Move) -> List[PieceParticipation]:
        """Get pieces involved in a capture."""
        participants = []
        
        # Find defenders of the capturing piece
        attackers = board.attackers(not board.turn, move.to_square)
        defenders = board.attackers(board.turn, move.to_square)
        
        for sq in attackers:
            piece = board.piece_at(sq)
            if piece:
                participants.append(PieceParticipation(
                    square=chess.square_name(sq),
                    piece_type=self._piece_type_name(piece.piece_type),
                    color="white" if piece.color == chess.WHITE else "black",
                    role="attacker",
                    moved_in_pattern=False
                ))
        
        for sq in defenders:
            if sq != move.to_square:  # Don't duplicate the moved piece
                piece = board.piece_at(sq)
                if piece:
                    participants.append(PieceParticipation(
                        square=chess.square_name(sq),
                        piece_type=self._piece_type_name(piece.piece_type),
                        color="white" if piece.color == chess.WHITE else "black",
                        role="defender",
                        moved_in_pattern=False
                    ))
        
        return participants
    
    def _get_attack_line_participants(self, board: chess.Board, move: chess.Move) -> List[PieceParticipation]:
        """Get pieces on the attack line."""
        # Simplified - would need more complex logic for discovered attacks
        return []
    
    def _get_key_defenders_attackers(self, board: chess.Board, move: chess.Move) -> List[PieceParticipation]:
        """Get key defenders and attackers (limit to most important)."""
        participants = []
        
        # Only include pieces directly attacking or defending the moved piece
        attackers = list(board.attackers(not board.turn, move.to_square))[:2]  # Limit to 2
        defenders = list(board.attackers(board.turn, move.to_square))[:2]
        
        for sq in attackers:
            piece = board.piece_at(sq)
            if piece and sq != move.to_square:
                participants.append(PieceParticipation(
                    square=chess.square_name(sq),
                    piece_type=self._piece_type_name(piece.piece_type),
                    color="white" if piece.color == chess.WHITE else "black",
                    role="attacker",
                    moved_in_pattern=False
                ))
        
        for sq in defenders:
            piece = board.piece_at(sq)
            if piece and sq != move.to_square:
                participants.append(PieceParticipation(
                    square=chess.square_name(sq),
                    piece_type=self._piece_type_name(piece.piece_type),
                    color="white" if piece.color == chess.WHITE else "black",
                    role="defender",
                    moved_in_pattern=False
                ))
        
        return participants
    
    def _detect_exchange_sequence(
        self,
        board: chess.Board,
        initial_move: chess.Move,
        depth: int = 3
    ) -> Optional[ExchangeSequence]:
        """
        Detect forced exchange sequences 2-3 moves ahead.
        
        An exchange is a sequence of captures on the same square (or nearby squares)
        that is relatively forced.
        """
        if not board.is_capture(initial_move):
            # Check if the moved piece is hanging (potential sacrifice/exchange)
            attackers = list(board.attackers(not board.turn, initial_move.to_square))
            if not attackers:
                return None
        
        # Simulate exchange sequence
        sequence_board = board.copy()
        exchange_moves = []
        target_square = initial_move.to_square
        participating_squares = {chess.square_name(target_square)}
        
        material_before = self._calculate_material_balance(sequence_board)
        
        # Simulate captures on this square
        for move_num in range(depth):
            # Find best recapture
            recapture_move = self._find_best_recapture(sequence_board, target_square)
            
            if recapture_move is None:
                break
            
            exchange_moves.append(recapture_move.uci())
            participating_squares.add(chess.square_name(recapture_move.from_square))
            sequence_board.push(recapture_move)
            
            # Update target if move changed the capture square
            if recapture_move.to_square != target_square:
                target_square = recapture_move.to_square
                participating_squares.add(chess.square_name(target_square))
        
        if not exchange_moves:
            return None
        
        material_after = self._calculate_material_balance(sequence_board)
        material_change = material_after - material_before
        
        # Determine if exchange is forced (all moves are captures/recaptures)
        forced = all(sequence_board.is_capture(chess.Move.from_uci(m)) for m in exchange_moves)
        
        return ExchangeSequence(
            moves=exchange_moves,
            material_balance=material_change,
            forced=forced,
            evaluation_change=float(material_change),
            participating_squares=list(participating_squares)
        )
    
    def _find_best_recapture(self, board: chess.Board, square: int) -> Optional[chess.Move]:
        """Find the best recapture on a square."""
        # Get all attackers of the square
        attackers = board.attackers(board.turn, square)
        
        if not attackers:
            return None
        
        # Find lowest value attacker (basic MVV-LVA)
        best_move = None
        lowest_value = float('inf')
        
        for attacker_sq in attackers:
            piece = board.piece_at(attacker_sq)
            if piece:
                piece_value = self.piece_values.get(piece.piece_type, 0)
                if piece_value < lowest_value:
                    # Create the capture move
                    move = chess.Move(attacker_sq, square)
                    if move in board.legal_moves:
                        best_move = move
                        lowest_value = piece_value
        
        return best_move
    
    def _calculate_material_balance(self, board: chess.Board) -> int:
        """Calculate material balance (positive = white advantage)."""
        balance = 0
        for square, piece in board.piece_map().items():
            value = self.piece_values.get(piece.piece_type, 0)
            if piece.color == chess.WHITE:
                balance += value
            else:
                balance -= value
        return balance
    
    def _get_game_phase(self, board: chess.Board) -> str:
        """Determine game phase."""
        piece_count = len([p for p in board.piece_map().values() 
                          if p.piece_type != chess.KING])
        
        if board.fullmove_number <= 10:
            return "opening"
        elif piece_count <= 12:
            return "endgame"
        else:
            return "middlegame"
    
    def _is_fork(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move creates a fork."""
        piece = board.piece_at(move.to_square)
        if not piece or piece.piece_type not in [chess.KNIGHT, chess.BISHOP, chess.PAWN]:
            return False
        
        attacks = board.attacks(move.to_square)
        valuable_targets = 0
        
        for target_sq in attacks:
            target = board.piece_at(target_sq)
            if target and target.color != piece.color:
                if target.piece_type in [chess.QUEEN, chess.ROOK, chess.KING]:
                    valuable_targets += 1
        
        return valuable_targets >= 2
    
    def _is_pin(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move creates a pin."""
        piece = board.piece_at(move.to_square)
        if not piece or piece.piece_type not in [chess.BISHOP, chess.ROOK, chess.QUEEN]:
            return False
        
        enemy_color = not piece.color
        enemy_king_sq = board.king(enemy_color)
        
        if enemy_king_sq is None:
            return False
        
        try:
            between_squares = chess.SquareSet(chess.between(move.to_square, enemy_king_sq))
            if len(between_squares) == 1:
                pinned_sq = list(between_squares)[0]
                pinned_piece = board.piece_at(pinned_sq)
                return pinned_piece is not None and pinned_piece.color == enemy_color
        except:
            pass
        
        return False
    
    def _is_skewer(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move creates a skewer."""
        # Simplified skewer detection
        return False
    
    def _is_discovered_attack(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move creates discovered attack."""
        # Would need to compare attacks before/after move
        return False
    
    def _is_centralization(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move centralizes a piece."""
        # Central squares
        center = {chess.D4, chess.D5, chess.E4, chess.E5}
        extended_center = {chess.C3, chess.C4, chess.C5, chess.C6,
                          chess.D3, chess.D6, chess.E3, chess.E6,
                          chess.F3, chess.F4, chess.F5, chess.F6}
        
        return move.to_square in center or move.to_square in extended_center
    
    def _piece_type_name(self, piece_type: int) -> str:
        """Convert piece type to name."""
        names = {
            chess.PAWN: "pawn",
            chess.KNIGHT: "knight",
            chess.BISHOP: "bishop",
            chess.ROOK: "rook",
            chess.QUEEN: "queen",
            chess.KING: "king"
        }
        return names.get(piece_type, "unknown")
    
    def save_pattern(self, pattern: EnhancedPattern) -> Path:
        """Save pattern to individual JSON file."""
        filename = f"{pattern.pattern_id}.json"
        filepath = self.patterns_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(pattern.to_dict(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved pattern {pattern.pattern_id} to {filepath}")
        return filepath
    
    def load_pattern(self, pattern_id: str) -> Optional[EnhancedPattern]:
        """Load pattern from JSON file."""
        filepath = self.patterns_dir / f"{pattern_id}.json"
        
        if not filepath.exists():
            logger.warning(f"Pattern file not found: {filepath}")
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return EnhancedPattern.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load pattern {pattern_id}: {e}")
            return None
    
    def list_patterns(self, pattern_type: Optional[str] = None) -> List[str]:
        """List all pattern IDs, optionally filtered by type."""
        pattern_files = list(self.patterns_dir.glob("*.json"))
        
        if not pattern_type:
            return [f.stem for f in pattern_files]
        
        filtered = []
        for pf in pattern_files:
            try:
                pattern = self.load_pattern(pf.stem)
                if pattern and pattern.pattern_type == pattern_type:
                    filtered.append(pf.stem)
            except:
                continue
        
        return filtered
    
    def delete_pattern(self, pattern_id: str) -> bool:
        """Delete a pattern file."""
        filepath = self.patterns_dir / f"{pattern_id}.json"
        
        if filepath.exists():
            filepath.unlink()
            logger.info(f"Deleted pattern {pattern_id}")
            return True
        
        return False
    
    def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get statistics about detected patterns."""
        pattern_files = list(self.patterns_dir.glob("*.json"))
        
        stats = {
            "total_patterns": len(pattern_files),
            "by_type": {},
            "by_game_phase": {},
            "with_exchanges": 0,
            "average_participants": 0
        }
        
        total_participants = 0
        
        for pf in pattern_files:
            try:
                pattern = self.load_pattern(pf.stem)
                if pattern:
                    # Count by type
                    ptype = pattern.pattern_type
                    stats["by_type"][ptype] = stats["by_type"].get(ptype, 0) + 1
                    
                    # Count by game phase
                    phase = pattern.evaluation.get("game_phase", "unknown")
                    stats["by_game_phase"][phase] = stats["by_game_phase"].get(phase, 0) + 1
                    
                    # Count exchanges
                    if pattern.exchange_sequence:
                        stats["with_exchanges"] += 1
                    
                    # Track participants
                    total_participants += len(pattern.participating_pieces)
            except:
                continue
        
        if len(pattern_files) > 0:
            stats["average_participants"] = total_participants / len(pattern_files)
        
        return stats
