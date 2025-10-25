#!/usr/bin/env python3
"""
Launcher script for the Chess Pattern Editor/Viewer.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up environment
if not os.environ.get("STOCKFISH_PATH"):
    stockfish_path = project_root / "bin" / "stockfish-bin"
    if stockfish_path.exists():
        os.environ["STOCKFISH_PATH"] = str(stockfish_path)

# Import and run
from pattern_editor_viewer import main

if __name__ == "__main__":
    print("🎯 Starting Chess Pattern Editor & Viewer...")
    print("=" * 60)
    print("This tool detects and catalogs interesting chess patterns")
    print("during bot vs bot games for learning and analysis.")
    print("=" * 60)
    main()
