#!/usr/bin/env python3
"""
Simple script to run the web-based chess tournament system.

This script provides an easy way to start the tournament with sensible defaults.
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Run the web-based tournament system"""
    
    # Check if we're in the right directory
    if not Path("tournament_web.py").exists():
        print("Error: tournament_web.py not found. Make sure you're in the correct directory.")
        sys.exit(1)
    
    print("🏆 Starting Chess Tournament Web System")
    print("=" * 50)
    print()
    print("This will start a web-based tournament system with:")
    print("• Real-time chess board visualization")
    print("• Live tournament progress tracking")
    print("• Interactive controls for starting/stopping tournaments")
    print("• Statistics and standings")
    print()
    print("The web interface will be available at: http://localhost:5000")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    print()
    
    try:
        # Run the tournament web system
        subprocess.run([sys.executable, "tournament_web.py", "--serve"], check=True)
    except KeyboardInterrupt:
        print("\n\nTournament server stopped by user.")
    except subprocess.CalledProcessError as e:
        print(f"\nError running tournament server: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()