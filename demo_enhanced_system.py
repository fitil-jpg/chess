#!/usr/bin/env python3
"""
Demo script for the Enhanced Chess Pattern System
Shows pattern detection, filtering, and management in action.
"""

import sys
import os
from pathlib import Path
import chess
import logging
import time

# Add the workspace to Python path
workspace_root = Path(__file__).parent
sys.path.insert(0, str(workspace_root))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def demo_pattern_detection():
    """Demonstrate pattern detection capabilities"""
    logger.info("🎯 Pattern Detection Demo")
    print("=" * 50)
    
    try:
        from chess_ai.pattern_detector import PatternDetector
        
        detector = PatternDetector()
        
        # Create a position with tactical potential
        board = chess.Board("rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2")
        
        print(f"Position: {board.fen()}")
        print(f"Legal moves: {[board.san(move) for move in board.legal_moves[:5]]}...")
        
        # Test different moves
        test_moves = [
            chess.Move.from_uci("d2d4"),  # Central pawn advance
            chess.Move.from_uci("g1f3"),  # Knight development
            chess.Move.from_uci("f1c4"),  # Bishop development
        ]
        
        for move in test_moves:
            if move in board.legal_moves:
                print(f"\nAnalyzing move: {board.san(move)}")
                
                # Simulate evaluation change
                eval_before = {"total": 0}
                eval_after = {"total": 15}  # Simulate improvement
                
                patterns = detector.detect_patterns(board, move, eval_before, eval_after)
                
                if patterns:
                    for pattern in patterns:
                        print(f"  Pattern: {', '.join(pattern.pattern_types)}")
                        print(f"  Description: {pattern.description}")
                        print(f"  Evaluation change: {pattern.evaluation.get('change', 0)}")
                else:
                    print("  No patterns detected")
        
        print("\n✅ Pattern detection demo completed")
        
    except Exception as e:
        logger.error(f"❌ Pattern detection demo failed: {e}")

def demo_pattern_filtering():
    """Demonstrate pattern filtering capabilities"""
    logger.info("🔍 Pattern Filtering Demo")
    print("=" * 50)
    
    try:
        from chess_ai.pattern_filter import PatternFilter
        
        filter_system = PatternFilter()
        
        # Create a complex position
        board = chess.Board("r3k2r/ppp2ppp/2n1bn2/2b1p3/2B1P3/2N1BN2/PPP2PPP/R3K2R w KQkq - 0 8")
        
        print(f"Position: {board.fen()}")
        print("\nBoard visualization:")
        print(board)
        
        # Test a tactical move
        move = chess.Move.from_uci("d1d5")  # Queen to center
        print(f"\nAnalyzing move: {board.san(move)}")
        
        # Analyze pattern relevance
        result = filter_system.analyze_pattern_relevance(
            board, move, ["tactical_moment", "pin", "fork"]
        )
        
        print(f"\nFiltering Results:")
        print(f"  Relevant pieces: {len(result['relevant_pieces'])}")
        print(f"  Irrelevant pieces: {len(result['irrelevant_pieces'])}")
        print(f"  Relevance score: {result.get('relevance_score', 0):.2f}")
        
        # Show pattern analysis
        pattern_analysis = result.get("pattern_analysis", {})
        for pattern_type, analysis in pattern_analysis.items():
            print(f"\n  {pattern_type.upper()} Analysis:")
            for key, value in analysis.items():
                if key != "relevant_squares":
                    print(f"    {key}: {value}")
        
        # Test exchange detection
        exchange_info = filter_system.detect_exchange_pattern(board, move)
        if exchange_info:
            print(f"\n  Exchange Pattern:")
            print(f"    Value: {exchange_info.get('exchange_value', 0)}")
            print(f"    Forced: {exchange_info.get('is_forced', False)}")
        else:
            print(f"\n  No exchange pattern detected")
        
        print("\n✅ Pattern filtering demo completed")
        
    except Exception as e:
        logger.error(f"❌ Pattern filtering demo failed: {e}")

def demo_pattern_management():
    """Demonstrate pattern management capabilities"""
    logger.info("📚 Pattern Management Demo")
    print("=" * 50)
    
    try:
        from chess_ai.pattern_manager import PatternManager
        from chess_ai.pattern_detector import ChessPattern
        
        manager = PatternManager("demo_patterns")
        
        # Create some sample patterns
        sample_patterns = [
            ChessPattern(
                fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                move="e4",
                pattern_types=["opening", "tactical_moment"],
                description="Central pawn advance",
                influencing_pieces=["e4", "d2"],
                evaluation={"before": {"total": 0}, "after": {"total": 10}, "change": 10},
                metadata={"demo": True}
            ),
            ChessPattern(
                fen="rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2",
                move="Nf3",
                pattern_types=["development", "tactical_moment"],
                description="Knight development",
                influencing_pieces=["g1", "f3"],
                evaluation={"before": {"total": 10}, "after": {"total": 15}, "change": 5},
                metadata={"demo": True}
            ),
            ChessPattern(
                fen="r3k2r/ppp2ppp/2n1bn2/2b1p3/2B1P3/2N1BN2/PPP2PPP/R3K2R w KQkq - 0 8",
                move="d5",
                pattern_types=["fork", "tactical_moment"],
                description="Queen fork",
                influencing_pieces=["d1", "d5", "c6", "e5"],
                evaluation={"before": {"total": 0}, "after": {"total": 5}, "change": 5},
                metadata={"demo": True}
            )
        ]
        
        print("Adding sample patterns...")
        pattern_ids = []
        for pattern in sample_patterns:
            pattern_id = manager.add_pattern(pattern)
            pattern_ids.append(pattern_id)
            print(f"  Added: {pattern.move} -> {pattern_id}")
        
        # Search patterns
        print(f"\nSearching patterns by type 'tactical_moment':")
        tactical_patterns = manager.search_patterns(pattern_types=["tactical_moment"])
        for pattern in tactical_patterns:
            print(f"  Found: {pattern.move} - {', '.join(pattern.pattern_types)}")
        
        # Get statistics
        stats = manager.get_pattern_statistics()
        print(f"\nPattern Statistics:")
        print(f"  Total patterns: {stats['total_patterns']}")
        print(f"  By type: {stats['by_type']}")
        print(f"  By piece: {stats['by_piece']}")
        
        # Export patterns
        export_path = "demo_patterns_export.json"
        if manager.export_patterns(export_path, pattern_ids):
            print(f"\nExported patterns to: {export_path}")
        
        # Clean up
        for pattern_id in pattern_ids:
            manager.delete_pattern(pattern_id)
        print(f"\nCleaned up {len(pattern_ids)} demo patterns")
        
        print("\n✅ Pattern management demo completed")
        
    except Exception as e:
        logger.error(f"❌ Pattern management demo failed: {e}")

def demo_enhanced_bot():
    """Demonstrate Enhanced DynamicBot capabilities"""
    logger.info("🤖 Enhanced DynamicBot Demo")
    print("=" * 50)
    
    try:
        from chess_ai.enhanced_dynamic_bot import make_enhanced_dynamic_bot
        
        # Initialize bot
        bot = make_enhanced_dynamic_bot(chess.WHITE)
        
        print("Bot Information:")
        info = bot.get_agent_info()
        for key, value in info.items():
            print(f"  {key}: {value}")
        
        # Simulate a game
        board = chess.Board()
        print(f"\nStarting position: {board.fen()}")
        
        moves_played = 0
        max_moves = 5
        
        while not board.is_game_over() and moves_played < max_moves:
            print(f"\nMove {moves_played + 1}:")
            print(f"  Position: {board.fen()}")
            print(f"  Legal moves: {len(list(board.legal_moves))}")
            
            # Bot chooses move
            move = bot.choose_move(board)
            if move:
                print(f"  Bot chose: {board.san(move)}")
                board.push(move)
                moves_played += 1
            else:
                print("  Bot couldn't choose a move")
                break
        
        print(f"\nFinal position after {moves_played} moves:")
        print(board)
        print(f"Game result: {board.result()}")
        
        print("\n✅ Enhanced DynamicBot demo completed")
        
    except Exception as e:
        logger.error(f"❌ Enhanced DynamicBot demo failed: {e}")

def demo_integration():
    """Demonstrate full system integration"""
    logger.info("🔗 System Integration Demo")
    print("=" * 50)
    
    try:
        from chess_ai.pattern_manager import PatternManager
        from chess_ai.pattern_detector import PatternDetector
        from chess_ai.pattern_filter import PatternFilter
        from chess_ai.enhanced_dynamic_bot import make_enhanced_dynamic_bot
        
        # Initialize all components
        manager = PatternManager("integration_demo")
        detector = PatternDetector()
        filter_system = PatternFilter()
        bot = make_enhanced_dynamic_bot(chess.WHITE)
        
        print("Initialized all system components")
        
        # Simulate a game with pattern detection
        board = chess.Board()
        move_count = 0
        max_moves = 3
        
        print(f"\nSimulating game with pattern detection...")
        
        while not board.is_game_over() and move_count < max_moves:
            print(f"\n--- Move {move_count + 1} ---")
            
            # Bot chooses move
            move = bot.choose_move(board)
            if not move:
                break
            
            print(f"Move: {board.san(move)}")
            
            # Simulate evaluation
            eval_before = {"total": 0}
            eval_after = {"total": 10 + move_count * 5}
            
            # Detect patterns
            patterns = detector.detect_patterns(board, move, eval_before, eval_after)
            print(f"Detected {len(patterns)} patterns")
            
            # Process each pattern
            for pattern in patterns:
                print(f"  Pattern: {', '.join(pattern.pattern_types)}")
                
                # Save to manager
                pattern_id = manager.add_pattern(pattern)
                print(f"  Saved as: {pattern_id}")
                
                # Apply filtering
                filter_result = filter_system.analyze_pattern_relevance(
                    board, move, pattern.pattern_types
                )
                print(f"  Relevance score: {filter_result.get('relevance_score', 0):.2f}")
                
                # Check for exchanges
                exchange_info = filter_system.detect_exchange_pattern(board, move)
                if exchange_info:
                    print(f"  Exchange detected: {exchange_info.get('exchange_value', 0)} points")
            
            # Make the move
            board.push(move)
            move_count += 1
        
        # Show final statistics
        stats = manager.get_pattern_statistics()
        print(f"\nFinal Statistics:")
        print(f"  Total patterns detected: {stats['total_patterns']}")
        print(f"  Pattern types: {stats['by_type']}")
        
        # Clean up
        all_patterns = manager.search_patterns()
        for pattern in all_patterns:
            if pattern.metadata.get("id"):
                manager.delete_pattern(pattern.metadata["id"])
        
        print("\n✅ System integration demo completed")
        
    except Exception as e:
        logger.error(f"❌ System integration demo failed: {e}")

def cleanup_demo_files():
    """Clean up demo files"""
    try:
        import shutil
        demo_dirs = ["demo_patterns", "integration_demo"]
        for demo_dir in demo_dirs:
            if Path(demo_dir).exists():
                shutil.rmtree(demo_dir)
        
        demo_files = ["demo_patterns_export.json"]
        for demo_file in demo_files:
            if Path(demo_file).exists():
                Path(demo_file).unlink()
        
        logger.info("Demo files cleaned up")
    except Exception as e:
        logger.warning(f"Failed to clean up demo files: {e}")

def main():
    """Run all demos"""
    logger.info("🚀 Starting Enhanced Chess Pattern System Demo")
    print("=" * 60)
    
    demos = [
        demo_pattern_detection,
        demo_pattern_filtering,
        demo_pattern_management,
        demo_enhanced_bot,
        demo_integration
    ]
    
    for demo in demos:
        try:
            demo()
            print("\n" + "=" * 60)
            time.sleep(1)  # Brief pause between demos
        except Exception as e:
            logger.error(f"Demo {demo.__name__} failed: {e}")
            print("\n" + "=" * 60)
    
    # Cleanup
    cleanup_demo_files()
    
    print("\n🎉 All demos completed!")
    print("To run the interactive viewer, use: python run_enhanced_viewer.py")

if __name__ == "__main__":
    main()