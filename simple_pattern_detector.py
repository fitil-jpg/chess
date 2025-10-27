#!/usr/bin/env python3
"""
Simple pattern detection system for chess games.
Detects basic patterns without complex dependencies.
"""

import chess
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SimplePattern:
    """Simple chess pattern representation"""
    fen: str
    move: str
    pattern_types: List[str]
    description: str
    evaluation: Dict[str, Any]
    metadata: Dict[str, Any]


class SimplePatternDetector:
    """Simple pattern detector for basic chess patterns"""
    
    def __init__(self):
        self.patterns_detected = []
    
    def detect_patterns(self, board: chess.Board, move: chess.Move) -> List[SimplePattern]:
        """Detect patterns in the current position"""
        patterns = []
        
        # Check for basic patterns
        if self._is_capture(board, move):
            patterns.append(self._create_capture_pattern(board, move))
        
        if self._is_check(board, move):
            patterns.append(self._create_check_pattern(board, move))
        
        if self._is_castling(board, move):
            patterns.append(self._create_castling_pattern(board, move))
        
        if self._is_promotion(board, move):
            patterns.append(self._create_promotion_pattern(board, move))
        
        if self._is_center_control(board, move):
            patterns.append(self._create_center_control_pattern(board, move))
        
        if self._is_development(board, move):
            patterns.append(self._create_development_pattern(board, move))
        
        return patterns
    
    def _is_capture(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move is a capture"""
        return board.is_capture(move)
    
    def _is_check(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move gives check"""
        # Create a copy of the board to test the move
        test_board = board.copy()
        test_board.push(move)
        return test_board.is_check()
    
    def _is_castling(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move is castling"""
        return board.is_castling(move)
    
    def _is_promotion(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move is a promotion"""
        # Check if move is to/from promotion squares
        return (chess.square_rank(move.to_square) in [0, 7] and 
                board.piece_at(move.from_square) and 
                board.piece_at(move.from_square).piece_type == chess.PAWN)
    
    def _is_center_control(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move controls center squares"""
        center_squares = [chess.E4, chess.E5, chess.D4, chess.D5]
        return move.to_square in center_squares
    
    def _is_development(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move develops a piece"""
        piece = board.piece_at(move.from_square)
        if piece is None:
            return False
        
        # Check if moving from starting position
        if piece.piece_type == chess.PAWN:
            # Pawn moves from rank 2 (white) or 7 (black)
            return (chess.square_rank(move.from_square) == 1 and piece.color == chess.WHITE) or \
                   (chess.square_rank(move.from_square) == 6 and piece.color == chess.BLACK)
        elif piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
            # Minor pieces from back rank
            return (chess.square_rank(move.from_square) == 0 and piece.color == chess.WHITE) or \
                   (chess.square_rank(move.from_square) == 7 and piece.color == chess.BLACK)
        
        return False
    
    def _create_capture_pattern(self, board: chess.Board, move: chess.Move) -> SimplePattern:
        """Create capture pattern"""
        captured_piece = board.piece_at(move.to_square)
        piece_values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, 
                       chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}
        
        captured_value = piece_values.get(captured_piece.piece_type, 0) if captured_piece else 0
        
        return SimplePattern(
            fen=board.fen(),
            move=move.uci(),
            pattern_types=["capture"],
            description=f"Captures {captured_piece.symbol() if captured_piece else 'piece'} (value: {captured_value})",
            evaluation={"captured_value": captured_value},
            metadata={"pattern_type": "capture", "captured_piece": captured_piece.symbol() if captured_piece else None}
        )
    
    def _create_check_pattern(self, board: chess.Board, move: chess.Move) -> SimplePattern:
        """Create check pattern"""
        return SimplePattern(
            fen=board.fen(),
            move=move.uci(),
            pattern_types=["check"],
            description="Gives check to opponent king",
            evaluation={"check": True},
            metadata={"pattern_type": "check"}
        )
    
    def _create_castling_pattern(self, board: chess.Board, move: chess.Move) -> SimplePattern:
        """Create castling pattern"""
        side = "kingside" if move.to_square > move.from_square else "queenside"
        return SimplePattern(
            fen=board.fen(),
            move=move.uci(),
            pattern_types=["castling"],
            description=f"{side} castling",
            evaluation={"castling": side},
            metadata={"pattern_type": "castling", "side": side}
        )
    
    def _create_promotion_pattern(self, board: chess.Board, move: chess.Move) -> SimplePattern:
        """Create promotion pattern"""
        # Default to queen promotion if not specified
        promoted_to = "Q"  # Default promotion
        return SimplePattern(
            fen=board.fen(),
            move=move.uci(),
            pattern_types=["promotion"],
            description=f"Pawn promotion to {promoted_to}",
            evaluation={"promotion": promoted_to},
            metadata={"pattern_type": "promotion", "promoted_to": promoted_to}
        )
    
    def _create_center_control_pattern(self, board: chess.Board, move: chess.Move) -> SimplePattern:
        """Create center control pattern"""
        return SimplePattern(
            fen=board.fen(),
            move=move.uci(),
            pattern_types=["center_control"],
            description="Controls center square",
            evaluation={"center_control": True},
            metadata={"pattern_type": "center_control", "square": chess.square_name(move.to_square)}
        )
    
    def _create_development_pattern(self, board: chess.Board, move: chess.Move) -> SimplePattern:
        """Create development pattern"""
        piece = board.piece_at(move.from_square)
        return SimplePattern(
            fen=board.fen(),
            move=move.uci(),
            pattern_types=["development"],
            description=f"Develops {piece.symbol()} from starting position",
            evaluation={"development": True},
            metadata={"pattern_type": "development", "piece": piece.symbol()}
        )


class SimplePatternStorage:
    """Simple pattern storage system"""
    
    def __init__(self, directory: str):
        self.directory = directory
        import os
        os.makedirs(directory, exist_ok=True)
    
    def save_pattern(self, pattern: SimplePattern):
        """Save a pattern to file"""
        import json
        import os
        
        # Convert pattern to dictionary
        pattern_dict = {
            "fen": pattern.fen,
            "move": pattern.move,
            "pattern_types": pattern.pattern_types,
            "description": pattern.description,
            "evaluation": pattern.evaluation,
            "metadata": pattern.metadata
        }
        
        # Save to file
        filename = f"{self.directory}/pattern_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
        with open(filename, 'w') as f:
            json.dump(pattern_dict, f, indent=2)
    
    def save_patterns(self, patterns: List[SimplePattern]):
        """Save multiple patterns to files"""
        for pattern in patterns:
            self.save_pattern(pattern)