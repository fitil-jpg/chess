#!/usr/bin/env python3
"""
Запуск Enhanced Pattern Viewer
"""

import sys
import os
from pathlib import Path

# Добавляем корень проекта в путь
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Запуск Pattern Viewer"""
    try:
        from enhanced_pattern_viewer import main as viewer_main
        viewer_main()
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure all dependencies are installed:")
        print("pip install PySide6 python-chess")
        return 1
    except Exception as e:
        print(f"Error starting Pattern Viewer: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
