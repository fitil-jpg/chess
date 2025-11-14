#!/usr/bin/env python3
"""
Performance Analysis for Chess AI System
Анализ производительности и определение узких мест
"""

import time
import cProfile
import pstats
import io
import chess
from typing import Dict, List, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import all bots for testing
from chess_ai.critical_bot import CriticalBot
from chess_ai.pawn_bot import PawnBot
from chess_ai.king_value_bot import KingValueBot
from chess_ai.aggressive_bot import AggressiveBot
from chess_ai.dynamic_bot import DynamicBot
from core.evaluator import Evaluator
from utils import GameContext

class PerformanceProfiler:
    """Profiler for chess AI performance analysis."""
    
    def __init__(self):
        self.results = {}
        
    def profile_bot(self, bot, board: chess.Board, iterations: int = 100) -> Dict:
        """Profile a single bot's performance."""
        
        evaluator = Evaluator(board)
        context = GameContext(material_diff=0, mobility=0, king_safety=0)
        
        # Time profiling
        times = []
        successful_runs = 0
        
        for i in range(iterations):
            start_time = time.perf_counter()
            try:
                move, score = bot.choose_move(board, context, evaluator, debug=False)
                if move is not None:
                    successful_runs += 1
                end_time = time.perf_counter()
                times.append(end_time - start_time)
            except Exception as e:
                logger.warning(f"Bot {type(bot).__name__} failed on iteration {i}: {e}")
                continue
        
        if not times:
            return {"error": "All runs failed"}
        
        # CPU profiling for detailed analysis
        pr = cProfile.Profile()
        pr.enable()
        
        # Run a few iterations for detailed profiling
        for i in range(10):
            try:
                bot.choose_move(board, context, evaluator, debug=False)
            except:
                pass
                
        pr.disable()
        
        # Get profiling stats
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats(20)  # Top 20 functions
        
        return {
            "bot_name": type(bot).__name__,
            "avg_time": sum(times) / len(times),
            "min_time": min(times),
            "max_time": max(times),
            "success_rate": successful_runs / iterations,
            "total_runs": len(times),
            "profile_stats": s.getvalue(),
            "times_ms": [t * 1000 for t in times[:10]]  # First 10 times in ms
        }
    
    def compare_bots(self, positions: List[chess.Board]) -> Dict:
        """Compare performance across multiple bots."""
        
        bots = {
            "CriticalBot": CriticalBot(chess.WHITE, enable_hierarchy=True),
            "PawnBot": PawnBot(chess.WHITE),
            "KingValueBot": KingValueBot(chess.WHITE, enable_heatmaps=True),
            "AggressiveBot": AggressiveBot(chess.WHITE),
            "DynamicBot": DynamicBot(chess.WHITE)
        }
        
        results = {}
        
        for pos_name, board in positions:
            logger.info(f"Testing position: {pos_name}")
            results[pos_name] = {}
            
            for bot_name, bot in bots.items():
                logger.info(f"  Profiling {bot_name}...")
                perf = self.profile_bot(bot, board, iterations=50)
                results[pos_name][bot_name] = perf
                
                # Print summary
                if "error" not in perf:
                    logger.info(f"    Avg time: {perf['avg_time']*1000:.2f}ms, "
                              f"Success: {perf['success_rate']:.1%}")
        
        return results
    
    def identify_bottlenecks(self, results: Dict) -> Dict:
        """Identify performance bottlenecks."""
        
        bottlenecks = {
            "slowest_bots": [],
            "least_reliable": [],
            "recommendations": []
        }
        
        # Analyze each position
        for pos_name, pos_results in results.items():
            # Find slowest bot
            slowest = None
            max_time = 0
            
            for bot_name, perf in pos_results.items():
                if "error" not in perf and perf["avg_time"] > max_time:
                    max_time = perf["avg_time"]
                    slowest = bot_name
            
            if slowest:
                bottlenecks["slowest_bots"].append({
                    "position": pos_name,
                    "bot": slowest,
                    "time_ms": max_time * 1000
                })
            
            # Find least reliable
            least_reliable = None
            min_success = 1.0
            
            for bot_name, perf in pos_results.items():
                if "error" not in perf and perf["success_rate"] < min_success:
                    min_success = perf["success_rate"]
                    least_reliable = bot_name
            
            if least_reliable and min_success < 0.9:
                bottlenecks["least_reliable"].append({
                    "position": pos_name,
                    "bot": least_reliable,
                    "success_rate": min_success
                })
        
        # Generate recommendations
        bottlenecks["recommendations"] = self._generate_recommendations(bottlenecks)
        
        return bottlenecks
    
    def _generate_recommendations(self, bottlenecks: Dict) -> List[str]:
        """Generate performance optimization recommendations."""
        
        recommendations = []
        
        # Analyze slowest bots
        slow_bots = [item["bot"] for item in bottlenecks["slowest_bots"]]
        if slow_bots:
            most_common = max(set(slow_bots), key=slow_bots.count)
            recommendations.append(
                f"🐌 Most critical bottleneck: {most_common} - "
                "consider caching evaluator results or reducing search depth"
            )
        
        # Analyze reliability
        if bottlenecks["least_reliable"]:
            recommendations.append(
                "⚠️  Some bots have reliability issues - "
                "add better error handling and fallback mechanisms"
            )
        
        # General recommendations
        recommendations.extend([
            "💡 Implement move caching across similar positions",
            "💡 Use lazy evaluation for expensive calculations",
            "💡 Consider parallel evaluation for independent bots",
            "💡 Optimize heatmap generation with precomputed patterns"
        ])
        
        return recommendations

def create_test_positions() -> List[Tuple[str, chess.Board]]:
    """Create diverse test positions for performance analysis."""
    
    positions = [
        ("Opening", chess.Board()),
        
        ("Tactical", chess.Board("r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 4")),
        
        ("Endgame", chess.Board("8/8/8/8/8/4k3/4P3/4K3 w - - 0 1")),
        
        ("Complex", chess.Board("r2q1rk1/ppp2ppp/2n1bn2/2b1p3/3pP3/2P2N2/PP1N1PPP/R1BQKB1R w KQ - 0 8")),
        
        ("King Safety", chess.Board("rnbqk2r/pppp1ppp/5n2/2b1p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 4"))
    ]
    
    return positions

def main():
    """Main performance analysis."""
    
    print("🔍 Chess AI Performance Analysis")
    print("=" * 50)
    
    profiler = PerformanceProfiler()
    positions = create_test_positions()
    
    # Run performance comparison
    results = profiler.compare_bots(positions)
    
    # Identify bottlenecks
    bottlenecks = profiler.identify_bottlenecks(results)
    
    # Print results
    print("\n📊 Performance Results:")
    print("-" * 30)
    
    for pos_name, pos_results in results.items():
        print(f"\n🎯 Position: {pos_name}")
        for bot_name, perf in pos_results.items():
            if "error" not in perf:
                print(f"  {bot_name:15}: {perf['avg_time']*1000:6.2f}ms "
                      f"({perf['success_rate']:.1%} success)")
            else:
                print(f"  {bot_name:15}: ERROR")
    
    print("\n🚨 Bottlenecks Identified:")
    print("-" * 30)
    
    for item in bottlenecks["slowest_bots"]:
        print(f"  Slow: {item['bot']} in {item['position']} "
              f"({item['time_ms']:.1f}ms)")
    
    for item in bottlenecks["least_reliable"]:
        print(f"  Unreliable: {item['bot']} in {item['position']} "
              f"({item['success_rate']:.1%} success)")
    
    print("\n💡 Recommendations:")
    print("-" * 30)
    for rec in bottlenecks["recommendations"]:
        print(f"  {rec}")
    
    # Save detailed results
    import json
    with open("performance_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to performance_results.json")

if __name__ == "__main__":
    main()
