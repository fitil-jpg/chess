"""
Lightweight game logging system for chess AI.

Designed to be minimal yet comprehensive - logs essential game data
without excessive overhead or storage requirements.
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import chess


class GameLogger:
    """
    Minimal game logger that captures essential chess game data.
    
    Features:
    - Compact JSON format
    - Automatic file management
    - Minimal performance overhead
    - Easy data retrieval and analysis
    """
    
    def __init__(self, log_dir: str = "logs/games", compress: bool = True):
        self.log_dir = log_dir
        self.compress = compress
        self.current_game = None
        self.start_time = None
        
        # Create log directory
        os.makedirs(log_dir, exist_ok=True)
    
    def start_game(self, white_bot: str, black_bot: str, 
                   time_control: Optional[str] = None) -> str:
        """Start logging a new game. Returns game ID."""
        game_id = f"game_{int(time.time())}_{white_bot}_vs_{black_bot}"
        
        self.current_game = {
            "game_id": game_id,
            "timestamp": datetime.now().isoformat(),
            "white_bot": white_bot,
            "black_bot": black_bot,
            "time_control": time_control,
            "start_fen": chess.Board().fen(),
            "moves": [],
            "result": None,
            "termination": None,
            "duration_seconds": None
        }
        
        self.start_time = time.time()
        return game_id
    
    def log_move(self, move: chess.Move, board: chess.Board, 
                 confidence: float = 0.0, think_time: float = 0.0,
                 eval_score: float = 0.0) -> None:
        """Log a single move with minimal essential data."""
        if not self.current_game:
            return
        
        move_data = {
            "ply": len(self.current_game["moves"]) + 1,
            "move": move.uci(),
            "fen": board.fen(),
            "confidence": round(confidence, 3),
            "think_time_ms": round(think_time * 1000, 1),
            "eval": round(eval_score, 2)
        }
        
        self.current_game["moves"].append(move_data)
    
    def end_game(self, result: str, termination: str) -> Dict[str, Any]:
        """End game and save to file. Returns complete game data."""
        if not self.current_game:
            return {}
        
        # Finalize game data
        self.current_game["result"] = result
        self.current_game["termination"] = termination
        self.current_game["duration_seconds"] = round(time.time() - self.start_time, 2)
        self.current_game["total_moves"] = len(self.current_game["moves"])
        
        # Add quick stats
        if self.current_game["moves"]:
            confidences = [m["confidence"] for m in self.current_game["moves"]]
            think_times = [m["think_time_ms"] for m in self.current_game["moves"]]
            
            self.current_game["stats"] = {
                "avg_confidence": round(sum(confidences) / len(confidences), 3),
                "avg_think_time_ms": round(sum(think_times) / len(think_times), 1),
                "total_think_time_ms": round(sum(think_times), 1)
            }
        
        # Save to file
        filename = os.path.join(self.log_dir, f"{self.current_game['game_id']}.json")
        with open(filename, 'w') as f:
            json.dump(self.current_game, f, indent=2 if not self.compress else None)
        
        game_data = self.current_game.copy()
        self.current_game = None
        self.start_time = None
        
        return game_data
    
    def get_recent_games(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent game files sorted by timestamp."""
        if not os.path.exists(self.log_dir):
            return []
        
        files = [f for f in os.listdir(self.log_dir) if f.endswith('.json')]
        files.sort(reverse=True)  # Most recent first
        
        games = []
        for filename in files[:limit]:
            try:
                filepath = os.path.join(self.log_dir, filename)
                with open(filepath, 'r') as f:
                    game = json.load(f)
                    games.append(game)
            except Exception:
                continue
        
        return games
    
    def get_stats_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get summary statistics for recent games."""
        games = self.get_recent_games(limit=100)  # Get more for accurate stats
        
        if not games:
            return {"total_games": 0}
        
        # Filter by date if needed
        cutoff = datetime.now().timestamp() - (days * 24 * 3600)
        recent_games = [g for g in games 
                       if datetime.fromisoformat(g["timestamp"]).timestamp() > cutoff]
        
        if not recent_games:
            return {"total_games": 0, "period_days": days}
        
        # Basic stats
        total_games = len(recent_games)
        results = {"1-0": 0, "0-1": 0, "1/2-1/2": 0, "*": 0}
        total_moves = 0
        total_duration = 0
        
        for game in recent_games:
            result = game.get("result", "*")
            results[result] = results.get(result, 0) + 1
            total_moves += game.get("total_moves", 0)
            total_duration += game.get("duration_seconds", 0)
        
        return {
            "total_games": total_games,
            "period_days": days,
            "results": results,
            "avg_moves_per_game": round(total_moves / total_games, 1),
            "avg_duration_seconds": round(total_duration / total_games, 1),
            "white_wins": results["1-0"],
            "black_wins": results["0-1"], 
            "draws": results["1/2-1/2"]
        }


class GameAnalyzer:
    """Lightweight analyzer for logged games."""
    
    @staticmethod
    def load_game(filepath: str) -> Dict[str, Any]:
        """Load a single game file."""
        with open(filepath, 'r') as f:
            return json.load(f)
    
    @staticmethod
    def replay_moves(moves: List[Dict[str, Any]]) -> List[chess.Board]:
        """Recreate board states from move list."""
        boards = []
        board = chess.Board()
        boards.append(board.copy())
        
        for move_data in moves:
            move = chess.Move.from_uci(move_data["move"])
            board.push(move)
            boards.append(board.copy())
        
        return boards
    
    @staticmethod
    def find_games_by_bot(log_dir: str, bot_name: str) -> List[Dict[str, Any]]:
        """Find all games where specific bot participated."""
        games = []
        
        if not os.path.exists(log_dir):
            return games
        
        for filename in os.listdir(log_dir):
            if not filename.endswith('.json'):
                continue
            
            try:
                filepath = os.path.join(log_dir, filename)
                game = GameAnalyzer.load_game(filepath)
                
                if (game.get("white_bot") == bot_name or 
                    game.get("black_bot") == bot_name):
                    games.append(game)
            except Exception:
                continue
        
        return games


# Convenience function for quick logging
def quick_log_game(white_bot: str, black_bot: str, moves_data: List[Dict[str, Any]], 
                   result: str, termination: str, log_dir: str = "logs/games") -> str:
    """Quick way to log a complete game at once."""
    logger = GameLogger(log_dir)
    game_id = logger.start_game(white_bot, black_bot)
    
    # Simulate the moves for logging
    board = chess.Board()
    for move_data in moves_data:
        move = chess.Move.from_uci(move_data["move"])
        board.push(move)
        logger.log_move(move, board, **move_data.get("metadata", {}))
    
    logger.end_game(result, termination)
    return game_id
