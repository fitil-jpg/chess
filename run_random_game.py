#!/usr/bin/env python3
"""
Script to run a chess match between two RandomBot agents with console output
and pattern saving to a "random_games" catalog.
"""

import chess
import json
import os
from datetime import datetime
from typing import List, Dict, Any

# Import the bots
from chess_ai.random_bot import RandomBot
from evaluation import evaluate

# Import pattern detection and saving
try:
    from chess_ai.pattern_detector import PatternDetector, ChessPattern
    from chess_ai.pattern_storage import PatternStorage
    PATTERN_SAVING_AVAILABLE = True
except ImportError:
    try:
        from chess_ai.enhanced_pattern_system import EnhancedPatternDetector
        from chess_ai.pattern_storage import PatternStorage
        PATTERN_SAVING_AVAILABLE = True
    except ImportError:
        try:
            from simple_pattern_detector import SimplePatternDetector, SimplePatternStorage
            PATTERN_SAVING_AVAILABLE = True
        except ImportError:
            PATTERN_SAVING_AVAILABLE = False
            print("Warning: Pattern saving not available. Install required dependencies.")


class RandomGameRunner:
    def __init__(self, save_patterns: bool = True):
        self.save_patterns = save_patterns and PATTERN_SAVING_AVAILABLE
        self.patterns_detected = []
        
        if self.save_patterns:
            try:
                self.pattern_detector = PatternDetector()
                self.pattern_storage = PatternStorage("patterns/random_games")
            except:
                try:
                    self.pattern_detector = SimplePatternDetector()
                    self.pattern_storage = SimplePatternStorage("patterns/random_games")
                except:
                    self.pattern_detector = None
                    self.pattern_storage = None
            # Create random_games directory if it doesn't exist
            os.makedirs("patterns/random_games", exist_ok=True)
        
    def run_game(self, max_plies: int = 50) -> Dict[str, Any]:
        """Run a single game between two RandomBot agents."""
        board = chess.Board()
        white_bot = RandomBot(chess.WHITE, temperature=1.0)
        black_bot = RandomBot(chess.BLACK, temperature=1.0)
        
        game_data = {
            "start_fen": board.fen(),
            "moves": [],
            "result": None,
            "reason": None,
            "patterns_detected": [],
            "total_plies": 0
        }
        
        print("=== RANDOM BOT GAME ===")
        print(f"Start FEN: {board.fen()}")
        print()
        
        ply = 0
        while not board.is_game_over() and ply < max_plies:
            side = "White" if board.turn == chess.WHITE else "Black"
            bot = white_bot if board.turn == chess.WHITE else black_bot
            
            # Get move from bot
            move, confidence = bot.choose_move(board)
            if move is None:
                break
                
            # Evaluate position before move
            try:
                pre_score, pre_details = evaluate(board)
            except Exception:
                pre_score, pre_details = 0, {}
            
            # Detect patterns before making the move
            if self.save_patterns and self.pattern_detector:
                try:
                    patterns = self.pattern_detector.detect_patterns(board, move)
                    for pattern in patterns:
                        if hasattr(pattern, 'metadata'):
                            pattern.metadata["game_id"] = f"random_game_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                            pattern.metadata["added_at"] = datetime.now().isoformat()
                        else:
                            pattern.metadata = {
                                "game_id": f"random_game_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                                "added_at": datetime.now().isoformat()
                            }
                        self.patterns_detected.append(pattern)
                        game_data["patterns_detected"].append({
                            "pattern_type": pattern.pattern_types,
                            "description": pattern.description,
                            "evaluation_change": pattern.evaluation.get("change", 0)
                        })
                except Exception as e:
                    print(f"Warning: Pattern detection failed: {e}")
            
            # Make the move
            board.push(move)
            ply += 1
            
            # Evaluate position after move
            try:
                post_score, post_details = evaluate(board)
            except Exception:
                post_score, post_details = 0, {}
            
            # Store move data
            move_data = {
                "ply": ply,
                "side": side,
                "move": move.uci(),
                "fen": board.fen(),
                "pre_score": pre_score,
                "post_score": post_score,
                "confidence": confidence,
                "details": post_details
            }
            game_data["moves"].append(move_data)
            
            # Print move info
            print(f"[Ply {ply:02d}] {side} played {move.uci()}")
            if post_details:
                print(f"  material={post_details.get('material', 'n/a')}  "
                      f"pst={post_details.get('pst', 'n/a')}  "
                      f"mobility={post_details.get('mobility', 'n/a')}  "
                      f"att_w={post_details.get('attacks_white', 'n/a')} "
                      f"att_b={post_details.get('attacks_black', 'n/a')}  "
                      f"delta_att={post_details.get('delta_attacks', 'n/a')}")
            print(f"  eval_before≈{pre_score}   eval_after={post_score}   confidence={confidence:.3f}")
            print(f"  FEN: {board.fen()}")
            print("-")
        
        # Determine game result
        if board.is_game_over():
            result = board.result(claim_draw=True)
            if board.is_checkmate():
                reason = "checkmate"
            elif board.is_stalemate():
                reason = "stalemate"
            elif board.is_insufficient_material():
                reason = "insufficient material"
            elif board.is_seventyfive_moves():
                reason = "seventy-five move rule"
            elif board.is_fivefold_repetition():
                reason = "fivefold repetition"
            else:
                reason = "repetition"
        else:
            result = "*"
            reason = "move limit reached"
        
        game_data["result"] = result
        game_data["reason"] = reason
        game_data["total_plies"] = ply
        
        print(f"\nResult: {result}")
        print(f"Game over reason: {reason}")
        print(f"Total plies: {ply}")
        
        # Save patterns if enabled
        if self.save_patterns and self.patterns_detected and self.pattern_storage:
            try:
                for pattern in self.patterns_detected:
                    self.pattern_storage.save_pattern(pattern)
                print(f"\n✓ Saved {len(self.patterns_detected)} patterns to patterns/random_games/")
            except Exception as e:
                print(f"Warning: Failed to save patterns: {e}")
        
        return game_data


def main():
    """Main function to run the random bot game."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run a chess game between two RandomBot agents")
    parser.add_argument("--max-plies", type=int, default=50, help="Maximum number of plies to play")
    parser.add_argument("--no-patterns", action="store_true", help="Disable pattern saving")
    parser.add_argument("--games", type=int, default=1, help="Number of games to play")
    
    args = parser.parse_args()
    
    runner = RandomGameRunner(save_patterns=not args.no_patterns)
    
    all_games = []
    for game_num in range(1, args.games + 1):
        print(f"\n{'='*50}")
        print(f"GAME {game_num}/{args.games}")
        print(f"{'='*50}")
        
        game_data = runner.run_game(max_plies=args.max_plies)
        all_games.append(game_data)
        
        # Save game data to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"patterns/random_games/game_{timestamp}_{game_num}.json"
        os.makedirs("patterns/random_games", exist_ok=True)
        
        with open(filename, 'w') as f:
            json.dump(game_data, f, indent=2, default=str)
        
        print(f"✓ Game data saved to {filename}")
    
    # Save summary
    if args.games > 1:
        summary = {
            "total_games": args.games,
            "games": all_games,
            "summary": {
                "total_patterns": sum(len(g["patterns_detected"]) for g in all_games),
                "avg_plies": sum(g["total_plies"] for g in all_games) / len(all_games),
                "results": {}
            }
        }
        
        # Count results
        for game in all_games:
            result = game["result"]
            summary["summary"]["results"][result] = summary["summary"]["results"].get(result, 0) + 1
        
        summary_file = f"patterns/random_games/summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"\n✓ Summary saved to {summary_file}")
        print(f"Total patterns detected: {summary['summary']['total_patterns']}")
        print(f"Average plies per game: {summary['summary']['avg_plies']:.1f}")


if __name__ == "__main__":
    main()