#!/usr/bin/env python3
"""
Quick game logger script - minimal setup for testing the logging system.

Usage:
    python scripts/quick_game_logger.py --white RandomBot --black AggressiveBot --moves 50
"""

import argparse
import time
import chess
from datetime import datetime

# Import the logging system
from utils.game_logger import GameLogger
from utils.game_analytics import quick_summary

# Import some bots for testing
try:
    from chess_ai.random_bot import RandomBot
    from chess_ai.aggressive_bot import AggressiveBot
    from chess_ai.fortify_bot import FortifyBot
    from evaluation import evaluate
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the chess project root")
    exit(1)


def play_game_with_logging(white_bot_class, black_bot_class, max_moves: int = 50):
    """Play a game with full logging."""
    
    # Initialize logger
    logger = GameLogger()
    
    # Create bots
    white_bot = white_bot_class(chess.WHITE)
    black_bot = black_bot_class(chess.BLACK)
    
    # Start logging
    game_id = logger.start_game(
        white_bot=white_bot_class.__name__,
        black_bot=black_bot_class.__name__,
        time_control=f"max_{max_moves}_moves"
    )
    
    print(f"Started game: {game_id}")
    
    # Play the game
    board = chess.Board()
    move_count = 0
    
    while not board.is_game_over() and move_count < max_moves:
        # Get current bot
        current_bot = white_bot if board.turn == chess.WHITE else black_bot
        
        # Time the move
        start_time = time.time()
        move, confidence = current_bot.choose_move(board)
        think_time = time.time() - start_time
        
        if move is None:
            break
        
        # Evaluate position
        try:
            eval_score, _ = evaluate(board)
        except:
            eval_score = 0.0
        
        # Log the move
        logger.log_move(move, board, confidence, think_time, eval_score)
        
        # Make the move
        board.push(move)
        move_count += 1
        
        print(f"Move {move_count}: {move.uci()} (conf: {confidence:.2f}, time: {think_time*1000:.0f}ms)")
    
    # Determine result
    if board.is_game_over():
        result = board.result(claim_draw=True)
        if board.is_checkmate():
            termination = "checkmate"
        elif board.is_stalemate():
            termination = "stalemate"
        elif board.is_insufficient_material():
            termination = "insufficient_material"
        else:
            termination = "draw_rule"
    else:
        result = "*"
        termination = "move_limit"
    
    # End and save game
    game_data = logger.end_game(result, termination)
    
    print(f"\nGame completed: {result} ({termination})")
    print(f"Total moves: {move_count}")
    print(f"Duration: {game_data['duration_seconds']:.1f}s")
    
    return game_data


def main():
    parser = argparse.ArgumentParser(description="Quick game logger with chess bots")
    parser.add_argument("--white", default="RandomBot", help="White bot class name")
    parser.add_argument("--black", default="AggressiveBot", help="Black bot class name")
    parser.add_argument("--moves", type=int, default=50, help="Maximum moves")
    parser.add_argument("--games", type=int, default=1, help="Number of games to play")
    parser.add_argument("--summary", action="store_true", help="Show summary after games")
    
    args = parser.parse_args()
    
    # Map bot names to classes
    bot_classes = {
        "RandomBot": RandomBot,
        "AggressiveBot": AggressiveBot,
        "FortifyBot": FortifyBot,
    }
    
    white_bot_class = bot_classes.get(args.white, RandomBot)
    black_bot_class = bot_classes.get(args.black, RandomBot)
    
    print(f"Playing {args.games} game(s): {args.white} vs {args.black}")
    print("=" * 50)
    
    # Play games
    all_games = []
    for i in range(args.games):
        print(f"\n--- Game {i+1}/{args.games} ---")
        game_data = play_game_with_logging(white_bot_class, black_bot_class, args.moves)
        all_games.append(game_data)
    
    # Show summary
    if args.summary and args.games > 1:
        print("\n" + "=" * 50)
        print("TOURNAMENT SUMMARY")
        print("=" * 50)
        
        results = {}
        total_moves = 0
        total_time = 0
        
        for game in all_games:
            result = game["result"]
            results[result] = results.get(result, 0) + 1
            total_moves += game["total_moves"]
            total_time += game["duration_seconds"]
        
        print(f"Results: {dict(results)}")
        print(f"Average moves per game: {total_moves/len(all_games):.1f}")
        print(f"Average duration: {total_time/len(all_games):.1f}s")
        
        # Show quick analytics summary
        print("\n" + quick_summary())


if __name__ == "__main__":
    main()
