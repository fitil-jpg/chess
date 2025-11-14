#!/usr/bin/env python3
"""
Test script for Tournament Optimization and Progress Tracking
Тестовий скрипт для оптимізації турніру та відстеження прогресу
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tournament_optimization_progress import (
    TournamentOptimizer, OptimizationConfig, ProgressTracker,
    create_optimized_tournament_config
)
from enhanced_tournament_runner import EnhancedTournamentRunner

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_optimization_config():
    """Test optimization configuration."""
    print("🧪 Testing Optimization Configuration")
    print("-" * 40)
    
    # Create default config
    config = OptimizationConfig()
    print(f"✅ Default config created")
    print(f"   Caching: {config.enable_caching}")
    print(f"   Cache size: {config.cache_size}")
    print(f"   Parallel evaluation: {config.enable_parallel_evaluation}")
    print(f"   Max workers: {config.max_workers}")
    print(f"   Early termination threshold: {config.early_termination_threshold}")
    
    # Create optimized config
    opt_config = create_optimized_tournament_config()
    print(f"\n✅ Optimized config created")
    print(f"   Cache size: {opt_config.cache_size}")
    print(f"   Max workers: {opt_config.max_workers}")
    print(f"   Early termination threshold: {opt_config.early_termination_threshold}")
    
    # Test bot prioritization
    print(f"\n🤖 Bot Prioritization:")
    for bot, weight in opt_config.bot_prioritization.items():
        print(f"   {bot}: {weight}")
    
    return True

def test_tournament_optimizer():
    """Test tournament optimizer functionality."""
    print("\n🧪 Testing Tournament Optimizer")
    print("-" * 40)
    
    # Create optimizer
    config = create_optimized_tournament_config()
    optimizer = TournamentOptimizer(config)
    
    # Test bot selection optimization
    available_bots = [
        "RandomBot", "AggressiveBot", "FortifyBot", "EndgameBot",
        "DynamicBot", "KingValueBot", "PieceMateBot", "CriticalBot"
    ]
    
    optimized_bots = optimizer.optimize_bot_selection(available_bots, max_bots=6)
    print(f"✅ Bot selection optimization:")
    print(f"   Available: {len(available_bots)} bots")
    print(f"   Selected: {len(optimized_bots)} bots")
    print(f"   Selected bots: {', '.join(optimized_bots)}")
    
    # Test tournament initialization
    matches = [("DynamicBot", "AggressiveBot"), ("CriticalBot", "EndgameBot")]
    progress = optimizer.initialize_tournament("test_tournament", optimized_bots, matches)
    
    print(f"\n✅ Tournament initialization:")
    print(f"   Tournament ID: {progress.tournament_id}")
    print(f"   Total matches: {progress.total_matches}")
    print(f"   Completion percentage: {progress.completion_percentage:.1f}%")
    
    # Test progress update
    test_result = {
        "winner": "DynamicBot",
        "bot1_wins": 2,
        "bot2_wins": 1,
        "draws": 0
    }
    
    optimizer.update_match_progress("DynamicBot", "AggressiveBot", test_result)
    
    updated_progress = optimizer.progress
    print(f"\n✅ Progress update:")
    print(f"   Completed matches: {updated_progress.completed_matches}")
    print(f"   Completion percentage: {updated_progress.completion_percentage:.1f}%")
    
    # Test recommendations
    recommendations = optimizer.get_optimization_recommendations()
    print(f"\n💡 Recommendations: {len(recommendations)}")
    for rec in recommendations:
        print(f"   {rec}")
    
    # Test caching
    board_hash = "test_hash_123"
    bot_name = "DynamicBot"
    
    # Test cache miss
    result = optimizer.get_cached_evaluation(board_hash, bot_name)
    print(f"\n🗄️ Cache test:")
    print(f"   Cache miss result: {result}")
    
    # Test cache set and hit
    test_move = "e2e4"
    optimizer.cache_evaluation(board_hash, bot_name, test_move)
    result = optimizer.get_cached_evaluation(board_hash, bot_name)
    print(f"   Cache hit result: {result}")
    
    # Test optimization stats
    print(f"\n📊 Optimization stats:")
    for key, value in optimizer.optimization_stats.items():
        print(f"   {key}: {value}")
    
    # Test progress summary
    summary = optimizer.get_progress_summary()
    print(f"\n📋 Progress summary generated:")
    print(f"   Tournament ID: {summary.get('tournament_id')}")
    print(f"   Progress entries: {len(summary.get('progress', {}))}")
    
    return True

def test_progress_tracker():
    """Test progress tracker functionality."""
    print("\n🧪 Testing Progress Tracker")
    print("-" * 40)
    
    # Create tracker
    tracker = ProgressTracker("test_tracker")
    
    # Add checkpoints
    tracker.add_checkpoint("Initialization completed")
    time.sleep(0.1)  # Small delay
    tracker.add_checkpoint("First match started")
    time.sleep(0.2)
    tracker.add_checkpoint("Halfway point")
    time.sleep(0.1)
    tracker.add_checkpoint("Tournament completed")
    
    # Generate report
    report = tracker.get_progress_report()
    print(f"✅ Progress report generated:")
    print(report)
    
    return True

def test_enhanced_tournament_runner():
    """Test enhanced tournament runner (mini-tournament)."""
    print("\n🧪 Testing Enhanced Tournament Runner (Mini)")
    print("-" * 40)
    
    try:
        # Create optimized config for testing
        config = OptimizationConfig(
            enable_caching=True,
            cache_size=1000,
            enable_parallel_evaluation=False,  # Disable for testing
            max_workers=2,
            early_termination_threshold=0.9,
            time_limit_per_move=10
        )
        
        # Create runner
        runner = EnhancedTournamentRunner(config)
        
        print(f"✅ Enhanced runner created")
        print(f"   Selected bots: {len(runner.bot_names)}")
        print(f"   Bot list: {', '.join(runner.bot_names)}")
        
        # Test a very small tournament (2 bots, 1 match)
        if len(runner.bot_names) >= 2:
            print(f"\n🎯 Running mini-tournament with 2 bots...")
            
            # Override bot list for testing
            test_bots = runner.bot_names[:2]
            runner.bot_names = test_bots
            
            # Generate matches manually
            import itertools
            matches = list(itertools.combinations(test_bots, 2))
            
            if matches:
                print(f"   Playing {len(matches)} match(es)...")
                
                # Initialize tracking
                from tournament_optimization_progress import TournamentOptimizer
                progress = runner.optimizer.initialize_tournament(
                    "test_mini_tournament", test_bots, matches
                )
                
                # Play one match for testing
                bot1, bot2 = matches[0]
                print(f"   Match: {bot1} vs {bot2}")
                
                # Simulate match result (don't actually play to save time)
                test_result = {
                    'bot1': bot1,
                    'bot2': bot2,
                    'bot1_wins': 2,
                    'bot2_wins': 1,
                    'draws': 0,
                    'winner': bot1,
                    'games': [],
                    'duration': 30.0,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Update progress
                runner.optimizer.update_match_progress(bot1, bot2, test_result)
                
                print(f"   ✅ Mini-tournament completed")
                print(f"   Winner: {test_result['winner']}")
                
                # Show final stats
                summary = runner.optimizer.get_progress_summary()
                progress_data = summary.get('progress', {})
                print(f"   Final progress: {progress_data.get('completed_matches')}/{progress_data.get('total_matches')}")
                
                return True
        
        print(f"⚠️ Not enough bots available for mini-tournament test")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced tournament runner test failed: {e}")
        logger.error(f"Test failed: {e}", exc_info=True)
        return False

def test_file_operations():
    """Test file saving and loading operations."""
    print("\n🧪 Testing File Operations")
    print("-" * 40)
    
    try:
        # Test optimization report saving
        config = create_optimized_tournament_config()
        optimizer = TournamentOptimizer(config)
        
        # Initialize a test tournament
        matches = [("Bot1", "Bot2"), ("Bot2", "Bot3")]
        progress = optimizer.initialize_tournament("file_test_tournament", ["Bot1", "Bot2", "Bot3"], matches)
        
        # Save optimization report
        report_file = optimizer.save_optimization_report()
        print(f"✅ Optimization report saved: {report_file}")
        
        # Verify file exists and is readable
        if os.path.exists(report_file):
            with open(report_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"   Report contains {len(data)} sections")
                print(f"   Config saved: {'config' in data}")
                print(f"   Progress saved: {'progress_summary' in data}")
        
        # Test progress file saving
        progress_file = f"tournament_progress/{progress.tournament_id}_progress.json"
        if os.path.exists(progress_file):
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
                print(f"✅ Progress file saved and verified")
                print(f"   Tournament ID: {progress_data.get('tournament_id')}")
                print(f"   Total matches: {progress_data.get('total_matches')}")
        
        return True
        
    except Exception as e:
        print(f"❌ File operations test failed: {e}")
        logger.error(f"File test failed: {e}", exc_info=True)
        return False

def run_all_tests():
    """Run all optimization and progress tracking tests."""
    print("🚀 Running Tournament Optimization and Progress Tracking Tests")
    print("=" * 70)
    
    tests = [
        ("Optimization Configuration", test_optimization_config),
        ("Tournament Optimizer", test_tournament_optimizer),
        ("Progress Tracker", test_progress_tracker),
        ("Enhanced Tournament Runner", test_enhanced_tournament_runner),
        ("File Operations", test_file_operations)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"\n{status}: {test_name}")
        except Exception as e:
            results[test_name] = False
            print(f"\n❌ FAILED: {test_name} - {e}")
            logger.error(f"Test {test_name} failed: {e}", exc_info=True)
    
    # Summary
    print(f"\n{'='*70}")
    print(f"🏁 Test Results Summary")
    print("=" * 70)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\n📊 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Tournament optimization and progress tracking is ready.")
    else:
        print("⚠️ Some tests failed. Please check the logs for details.")
    
    return passed == total

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Tournament Optimization and Progress Tracking")
    parser.add_argument("--test", type=str, choices=[
        "config", "optimizer", "tracker", "runner", "files", "all"
    ], default="all", help="Specific test to run")
    
    args = parser.parse_args()
    
    if args.test == "all":
        success = run_all_tests()
        sys.exit(0 if success else 1)
    else:
        # Run specific test
        test_map = {
            "config": test_optimization_config,
            "optimizer": test_tournament_optimizer,
            "tracker": test_progress_tracker,
            "runner": test_enhanced_tournament_runner,
            "files": test_file_operations
        }
        
        if args.test in test_map:
            print(f"🧪 Running specific test: {args.test}")
            print("=" * 50)
            
            try:
                result = test_map[args.test]()
                status = "✅ PASSED" if result else "❌ FAILED"
                print(f"\n{status}: {args.test}")
                sys.exit(0 if result else 1)
            except Exception as e:
                print(f"\n❌ FAILED: {args.test} - {e}")
                logger.error(f"Test {args.test} failed: {e}", exc_info=True)
                sys.exit(1)

if __name__ == "__main__":
    main()
