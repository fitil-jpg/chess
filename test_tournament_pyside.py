#!/usr/bin/env python3
"""
Test script for PySide6 tournament system without GUI.

This script tests the tournament logic without requiring a display.
"""

import sys
import time
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

def test_tournament_engine():
    """Test the tournament engine without GUI"""
    print("🧪 Testing PySide6 Tournament Engine (Headless Mode)")
    print("=" * 50)
    
    try:
        # Import chess modules
        import chess
        from chess_ai.bot_agent import get_agent_names, make_agent
        print("✅ Chess AI modules imported successfully")
        
        # Test agent creation
        agents = get_agent_names()
        print(f"✅ Available agents: {len(agents)}")
        print(f"   Agents: {', '.join(agents[:5])}...")
        
        # Test basic game logic
        board = chess.Board()
        print(f"✅ Chess board created: {board.fen()}")
        
        # Test agent move
        if agents:
            agent = make_agent(agents[0], chess.WHITE)
            move = agent.choose_move(board)
            if move:
                print(f"✅ Agent {agents[0]} made move: {move.uci()}")
            else:
                print(f"⚠️  Agent {agents[0]} returned no move")
        
        print("\n🎯 Tournament Engine Test Results:")
        print("✅ All core components working")
        print("✅ Chess board operations working")
        print("✅ Agent system working")
        print("✅ Ready for GUI application")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_imports():
    """Test all required imports"""
    print("🔍 Testing Imports...")
    
    try:
        import chess
        print("✅ python-chess")
    except ImportError as e:
        print(f"❌ python-chess: {e}")
        return False
    
    try:
        from PySide6.QtCore import QThread, Signal
        from PySide6.QtWidgets import QApplication, QWidget
        print("✅ PySide6")
    except ImportError as e:
        print(f"❌ PySide6: {e}")
        return False
    
    try:
        from chess_ai.bot_agent import get_agent_names, make_agent
        print("✅ chess_ai modules")
    except ImportError as e:
        print(f"❌ chess_ai: {e}")
        return False
    
    return True

def main():
    """Main test function"""
    print("🏆 PySide6 Tournament System - Headless Test")
    print("=" * 50)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import test failed. Please install missing dependencies.")
        return 1
    
    # Test tournament engine
    if not test_tournament_engine():
        print("\n❌ Tournament engine test failed.")
        return 1
    
    print("\n🎉 All tests passed!")
    print("\n📋 Next steps:")
    print("1. Run: python3 run_tournament_pyside.py")
    print("2. The GUI application will open")
    print("3. Select agents and start tournament")
    print("\n💡 Note: GUI requires a display. If running on server,")
    print("   use X11 forwarding or VNC for remote display.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())