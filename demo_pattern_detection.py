#!/usr/bin/env python3
"""
Demo script showing pattern detection during bot games (CLI version).
This shows how the pattern system works without GUI.
"""

import sys
import chess
from chess_ai.bot_agent import make_agent
from chess_ai.pattern_detector import PatternDetector, PatternType
from chess_ai.pattern_storage import PatternCatalog
from evaluation import evaluate

def play_game_with_pattern_detection(num_games=3):
    """Play games and detect patterns"""
    
    print("🎯 Pattern Detection Demo")
    print("=" * 60)
    print(f"Playing {num_games} games with pattern detection")
    print("Using RandomBot vs RandomBot for quick demonstration")
    print("=" * 60)
    
    # Initialize agents - use RandomBot for simplicity in demo
    white_agent = make_agent("RandomBot", chess.WHITE)
    black_agent = make_agent("RandomBot", chess.BLACK)
    
    # Initialize pattern detector
    detector = PatternDetector()
    catalog = PatternCatalog("patterns/demo_catalog.json")
    
    all_patterns = []
    
    for game_num in range(num_games):
        print(f"\n📋 Game {game_num + 1}/{num_games}")
        print("-" * 60)
        
        board = chess.Board()
        move_count = 0
        max_moves = 30  # Limit moves per game (reduced for demo)
        game_patterns = []
        
        while not board.is_game_over() and move_count < max_moves:
            # Get evaluation before move
            eval_before, eval_details_before = evaluate(board)
            eval_before_dict = {"total": eval_before, **eval_details_before}
            
            # Choose move
            mover_color = board.turn
            agent = white_agent if mover_color == chess.WHITE else black_agent
            
            try:
                move = agent.choose_move(board)
                if move is None or not board.is_legal(move):
                    break
                
                # Get move in SAN before pushing
                move_san = board.san(move)
                
                # Push move
                board.push(move)
                move_count += 1
                
                # Get evaluation after move
                eval_after, eval_details_after = evaluate(board)
                eval_after_dict = {"total": eval_after, **eval_details_after}
                
                # Detect patterns
                patterns = detector.detect_patterns(
                    board,
                    move,
                    eval_before_dict,
                    eval_after_dict
                )
                
                # If patterns detected, print them
                if patterns:
                    for pattern in patterns:
                        pattern.metadata["game_id"] = game_num
                        pattern.metadata["move_number"] = move_count
                        game_patterns.append(pattern)
                        all_patterns.append(pattern)
                        
                        print(f"\n  🎯 Pattern detected at move {move_count}!")
                        print(f"     Move: {move_san}")
                        print(f"     Types: {', '.join(pattern.pattern_types[:3])}")
                        print(f"     Description: {pattern.description}")
                        print(f"     Eval change: {pattern.evaluation.get('change', 0):.1f}")
                        
            except Exception as e:
                import traceback
                print(f"  ⚠️  Error at move {move_count}: {e}")
                traceback.print_exc()  # Show detailed error
                break
        
        # Game summary
        result = board.result()
        print(f"\n  Game result: {result}")
        print(f"  Moves played: {move_count}")
        print(f"  Patterns found: {len(game_patterns)}")
    
    # Overall summary
    print("\n" + "=" * 60)
    print("📊 Detection Summary")
    print("=" * 60)
    print(f"Total patterns detected: {len(all_patterns)}")
    
    if all_patterns:
        # Count by type
        type_counts = {}
        for pattern in all_patterns:
            for pt in pattern.pattern_types:
                type_counts[pt] = type_counts.get(pt, 0) + 1
        
        print("\nPatterns by type:")
        for pattern_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            print(f"  {pattern_type}: {count}")
        
        # Save patterns
        catalog.clear_patterns()
        for pattern in all_patterns:
            catalog.add_pattern(pattern)
        catalog.save_patterns()
        
        print(f"\n✓ Patterns saved to patterns/demo_catalog.json")
        
        # Show a few examples
        print("\n📝 Example patterns:")
        for i, pattern in enumerate(all_patterns[:3], 1):
            print(f"\n  Example {i}:")
            print(f"    Move: {pattern.move}")
            print(f"    Types: {', '.join(pattern.pattern_types)}")
            print(f"    FEN: {pattern.fen[:50]}...")
            print(f"    Influencing pieces: {len(pattern.influencing_pieces)}")
    else:
        print("  No patterns detected in these games.")
        print("  Try running with stronger bots or more games.")
    
    print("\n" + "=" * 60)
    print("Demo complete!")
    print("\nTo view patterns in GUI:")
    print("  python3 run_pattern_editor.py")
    print("\nTo test the system:")
    print("  python3 test_pattern_system.py")
    print("=" * 60)

def main():
    """Main function"""
    import sys
    
    num_games = 3
    if len(sys.argv) > 1:
        try:
            num_games = int(sys.argv[1])
        except ValueError:
            print("Usage: python3 demo_pattern_detection.py [num_games]")
            return 1
    
    play_game_with_pattern_detection(num_games)
    return 0

if __name__ == "__main__":
    sys.exit(main())
