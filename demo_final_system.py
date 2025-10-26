#!/usr/bin/env python3
"""
Final demonstration of the Enhanced Chess Pattern System
Shows all working features and capabilities.
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

def demo_pattern_management():
    """Demonstrate pattern management capabilities"""
    print("\n" + "="*60)
    print("🎯 PATTERN MANAGEMENT DEMONSTRATION")
    print("="*60)
    
    try:
        from chess_ai.pattern_manager import PatternManager
        from chess_ai.pattern_detector import ChessPattern
        
        # Initialize manager
        manager = PatternManager("demo_patterns")
        print("✅ PatternManager initialized")
        
        # Create sample patterns
        sample_patterns = [
            ChessPattern(
                fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                move="e4",
                pattern_types=["opening", "tactical_moment"],
                description="Central pawn advance - King's Pawn Opening",
                influencing_pieces=["e4", "d2"],
                evaluation={"before": {"total": 0}, "after": {"total": 10}, "change": 10},
                metadata={"demo": True, "complexity": "simple"}
            ),
            ChessPattern(
                fen="rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2",
                move="Nf3",
                pattern_types=["development", "tactical_moment"],
                description="Knight development - King's Knight Opening",
                influencing_pieces=["g1", "f3"],
                evaluation={"before": {"total": 10}, "after": {"total": 15}, "change": 5},
                metadata={"demo": True, "complexity": "moderate"}
            ),
            ChessPattern(
                fen="r3k2r/ppp2ppp/2n1bn2/2b1p3/2B1P3/2N1BN2/PPP2PPP/R3K2R w KQkq - 0 8",
                move="d5",
                pattern_types=["fork", "tactical_moment"],
                description="Queen fork - Central fork pattern",
                influencing_pieces=["d1", "d5", "c6", "e5"],
                evaluation={"before": {"total": 0}, "after": {"total": 5}, "change": 5},
                metadata={"demo": True, "complexity": "complex"}
            )
        ]
        
        print(f"\n📝 Creating {len(sample_patterns)} sample patterns...")
        pattern_ids = []
        for i, pattern in enumerate(sample_patterns, 1):
            pattern_id = manager.add_pattern(pattern)
            pattern_ids.append(pattern_id)
            print(f"  {i}. {pattern.move} - {', '.join(pattern.pattern_types)} (ID: {pattern_id[:8]}...)")
        
        # Search patterns
        print(f"\n🔍 Searching patterns by type 'tactical_moment':")
        tactical_patterns = manager.search_patterns(pattern_types=["tactical_moment"])
        for pattern in tactical_patterns:
            print(f"  Found: {pattern.move} - {pattern.description}")
        
        # Get statistics
        stats = manager.get_pattern_statistics()
        print(f"\n📊 Pattern Statistics:")
        print(f"  Total patterns: {stats['total_patterns']}")
        print(f"  By type: {stats['by_type']}")
        print(f"  By piece: {stats['by_piece']}")
        
        # Export patterns
        export_path = "demo_patterns_export.json"
        if manager.export_patterns(export_path, pattern_ids):
            print(f"\n📤 Exported patterns to: {export_path}")
        
        # Clean up
        for pattern_id in pattern_ids:
            manager.delete_pattern(pattern_id)
        print(f"\n🧹 Cleaned up {len(pattern_ids)} demo patterns")
        
        print("✅ Pattern management demonstration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Pattern management demo failed: {e}")
        return False

def demo_pattern_filtering():
    """Demonstrate pattern filtering capabilities"""
    print("\n" + "="*60)
    print("🔍 PATTERN FILTERING DEMONSTRATION")
    print("="*60)
    
    try:
        from chess_ai.pattern_filter import PatternFilter
        
        # Initialize filter
        filter_system = PatternFilter()
        print("✅ PatternFilter initialized")
        
        # Create a complex position
        board = chess.Board("r3k2r/ppp2ppp/2n1bn2/2b1p3/2B1P3/2N1BN2/PPP2PPP/R3K2R w KQkq - 0 8")
        print(f"\n📋 Test position: {board.fen()}")
        print("\nBoard visualization:")
        print(board)
        
        # Test different moves
        test_moves = [
            chess.Move.from_uci("d1d5"),  # Queen to center
            chess.Move.from_uci("g1f3"),  # Knight development
            chess.Move.from_uci("e1g1"),  # Castling
        ]
        
        for i, move in enumerate(test_moves, 1):
            if move in board.legal_moves:
                print(f"\n{i}. Analyzing move: {board.san(move)}")
                
                # Analyze pattern relevance
                result = filter_system.analyze_pattern_relevance(
                    board, move, ["tactical_moment", "pin", "fork"]
                )
                
                print(f"   Relevant pieces: {len(result['relevant_pieces'])}")
                print(f"   Irrelevant pieces: {len(result['irrelevant_pieces'])}")
                print(f"   Relevance score: {result.get('relevance_score', 0):.2f}")
                
                # Show pattern analysis
                pattern_analysis = result.get("pattern_analysis", {})
                for pattern_type, analysis in pattern_analysis.items():
                    print(f"   {pattern_type.upper()}: {analysis.get('description', 'No description')}")
                
                # Test exchange detection
                exchange_info = filter_system.detect_exchange_pattern(board, move)
                if exchange_info:
                    print(f"   Exchange detected: {exchange_info.get('exchange_value', 0)} points")
                else:
                    print(f"   No exchange pattern detected")
            else:
                print(f"\n{i}. Move {board.san(move)} is not legal in this position")
        
        print("\n✅ Pattern filtering demonstration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Pattern filtering demo failed: {e}")
        return False

def demo_working_bot():
    """Demonstrate working bot implementation"""
    print("\n" + "="*60)
    print("🤖 WORKING BOT DEMONSTRATION")
    print("="*60)
    
    try:
        from simple_enhanced_bot import make_simple_enhanced_bot
        
        # Initialize bot
        bot = make_simple_enhanced_bot(chess.WHITE)
        print("✅ Simple Enhanced Bot initialized")
        
        # Show bot info
        info = bot.get_agent_info()
        print(f"\n📋 Bot Information:")
        for key, value in info.items():
            print(f"  {key}: {value}")
        
        # Simulate a short game
        board = chess.Board()
        print(f"\n🎮 Simulating a short game...")
        print(f"Initial position: {board.fen()}")
        
        moves_played = 0
        max_moves = 5
        
        while not board.is_game_over() and moves_played < max_moves:
            print(f"\nMove {moves_played + 1}:")
            print(f"  Position: {board.fen()}")
            print(f"  Legal moves: {len(list(board.legal_moves))}")
            
            # Bot chooses move
            move = bot.choose_move(board)
            if move and move in board.legal_moves:
                print(f"  Bot chose: {board.san(move)}")
                board.push(move)
                moves_played += 1
            else:
                print("  Bot couldn't choose a legal move")
                break
        
        print(f"\nFinal position after {moves_played} moves:")
        print(board)
        print(f"Game result: {board.result()}")
        
        print("\n✅ Working bot demonstration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Working bot demo failed: {e}")
        return False

def demo_system_integration():
    """Demonstrate full system integration"""
    print("\n" + "="*60)
    print("🔗 SYSTEM INTEGRATION DEMONSTRATION")
    print("="*60)
    
    try:
        from chess_ai.pattern_manager import PatternManager
        from chess_ai.pattern_detector import PatternDetector
        from chess_ai.pattern_filter import PatternFilter
        from simple_enhanced_bot import make_simple_enhanced_bot
        
        # Initialize all components
        manager = PatternManager("integration_demo")
        detector = PatternDetector()
        filter_system = PatternFilter()
        bot = make_simple_enhanced_bot(chess.WHITE)
        
        print("✅ All system components initialized")
        
        # Simulate a game with pattern detection
        board = chess.Board()
        print(f"\n🎮 Simulating game with pattern detection...")
        print(f"Starting position: {board.fen()}")
        
        move_count = 0
        max_moves = 3
        detected_patterns = []
        
        while not board.is_game_over() and move_count < max_moves:
            print(f"\n--- Move {move_count + 1} ---")
            
            # Bot chooses move
            move = bot.choose_move(board)
            if not move or move not in board.legal_moves:
                print("Bot couldn't choose a legal move")
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
                detected_patterns.append(pattern_id)
                print(f"  Saved as: {pattern_id[:8]}...")
                
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
        print(f"\n📊 Final Statistics:")
        print(f"  Total patterns detected: {stats['total_patterns']}")
        print(f"  Pattern types: {stats['by_type']}")
        print(f"  Patterns by piece: {stats['by_piece']}")
        
        # Clean up
        for pattern_id in detected_patterns:
            manager.delete_pattern(pattern_id)
        print(f"\n🧹 Cleaned up {len(detected_patterns)} detected patterns")
        
        print("\n✅ System integration demonstration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ System integration demo failed: {e}")
        return False

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
        
        print("🧹 Demo files cleaned up")
    except Exception as e:
        print(f"⚠️ Failed to clean up demo files: {e}")

def main():
    """Run all demonstrations"""
    print("🚀 ENHANCED CHESS PATTERN SYSTEM - FINAL DEMONSTRATION")
    print("="*80)
    
    demos = [
        ("Pattern Management", demo_pattern_management),
        ("Pattern Filtering", demo_pattern_filtering),
        ("Working Bot", demo_working_bot),
        ("System Integration", demo_system_integration)
    ]
    
    passed = 0
    total = len(demos)
    
    for name, demo_func in demos:
        try:
            print(f"\n🎯 Starting {name} demonstration...")
            if demo_func():
                passed += 1
                print(f"✅ {name} demonstration completed successfully!")
            else:
                print(f"❌ {name} demonstration failed!")
        except Exception as e:
            print(f"❌ {name} demonstration crashed: {e}")
        
        time.sleep(1)  # Brief pause between demos
    
    # Cleanup
    cleanup_demo_files()
    
    # Final results
    print("\n" + "="*80)
    print(f"🎉 DEMONSTRATION COMPLETE: {passed}/{total} demos passed")
    
    if passed == total:
        print("🎊 ALL DEMONSTRATIONS SUCCESSFUL!")
        print("\n🚀 The Enhanced Chess Pattern System is ready for use!")
        print("   Run 'python3 run_enhanced_viewer.py' to start the interactive viewer.")
    else:
        print(f"⚠️ {total - passed} demonstrations failed.")
        print("   Check the errors above for details.")
    
    print("\n📚 For more information, see:")
    print("   - ENHANCED_SYSTEM_FINAL_README.md")
    print("   - ENHANCED_PATTERN_SYSTEM_README.md")
    print("   - ENHANCED_SYSTEM_QUICK_START.md")

if __name__ == "__main__":
    main()