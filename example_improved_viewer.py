#!/usr/bin/env python3
"""
Example usage of the improved ChessViewer with configuration support.
"""

import sys
from PySide6.QtWidgets import QApplication
from ui.chess_viewer_factory import ChessViewerFactory


def main():
    app = QApplication(sys.argv)
    
    print("=== Chess Viewer Configuration Examples ===")
    
    # Example 1: Default viewer with full configuration
    print("\n1. Creating default viewer...")
    viewer1 = ChessViewerFactory.create_full_viewer()
    
    # Example 2: Minimal viewer for testing
    print("2. Creating minimal viewer...")
    viewer2 = ChessViewerFactory.create_minimal_viewer()
    
    # Example 3: Custom viewer with specific settings
    print("3. Creating custom viewer...")
    viewer3 = ChessViewerFactory.create_viewer(
        window_title="Custom Chess Viewer",
        window_min_size=[1000, 700],
        layout_board_size=600,
        layout_console_height=160,
        tab_position="west",
        features_debug_mode=True
    )
    
    # Example 4: Viewer from custom config file
    print("4. Creating viewer from custom config...")
    # You can create a custom JSON config file and load it:
    # viewer4 = ChessViewerFactory.create_viewer("path/to/custom_config.json")
    
    # Show the default viewer (you can change this to test others)
    viewer1.show()
    
    print("\nViewer is ready! Configuration loaded successfully.")
    print("Available features:")
    print("- Configurable window size and position")
    print("- Adjustable board and console dimensions")
    print("- Flexible tab positioning")
    print("- Feature toggles (debug mode, compact mode, etc.)")
    print("- Auto-save window geometry")
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
