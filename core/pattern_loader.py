from __future__ import annotations

import logging
logger = logging.getLogger(__name__)

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    yaml = None

import chess
from opening_pattern import CowOpeningPlanner, COW_TAG


class PatternType(Enum):
    """Types of chess patterns."""
    OPENING = "opening"
    TACTICAL = "tactical"
    ENDGAME = "endgame"
    POSITIONAL = "positional"
    COW_OPENING = "cow_opening"


@dataclass
class ChessPattern:
    """Enhanced chess pattern with metadata."""
    situation: str  # FEN or partial FEN
    action: str     # Move in UCI format
    pattern_type: PatternType = PatternType.POSITIONAL
    name: str = ""
    description: str = ""
    frequency: float = 1.0
    confidence: float = 1.0
    game_phase: str = "any"  # opening, middlegame, endgame, any
    constraints: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.constraints is None:
            self.constraints = {}


class PatternResponder:
    """Enhanced pattern responder with tactical patterns and COW opening support.

    A pattern is a mapping with keys:
    ``situation`` – the piece placement portion of a FEN string,
    ``action`` – an arbitrary response (usually a move in UCI format),
    and optional metadata for pattern classification and evaluation.
    """

    def __init__(self, patterns: List[Dict[str, Any]] = None) -> None:
        self.patterns = patterns or []
        self.chess_patterns: List[ChessPattern] = []
        self.cow_planner_white = CowOpeningPlanner(chess.WHITE)
        self.cow_planner_black = CowOpeningPlanner(chess.BLACK)
        
        # Convert legacy patterns to ChessPattern objects
        self._convert_legacy_patterns()
        
        # Add built-in tactical and opening patterns
        self.add_tactical_patterns()
        self.add_cow_opening_patterns()
        self.add_common_opening_patterns()

    def _convert_legacy_patterns(self) -> None:
        """Convert legacy pattern format to ChessPattern objects."""
        for pattern_data in self.patterns:
            if isinstance(pattern_data, dict):
                chess_pattern = ChessPattern(
                    situation=pattern_data.get("situation", ""),
                    action=pattern_data.get("action", ""),
                    name=pattern_data.get("name", ""),
                    description=pattern_data.get("description", ""),
                    frequency=pattern_data.get("frequency", 1.0),
                    confidence=pattern_data.get("confidence", 1.0),
                    game_phase=pattern_data.get("game_phase", "any"),
                    constraints=pattern_data.get("constraints", {})
                )
                self.chess_patterns.append(chess_pattern)

    @classmethod
    def from_file(cls, path: str | Path) -> "PatternResponder":
        """Create a responder from a JSON or YAML file."""
        p = Path(path)
        with p.open("r", encoding="utf8") as fh:
            if p.suffix in {".yaml", ".yml"}:
                if yaml is None:  # pragma: no cover - defensive
                    raise RuntimeError("PyYAML is required for YAML pattern files")
                data = yaml.safe_load(fh)
            else:
                data = json.load(fh)
        if isinstance(data, dict):
            patterns = data.get("patterns", [])
        else:
            patterns = data
        return cls(patterns)

    def match(self, board: chess.Board) -> Optional[str]:
        """Return the action for the current board state, if any."""
        # First try COW opening patterns
        cow_move, cow_reason = self._try_cow_opening(board)
        if cow_move:
            return cow_move
        
        # Then try regular patterns
        layout = board.board_fen()
        
        # Try exact matches first
        for pattern in self.chess_patterns:
            if pattern.situation == layout:
                return pattern.action
        
        # Try partial matches for tactical patterns
        return self._try_tactical_patterns(board)
    
    def _try_cow_opening(self, board: chess.Board) -> Tuple[Optional[str], str]:
        """Try COW opening patterns."""
        if board.turn == chess.WHITE:
            planner = self.cow_planner_white
        else:
            planner = self.cow_planner_black
        
        if not planner.is_complete(board):
            move, reason = planner.choose_move(board, debug=True)
            if move:
                return move.uci(), reason
        
        return None, ""
    
    def _try_tactical_patterns(self, board: chess.Board) -> Optional[str]:
        """Try tactical pattern matching."""
        for pattern in self.chess_patterns:
            if pattern.pattern_type == PatternType.TACTICAL:
                if self._matches_tactical_pattern(board, pattern):
                    return pattern.action
        return None
    
    def _matches_tactical_pattern(self, board: chess.Board, pattern: ChessPattern) -> bool:
        """Check if board matches a tactical pattern."""
        # Simple pattern matching - can be enhanced
        # For now, just check if key pieces are in expected positions
        constraints = pattern.constraints
        
        if "fork" in constraints:
            return self._check_fork_pattern(board, pattern)
        elif "pin" in constraints:
            return self._check_pin_pattern(board, pattern)
        elif "skewer" in constraints:
            return self._check_skewer_pattern(board, pattern)
        elif "discovered_attack" in constraints:
            return self._check_discovered_attack_pattern(board, pattern)
        
        return False
    
    def _check_fork_pattern(self, board: chess.Board, pattern: ChessPattern) -> bool:
        """Check for fork tactical patterns."""
        # Look for knight forks
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.piece_type == chess.KNIGHT and piece.color == board.turn:
                attacks = board.attacks(square)
                enemy_pieces = []
                for attack_square in attacks:
                    attacked_piece = board.piece_at(attack_square)
                    if attacked_piece and attacked_piece.color != board.turn:
                        if attacked_piece.piece_type in [chess.QUEEN, chess.ROOK, chess.KING]:
                            enemy_pieces.append(attacked_piece)
                
                if len(enemy_pieces) >= 2:
                    return True
        return False
    
    def _check_pin_pattern(self, board: chess.Board, pattern: ChessPattern) -> bool:
        """Check for pin tactical patterns."""
        # Look for pins along ranks, files, and diagonals
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.color == board.turn:
                if piece.piece_type in [chess.ROOK, chess.QUEEN, chess.BISHOP]:
                    # Check if this piece can create a pin
                    if self._creates_pin(board, square, piece):
                        return True
        return False
    
    def _creates_pin(self, board: chess.Board, square: chess.Square, piece: chess.Piece) -> bool:
        """Check if a piece creates a pin."""
        attacks = board.attacks(square)
        for attack_square in attacks:
            attacked_piece = board.piece_at(attack_square)
            if attacked_piece and attacked_piece.color != piece.color:
                # Check if there's a more valuable piece behind this one
                direction = self._get_direction(square, attack_square)
                if direction:
                    next_square = attack_square + direction
                    if chess.square_file(next_square) >= 0 and chess.square_rank(next_square) >= 0:
                        next_piece = board.piece_at(next_square)
                        if (next_piece and next_piece.color != piece.color and
                            next_piece.piece_type > attacked_piece.piece_type):
                            return True
        return False
    
    def _get_direction(self, from_square: chess.Square, to_square: chess.Square) -> Optional[int]:
        """Get direction vector between two squares."""
        from_file, from_rank = chess.square_file(from_square), chess.square_rank(from_square)
        to_file, to_rank = chess.square_file(to_square), chess.square_rank(to_square)
        
        file_diff = to_file - from_file
        rank_diff = to_rank - from_rank
        
        if file_diff == 0 and rank_diff != 0:  # Same file
            return 8 if rank_diff > 0 else -8
        elif rank_diff == 0 and file_diff != 0:  # Same rank
            return 1 if file_diff > 0 else -1
        elif abs(file_diff) == abs(rank_diff):  # Diagonal
            if file_diff > 0 and rank_diff > 0:
                return 9
            elif file_diff > 0 and rank_diff < 0:
                return -7
            elif file_diff < 0 and rank_diff > 0:
                return 7
            else:
                return -9
        
        return None
    
    def _check_skewer_pattern(self, board: chess.Board, pattern: ChessPattern) -> bool:
        """Check for skewer tactical patterns."""
        # Similar to pin but with more valuable piece in front
        return False  # Simplified for now
    
    def _check_discovered_attack_pattern(self, board: chess.Board, pattern: ChessPattern) -> bool:
        """Check for discovered attack patterns."""
        # Check for pieces that can move to reveal an attack
        return False  # Simplified for now

    def add_tactical_patterns(self) -> None:
        """Add common tactical patterns."""
        tactical_patterns = [
            # Knight fork patterns
            ChessPattern(
                situation="",  # Will be matched by tactical logic
                action="",     # Will be determined by tactical analysis
                pattern_type=PatternType.TACTICAL,
                name="Knight Fork",
                description="Knight attacks two or more enemy pieces simultaneously",
                frequency=0.4,
                confidence=0.8,
                game_phase="middlegame",
                constraints={"fork": True, "piece_type": "knight"}
            ),
            
            # Pin patterns
            ChessPattern(
                situation="",
                action="",
                pattern_type=PatternType.TACTICAL,
                name="Pin",
                description="Piece cannot move without exposing more valuable piece",
                frequency=0.3,
                confidence=0.7,
                game_phase="any",
                constraints={"pin": True}
            ),
            
            # Skewer patterns
            ChessPattern(
                situation="",
                action="",
                pattern_type=PatternType.TACTICAL,
                name="Skewer",
                description="Valuable piece forced to move, exposing less valuable piece",
                frequency=0.2,
                confidence=0.8,
                game_phase="any",
                constraints={"skewer": True}
            ),
            
            # Discovered attack patterns
            ChessPattern(
                situation="",
                action="",
                pattern_type=PatternType.TACTICAL,
                name="Discovered Attack",
                description="Moving piece reveals attack from another piece",
                frequency=0.25,
                confidence=0.7,
                game_phase="any",
                constraints={"discovered_attack": True}
            )
        ]
        
        self.chess_patterns.extend(tactical_patterns)
    
    def add_cow_opening_patterns(self) -> None:
        """Add COW (Caro-Kann Opening Variation) patterns."""
        cow_patterns = [
            ChessPattern(
                situation="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                action="e2e3",
                pattern_type=PatternType.COW_OPENING,
                name="COW Opening - Pawn e3",
                description="COW opening: advance e-pawn to e3",
                frequency=0.9,
                confidence=0.95,
                game_phase="opening",
                constraints={"cow_phase": "pawn", "center_control": True}
            ),
            
            ChessPattern(
                situation="rnbqkbnr/pppppppp/8/8/8/4P3/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
                action="e7e6",
                pattern_type=PatternType.COW_OPENING,
                name="COW Opening - Black Pawn e6",
                description="COW opening response: advance e-pawn to e6",
                frequency=0.9,
                confidence=0.95,
                game_phase="opening",
                constraints={"cow_phase": "pawn", "center_control": True}
            ),
            
            ChessPattern(
                situation="rnbqkbnr/pppp1ppp/4p3/8/8/4P3/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
                action="d2d3",
                pattern_type=PatternType.COW_OPENING,
                name="COW Opening - Pawn d3",
                description="COW opening: advance d-pawn to d3",
                frequency=0.85,
                confidence=0.9,
                game_phase="opening",
                constraints={"cow_phase": "pawn", "center_control": True}
            )
        ]
        
        self.chess_patterns.extend(cow_patterns)
    
    def add_common_opening_patterns(self) -> None:
        """Add common opening patterns."""
        opening_patterns = [
            # Italian Game
            ChessPattern(
                situation="r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3",
                action="f7f5",
                pattern_type=PatternType.OPENING,
                name="Italian Game - Rousseau Gambit",
                description="Aggressive pawn push in Italian Game",
                frequency=0.3,
                confidence=0.6,
                game_phase="opening"
            ),
            
            # Sicilian Defense
            ChessPattern(
                situation="rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq c6 0 2",
                action="g1f3",
                pattern_type=PatternType.OPENING,
                name="Sicilian Defense - Open Sicilian",
                description="Knight development in Sicilian Defense",
                frequency=0.8,
                confidence=0.9,
                game_phase="opening"
            ),
            
            # French Defense
            ChessPattern(
                situation="rnbqkbnr/ppp2ppp/4p3/3p4/3PP3/8/PPP2PPP/RNBQKBNR w KQkq d6 0 3",
                action="b1c3",
                pattern_type=PatternType.OPENING,
                name="French Defense - Classical",
                description="Knight development in French Defense",
                frequency=0.7,
                confidence=0.8,
                game_phase="opening"
            )
        ]
        
        self.chess_patterns.extend(opening_patterns)
    
    def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get statistics about loaded patterns."""
        stats = {
            'total_patterns': len(self.chess_patterns),
            'by_type': {},
            'by_game_phase': {},
            'avg_confidence': 0.0,
            'avg_frequency': 0.0
        }
        
        total_confidence = 0.0
        total_frequency = 0.0
        
        for pattern in self.chess_patterns:
            # Count by type
            pattern_type = pattern.pattern_type.value
            stats['by_type'][pattern_type] = stats['by_type'].get(pattern_type, 0) + 1
            
            # Count by game phase
            game_phase = pattern.game_phase
            stats['by_game_phase'][game_phase] = stats['by_game_phase'].get(game_phase, 0) + 1
            
            # Accumulate for averages
            total_confidence += pattern.confidence
            total_frequency += pattern.frequency
        
        if len(self.chess_patterns) > 0:
            stats['avg_confidence'] = total_confidence / len(self.chess_patterns)
            stats['avg_frequency'] = total_frequency / len(self.chess_patterns)
        
        return stats
    
    def find_patterns_by_type(self, pattern_type: PatternType) -> List[ChessPattern]:
        """Find all patterns of a specific type."""
        return [p for p in self.chess_patterns if p.pattern_type == pattern_type]
    
    def find_patterns_by_phase(self, game_phase: str) -> List[ChessPattern]:
        """Find all patterns for a specific game phase."""
        return [p for p in self.chess_patterns if p.game_phase == game_phase or p.game_phase == "any"]