#!/usr/bin/env python3
"""
Test script for the Enhanced Chess Pattern System
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import chess
import logging
from chess_ai.enhanced_pattern_detector import EnhancedPatternDetector
from chess_ai.enhanced_dynamic_bot import EnhancedDynamicBot
from chess_ai.pattern_manager import PatternManager
from pathlib import Path
import chess
import logging

# Add the workspace to Python path
workspace_root = Path(__file__).parent
sys.path.insert(0, str(workspace_root))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_pattern_manager():
    """Test the PatternManager functionality"""
    logger.info("Testing PatternManager...")
    
    try:
        from chess_ai.pattern_manager import PatternManager
        from chess_ai.pattern_detector import ChessPattern
        
        # Initialize manager
        manager = PatternManager("test_patterns")
        
        # Create a test pattern
        test_pattern = ChessPattern(
            fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            move="e4",
            pattern_types=["tactical_moment", "opening"],
            description="Test pattern for system validation",
            influencing_pieces=["e4", "d2"],
            evaluation={"before": {"total": 0}, "after": {"total": 10}, "change": 10},
            metadata={"test": True, "created_by": "test_script"}
        )
        
        # Add pattern
        pattern_id = manager.add_pattern(test_pattern)
        logger.info(f"Added pattern with ID: {pattern_id}")
        
        # Retrieve pattern
        retrieved = manager.get_pattern(pattern_id)
        assert retrieved is not None, "Failed to retrieve pattern"
        assert retrieved.move == "e4", "Retrieved pattern has wrong move"
        logger.info("Pattern retrieval test passed")
        
        # Search patterns
        search_results = manager.search_patterns(pattern_types=["tactical_moment"])
        assert len(search_results) >= 1, "Search did not find the test pattern"
        logger.info(f"Search test passed: found {len(search_results)} patterns")
        
        # Get statistics
        stats = manager.get_pattern_statistics()
        assert stats["total_patterns"] >= 1, "Statistics show no patterns"
        logger.info(f"Statistics test passed: {stats['total_patterns']} total patterns")
        
        # Clean up
        manager.delete_pattern(pattern_id)
        logger.info("Pattern deletion test passed")
        
        logger.info("✅ PatternManager tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ PatternManager test failed: {e}")
        return False

def test_pattern_filter():
    """Test the PatternFilter functionality"""
    logger.info("Testing PatternFilter...")
    
    try:
        from chess_ai.pattern_filter import PatternFilter
        
        # Initialize filter
        filter_system = PatternFilter()
        
        # Create a test board and move
        board = chess.Board()
        move = chess.Move.from_uci("e2e4")
        
        # Test pattern relevance analysis
        result = filter_system.analyze_pattern_relevance(
            board, move, ["tactical_moment"]
        )
        
        assert "relevant_pieces" in result, "Result missing relevant_pieces"
        assert "irrelevant_pieces" in result, "Result missing irrelevant_pieces"
        assert "filtered_fen" in result, "Result missing filtered_fen"
        assert "pattern_analysis" in result, "Result missing pattern_analysis"
        
        logger.info("Pattern relevance analysis test passed")
        
        # Test exchange pattern detection
        exchange_info = filter_system.detect_exchange_pattern(board, move)
        # Exchange detection might return None for this simple position
        logger.info("Exchange pattern detection test completed")
        
        # Test complexity determination
        complexity = filter_system.get_pattern_complexity(result)
        assert complexity in ["simple", "moderate", "complex"], f"Invalid complexity: {complexity}"
        logger.info(f"Complexity determination test passed: {complexity}")
        
        logger.info("✅ PatternFilter tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ PatternFilter test failed: {e}")
        return False

def test_enhanced_dynamic_bot():
    """Test the Enhanced DynamicBot functionality"""
    logger.info("Testing Enhanced DynamicBot...")
    
    try:
        from chess_ai.enhanced_dynamic_bot import make_enhanced_dynamic_bot
        
        # Initialize bot
        bot = make_enhanced_dynamic_bot(chess.WHITE)
        
        # Test bot info
        info = bot.get_agent_info()
        assert "name" in info, "Bot info missing name"
        assert "version" in info, "Bot info missing version"
        assert "color" in info, "Bot info missing color"
        logger.info("Bot info test passed")
        
        # Test move selection
        board = chess.Board()
        move = bot.choose_move(board)
        
        assert move is not None, "Bot failed to choose a move"
        assert move in board.legal_moves, "Bot chose an illegal move"
        logger.info(f"Move selection test passed: {board.san(move)}")
        
        # Test move analysis (without making the move)
        eval_before = bot._evaluate_position(board)
        logger.info(f"Position evaluation test passed: {eval_before}")
        
        logger.info("✅ Enhanced DynamicBot tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Enhanced DynamicBot test failed: {e}")
        return False

def test_pattern_detector():
    """Test the PatternDetector functionality"""
    logger.info("Testing PatternDetector...")
    
    try:
        from chess_ai.pattern_detector import PatternDetector
        
        # Initialize detector
        detector = PatternDetector()
        
        # Create a test board and move
        board = chess.Board()
        move = chess.Move.from_uci("e2e4")
        
        # Test pattern detection
        patterns = detector.detect_patterns(
            board, move, {"total": 0}, {"total": 10}
        )
        
        assert isinstance(patterns, list), "Pattern detection should return a list"
        logger.info(f"Pattern detection test passed: found {len(patterns)} patterns")
        
        # Test individual pattern properties
        for pattern in patterns:
            assert hasattr(pattern, 'fen'), "Pattern missing fen"
            assert hasattr(pattern, 'move'), "Pattern missing move"
            assert hasattr(pattern, 'pattern_types'), "Pattern missing pattern_types"
            assert hasattr(pattern, 'evaluation'), "Pattern missing evaluation"
        
        logger.info("✅ PatternDetector tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ PatternDetector test failed: {e}")
        return False

def test_integration():
    """Test integration between components"""
    logger.info("Testing system integration...")
    
    try:
        from chess_ai.pattern_manager import PatternManager
        from chess_ai.pattern_detector import PatternDetector
        from chess_ai.pattern_filter import PatternFilter
        from chess_ai.enhanced_dynamic_bot import make_enhanced_dynamic_bot
        
        # Initialize all components
        manager = PatternManager("test_patterns")
        detector = PatternDetector()
        filter_system = PatternFilter()
        bot = make_enhanced_dynamic_bot(chess.WHITE)
        
        # Simulate a game move
        board = chess.Board()
        move = chess.Move.from_uci("e2e4")
        
        # Detect patterns
        patterns = detector.detect_patterns(board, move, {"total": 0}, {"total": 10})
        
        # Process each pattern
        for pattern in patterns:
            # Save to manager
            pattern_id = manager.add_pattern(pattern)
            
            # Apply filtering
            filter_result = filter_system.analyze_pattern_relevance(
                board, move, pattern.pattern_types
            )
            
            # Check exchange patterns
            exchange_info = filter_system.detect_exchange_pattern(board, move)
            
            logger.info(f"Processed pattern {pattern_id}: {pattern.move}")
        
        # Test bot move selection
        bot_move = bot.choose_move(board)
        assert bot_move is not None, "Bot integration test failed"
        
        logger.info("✅ Integration tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        return False

def cleanup_test_files():
    """Clean up test files"""
    try:
        import shutil
        test_dir = Path("test_patterns")
        if test_dir.exists():
            shutil.rmtree(test_dir)
        logger.info("Test files cleaned up")
    except Exception as e:
        logger.warning(f"Failed to clean up test files: {e}")

def main():
    """Run all tests"""
    logger.info("Starting Enhanced Chess Pattern System tests...")
    
    tests = [
        test_pattern_detector,
        test_pattern_manager,
        test_pattern_filter,
        test_enhanced_dynamic_bot,
        test_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            logger.error(f"Test {test.__name__} crashed: {e}")
    
    # Cleanup
    cleanup_test_files()
    
    # Results
    logger.info(f"\n{'='*50}")
    logger.info(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! The enhanced system is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed")

if __name__ == "__main__":
    main()