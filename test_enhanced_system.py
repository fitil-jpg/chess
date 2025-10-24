#!/usr/bin/env python3
"""
Test script for the enhanced chess system integration.

This script tests all components of the enhanced chess viewer system
to ensure proper integration and functionality.
"""

import sys
import logging
from pathlib import Path

# Add workspace to path
workspace_path = Path(__file__).parent
sys.path.insert(0, str(workspace_path))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all required modules can be imported."""
    logger.info("Testing imports...")
    
    try:
        import chess
        logger.info("✓ chess module imported")
    except ImportError as e:
        logger.error(f"✗ Failed to import chess: {e}")
        return False
    
    try:
        import numpy as np
        logger.info("✓ numpy module imported")
    except ImportError as e:
        logger.error(f"✗ Failed to import numpy: {e}")
        return False
    
    try:
        from PySide6.QtWidgets import QApplication
        logger.info("✓ PySide6 module imported")
    except ImportError as e:
        logger.error(f"✗ Failed to import PySide6: {e}")
        return False
    
    return True

def test_chess_ai_modules():
    """Test chess AI module imports."""
    logger.info("Testing chess AI modules...")
    
    try:
        from chess_ai.move_evaluation import MoveEvaluation, MoveEvaluator, create_move_evaluator
        logger.info("✓ move_evaluation module imported")
    except ImportError as e:
        logger.error(f"✗ Failed to import move_evaluation: {e}")
        return False
    
    try:
        from chess_ai.wfc_engine import create_chess_wfc_engine
        logger.info("✓ wfc_engine module imported")
    except ImportError as e:
        logger.error(f"✗ Failed to import wfc_engine: {e}")
        return False
    
    try:
        from chess_ai.bsp_engine import create_chess_bsp_engine
        logger.info("✓ bsp_engine module imported")
    except ImportError as e:
        logger.error(f"✗ Failed to import bsp_engine: {e}")
        return False
    
    try:
        from chess_ai.guardrails import Guardrails
        logger.info("✓ guardrails module imported")
    except ImportError as e:
        logger.error(f"✗ Failed to import guardrails: {e}")
        return False
    
    try:
        from chess_ai.pattern_responder import create_pattern_responder
        logger.info("✓ pattern_responder module imported")
    except ImportError as e:
        logger.error(f"✗ Failed to import pattern_responder: {e}")
        return False
    
    return True

def test_engine_creation():
    """Test that engines can be created successfully."""
    logger.info("Testing engine creation...")
    
    try:
        from chess_ai.wfc_engine import create_chess_wfc_engine
        wfc_engine = create_chess_wfc_engine()
        logger.info("✓ WFC engine created successfully")
    except Exception as e:
        logger.error(f"✗ Failed to create WFC engine: {e}")
        return False
    
    try:
        from chess_ai.bsp_engine import create_chess_bsp_engine
        bsp_engine = create_chess_bsp_engine()
        logger.info("✓ BSP engine created successfully")
    except Exception as e:
        logger.error(f"✗ Failed to create BSP engine: {e}")
        return False
    
    try:
        from chess_ai.guardrails import Guardrails
        guardrails = Guardrails()
        logger.info("✓ Guardrails created successfully")
    except Exception as e:
        logger.error(f"✗ Failed to create Guardrails: {e}")
        return False
    
    try:
        from chess_ai.pattern_responder import create_pattern_responder
        pattern_responder = create_pattern_responder()
        logger.info("✓ Pattern responder created successfully")
    except Exception as e:
        logger.error(f"✗ Failed to create Pattern responder: {e}")
        return False
    
    return True

def test_move_evaluation():
    """Test move evaluation system."""
    logger.info("Testing move evaluation...")
    
    try:
        import chess
        from chess_ai.move_evaluation import create_move_evaluator
        
        # Create test board and move
        board = chess.Board()
        move = chess.Move.from_uci("e2e4")
        
        # Create evaluator
        evaluator = create_move_evaluator()
        
        # Test evaluation
        evaluation = evaluator.evaluate_move(move, board, chess.WHITE)
        
        logger.info(f"✓ Move evaluation completed: {evaluation.get_status_summary()}")
        logger.info(f"  Final value: {evaluation.final_value:.2f}")
        logger.info(f"  Final confidence: {evaluation.final_confidence:.2f}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Move evaluation failed: {e}")
        return False

def test_pattern_matching():
    """Test pattern matching system."""
    logger.info("Testing pattern matching...")
    
    try:
        import chess
        from chess_ai.pattern_responder import create_pattern_responder
        
        # Create pattern responder
        responder = create_pattern_responder()
        
        # Test with starting position
        board = chess.Board()
        action = responder.match(board)
        
        logger.info(f"✓ Pattern matching completed: {action}")
        
        # Test pattern statistics
        stats = responder.get_pattern_statistics()
        logger.info(f"  Pattern statistics: {stats}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Pattern matching failed: {e}")
        return False

def test_wfc_analysis():
    """Test WFC analysis."""
    logger.info("Testing WFC analysis...")
    
    try:
        import chess
        from chess_ai.wfc_engine import create_chess_wfc_engine
        
        # Create WFC engine
        wfc_engine = create_chess_wfc_engine()
        
        # Test with starting position
        board = chess.Board()
        move = chess.Move.from_uci("e2e4")
        
        analysis = wfc_engine.analyze_move(board, move)
        logger.info(f"✓ WFC analysis completed")
        logger.info(f"  Compatible patterns: {len(analysis['compatible_patterns'])}")
        logger.info(f"  Pattern confidence: {analysis['pattern_confidence']:.2f}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ WFC analysis failed: {e}")
        return False

def test_bsp_analysis():
    """Test BSP analysis."""
    logger.info("Testing BSP analysis...")
    
    try:
        import chess
        from chess_ai.bsp_engine import create_chess_bsp_engine
        
        # Create BSP engine
        bsp_engine = create_chess_bsp_engine()
        
        # Test with starting position
        board = chess.Board()
        move = chess.Move.from_uci("e2e4")
        
        analysis = bsp_engine.analyze_move(board, move)
        logger.info(f"✓ BSP analysis completed")
        logger.info(f"  Move zone: {analysis['move_zone'].zone_type if analysis['move_zone'] else 'None'}")
        logger.info(f"  Zone importance: {analysis['zone_importance']:.2f}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ BSP analysis failed: {e}")
        return False

def test_guardrails():
    """Test guardrails system."""
    logger.info("Testing guardrails...")
    
    try:
        import chess
        from chess_ai.guardrails import Guardrails
        
        # Create guardrails
        guardrails = Guardrails()
        
        # Test with starting position
        board = chess.Board()
        move = chess.Move.from_uci("e2e4")
        
        # Test guardrails
        is_legal = guardrails.is_legal_and_sane(board, move)
        is_high_value_hang = guardrails.is_high_value_hang(board, move)
        is_blunder = guardrails.is_blunder(board, move)
        allow_move = guardrails.allow_move(board, move)
        
        logger.info(f"✓ Guardrails testing completed")
        logger.info(f"  Is legal: {is_legal}")
        logger.info(f"  Is high value hang: {is_high_value_hang}")
        logger.info(f"  Is blunder: {is_blunder}")
        logger.info(f"  Allow move: {allow_move}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Guardrails testing failed: {e}")
        return False

def test_ui_creation():
    """Test UI creation (without showing)."""
    logger.info("Testing UI creation...")
    
    try:
        from PySide6.QtWidgets import QApplication
        from enhanced_pyside_viewer import EnhancedChessViewer
        
        # Create QApplication (required for Qt widgets)
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Create viewer (but don't show it)
        viewer = EnhancedChessViewer()
        
        logger.info("✓ UI creation successful")
        
        # Clean up
        viewer.close()
        
        return True
        
    except Exception as e:
        logger.error(f"✗ UI creation failed: {e}")
        return False

def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("Enhanced Chess System Integration Test")
    logger.info("=" * 60)
    
    tests = [
        ("Import Tests", test_imports),
        ("Chess AI Module Tests", test_chess_ai_modules),
        ("Engine Creation Tests", test_engine_creation),
        ("Move Evaluation Tests", test_move_evaluation),
        ("Pattern Matching Tests", test_pattern_matching),
        ("WFC Analysis Tests", test_wfc_analysis),
        ("BSP Analysis Tests", test_bsp_analysis),
        ("Guardrails Tests", test_guardrails),
        ("UI Creation Tests", test_ui_creation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            if test_func():
                logger.info(f"✓ {test_name} PASSED")
                passed += 1
            else:
                logger.error(f"✗ {test_name} FAILED")
        except Exception as e:
            logger.error(f"✗ {test_name} FAILED with exception: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! System is ready to use.")
        return 0
    else:
        logger.error(f"❌ {total - passed} tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())