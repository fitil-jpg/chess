from __future__ import annotations

import logging
logger = logging.getLogger(__name__)

import chess
from typing import Tuple, Optional

from .chess_bot import ChessBot
from utils import GameContext
from core.evaluator import Evaluator


class PawnBot(ChessBot):
    """Bot that focuses on pawn structure optimization.
    
    Specializes in:
    - Creating and maintaining doubled pawns
    - Positioning pawns near the opponent's king
    - Pawn chain formation
    - Passed pawn creation
    """
    
    def __init__(self, color: bool, doubled_pawn_bonus: float = 50.0, 
                 king_pressure_bonus: float = 80.0) -> None:
        super().__init__(color)
        self.doubled_pawn_bonus = doubled_pawn_bonus
        self.king_pressure_bonus = king_pressure_bonus
    
    def evaluate_move(self, board: chess.Board, move: chess.Move, 
                     context: GameContext | None = None) -> Tuple[float, str]:
        """Evaluate move based on pawn structure considerations."""
        base_score, reason = super().evaluate_move(board, move, context)
        
        piece = board.piece_at(move.from_square)
        if not piece or piece.piece_type != chess.PAWN:
            return base_score, reason
        
        score = base_score
        reasons = [reason] if reason else []
        
        tmp = board.copy(stack=False)
        tmp.push(move)
        
        # 1) Doubled pawn creation bonus
        doubled_bonus = self._evaluate_doubled_pawns(tmp, move)
        if doubled_bonus > 0:
            score += doubled_bonus
            reasons.append(f"doubled pawns (+{doubled_bonus})")
        
        # 2) Pawn pressure on opponent king
        king_pressure = self._evaluate_king_pressure(tmp, move)
        if king_pressure > 0:
            score += king_pressure
            reasons.append(f"king pressure (+{king_pressure})")
        
        # 3) Passed pawn potential
        passed_bonus = self._evaluate_passed_pawn_potential(tmp, move)
        if passed_bonus > 0:
            score += passed_bonus
            reasons.append(f"passed pawn (+{passed_bonus})")
        
        # 4) Pawn chain formation
        chain_bonus = self._evaluate_pawn_chains(tmp, move)
        if chain_bonus > 0:
            score += chain_bonus
            reasons.append(f"pawn chain (+{chain_bonus})")
        
        final_reason = " | ".join(reasons) if reasons else "pawn structure"
        return score, final_reason
    
    def _evaluate_doubled_pawns(self, board: chess.Board, move: chess.Move) -> float:
        """Evaluate bonus for creating doubled pawns on same file."""
        if board.piece_at(move.to_square) is None:  # Not a capture
            to_file = chess.square_file(move.to_square)
            
            # Count pawns on this file for current color
            pawns_on_file = 0
            for square in chess.SQUARES:
                piece = board.piece_at(square)
                if piece and piece.piece_type == chess.PAWN and piece.color == self.color:
                    if chess.square_file(square) == to_file:
                        pawns_on_file += 1
            
            # Bonus for having 2+ pawns on same file
            if pawns_on_file >= 2:
                return self.doubled_pawn_bonus * (pawns_on_file - 1)
        
        return 0.0
    
    def _evaluate_king_pressure(self, board: chess.Board, move: chess.Move) -> float:
        """Evaluate pawn pressure on opponent king area."""
        opponent_king_square = board.king(not self.color)
        if opponent_king_square is None:
            return 0.0
        
        pawn_square = move.to_square
        
        # Distance from pawn to opponent king
        file_dist = abs(chess.square_file(pawn_square) - chess.square_file(opponent_king_square))
        rank_dist = abs(chess.square_rank(pawn_square) - chess.square_rank(opponent_king_square))
        total_distance = file_dist + rank_dist
        
        # Bonus based on proximity (closer = more pressure)
        if total_distance <= 2:
            return self.king_pressure_bonus
        elif total_distance <= 3:
            return self.king_pressure_bonus * 0.6
        elif total_distance <= 4:
            return self.king_pressure_bonus * 0.3
        
        return 0.0
    
    def _evaluate_passed_pawn_potential(self, board: chess.Board, move: chess.Move) -> float:
        """Evaluate potential for creating passed pawns."""
        pawn_square = move.to_square
        pawn_rank = chess.square_rank(pawn_square)
        
        # Check if pawn is advanced (closer to promotion)
        if self.color == chess.WHITE:
            advancement_bonus = pawn_rank * 10  # White: higher rank = better
        else:
            advancement_bonus = (7 - pawn_rank) * 10  # Black: lower rank = better
        
        # Check for clear path ahead
        file = chess.square_file(pawn_square)
        has_obstacles = False
        
        if self.color == chess.WHITE:
            # Check squares ahead of white pawn
            for rank in range(pawn_rank + 1, 8):
                square = chess.square(file, rank)
                piece = board.piece_at(square)
                if piece and piece.piece_type == chess.PAWN:
                    has_obstacles = True
                    break
        else:
            # Check squares ahead of black pawn
            for rank in range(pawn_rank - 1, -1, -1):
                square = chess.square(file, rank)
                piece = board.piece_at(square)
                if piece and piece.piece_type == chess.PAWN:
                    has_obstacles = True
                    break
        
        if not has_obstacles:
            return advancement_bonus * 1.5  # Extra bonus for clear path
        
        return advancement_bonus * 0.5
    
    def _evaluate_pawn_chains(self, board: chess.Board, move: chess.Move) -> float:
        """Evaluate bonus for creating pawn chains."""
        pawn_square = move.to_square
        file = chess.square_file(pawn_square)
        rank = chess.square_rank(pawn_square)
        
        chain_bonus = 0.0
        
        # Check for supporting pawns on adjacent files
        for adj_file in [file - 1, file + 1]:
            if 0 <= adj_file < 8:
                # Look for supporting pawn one rank behind
                if self.color == chess.WHITE:
                    support_rank = rank - 1
                    if 0 <= support_rank < 8:
                        support_square = chess.square(adj_file, support_rank)
                        piece = board.piece_at(support_square)
                        if piece and piece.piece_type == chess.PAWN and piece.color == self.color:
                            chain_bonus += 25.0
                else:
                    support_rank = rank + 1
                    if 0 <= support_rank < 8:
                        support_square = chess.square(adj_file, support_rank)
                        piece = board.piece_at(support_square)
                        if piece and piece.piece_type == chess.PAWN and piece.color == self.color:
                            chain_bonus += 25.0
        
        return chain_bonus


__all__ = ["PawnBot"]
