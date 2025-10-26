#!/usr/bin/env python3
"""
<<<<<<< HEAD
Runner script for the Chess Pattern Editor/Viewer

This script launches the pattern editor with proper environment setup.
=======
Launcher script for the Chess Pattern Editor/Viewer.
>>>>>>> main
"""

import sys
import os
from pathlib import Path

<<<<<<< HEAD
# Add the workspace to Python path
workspace_path = Path(__file__).parent
sys.path.insert(0, str(workspace_path))

# Set up environment
if not os.environ.get("STOCKFISH_PATH"):
    stockfish_path = workspace_path / "bin" / "stockfish-bin"
    if stockfish_path.exists():
        os.environ["STOCKFISH_PATH"] = str(stockfish_path)

def main():
    """Launch the pattern editor"""
    try:
        from pattern_editor_viewer import main as pattern_main
        pattern_main()
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure all dependencies are installed:")
        print("pip install PySide6 chess")
        sys.exit(1)
    except Exception as e:
        print(f"Error launching pattern editor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
=======
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
>>>>>>> main
