#!/usr/bin/env python3
"""
Simple test for Enhanced DynamicBot
"""

import sys
import os
from pathlib import Path
import chess
import logging

# Add the workspace to Python path
workspace_root = Path(__file__).parent
sys.path.insert(0, str(workspace_root))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_simple_bot():
    """Simple test for Enhanced DynamicBot"""
    try:
        from chess_ai.enhanced_dynamic_bot import make_enhanced_dynamic_bot
        
        # Initialize bot
        bot = make_enhanced_dynamic_bot(chess.WHITE)
        
        # Test bot info
        info = bot.get_agent_info()
        print(f"Bot info: {info}")
        
        # Test move selection
        board = chess.Board()
        print(f"Initial position: {board.fen()}")
        print(f"Legal moves: {[board.san(move) for move in list(board.legal_moves)[:5]]}")
        
        move = bot.choose_move(board)
        print(f"Bot chose: {move}")
        
        if move:
            print(f"Move is legal: {move in board.legal_moves}")
            if move in board.legal_moves:
                print(f"Move in SAN: {board.san(move)}")
                print("✅ Bot test passed")
                return True
            else:
                print("❌ Bot chose illegal move")
                return False
        else:
            print("❌ Bot failed to choose a move")
            return False
            
    except Exception as e:
        logger.error(f"❌ Bot test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_bot()
    sys.exit(0 if success else 1)