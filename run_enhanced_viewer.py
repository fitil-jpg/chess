#!/usr/bin/env python3
"""
Enhanced Chess Viewer Runner

This script runs the enhanced chess viewer with all integrated systems:
- Move evaluation with WFC, BSP, guardrails, and pattern matching
- Real-time visualization of patterns and zones
- Interactive move analysis and bot tracking
"""

import sys
import os
import logging
from pathlib import Path

# Add the workspace to Python path
workspace_path = Path(__file__).parent
sys.path.insert(0, str(workspace_path))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if all required dependencies are available."""
    try:
        import chess
        import numpy as np
        from PySide6.QtWidgets import QApplication
        logger.info("✓ All dependencies available")
        return True
    except ImportError as e:
        logger.error(f"✗ Missing dependency: {e}")
        return False

def initialize_systems():
    """Initialize all chess AI systems."""
    try:
        from chess_ai.move_evaluation import create_move_evaluator
        from chess_ai.wfc_engine import create_chess_wfc_engine
        from chess_ai.bsp_engine import create_chess_bsp_engine
        from chess_ai.guardrails import Guardrails
        from chess_ai.pattern_responder import create_pattern_responder
        
        logger.info("Initializing chess AI systems...")
        
        # Create engines
        wfc_engine = create_chess_wfc_engine()
        bsp_engine = create_chess_bsp_engine()
        guardrails = Guardrails()
        pattern_responder = create_pattern_responder()
        
        logger.info("✓ WFC Engine initialized")
        logger.info("✓ BSP Engine initialized")
        logger.info("✓ Guardrails initialized")
        logger.info("✓ Pattern Responder initialized")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to initialize systems: {e}")
        return False

def create_sample_patterns():
    """Create sample pattern files for demonstration."""
    try:
        patterns_dir = Path("patterns")
        patterns_dir.mkdir(exist_ok=True)
        
        # Create COW opening patterns
        cow_patterns = {
            "patterns": [
                {
                    "situation": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                    "action": "e2e4",
                    "pattern_type": "opening",
                    "confidence": 0.9,
                    "frequency": 0.8,
                    "description": "COW Opening: King's Pawn"
                },
                {
                    "situation": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
                    "action": "e7e6",
                    "pattern_type": "opening",
                    "confidence": 0.9,
                    "frequency": 0.7,
                    "description": "COW Opening: Black King's Pawn"
                },
                {
                    "situation": "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2",
                    "action": "d2d3",
                    "pattern_type": "opening",
                    "confidence": 0.8,
                    "frequency": 0.6,
                    "description": "COW Opening: Queen's Pawn"
                }
            ]
        }
        
        import json
        with open(patterns_dir / "cow_opening.json", 'w') as f:
            json.dump(cow_patterns, f, indent=2)
        
        logger.info("✓ Sample patterns created")
        return True
        
    except Exception as e:
        logger.warning(f"Could not create sample patterns: {e}")
        return False

def main():
    """Main function to run the enhanced viewer."""
    print("=" * 60)
    print("Enhanced Chess Viewer - Move Evaluation & Pattern Analysis")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Missing required dependencies. Please install:")
        print("   pip install chess numpy PySide6")
        return 1
    
    # Initialize systems
    if not initialize_systems():
        print("\n❌ Failed to initialize chess AI systems.")
        return 1
    
    # Create sample patterns
    create_sample_patterns()
    
    print("\n🚀 Starting Enhanced Chess Viewer...")
    print("\nFeatures:")
    print("  • Move evaluation with WFC, BSP, and guardrails")
    print("  • Real-time pattern visualization")
    print("  • Interactive heatmap display")
    print("  • Bot tracking and analysis")
    print("  • COW opening pattern recognition")
    print("\nControls:")
    print("  • ▶ Auto Play: Start automatic game")
    print("  • ⏸ Pause: Pause automatic play")
    print("  • 🔍 Evaluate Move: Analyze current position")
    print("  • 🔄 Reset: Reset game to starting position")
    print("  • Move Delay Slider: Adjust move timing (100-2000ms)")
    print("\nTabs:")
    print("  • 🔍 Move Evaluation: Detailed move analysis")
    print("  • 🔥 Heatmaps: Pattern visualization")
    print("  • 📊 Usage: Statistics and bot tracking")
    
    try:
        from enhanced_pyside_viewer import main as viewer_main
        viewer_main()
        
    except Exception as e:
        logger.error(f"Failed to start viewer: {e}")
        print(f"\n❌ Error starting viewer: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())