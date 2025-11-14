#!/usr/bin/env python3
"""
Tournament Optimization and Progress Tracking Module
Базова оптимізація для поточних турнірів та відстеження прогресу
"""

import os
import json
import time
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TournamentProgress:
    """Tracks tournament progress and performance metrics."""
    tournament_id: str
    total_matches: int
    completed_matches: int = 0
    current_match: Optional[Tuple[str, str]] = None
    start_time: Optional[float] = None
    estimated_end_time: Optional[float] = None
    matches_per_hour: float = 0.0
    bot_performance: Dict[str, Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.bot_performance is None:
            self.bot_performance = {}
    
    @property
    def completion_percentage(self) -> float:
        """Calculate tournament completion percentage."""
        if self.total_matches == 0:
            return 0.0
        return (self.completed_matches / self.total_matches) * 100
    
    @property
    def elapsed_time(self) -> float:
        """Calculate elapsed time in seconds."""
        if not self.start_time:
            return 0.0
        return time.time() - self.start_time
    
    @property
    def estimated_remaining_time(self) -> float:
        """Estimate remaining time in seconds."""
        if self.matches_per_hour == 0 or self.completed_matches == 0:
            return 0.0
        remaining_matches = self.total_matches - self.completed_matches
        return (remaining_matches / self.matches_per_hour) * 3600

@dataclass
class OptimizationConfig:
    """Configuration for tournament optimizations."""
    enable_caching: bool = True
    cache_size: int = 10000
    enable_parallel_evaluation: bool = True
    max_workers: int = 4
    time_limit_per_move: int = 60
    early_termination_threshold: float = 0.95
    adaptive_time_control: bool = True
    bot_prioritization: Dict[str, float] = None
    
    def __post_init__(self):
        if self.bot_prioritization is None:
            # Optimized bot weights based on performance analysis
            self.bot_prioritization = {
                "DynamicBot": 1.5,
                "AggressiveBot": 1.2,
                "CriticalBot": 1.0,
                "EndgameBot": 1.1,
                "FortifyBot": 0.8,
                "KingValueBot": 0.7,
                "RandomBot": 0.0,
                "PieceMateBot": 0.9,
                "NeuralBot": 0.6
            }

class TournamentOptimizer:
    """Main optimization and progress tracking class."""
    
    def __init__(self, config: Optional[OptimizationConfig] = None):
        self.config = config or OptimizationConfig()
        self.progress: Optional[TournamentProgress] = None
        self.cache: Dict[str, Any] = {}
        self.performance_history: List[Dict[str, Any]] = []
        self.optimization_stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "early_terminations": 0,
            "parallel_evaluations": 0,
            "time_savings": 0.0
        }
        
        # Ensure directories exist
        os.makedirs("tournament_optimization", exist_ok=True)
        os.makedirs("tournament_progress", exist_ok=True)
        
        # Load previous state if available
        self._load_state()
    
    def initialize_tournament(self, tournament_id: str, bot_names: List[str], 
                            matches: List[Tuple[str, str]]) -> TournamentProgress:
        """Initialize tournament tracking."""
        self.progress = TournamentProgress(
            tournament_id=tournament_id,
            total_matches=len(matches),
            start_time=time.time()
        )
        
        # Initialize bot performance tracking
        for bot_name in bot_names:
            self.progress.bot_performance[bot_name] = {
                "wins": 0,
                "losses": 0,
                "draws": 0,
                "points": 0.0,
                "avg_think_time": 0.0,
                "total_moves": 0,
                "errors": 0
            }
        
        self._save_progress()
        logger.info(f"🏆 Initialized tournament {tournament_id} with {len(matches)} matches")
        return self.progress
    
    def update_match_progress(self, bot1: str, bot2: str, result: Dict[str, Any]) -> None:
        """Update progress after a match completes."""
        if not self.progress:
            return
        
        self.progress.completed_matches += 1
        self.progress.current_match = None
        
        # Update match rate calculation
        elapsed = self.progress.elapsed_time
        if elapsed > 0:
            self.progress.matches_per_hour = (self.progress.completed_matches / elapsed) * 3600
        
        # Estimate completion time
        if self.progress.matches_per_hour > 0:
            remaining_matches = self.progress.total_matches - self.progress.completed_matches
            remaining_time = (remaining_matches / self.progress.matches_per_hour) * 3600
            self.progress.estimated_end_time = time.time() + remaining_time
        
        # Update bot performance
        self._update_bot_performance(bot1, bot2, result)
        
        # Save progress
        self._save_progress()
        
        logger.info(f"📊 Match completed: {self.progress.completed_matches}/{self.progress.total_matches} "
                   f"({self.progress.completion_percentage:.1f}%)")
    
    def _update_bot_performance(self, bot1: str, bot2: str, result: Dict[str, Any]) -> None:
        """Update individual bot performance metrics."""
        winner = result.get("winner")
        bot1_wins = result.get("bot1_wins", 0)
        bot2_wins = result.get("bot2_wins", 0)
        draws = result.get("draws", 0)
        
        # Update bot1 stats
        if bot1 in self.progress.bot_performance:
            perf = self.progress.bot_performance[bot1]
            perf["wins"] += bot1_wins
            perf["losses"] += bot2_wins
            perf["draws"] += draws
            perf["points"] += bot1_wins * 1.0 + draws * 0.5
        
        # Update bot2 stats
        if bot2 in self.progress.bot_performance:
            perf = self.progress.bot_performance[bot2]
            perf["wins"] += bot2_wins
            perf["losses"] += bot1_wins
            perf["draws"] += draws
            perf["points"] += bot2_wins * 1.0 + draws * 0.5
    
    def get_optimization_recommendations(self) -> List[str]:
        """Get real-time optimization recommendations."""
        recommendations = []
        
        if not self.progress:
            return recommendations
        
        # Check performance issues
        for bot_name, perf in self.progress.bot_performance.items():
            if perf.get("errors", 0) > 5:
                recommendations.append(f"⚠️ {bot_name} has {perf['errors']} errors - consider debugging")
            
            if perf.get("avg_think_time", 0) > 30:
                recommendations.append(f"⏱️ {bot_name} is slow ({perf['avg_think_time']:.1f}s avg) - reduce time limit")
        
        # Check tournament pace
        if self.progress.matches_per_hour < 5:
            recommendations.append("🐌 Tournament is running slowly - consider parallel evaluation")
        
        # Check cache efficiency
        total_requests = self.optimization_stats["cache_hits"] + self.optimization_stats["cache_misses"]
        if total_requests > 0:
            hit_rate = self.optimization_stats["cache_hits"] / total_requests
            if hit_rate < 0.3:
                recommendations.append("🗄️ Cache hit rate is low - consider increasing cache size")
        
        return recommendations
    
    def optimize_bot_selection(self, available_bots: List[str], 
                              max_bots: int = 8) -> List[str]:
        """Optimize bot selection based on performance weights."""
        scored_bots = []
        for bot in available_bots:
            score = self.config.bot_prioritization.get(bot, 0.5)
            scored_bots.append((bot, score))
        
        # Sort by score and select top bots
        scored_bots.sort(key=lambda x: x[1], reverse=True)
        return [bot for bot, _ in scored_bots[:max_bots]]
    
    def should_terminate_early(self, board, confidence: float) -> bool:
        """Determine if evaluation should terminate early."""
        if confidence >= self.config.early_termination_threshold:
            self.optimization_stats["early_terminations"] += 1
            return True
        return False
    
    def get_cached_evaluation(self, board_hash: str, bot_name: str) -> Optional[Any]:
        """Get cached evaluation result."""
        if not self.config.enable_caching:
            return None
        
        key = f"{board_hash}_{bot_name}"
        if key in self.cache:
            self.optimization_stats["cache_hits"] += 1
            return self.cache[key]
        
        self.optimization_stats["cache_misses"] += 1
        return None
    
    def cache_evaluation(self, board_hash: str, bot_name: str, result: Any) -> None:
        """Cache evaluation result."""
        if not self.config.enable_caching:
            return
        
        key = f"{board_hash}_{bot_name}"
        
        # Implement simple LRU by removing oldest entries
        if len(self.cache) >= self.config.cache_size:
            oldest_keys = list(self.cache.keys())[:100]
            for k in oldest_keys:
                del self.cache[k]
        
        self.cache[key] = result
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get comprehensive progress summary."""
        if not self.progress:
            return {"error": "No tournament in progress"}
        
        # Sort bots by performance
        sorted_bots = sorted(
            self.progress.bot_performance.items(),
            key=lambda x: x[1]["points"],
            reverse=True
        )
        
        return {
            "tournament_id": self.progress.tournament_id,
            "progress": {
                "completed_matches": self.progress.completed_matches,
                "total_matches": self.progress.total_matches,
                "completion_percentage": round(self.progress.completion_percentage, 1),
                "matches_per_hour": round(self.progress.matches_per_hour, 1),
                "elapsed_time": round(self.progress.elapsed_time, 1),
                "estimated_remaining_time": round(self.progress.estimated_remaining_time, 1)
            },
            "bot_rankings": [
                {
                    "rank": i + 1,
                    "name": bot_name,
                    "points": round(perf["points"], 1),
                    "wins": perf["wins"],
                    "draws": perf["draws"],
                    "losses": perf["losses"]
                }
                for i, (bot_name, perf) in enumerate(sorted_bots)
            ],
            "optimization_stats": self.optimization_stats,
            "recommendations": self.get_optimization_recommendations()
        }
    
    def save_optimization_report(self) -> str:
        """Save detailed optimization report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tournament_optimization/optimization_report_{timestamp}.json"
        
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "config": asdict(self.config),
            "progress_summary": self.get_progress_summary(),
            "performance_history": self.performance_history[-10:],  # Last 10 entries
            "optimization_stats": self.optimization_stats
        }
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Optimization report saved to {filename}")
        return filename
    
    def _save_progress(self) -> None:
        """Save current progress state."""
        if not self.progress:
            return
        
        filename = f"tournament_progress/{self.progress.tournament_id}_progress.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(asdict(self.progress), f, indent=2, ensure_ascii=False)
    
    def _load_state(self) -> None:
        """Load previous optimization state."""
        try:
            # Load latest progress if available
            progress_dir = Path("tournament_progress")
            if progress_dir.exists():
                progress_files = list(progress_dir.glob("*_progress.json"))
                if progress_files:
                    latest_file = max(progress_files, key=lambda p: p.stat().st_mtime)
                    with open(latest_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        self.progress = TournamentProgress(**data)
        except Exception as e:
            logger.warning(f"Could not load previous state: {e}")

class ProgressTracker:
    """Simple progress tracking utility for tournaments."""
    
    def __init__(self, tournament_id: str):
        self.tournament_id = tournament_id
        self.start_time = time.time()
        self.checkpoints: List[Tuple[float, str]] = []
    
    def add_checkpoint(self, description: str) -> None:
        """Add a progress checkpoint."""
        elapsed = time.time() - self.start_time
        self.checkpoints.append((elapsed, description))
        logger.info(f"📍 [{self.tournament_id}] {elapsed:.1f}s - {description}")
    
    def get_progress_report(self) -> str:
        """Get formatted progress report."""
        if not self.checkpoints:
            return "No progress checkpoints recorded"
        
        report = f"📊 Progress Report for {self.tournament_id}:\n"
        total_time = self.checkpoints[-1][0]
        report += f"Total time: {total_time:.1f}s\n\n"
        
        for i, (elapsed, desc) in enumerate(self.checkpoints, 1):
            percentage = (elapsed / total_time) * 100 if total_time > 0 else 0
            report += f"{i:2d}. {elapsed:6.1f}s ({percentage:5.1f}%) - {desc}\n"
        
        return report

# Utility functions
def create_optimized_tournament_config() -> OptimizationConfig:
    """Create optimized tournament configuration."""
    return OptimizationConfig(
        enable_caching=True,
        cache_size=15000,
        enable_parallel_evaluation=True,
        max_workers=min(8, os.cpu_count() or 4),
        time_limit_per_move=45,
        early_termination_threshold=0.92,
        adaptive_time_control=True,
        bot_prioritization={
            "DynamicBot": 1.6,
            "AggressiveBot": 1.3,
            "CriticalBot": 1.1,
            "EndgameBot": 1.2,
            "FortifyBot": 0.9,
            "KingValueBot": 0.8,
            "RandomBot": 0.0,
            "PieceMateBot": 1.0,
            "NeuralBot": 0.7
        }
    )

def monitor_tournament_progress(tournament_id: str) -> Dict[str, Any]:
    """Monitor ongoing tournament progress."""
    optimizer = TournamentOptimizer()
    
    # Load progress if available
    progress_file = f"tournament_progress/{tournament_id}_progress.json"
    if os.path.exists(progress_file):
        with open(progress_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            optimizer.progress = TournamentProgress(**data)
    
    return optimizer.get_progress_summary()

if __name__ == "__main__":
    # Demo usage
    print("🚀 Tournament Optimization and Progress Tracking")
    print("=" * 50)
    
    # Create optimizer
    config = create_optimized_tournament_config()
    optimizer = TournamentOptimizer(config)
    
    # Demo tournament initialization
    bots = ["DynamicBot", "AggressiveBot", "CriticalBot", "EndgameBot"]
    matches = [("DynamicBot", "AggressiveBot"), ("CriticalBot", "EndgameBot")]
    
    progress = optimizer.initialize_tournament("demo_tournament", bots, matches)
    
    print(f"✅ Tournament initialized: {progress.tournament_id}")
    print(f"📊 Total matches: {progress.total_matches}")
    
    # Get recommendations
    recommendations = optimizer.get_optimization_recommendations()
    if recommendations:
        print("\n💡 Recommendations:")
        for rec in recommendations:
            print(f"   {rec}")
    
    print("\n🎯 Optimization system ready!")
