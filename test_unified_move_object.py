#!/usr/bin/env python3
"""
Test script for the unified Move Object implementation.

This script demonstrates the key features of the unified MoveObject
that combines both implementations.
"""

import sys
import os

# Add the workspace to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_move_object_creation():
    """Test basic move object creation."""
    print("=== Testing Move Object Creation ===")
    
    try:
        from core.move_object import (
            MoveObject, MovePhase, MoveStatus, MethodStatus,
            create_move_object, move_evaluation_manager
        )
        print("✓ Successfully imported unified move object classes")
        
        # Test enum values
        print(f"✓ MovePhase values: {[phase.value for phase in MovePhase]}")
        print(f"✓ MoveStatus values: {[status.value for status in MoveStatus]}")
        print(f"✓ MethodStatus values: {[status.value for status in MethodStatus]}")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_move_object_functionality():
    """Test move object functionality."""
    print("\n=== Testing Move Object Functionality ===")
    
    try:
        from core.move_object import MoveObject, MovePhase, MethodStatus
        import chess
        
        # Create a test board and move
        board = chess.Board()
        move = chess.Move.from_uci("e2e4")
        
        # Create move object
        move_obj = MoveObject(
            move=move,
            board_fen=board.fen(),
            move_number=board.fullmove_number,
            color=board.turn
        )
        
        print(f"✓ Created MoveObject for move: {move.uci()}")
        print(f"✓ Current phase: {move_obj.current_phase.value}")
        print(f"✓ Status: {move_obj.status.value}")
        
        # Test phase transitions
        move_obj.start_phase(MovePhase.PATTERN_MATCHING)
        print(f"✓ Started pattern matching phase")
        
        # Test method results
        move_obj.add_method_result(
            "PatternResponder",
            MethodStatus.COMPLETED,
            value=75.0,
            active=True,
            confidence=0.8,
            reason="Found opening pattern"
        )
        print(f"✓ Added method result")
        
        # Test pattern matching
        move_obj.add_pattern_match(
            "opening",
            {"name": "King's Pawn Opening", "confidence": 0.9},
            confidence=0.9
        )
        print(f"✓ Added pattern match")
        
        # Test score calculation
        move_obj.pattern_score = 75.0
        move_obj.tactical_score = 60.0
        move_obj.positional_score = 80.0
        final_score = move_obj.calculate_final_score()
        print(f"✓ Calculated final score: {final_score:.2f}")
        
        # Test visualization data
        viz_data = move_obj.get_visualization_data()
        print(f"✓ Visualization data keys: {list(viz_data.keys())}")
        
        # Test summary
        summary = move_obj.get_evaluation_summary()
        print(f"✓ Evaluation summary: {summary}")
        
        return True
        
    except Exception as e:
        print(f"✗ Functionality test failed: {e}")
        return False

def test_move_evaluation_manager():
    """Test move evaluation manager."""
    print("\n=== Testing Move Evaluation Manager ===")
    
    try:
        from core.move_object import move_evaluation_manager
        import chess
        
        # Create test board and move
        board = chess.Board()
        move = chess.Move.from_uci("e2e4")
        
        # Create move evaluation
        move_eval = move_evaluation_manager.create_move_evaluation(move, board, "TestBot")
        print(f"✓ Created move evaluation: {move_eval.move.uci()}")
        
        # Add some test data
        move_eval.add_method_result(
            "TestMethod",
            MethodStatus.COMPLETED,
            value=50.0,
            active=True
        )
        
        # Finalize move
        move_eval.finalize_evaluation(50.0, "Test evaluation", 0.8)
        move_evaluation_manager.finalize_current_move()
        
        print(f"✓ Finalized move evaluation")
        print(f"✓ Move history length: {len(move_evaluation_manager.move_history)}")
        
        # Test statistics
        stats = move_evaluation_manager.export_evaluation_data()
        print(f"✓ Exported evaluation data with keys: {list(stats.keys())}")
        
        return True
        
    except Exception as e:
        print(f"✗ Manager test failed: {e}")
        return False

def test_backward_compatibility():
    """Test backward compatibility with existing code."""
    print("\n=== Testing Backward Compatibility ===")
    
    try:
        # Test that old imports still work
        from chess_ai.move_evaluation import MoveEvaluation, MoveEvaluator, create_move_evaluator
        print("✓ Successfully imported from chess_ai.move_evaluation")
        
        # Test that MoveEvaluation is actually MoveObject
        from core.move_object import MoveObject
        assert MoveEvaluation is MoveObject, "MoveEvaluation should be an alias for MoveObject"
        print("✓ MoveEvaluation is correctly aliased to MoveObject")
        
        # Test factory function
        evaluator = create_move_evaluator()
        print(f"✓ Created move evaluator: {type(evaluator).__name__}")
        
        return True
        
    except Exception as e:
        print(f"✗ Backward compatibility test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Testing Unified Move Object Implementation")
    print("=" * 50)
    
    tests = [
        test_move_object_creation,
        test_move_object_functionality,
        test_move_evaluation_manager,
        test_backward_compatibility
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The unified move object is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)