#!/usr/bin/env python3
"""
Run the Enhanced Chess Viewer with Pattern Management
"""

import sys
import os
from pathlib import Path

# Add the workspace to Python path
workspace_root = Path(__file__).parent
sys.path.insert(0, str(workspace_root))

# Set environment variables
os.environ.setdefault("STOCKFISH_PATH", "/workspace/bin/stockfish-bin")

if __name__ == "__main__":
    try:
        from enhanced_pyside_viewer import main
        main()
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure all dependencies are installed:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting enhanced viewer: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)