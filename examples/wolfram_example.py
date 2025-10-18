#!/usr/bin/env python3
"""Example demonstrating Wolfram Engine integration with chess AI.

This script shows how to use WolframBot for chess position analysis
and how to generate heatmaps using the Wolfram Engine.
"""

import chess
from chess_ai.wolfram_bot import WolframBot
from utils.integration import generate_heatmaps, compute_metrics


def main():
    """Demonstrate Wolfram Engine integration."""
    print("♟️  Wolfram Engine Chess AI Demo")
    print("=" * 40)
    
    # Check if Wolfram Engine is available
    try:
        bot = WolframBot(chess.WHITE, evaluation_depth=3)
        print("✅ Wolfram Engine is available")
    except RuntimeError as e:
        print(f"❌ Wolfram Engine not available: {e}")
        print("Please install Wolfram Engine from https://www.wolfram.com/engine/")
        return
    
    # Example 1: Basic move selection
    print("\n📋 Example 1: Basic Move Selection")
    print("-" * 30)
    
    board = chess.Board()
    print(f"Starting position: {board.fen()}")
    
    try:
        move, confidence = bot.choose_move(board, debug=True)
        print(f"WolframBot suggests: {move} (confidence: {confidence:.3f})")
    except Exception as e:
        print(f"Move selection failed: {e}")
    
    # Example 2: Position evaluation
    print("\n📊 Example 2: Position Evaluation")
    print("-" * 30)
    
    # Set up an interesting position
    board = chess.Board("r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 4 4")
    print(f"Position: {board.fen()}")
    
    try:
        evaluation = bot.get_position_evaluation(board)
        if evaluation:
            print("Position analysis:")
            for key, value in evaluation.items():
                if isinstance(value, (int, float)):
                    print(f"  {key}: {value}")
        else:
            print("Position evaluation failed")
    except Exception as e:
        print(f"Position evaluation failed: {e}")
    
    # Example 3: Heatmap generation
    print("\n🗺️  Example 3: Heatmap Generation")
    print("-" * 30)
    
    # Sample positions
    sample_fens = [
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
        "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2"
    ]
    
    print(f"Generating heatmaps for {len(sample_fens)} positions...")
    
    try:
        heatmaps = generate_heatmaps(
            sample_fens,
            pattern_set="wolfram_demo",
            use_wolfram=True
        )
        
        print("✅ Heatmaps generated successfully!")
        print(f"Generated patterns: {list(heatmaps.keys())}")
        
        for pattern, pieces in heatmaps.items():
            print(f"\nPattern '{pattern}':")
            for piece, matrix in pieces.items():
                total_positions = sum(sum(row) for row in matrix)
                print(f"  {piece}: {total_positions} total positions")
                
    except Exception as e:
        print(f"❌ Heatmap generation failed: {e}")
        print("Falling back to R-based generation...")
        
        try:
            heatmaps = generate_heatmaps(
                sample_fens,
                pattern_set="r_demo",
                use_wolfram=False
            )
            print("✅ R-based heatmaps generated successfully!")
        except Exception as e2:
            print(f"❌ R-based generation also failed: {e2}")
    
    # Example 4: Metrics computation
    print("\n📈 Example 4: Metrics Computation")
    print("-" * 30)
    
    try:
        metrics = compute_metrics(board.fen())
        print("Position metrics:")
        
        for category, category_metrics in metrics.items():
            print(f"\n{category}:")
            for metric, value in category_metrics.items():
                if isinstance(value, (int, float)):
                    print(f"  {metric}: {value}")
                    
    except Exception as e:
        print(f"Metrics computation failed: {e}")
    
    # Example 5: Bot comparison
    print("\n🤖 Example 5: Bot Comparison")
    print("-" * 30)
    
    try:
        from chess_ai.aggressive_bot import AggressiveBot
        from chess_ai.fortify_bot import FortifyBot
        
        aggressive_bot = AggressiveBot(chess.WHITE)
        fortify_bot = FortifyBot(chess.WHITE)
        
        # Compare move suggestions
        wolfram_move, wolfram_conf = bot.choose_move(board)
        aggressive_move, aggressive_conf = aggressive_bot.choose_move(board)
        fortify_move, fortify_conf = fortify_bot.choose_move(board)
        
        print("Move suggestions:")
        print(f"  WolframBot:    {wolfram_move} (confidence: {wolfram_conf:.3f})")
        print(f"  AggressiveBot: {aggressive_move} (confidence: {aggressive_conf:.3f})")
        print(f"  FortifyBot:    {fortify_move} (confidence: {fortify_conf:.3f})")
        
    except Exception as e:
        print(f"Bot comparison failed: {e}")
    
    print("\n🎉 Demo completed!")
    print("\nFor more information, see:")
    print("- WOLFRAM_SETUP.md for installation instructions")
    print("- chess_ai/wolfram_bot.py for WolframBot implementation")
    print("- analysis/heatmaps/generate_heatmaps.wl for Wolfram heatmap script")


if __name__ == "__main__":
    main()