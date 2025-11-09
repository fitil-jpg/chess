#!/usr/bin/env python3
"""
Simple tournament runner without Docker dependencies.
Just run this script to start a tournament with all available bots.
"""

import os
import sys
import subprocess

def main():
    print("=== SIMPLE CHESS BOT TOURNAMENT ===")
    print("Starting tournament without Docker...")
    
    # Check if we're in the right directory
    if not os.path.exists('tournament_runner.py'):
        print("❌ Error: tournament_runner.py not found!")
        print("Please run this script from the chess project directory.")
        sys.exit(1)
    
    # Create necessary directories
    print("📁 Creating directories...")
    os.makedirs('tournament_logs', exist_ok=True)
    os.makedirs('tournament_patterns', exist_ok=True)
    os.makedirs('tournament_stats', exist_ok=True)
    
    # Set environment variables
    os.environ['GAMES_PER_MATCH'] = '3'
    os.environ['TIME_PER_GAME'] = '180'
    
    print("🚀 Starting tournament...")
    print("Format: Bo3 (Best of 3 games)")
    print("Time control: 3 minutes per game")
    print("Participants: All available bots")
    print()
    
    try:
        # Run the tournament
        result = subprocess.run([sys.executable, 'tournament_runner.py'], 
                              capture_output=False, text=True)
        
        if result.returncode == 0:
            print("\n✅ Tournament completed successfully!")
            print("\n📊 Results saved to:")
            print("  - tournament_logs/tournament.log")
            print("  - tournament_patterns/patterns.json")
            print("  - tournament_stats/final_results_*.json")
            
            # Show latest report if available
            import glob
            reports = glob.glob('tournament_stats/tournament_report_*.txt')
            if reports:
                latest = max(reports, key=os.path.getctime)
                print(f"\n📋 Latest report: {latest}")
                with open(latest, 'r') as f:
                    print(f.read())
            
            print("\n🎮 To view results with GUI:")
            print("  python3 run_tournament_pattern_viewer.py")
            
        else:
            print(f"❌ Tournament failed with exit code {result.returncode}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Tournament interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error running tournament: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
