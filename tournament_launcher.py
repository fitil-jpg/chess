#!/usr/bin/env python3
"""
Interactive tournament launcher with menu options
"""

import os
import sys
import subprocess

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def show_menu():
    clear_screen()
    print("🏆 CHESS BOT TOURNAMENT LAUNCHER")
    print("=" * 50)
    print()
    print("1. 🚀 Quick Tournament (Python)")
    print("2. 🐳 Docker Tournament") 
    print("3. 🧪 Run Tests")
    print("4. 📊 View Results (GUI)")
    print("5. 📋 View Latest Report")
    print("6. ⚙️  Settings & Configuration")
    print("7. 📁 Show Tournament Files")
    print("8. ❌ Exit")
    print()
    print("Available bots:", ', '.join(get_bot_list()))
    print()

def get_bot_list():
    try:
        from chess_ai.bot_agent import get_agent_names
        all_bots = get_agent_names()
        # Filter to main tournament bots
        tournament_bots = ['RandomBot', 'AggressiveBot', 'FortifyBot', 'EndgameBot', 
                          'DynamicBot', 'KingValueBot', 'PieceMateBot', 'ChessBot']
        return [bot for bot in tournament_bots if bot in all_bots]
    except:
        return []

def run_quick_tournament():
    print("\n🚀 Starting Quick Tournament...")
    print("Format: Bo3, 3 minutes per game")
    print("Press Ctrl+C to interrupt")
    print()
    
    try:
        subprocess.run([sys.executable, 'run_simple_tournament.py'], check=True)
        input("\nPress Enter to continue...")
    except KeyboardInterrupt:
        print("\n⏹️  Tournament interrupted")
        input("Press Enter to continue...")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tournament failed: {e}")
        input("Press Enter to continue...")

def run_docker_tournament():
    print("\n🐳 Starting Docker Tournament...")
    try:
        subprocess.run(['./quick_tournament_start.sh'], check=True)
        input("\nPress Enter to continue...")
    except KeyboardInterrupt:
        print("\n⏹️  Tournament interrupted")
        input("Press Enter to continue...")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Docker tournament failed: {e}")
        print("Make sure Docker is installed and running")
        input("Press Enter to continue...")

def run_tests():
    print("\n🧪 Running Tournament Tests...")
    try:
        result = subprocess.run([sys.executable, 'test_tournament.py'], 
                              capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        input("\nPress Enter to continue...")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        input("Press Enter to continue...")

def view_results_gui():
    print("\n📊 Starting Pattern Viewer GUI...")
    try:
        subprocess.run([sys.executable, 'run_tournament_pattern_viewer.py'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start viewer: {e}")
        input("Press Enter to continue...")

def view_latest_report():
    print("\n📋 Latest Tournament Report:")
    print("-" * 40)
    
    import glob
    reports = glob.glob('tournament_stats/tournament_report_*.txt')
    if reports:
        latest = max(reports, key=os.path.getctime)
        try:
            with open(latest, 'r') as f:
                content = f.read()
                print(content)
        except Exception as e:
            print(f"❌ Error reading report: {e}")
    else:
        print("No tournament reports found. Run a tournament first!")
    
    input("\nPress Enter to continue...")

def show_settings():
    clear_screen()
    print("⚙️  TOURNAMENT SETTINGS")
    print("=" * 40)
    print()
    
    print("Current Environment Variables:")
    print(f"GAMES_PER_MATCH: {os.environ.get('GAMES_PER_MATCH', '3')}")
    print(f"TIME_PER_GAME: {os.environ.get('TIME_PER_GAME', '180')} seconds")
    print()
    
    print("Configuration File (tournament_config.json):")
    try:
        import json
        with open('tournament_config.json', 'r') as f:
            config = json.load(f)
            print(f"Games per match: {config['tournament_settings']['games_per_match']}")
            print(f"Time per game: {config['tournament_settings']['time_per_game_seconds']}s")
            print(f"Participating bots: {len(config['participating_bots'])}")
            print(f"Pattern detection: {'enabled' if config['pattern_detection']['enabled'] else 'disabled'}")
    except Exception as e:
        print(f"❌ Error reading config: {e}")
    
    print()
    print("To change settings:")
    print("1. Edit tournament_config.json")
    print("2. Set environment variables:")
    print("   export GAMES_PER_MATCH=5")
    print("   export TIME_PER_GAME=300")
    print()
    
    input("Press Enter to continue...")

def show_tournament_files():
    clear_screen()
    print("📁 TOURNAMENT FILES")
    print("=" * 40)
    print()
    
    directories = ['tournament_logs', 'tournament_patterns', 'tournament_stats']
    
    for directory in directories:
        if os.path.exists(directory):
            print(f"\n📂 {directory}/:")
            try:
                files = os.listdir(directory)
                for file in sorted(files):
                    path = os.path.join(directory, file)
                    size = os.path.getsize(path)
                    modified = os.path.getmtime(path)
                    import datetime
                    mod_time = datetime.datetime.fromtimestamp(modified).strftime('%Y-%m-%d %H:%M')
                    print(f"  📄 {file} ({size:,} bytes, {mod_time})")
            except Exception as e:
                print(f"  ❌ Error listing files: {e}")
        else:
            print(f"\n📂 {directory}/: (not created yet)")
    
    print()
    input("Press Enter to continue...")

def main():
    while True:
        show_menu()
        
        try:
            choice = input("Select option (1-8): ").strip()
            
            if choice == '1':
                run_quick_tournament()
            elif choice == '2':
                run_docker_tournament()
            elif choice == '3':
                run_tests()
            elif choice == '4':
                view_results_gui()
            elif choice == '5':
                view_latest_report()
            elif choice == '6':
                show_settings()
            elif choice == '7':
                show_tournament_files()
            elif choice == '8':
                print("\n👋 Goodbye!")
                break
            else:
                print("\n❌ Invalid option. Please select 1-8.")
                input("Press Enter to continue...")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            input("Press Enter to continue...")

if __name__ == "__main__":
    main()
