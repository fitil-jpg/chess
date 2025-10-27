#!/usr/bin/env python3
"""
Simple script to run the PySide6 chess tournament application.

This script provides an easy way to start the tournament with PySide6.
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Run the PySide6 tournament application"""
    
    # Check if we're in the right directory
    if not Path("tournament_pyside.py").exists():
        print("Error: tournament_pyside.py not found. Make sure you're in the correct directory.")
        sys.exit(1)
    
    print("🏆 Starting Chess Tournament PySide6 Application")
    print("=" * 50)
    print()
    print("This will start a professional PySide6 tournament application with:")
    print("• Real-time chess board visualization")
    print("• Interactive tournament controls")
    print("• Live statistics and standings")
    print("• Professional Qt interface")
    print()
    print("The application will open in a new window.")
    print()
    print("Press Ctrl+C to stop the application")
    print("=" * 50)
    print()
    
    try:
        # Check if PySide6 is available
        try:
            import PySide6
            print("✅ PySide6 is available")
        except ImportError:
            print("❌ PySide6 not found. Installing...")
            subprocess.run([sys.executable, "-m", "pip", "install", "PySide6"], check=True)
            print("✅ PySide6 installed successfully")
        
        # Run the tournament application
        subprocess.run([sys.executable, "tournament_pyside.py"], check=True)
    except KeyboardInterrupt:
        print("\n\nTournament application stopped by user.")
    except subprocess.CalledProcessError as e:
        print(f"\nError running tournament application: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()