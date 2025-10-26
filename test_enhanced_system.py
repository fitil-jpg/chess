#!/usr/bin/env python3
"""
Test script for enhanced pattern detection and DynamicBot system.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import chess
import logging
from chess_ai.enhanced_pattern_detector import EnhancedPatternDetector
from chess_ai.enhanced_dynamic_bot import EnhancedDynamicBot
from chess_ai.pattern_manager import PatternManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_pattern_detection():
    """Test enhanced pattern detection"""
    print("Testing Enhanced Pattern Detection...")
    
    detector = EnhancedPatternDetector()
    manager = PatternManager()
    
    # Create a test position with a fork
    board = chess.Board("rnbqkb1r/pppp1ppp/5n2/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 2 3")
    move = chess.Move.from_uci("f6e4")  # Knight fork
    
    # Detect patterns
    patterns = detector.detect_patterns(
        board, move, 
        {"total": 0}, 
        {"total": 300}
    )
    
    print(f"Detected {len(patterns)} patterns")
    for pattern in patterns:
        print(f"  - {pattern.pattern_types}: {pattern.description}")
        
    return len(patterns) > 0

def test_enhanced_dynamic_bot():
    """Test Enhanced DynamicBot"""
    print("\nTesting Enhanced DynamicBot...")
    
    bot = EnhancedDynamicBot(chess.BLACK)
    
    # Test position
    board = chess.Board()
    
    # Get move
    move, confidence = bot.choose_move(board)
    
    print(f"Bot chose move: {move}")
    print(f"Confidence: {confidence:.3f}")
    print(f"Reason: {bot.get_last_reason()}")
    print(f"Features: {bot.get_last_features()}")
    
    return move is not None

def test_pattern_manager():
    """Test pattern management system"""
    print("\nTesting Pattern Manager...")
    
    manager = PatternManager()
    
    # Create a test pattern
    pattern_id = manager.create_custom_pattern(
        fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        move="e4",
        pattern_types=["opening_trick"],
        description="Test opening move",
        evaluation={"before": {"total": 0}, "after": {"total": 20}, "change": 20}
    )
    
    print(f"Created pattern with ID: {pattern_id}")
    
    # Get statistics
    stats = manager.get_pattern_statistics()
    print(f"Pattern statistics: {stats}")
    
    return pattern_id is not None

def main():
    """Run all tests"""
    print("Enhanced Chess System Test")
    print("=" * 40)
    
    tests = [
        ("Pattern Detection", test_pattern_detection),
        ("Enhanced DynamicBot", test_enhanced_dynamic_bot),
        ("Pattern Manager", test_pattern_manager)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"✅ {test_name}: {'PASSED' if result else 'FAILED'}")
        except Exception as e:
            results.append((test_name, False))
            print(f"❌ {test_name}: FAILED - {e}")
    
    print("\n" + "=" * 40)
    print("Test Summary:")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed")

if __name__ == "__main__":
    main()