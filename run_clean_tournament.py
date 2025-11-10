#!/usr/bin/env python3
"""
Clean tournament runner with optimized output.
Shows only tournament standings and metrics, no verbose logs.
"""

import os
import sys
import subprocess

def main():
    print("🏆 CLEAN CHESS BOT TOURNAMENT")
    print("=" * 50)
    print("Optimized output - standings and metrics only")
    print("Verbose logs saved to tournament_logs/")
    print()
    
    # Check if we're in the right directory
    if not os.path.exists('tournament_runner.py'):
        print("❌ Error: tournament_runner.py not found!")
        print("Please run this script from the chess project directory.")
        sys.exit(1)
    
    # Set environment for clean output
    os.environ['GAMES_PER_MATCH'] = '3'
    os.environ['TIME_PER_GAME'] = '180'
    
    print("🚀 Starting clean tournament...")
    print("Format: Bo3, 3 minutes per game")
    print("Press Ctrl+C to interrupt")
    print()
    
    try:
        # Run the tournament with optimized runner
        result = subprocess.run([sys.executable, 'tournament_runner.py'], 
                              capture_output=False, text=True)
        
        if result.returncode == 0:
            print("\n" + "=" * 50)
            print("✅ TOURNAMENT COMPLETED SUCCESSFULLY!")
            print("=" * 50)
            
            # Show summary
            print("\n📊 SUMMARY:")
            print("  - Tournament results saved to tournament_stats/")
            print("  - Game patterns saved to tournament_patterns/")
            print("  - Bot metrics saved to tournament_stats/bot_metrics.json")
            print("  - Errors logged to tournament_logs/tournament.log")
            
            # Show latest files
            import glob
            reports = glob.glob('tournament_stats/final_results_*.json')
            if reports:
                latest = max(reports, key=os.path.getctime)
                print(f"  - Latest results: {latest}")
            
            print("\n🎮 To view results with GUI:")
            print("  python3 run_tournament_pattern_viewer.py")
            
            print("\n📈 To view bot metrics:")
            print("  cat tournament_stats/bot_metrics.json")
            
        else:
            print(f"\n❌ Tournament failed with exit code {result.returncode}")
            print("Check tournament_logs/tournament.log for errors")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Tournament interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error running tournament: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
