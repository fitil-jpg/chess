#!/usr/bin/env python3
"""
Test script for Enhanced Bot statistics functionality.
"""

import logging
import chess
from chess_ai.enhanced_dynamic_bot import EnhancedDynamicBot

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_enhanced_bot_stats():
    """Test Enhanced Bot statistics tracking."""
    
    print("🤖 Testing Enhanced Bot Statistics")
    print("=" * 50)
    
    # Create Enhanced Bot
    bot = EnhancedDynamicBot(chess.WHITE)
    
    # Create test board
    board = chess.Board()
    
    print(f"Initial stats: {bot.get_stats_summary()}")
    
    # Make some moves to generate statistics
    for i in range(5):
        move, confidence = bot.choose_move(board, debug=True)
        if move:
            board.push(move)
            print(f"Move {i+1}: {move} (confidence: {confidence:.3f})")
        else:
            print(f"Move {i+1}: No move available")
            break
    
    print(f"\nFinal stats: {bot.get_stats_summary()}")
    
    # Test reset
    print("\nResetting stats...")
    bot.reset_stats()
    print(f"After reset: {bot.get_stats_summary()}")
    
    print("\n✅ Enhanced Bot stats test completed!")

if __name__ == "__main__":
    test_enhanced_bot_stats()