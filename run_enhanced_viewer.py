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
import argparse
import platform
import importlib
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

# Add the workspace to Python path
workspace_path = Path(__file__).parent
sys.path.insert(0, str(workspace_path))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _get_module_info(module_name: str) -> Dict[str, Any]:
    """Return best-effort info about a Python module.

    Keys: installed (bool), version (str|None), location (str|None), error (str|None)
    """
    info: Dict[str, Any] = {
        "installed": False,
        "version": None,
        "location": None,
        "error": None,
    }

    try:
        module = importlib.import_module(module_name)
        info["installed"] = True
        # Version resolution (package-specific fallbacks)
        version = getattr(module, "__version__", None)
        if version is None and module_name == "PySide6":
            try:
                from PySide6 import __version__ as pyside_version  # type: ignore
                version = pyside_version
            except Exception:  # pragma: no cover - best effort only
                version = None
        info["version"] = version
        # Location
        module_file = getattr(module, "__file__", None)
        if module_file:
            info["location"] = os.path.dirname(module_file)
    except Exception as e:  # ImportError or any other
        info["error"] = str(e)

    return info


def print_debug_stats(import_error: Optional[BaseException] = None) -> None:
    """Print concise environment and dependency stats to help debug failures.

    Safe to call even if imports fail.
    """
    print("\n--- Debug info (environment & dependencies) ---")
    # Python / Platform
    print(f"Python: {sys.version.splitlines()[0]}")
    print(f"Executable: {sys.executable}")
    print(f"Implementation: {platform.python_implementation()}")
    try:
        print(f"Platform: {platform.platform()}")
    except Exception:
        pass
    print(f"Arch: {platform.machine()} | {platform.architecture()[0]}")

    # Virtual env & paths
    venv = os.environ.get("VIRTUAL_ENV")
    print(f"VIRTUAL_ENV: {venv if venv else '(none)'}")
    py_path = os.environ.get("PYTHONPATH")
    if py_path:
        print(f"PYTHONPATH entries: {len(py_path.split(os.pathsep))}")
    # Show a few sys.path entries
    displayed_paths = sys.path[:5]
    if len(sys.path) > 5:
        displayed_paths.append("…")
        displayed_paths.extend(sys.path[-2:])
    print("sys.path sample:")
    for p in displayed_paths:
        print(f"  - {p}")

    # pip version (best-effort)
    try:
        import pip  # type: ignore
        pip_version = getattr(pip, "__version__", None) or "(unknown)"
        print(f"pip: {pip_version}")
    except Exception as e:
        print(f"pip: not importable ({e})")

    # Key dependencies
    for mod in ("chess", "numpy", "PySide6"):
        info = _get_module_info(mod)
        status = "installed" if info["installed"] else "missing"
        version = info["version"] or "(unknown)"
        location = info["location"] or "(unknown)"
        extra = f" | error: {info['error']}" if info["error"] else ""
        print(f"dep {mod}: {status}, version: {version}, location: {location}{extra}")

    if import_error is not None:
        print(f"last ImportError: {import_error}")

    print("--- End debug info ---\n")

def check_dependencies() -> Tuple[bool, Optional[ImportError]]:
    """Check if all required dependencies are available.

    Returns (ok, import_error)
    """
    try:
        import chess  # noqa: F401
        import numpy as np  # noqa: F401
        from PySide6.QtWidgets import QApplication  # noqa: F401
        logger.info("✓ All dependencies available")
        return True, None
    except ImportError as e:
        logger.error(f"✗ Missing dependency: {e}")
        return False, e

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

def main() -> int:
    """Main function to run the enhanced viewer."""
    parser = argparse.ArgumentParser(description="Enhanced Chess Viewer runner")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print environment and dependency debug stats at startup",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Enhanced Chess Viewer - Move Evaluation & Pattern Analysis")
    print("=" * 60)

    if args.debug:
        print_debug_stats()

    # Check dependencies
    ok, err = check_dependencies()
    if not ok:
        print("\n❌ Missing required dependencies. Please install:")
        # Prefer using the current interpreter to install
        install_hint = f"{sys.executable} -m pip install --upgrade chess numpy PySide6"
        print(f"   {install_hint}")
        print_debug_stats(err)
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