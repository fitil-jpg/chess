#!/usr/bin/env python3
"""
Demo script to show Enhanced Bot statistics in PySide viewer.
"""

import sys
import os
sys.path.append('/workspace')

def main():
    """Run the PySide viewer with Enhanced Bot statistics."""
    
    print("🎮 Starting PySide Viewer with Enhanced Bot Statistics")
    print("=" * 60)
    print("Features:")
    print("• Enhanced Bot with detailed statistics tracking")
    print("• AI Stats display in the status panel")
    print("• Reset AI Stats button")
    print("• Real-time statistics updates")
    print("=" * 60)
    
    try:
        from pyside_viewer import ChessViewer
        from PySide6.QtWidgets import QApplication
        
        app = QApplication(sys.argv)
        viewer = ChessViewer()
        viewer.show()
        
        print("✅ PySide Viewer started successfully!")
        print("📊 Look for 'AI Stats' in the status panel")
        print("🔄 Use 'Reset AI Stats' button to reset statistics")
        
        sys.exit(app.exec())
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure PySide6 and other dependencies are installed.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()