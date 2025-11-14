"""
Lightweight analytics utilities for logged chess games.

Provides quick insights without heavy data processing.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import chess
from collections import Counter, defaultdict


class GameAnalytics:
    """Quick analytics for chess game logs."""
    
    def __init__(self, log_dir: str = "logs/games"):
        self.log_dir = log_dir
    
    def load_games(self, limit: int = None) -> List[Dict[str, Any]]:
        """Load games from log directory."""
        if not os.path.exists(self.log_dir):
            return []
        
        files = [f for f in os.listdir(self.log_dir) if f.endswith('.json')]
        files.sort(reverse=True)  # Most recent first
        
        if limit:
            files = files[:limit]
        
        games = []
        for filename in files:
            try:
                filepath = os.path.join(self.log_dir, filename)
                with open(filepath, 'r') as f:
                    games.append(json.load(f))
            except Exception:
                continue
        
        return games
    
    def bot_performance(self, bot_name: str, days: int = 30) -> Dict[str, Any]:
        """Get performance stats for a specific bot."""
        cutoff = datetime.now() - timedelta(days=days)
        games = self.load_games()
        
        bot_games = []
        for game in games:
            game_time = datetime.fromisoformat(game["timestamp"])
            if game_time < cutoff:
                continue
            
            if game["white_bot"] == bot_name:
                bot_games.append((game, "white"))
            elif game["black_bot"] == bot_name:
                bot_games.append((game, "black"))
        
        if not bot_games:
            return {"error": f"No games found for {bot_name}"}
        
        # Calculate stats
        wins, draws, losses = 0, 0, 0
        total_moves = 0
        total_confidence = 0
        move_count = 0
        
        for game, side in bot_games:
            result = game["result"]
            if side == "white":
                if result == "1-0":
                    wins += 1
                elif result == "0-1":
                    losses += 1
                elif result == "1/2-1/2":
                    draws += 1
            else:  # black
                if result == "0-1":
                    wins += 1
                elif result == "1-0":
                    losses += 1
                elif result == "1/2-1/2":
                    draws += 1
            
            total_moves += game.get("total_moves", 0)
            
            # Calculate confidence for bot's moves only
            for i, move in enumerate(game.get("moves", [])):
                if (side == "white" and i % 2 == 0) or (side == "black" and i % 2 == 1):
                    total_confidence += move.get("confidence", 0)
                    move_count += 1
        
        total_games = len(bot_games)
        win_rate = wins / total_games if total_games > 0 else 0
        
        return {
            "bot_name": bot_name,
            "period_days": days,
            "total_games": total_games,
            "wins": wins,
            "draws": draws, 
            "losses": losses,
            "win_rate": round(win_rate, 3),
            "avg_moves_per_game": round(total_moves / total_games, 1),
            "avg_confidence": round(total_confidence / move_count, 3) if move_count > 0 else 0
        }
    
    def opening_stats(self, limit: int = 100) -> Dict[str, Any]:
        """Analyze opening patterns in recent games."""
        games = self.load_games(limit)
        
        openings = Counter()
        outcomes_by_opening = defaultdict(lambda: {"1-0": 0, "0-1": 0, "1/2-1/2": 0})
        
        for game in games:
            if not game.get("moves"):
                continue
            
            # Get first 3-5 moves to identify opening
            moves = game["moves"][:5]
            opening_moves = " ".join([m["move"] for m in moves])
            openings[opening_moves] += 1
            
            # Track outcome
            result = game["result"]
            outcomes_by_opening[opening_moves][result] += 1
        
        # Sort by frequency
        common_openings = openings.most_common(10)
        
        return {
            "total_games_analyzed": len(games),
            "common_openings": [
                {
                    "moves": moves,
                    "frequency": count,
                    "outcomes": outcomes_by_opening[moves]
                }
                for moves, count in common_openings
            ]
        }
    
    def time_analysis(self, bot_name: str = None) -> Dict[str, Any]:
        """Analyze thinking time patterns."""
        games = self.load_games()
        
        if bot_name:
            games = [g for g in games if bot_name in [g["white_bot"], g["black_bot"]]]
        
        all_times = []
        by_ply = defaultdict(list)
        
        for game in games:
            for i, move in enumerate(game.get("moves", [])):
                think_time = move.get("think_time_ms", 0)
                if think_time > 0:
                    all_times.append(think_time)
                    by_ply[i + 1].append(think_time)
        
        if not all_times:
            return {"error": "No timing data available"}
        
        # Calculate percentiles
        sorted_times = sorted(all_times)
        n = len(sorted_times)
        
        return {
            "total_moves_analyzed": len(all_times),
            "avg_think_time_ms": round(sum(all_times) / len(all_times), 1),
            "median_think_time_ms": round(sorted_times[n // 2], 1),
            "p95_think_time_ms": round(sorted_times[int(0.95 * n)], 1),
            "max_think_time_ms": max(all_times),
            "by_ply": {
                ply: {
                    "count": len(times),
                    "avg_ms": round(sum(times) / len(times), 1)
                }
                for ply, times in sorted(by_ply.items())[:20]  # First 20 plies
            }
        }
    
    def generate_report(self, days: int = 7, save_to_file: bool = True) -> Dict[str, Any]:
        """Generate comprehensive analytics report."""
        games = self.load_games()
        cutoff = datetime.now() - timedelta(days=days)
        recent_games = [g for g in games 
                       if datetime.fromisoformat(g["timestamp"]) > cutoff]
        
        if not recent_games:
            return {"error": "No recent games found"}
        
        # Overall stats
        total_games = len(recent_games)
        results = Counter(g["result"] for g in recent_games)
        
        # Bot performance
        bot_names = set()
        for g in recent_games:
            bot_names.add(g["white_bot"])
            bot_names.add(g["black_bot"])
        
        bot_stats = {}
        for bot in list(bot_names)[:10]:  # Limit to top 10 bots
            bot_stats[bot] = self.bot_performance(bot, days)
        
        # Opening analysis
        opening_data = self.opening_stats(total_games)
        
        # Time analysis
        time_data = self.time_analysis()
        
        report = {
            "report_generated": datetime.now().isoformat(),
            "period_days": days,
            "total_games": total_games,
            "results_distribution": dict(results),
            "bot_performance": bot_stats,
            "opening_analysis": opening_data,
            "timing_analysis": time_data
        }
        
        if save_to_file:
            filename = f"logs/analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            os.makedirs("logs", exist_ok=True)
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            report["saved_to"] = filename
        
        return report
    
    def find_longest_games(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Find longest games by move count."""
        games = self.load_games()
        sorted_games = sorted(games, key=lambda g: g.get("total_moves", 0), reverse=True)
        return sorted_games[:limit]
    
    def find_quick_games(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Find quickest games by duration."""
        games = self.load_games()
        sorted_games = sorted(games, key=lambda g: g.get("duration_seconds", float('inf')))
        return sorted_games[:limit]


# Quick utility functions
def get_top_bots(log_dir: str = "logs/games", days: int = 30, min_games: int = 5) -> List[Dict[str, Any]]:
    """Get top performing bots by win rate."""
    analytics = GameAnalytics(log_dir)
    games = analytics.load_games()
    
    # Count games per bot
    bot_game_counts = defaultdict(int)
    for game in games:
        bot_game_counts[game["white_bot"]] += 1
        bot_game_counts[game["black_bot"]] += 1
    
    # Get performance for bots with minimum games
    bot_performances = []
    for bot_name, game_count in bot_game_counts.items():
        if game_count >= min_games:
            perf = analytics.bot_performance(bot_name, days)
            if "error" not in perf:
                bot_performances.append(perf)
    
    # Sort by win rate
    bot_performances.sort(key=lambda x: x["win_rate"], reverse=True)
    return bot_performances[:10]


def quick_summary(log_dir: str = "logs/games") -> str:
    """Get a quick text summary of recent games."""
    analytics = GameAnalytics(log_dir)
    recent = analytics.load_games(20)
    
    if not recent:
        return "No games found"
    
    total = len(recent)
    results = Counter(g["result"] for g in recent)
    bots = set()
    for g in recent:
        bots.update([g["white_bot"], g["black_bot"]])
    
    summary = f"Recent {total} games:\n"
    summary += f"White wins: {results['1-0']} ({results['1-0']/total:.1%})\n"
    summary += f"Black wins: {results['0-1']} ({results['0-1']/total:.1%})\n"
    summary += f"Draws: {results['1/2-1/2']} ({results['1/2-1/2']/total:.1%})\n"
    summary += f"Active bots: {len(bots)}\n"
    
    return summary
