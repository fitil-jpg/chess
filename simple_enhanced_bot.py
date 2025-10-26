#!/usr/bin/env python3
"""
Simplified Enhanced DynamicBot for testing
"""

import chess
import random
from typing import Optional

class SimpleEnhancedBot:
    """Simplified version of Enhanced DynamicBot"""
    
    def __init__(self, color: chess.Color):
        self.color = color
        self.move_count = 0
    
    def choose_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Choose a move using simple analysis"""
        try:
            self.move_count += 1
            
            # Get all legal moves
            legal_moves = list(board.legal_moves)
            if not legal_moves:
                return None
            
            # Simple evaluation: prefer center moves and development
            scored_moves = []
            for move in legal_moves:
                score = self._evaluate_move(board, move)
                scored_moves.append((score, move))
            
            # Sort by score (descending)
            scored_moves.sort(key=lambda x: x[0], reverse=True)
            
            # Select from top 3 moves
            top_moves = scored_moves[:3]
            if not top_moves:
                return random.choice(legal_moves)
            
            # Random selection from top moves
            selected_score, selected_move = random.choice(top_moves)
            return selected_move
            
        except Exception as e:
            print(f"Error in choose_move: {e}")
            return random.choice(list(board.legal_moves)) if board.legal_moves else None
    
    def _evaluate_move(self, board: chess.Board, move: chess.Move) -> float:
        """Simple move evaluation"""
        score = 0.0
        
        # Center control
        center_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
        if move.to_square in center_squares:
            score += 1.0
        
        # Development
        if board.piece_at(move.from_square) and board.piece_at(move.from_square).piece_type in [chess.KNIGHT, chess.BISHOP]:
            score += 0.5
        
        # Captures
        if board.is_capture(move):
            score += 0.3
        
        # Checks
        if board.gives_check(move):
            score += 0.2
        
        # Random factor for variety
        score += random.random() * 0.1
        
        return score
    
    def get_agent_info(self):
        """Get bot information"""
        return {
            "name": "SimpleEnhancedBot",
            "version": "1.0",
            "color": "white" if self.color == chess.WHITE else "black",
            "move_count": self.move_count
        }

def make_simple_enhanced_bot(color: chess.Color):
    """Factory function"""
    return SimpleEnhancedBot(color)