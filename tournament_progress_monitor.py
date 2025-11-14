#!/usr/bin/env python3
"""
Tournament Progress Monitoring Utility
Утиліта для моніторингу прогресу турніру
"""

import os
import json
import time
import argparse
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path

from tournament_optimization_progress import monitor_tournament_progress

class TournamentProgressMonitor:
    """Real-time tournament progress monitoring."""
    
    def __init__(self, tournament_id: Optional[str] = None):
        self.tournament_id = tournament_id
        self.monitoring = False
        
    def start_monitoring(self, tournament_id: str, refresh_interval: int = 5) -> None:
        """Start real-time monitoring of a tournament."""
        self.tournament_id = tournament_id
        self.monitoring = True
        
        print(f"🔍 Starting real-time monitoring for tournament: {tournament_id}")
        print("=" * 60)
        print("Press Ctrl+C to stop monitoring\n")
        
        try:
            while self.monitoring:
                self._display_progress()
                time.sleep(refresh_interval)
        except KeyboardInterrupt:
            print("\n⏹️ Monitoring stopped by user")
            self.monitoring = False
    
    def _display_progress(self) -> None:
        """Display current tournament progress."""
        progress_data = monitor_tournament_progress(self.tournament_id)
        
        if "error" in progress_data:
            print(f"❌ {progress_data['error']}")
            return
        
        # Clear screen (simple approach)
        print("\033[2J\033[H", end="")
        
        # Header
        print(f"🏆 Tournament Progress Monitor")
        print(f"📊 Tournament ID: {self.tournament_id}")
        print(f"⏰ Last updated: {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 60)
        
        # Progress section
        progress = progress_data.get("progress", {})
        if progress:
            completed = progress.get("completed_matches", 0)
            total = progress.get("total_matches", 0)
            percentage = progress.get("completion_percentage", 0)
            matches_per_hour = progress.get("matches_per_hour", 0)
            elapsed = progress.get("elapsed_time", 0)
            remaining = progress.get("estimated_remaining_time", 0)
            
            print(f"📈 Progress: {completed}/{total} matches ({percentage:.1f}%)")
            
            # Progress bar
            bar_width = 40
            filled = int((percentage / 100) * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)
            print(f"   [{bar}]")
            
            print(f"⚡ Pace: {matches_per_hour:.1f} matches/hour")
            print(f"⏱️  Elapsed: {self._format_time(elapsed)}")
            print(f"🕐 Estimated remaining: {self._format_time(remaining)}")
        
        # Top rankings
        rankings = progress_data.get("bot_rankings", [])
        if rankings:
            print(f"\n🏅 Current Top 5:")
            print(f"{'Rank':<6} {'Bot':<15} {'Points':<8} {'W-D-L':<10}")
            print("-" * 45)
            
            for bot in rankings[:5]:
                print(f"{bot['rank']:<6} {bot['name']:<15} {bot['points']:<8.1f} "
                      f"{bot['wins']}-{bot['draws']}-{bot['losses']:<3}")
        
        # Optimization stats
        opt_stats = progress_data.get("optimization_stats", {})
        if opt_stats:
            print(f"\n⚡ Optimization Stats:")
            cache_hits = opt_stats.get("cache_hits", 0)
            cache_misses = opt_stats.get("cache_misses", 0)
            total_requests = cache_hits + cache_misses
            hit_rate = (cache_hits / total_requests * 100) if total_requests > 0 else 0
            
            print(f"   🗄️ Cache hit rate: {hit_rate:.1f}%")
            print(f"   🚀 Early terminations: {opt_stats.get('early_terminations', 0)}")
        
        # Recommendations
        recommendations = progress_data.get("recommendations", [])
        if recommendations:
            print(f"\n💡 Recommendations:")
            for rec in recommendations[:3]:
                print(f"   {rec}")
        
        print("\n" + "=" * 60)
    
    def _format_time(self, seconds: float) -> str:
        """Format time duration nicely."""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.0f}m"
        else:
            hours = seconds / 3600
            minutes = (seconds % 3600) / 60
            return f"{hours:.0f}h {minutes:.0f}m"
    
    def list_tournaments(self) -> List[str]:
        """List all available tournament progress files."""
        progress_dir = Path("tournament_progress")
        if not progress_dir.exists():
            return []
        
        tournament_files = list(progress_dir.glob("*_progress.json"))
        tournament_ids = []
        
        for file in tournament_files:
            # Extract tournament ID from filename
            tournament_id = file.stem.replace("_progress", "")
            tournament_ids.append(tournament_id)
        
        return sorted(tournament_ids, reverse=True)
    
    def show_tournament_summary(self, tournament_id: str) -> None:
        """Show detailed summary of a completed tournament."""
        progress_data = monitor_tournament_progress(tournament_id)
        
        if "error" in progress_data:
            print(f"❌ {progress_data['error']}")
            return
        
        print(f"📊 Tournament Summary: {tournament_id}")
        print("=" * 60)
        
        # Progress summary
        progress = progress_data.get("progress", {})
        if progress:
            completed = progress.get("completed_matches", 0)
            total = progress.get("total_matches", 0)
            percentage = progress.get("completion_percentage", 0)
            matches_per_hour = progress.get("matches_per_hour", 0)
            elapsed = progress.get("elapsed_time", 0)
            
            print(f"📈 Final Progress: {completed}/{total} matches ({percentage:.1f}%)")
            print(f"⚡ Average Pace: {matches_per_hour:.1f} matches/hour")
            print(f"⏱️  Total Duration: {self._format_time(elapsed)}")
        
        # Final rankings
        rankings = progress_data.get("bot_rankings", [])
        if rankings:
            print(f"\n🏅 Final Rankings:")
            print(f"{'Rank':<6} {'Bot':<15} {'Points':<8} {'W-D-L':<10} {'Win %':<7}")
            print("-" * 60)
            
            for bot in rankings:
                total_games = bot['wins'] + bot['draws'] + bot['losses']
                win_pct = (bot['wins'] / total_games * 100) if total_games > 0 else 0
                print(f"{bot['rank']:<6} {bot['name']:<15} {bot['points']:<8.1f} "
                      f"{bot['wins']}-{bot['draws']}-{bot['losses']:<3} "
                      f"{win_pct:<7.1f}")
        
        # Optimization summary
        opt_stats = progress_data.get("optimization_stats", {})
        if opt_stats:
            print(f"\n⚡ Optimization Summary:")
            cache_hits = opt_stats.get("cache_hits", 0)
            cache_misses = opt_stats.get("cache_misses", 0)
            total_requests = cache_hits + cache_misses
            hit_rate = (cache_hits / total_requests * 100) if total_requests > 0 else 0
            
            print(f"   🗄️ Total cache requests: {total_requests}")
            print(f"   🎯 Cache hit rate: {hit_rate:.1f}%")
            print(f"   🚀 Early terminations: {opt_stats.get('early_terminations', 0)}")
            print(f"   ⏱️  Time savings: {opt_stats.get('time_savings', 0):.1f}s")

def main():
    """Main function for progress monitoring CLI."""
    parser = argparse.ArgumentParser(description="Tournament Progress Monitor")
    parser.add_argument("--tournament", "-t", type=str, help="Tournament ID to monitor")
    parser.add_argument("--list", "-l", action="store_true", help="List available tournaments")
    parser.add_argument("--summary", "-s", type=str, help="Show tournament summary")
    parser.add_argument("--refresh", "-r", type=int, default=5, help="Refresh interval in seconds")
    
    args = parser.parse_args()
    
    monitor = TournamentProgressMonitor()
    
    if args.list:
        tournaments = monitor.list_tournaments()
        if tournaments:
            print("📋 Available Tournaments:")
            for i, tid in enumerate(tournaments, 1):
                print(f"   {i}. {tid}")
        else:
            print("❌ No tournament progress files found")
        return
    
    if args.summary:
        monitor.show_tournament_summary(args.summary)
        return
    
    if args.tournament:
        monitor.start_monitoring(args.tournament, args.refresh)
    else:
        # Auto-detect latest tournament
        tournaments = monitor.list_tournaments()
        if tournaments:
            latest = tournaments[0]
            print(f"🔍 Auto-detected latest tournament: {latest}")
            monitor.start_monitoring(latest, args.refresh)
        else:
            print("❌ No tournament progress files found. Use --list to see available tournaments.")
            print("💡 Use --tournament <ID> to specify a tournament ID")

if __name__ == "__main__":
    main()
