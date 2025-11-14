#!/usr/bin/env python3
"""
Test script for the new hierarchical CriticalBot system.
Demonstrates the delegation to AggressiveBot, PawnBot, and KingValueBot.
"""

import chess
import logging
from chess_ai.critical_bot import CriticalBot
from chess_ai.pawn_bot import PawnBot
from chess_ai.king_value_bot import KingValueBot
from chess_ai.aggressive_bot import AggressiveBot
from core.evaluator import Evaluator
from utils import GameContext

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_hierarchical_delegation():
    """Test the hierarchical delegation system."""
    
    print("=== Testing Hierarchical CriticalBot System ===\n")
    
    # Create test positions
    test_positions = [
        # Opening position - should delegate to PawnBot
        ("Opening Position", chess.Board(), "pawn"),
        
        # Position with tactical opportunities - should delegate to AggressiveBot
        ("Tactical Position", create_tactical_position(), "aggressive"),
        
        # Endgame position - should delegate to KingValueBot
        ("Endgame Position", create_endgame_position(), "king"),
    ]
    
    color = chess.WHITE
    
    for description, board, expected_delegate in test_positions:
        print(f"--- {description} ---")
        print(f"FEN: {board.fen()}")
        
        # Test hierarchical CriticalBot
        critical_bot = CriticalBot(color, enable_hierarchy=True)
        evaluator = Evaluator(board)
        context = GameContext(material_diff=0, mobility=0, king_safety=0)
        
        move, score = critical_bot.choose_move(board, context, evaluator, debug=True)
        
        if move:
            print(f"Selected move: {board.san(move)} (score: {score:.1f})")
        else:
            print("No move selected")
        
        # Test individual sub-bots for comparison
        print("\nSub-bot analysis:")
        sub_bots = {
            "AggressiveBot": AggressiveBot(color),
            "PawnBot": PawnBot(color), 
            "KingValueBot": KingValueBot(color, enable_heatmaps=True)
        }
        
        for bot_name, bot in sub_bots.items():
            try:
                sub_move, sub_score = bot.choose_move(board, context, evaluator, debug=False)
                if sub_move:
                    print(f"  {bot_name}: {board.san(sub_move)} (score: {sub_score:.1f})")
                else:
                    print(f"  {bot_name}: No move")
            except Exception as e:
                print(f"  {bot_name}: Error - {e}")
        
        print("\n" + "="*50 + "\n")

def create_tactical_position() -> chess.Board:
    """Create a position with tactical opportunities."""
    # Simple position with a capture opportunity
    fen = "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 4"
    return chess.Board(fen)

def create_endgame_position() -> chess.Board:
    """Create an endgame position."""
    # King and pawn endgame
    fen = "8/8/8/8/8/4k3/4P3/4K3 w - - 0 1"
    return chess.Board(fen)

def test_pawn_bot_heuristics():
    """Test PawnBot specific heuristics."""
    
    print("=== Testing PawnBot Heuristics ===\n")
    
    # Test doubled pawns
    board = chess.Board("rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2")
    pawn_bot = PawnBot(chess.WHITE)
    evaluator = Evaluator(board)
    context = GameContext(material_diff=0, mobility=0, king_safety=0)
    
    print("Testing doubled pawn creation:")
    print(f"FEN: {board.fen()}")
    
    for move in list(board.legal_moves)[:5]:  # Test first 5 moves
        score, reason = pawn_bot.evaluate_move(board, move, context)
        print(f"  {board.san(move)}: {score:.1f} - {reason}")
    
    print("\n" + "="*50 + "\n")

def test_king_value_bot_heatmaps():
    """Test KingValueBot heatmap integration."""
    
    print("=== Testing KingValueBot Heatmap Integration ===\n")
    
    # Position with king in center
    board = chess.Board("rnbqk2r/pppp1ppp/5n2/2b1p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 4")
    king_bot = KingValueBot(chess.WHITE, enable_heatmaps=True)
    evaluator = Evaluator(board)
    context = GameContext(material_diff=0, mobility=0, king_safety=0)
    
    print("Testing king zone heatmap analysis:")
    print(f"FEN: {board.fen()}")
    
    # Test best king zone move
    best_move, best_score = king_bot.get_best_king_zone_move(board, context)
    if best_move:
        print(f"Best king zone move: {board.san(best_move)} (score: {best_score:.1f})")
    else:
        print("No king zone improvements found")
    
    # Evaluate a few moves
    for move in list(board.legal_moves)[:5]:
        score, reason = king_bot.evaluate_move(board, move, context)
        print(f"  {board.san(move)}: {score:.1f} - {reason}")
    
    print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    try:
        test_hierarchical_delegation()
        test_pawn_bot_heuristics()
        test_king_value_bot_heatmaps()
        
        print("=== All tests completed ===")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
