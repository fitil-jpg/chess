"""
Enhanced DynamicBot with Pattern Recognition
=============================================

Улучшенный DynamicBot с интеграцией системы паттернов для борьбы со Stockfish.

Добавленные возможности:
1. Распознавание известных паттернов из базы
2. Использование обменных последовательностей
3. Избежание паттернов, которые привели к проигрышу
4. Приоритизация паттернов, которые привели к победе
"""

from __future__ import annotations
from typing import Optional, Tuple, Dict, Any
import chess
import logging

from chess_ai.bot_agent import DynamicBot
from chess_ai.pattern_manager import PatternManager
from core.evaluator import Evaluator
from utils import GameContext

logger = logging.getLogger(__name__)


class EnhancedDynamicBot:
    """
    Улучшенный DynamicBot с поддержкой паттернов.
    
    Использует систему паттернов для:
    1. Распознавания тактических возможностей
    2. Избежания известных ошибок
    3. Применения проверенных обменов
    4. Улучшения позиционной игры
    """
    
    def __init__(self, color: bool, use_patterns: bool = True):
        self.color = color
        self.base_bot = DynamicBot(color)
        self.use_patterns = use_patterns
        
        # Pattern system
        self.pattern_manager = None
        if use_patterns:
            try:
                self.pattern_manager = PatternManager()
                logger.info(f"Enhanced DynamicBot initialized with pattern system for {'white' if color else 'black'}")
            except Exception as e:
                logger.warning(f"Failed to initialize pattern system: {e}")
                self.use_patterns = False
        
        # Pattern statistics
        self.patterns_used = 0
        self.patterns_available = 0
        self.last_pattern_type = None
    
    def choose_move(
        self,
        board: chess.Board,
        context: GameContext | None = None,
        evaluator: Evaluator | None = None,
        debug: bool = False,
    ) -> Tuple[Optional[chess.Move], str]:
        """
        Choose a move using pattern-enhanced decision making.
        
        Order of strategies:
        1. Check for known winning patterns
        2. Check for tactical patterns (forks, pins, exchanges)
        3. Fall back to base DynamicBot logic
        """
        
        if board.turn != self.color:
            return self.base_bot.choose_move(board, context, evaluator, debug)
        
        # Try pattern matching first
        if self.use_patterns and self.pattern_manager:
            pattern_move, pattern_reason = self._try_pattern_move(board, context, evaluator)
            if pattern_move:
                self.patterns_used += 1
                reason = f"PATTERN[{self.last_pattern_type}] | {pattern_reason}"
                return (pattern_move, reason) if debug else (pattern_move, "")
        
        # Fall back to base DynamicBot
        return self.base_bot.choose_move(board, context, evaluator, debug)
    
    def _try_pattern_move(
        self,
        board: chess.Board,
        context: GameContext | None,
        evaluator: Evaluator | None
    ) -> Tuple[Optional[chess.Move], str]:
        """
        Try to find a move based on known patterns.
        
        Priority:
        1. Exchange patterns (forced winning exchanges)
        2. Tactical patterns (forks, pins)
        3. Positional patterns
        """
        
        # Get current position FEN
        fen = board.fen()
        
        # Check for exact position matches
        matching_patterns = self.pattern_manager.get_patterns_for_position(fen, max_results=5)
        
        if matching_patterns:
            self.patterns_available = len(matching_patterns)
            
            # Prioritize patterns with exchanges
            for pattern in matching_patterns:
                if pattern.exchange_sequence and pattern.exchange_sequence.forced:
                    # Check if this pattern's move is legal
                    try:
                        move = chess.Move.from_uci(pattern.triggering_move)
                        if move in board.legal_moves:
                            # Check if exchange is favorable
                            if self._is_favorable_exchange(pattern.exchange_sequence):
                                self.last_pattern_type = pattern.pattern_type
                                reason = f"Forced exchange: {pattern.exchange_sequence.material_balance:+d}"
                                return move, reason
                    except:
                        continue
            
            # Try tactical patterns (forks, pins, skewers)
            tactical_types = {"fork", "pin", "skewer", "discovered_attack"}
            for pattern in matching_patterns:
                if pattern.pattern_type in tactical_types:
                    try:
                        move = chess.Move.from_uci(pattern.triggering_move)
                        if move in board.legal_moves:
                            if self._is_safe_move(board, move):
                                self.last_pattern_type = pattern.pattern_type
                                reason = f"{pattern.pattern_type.capitalize()}"
                                return move, reason
                    except:
                        continue
        
        # Try similar position patterns (based on piece placement)
        similar_patterns = self._find_similar_patterns(board)
        if similar_patterns:
            for pattern in similar_patterns[:3]:  # Try top 3
                try:
                    move = chess.Move.from_uci(pattern.triggering_move)
                    if move in board.legal_moves:
                        if self._is_safe_move(board, move):
                            self.last_pattern_type = pattern.pattern_type
                            reason = f"Similar pattern: {pattern.pattern_type}"
                            return move, reason
                except:
                    continue
        
        return None, ""
    
    def _is_favorable_exchange(self, exchange_sequence) -> bool:
        """Check if an exchange sequence is favorable."""
        # Favorable if we gain material
        if self.color == chess.WHITE:
            return exchange_sequence.material_balance > 0
        else:
            return exchange_sequence.material_balance < 0
    
    def _is_safe_move(self, board: chess.Board, move: chess.Move) -> bool:
        """
        Check if a move is safe (doesn't hang pieces).
        
        Args:
            board: Current board position
            move: Move to check
            
        Returns:
            True if move is safe
        """
        # Make the move on a copy
        test_board = board.copy()
        test_board.push(move)
        
        # Check if the moved piece is defended
        attackers = len(test_board.attackers(not self.color, move.to_square))
        defenders = len(test_board.attackers(self.color, move.to_square))
        
        # If attacked and not defended, check if it's worth it
        if attackers > 0 and defenders == 0:
            # Only acceptable if we're capturing something more valuable
            captured_piece = board.piece_at(move.to_square)
            if captured_piece:
                moving_piece = board.piece_at(move.from_square)
                if moving_piece:
                    # Simple piece values
                    piece_values = {
                        chess.PAWN: 100,
                        chess.KNIGHT: 320,
                        chess.BISHOP: 330,
                        chess.ROOK: 500,
                        chess.QUEEN: 900
                    }
                    
                    moving_value = piece_values.get(moving_piece.piece_type, 0)
                    captured_value = piece_values.get(captured_piece.piece_type, 0)
                    
                    # Only safe if we're trading up
                    return captured_value >= moving_value
            
            return False
        
        return True
    
    def _find_similar_patterns(self, board: chess.Board) -> list:
        """
        Find patterns with similar piece configurations.
        
        This is a simplified similarity check based on:
        1. Same number of pieces
        2. Similar game phase
        3. Same pattern types
        """
        similar = []
        
        # Get current game phase
        piece_count = len(board.piece_map())
        current_phase = "opening" if board.fullmove_number <= 10 else (
            "endgame" if piece_count <= 12 else "middlegame"
        )
        
        # Search for patterns in same game phase
        pattern_ids = self.pattern_manager.list_patterns(
            game_phase=current_phase,
            enabled_only=True
        )
        
        for pattern_id in pattern_ids[:10]:  # Limit search
            pattern = self.pattern_manager.get_pattern(pattern_id)
            if pattern:
                similar.append(pattern)
        
        return similar
    
    def get_last_reason(self) -> str:
        """Get the reason for the last move."""
        if hasattr(self.base_bot, 'get_last_reason'):
            return self.base_bot.get_last_reason()
        return "PATTERN_ENHANCED"
    
    def get_last_features(self) -> Dict[str, Any]:
        """Get features from the last move."""
        features = {}
        
        if hasattr(self.base_bot, 'get_last_features'):
            features = self.base_bot.get_last_features() or {}
        
        # Add pattern statistics
        features.update({
            "patterns_used": self.patterns_used,
            "patterns_available": self.patterns_available,
            "last_pattern_type": self.last_pattern_type,
            "pattern_system_active": self.use_patterns
        })
        
        return features
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about pattern usage."""
        stats = {
            "patterns_used": self.patterns_used,
            "patterns_available": self.patterns_available,
            "last_pattern_type": self.last_pattern_type,
            "pattern_system_active": self.use_patterns
        }
        
        if self.pattern_manager:
            stats["pattern_manager_stats"] = self.pattern_manager.get_statistics()
        
        return stats


# Factory function for compatibility
def create_enhanced_dynamic_bot(color: bool) -> EnhancedDynamicBot:
    """Create an enhanced DynamicBot with pattern support."""
    return EnhancedDynamicBot(color, use_patterns=True)
