#!/usr/bin/env python3
"""Simple script to generate heatmaps from chess game data.

This script provides an easy way to generate heatmaps for the chess analysis UI.
It can generate heatmaps from:
1. Sample game positions (for testing)
2. PGN files (if available)
3. Run data (if available)

Usage:
    python3 generate_heatmaps.py [--sample] [--pgn PGN_FILE] [--runs RUNS_DIR]
"""

import argparse
import sys
from pathlib import Path

from utils.integration import generate_heatmaps
from analysis.generate_heatmaps_from_wins import generate_heatmaps_from_wins
import chess


def generate_sample_heatmaps():
    """Generate heatmaps from sample chess positions."""
    print("🎯 Generating sample heatmaps...")
    
    board = chess.Board()
    sample_fens = []
    
    # Add starting position
    sample_fens.append(board.fen())
    
    # Add some common opening moves
    moves = [
        'e4', 'e5', 'Nf3', 'Nc6', 'Bc4', 'Bc5', 'O-O', 'O-O', 
        'd3', 'd6', 'Nc3', 'Nf6', 'h3', 'h6', 'Be3', 'Be6',
        'Qd2', 'Qd7', 'O-O-O', 'O-O-O', 'g4', 'g5'
    ]
    
    for move in moves:
        try:
            board.push_san(move)
            sample_fens.append(board.fen())
        except:
            break
    
    print(f"Generated {len(sample_fens)} sample positions")
    
    try:
        result = generate_heatmaps(sample_fens, out_dir='analysis/heatmaps', pattern_set='sample')
        print(f"✅ Successfully generated sample heatmaps!")
        print(f"Pattern sets: {list(result.keys())}")
        for pattern_set, heatmaps in result.items():
            print(f"  {pattern_set}: {list(heatmaps.keys())}")
        return True
    except Exception as e:
        print(f"❌ Error generating sample heatmaps: {e}")
        return False


def generate_from_pgn(pgn_file):
    """Generate heatmaps from a PGN file."""
    print(f"📁 Generating heatmaps from PGN file: {pgn_file}")
    
    if not Path(pgn_file).exists():
        print(f"❌ PGN file not found: {pgn_file}")
        return False
    
    try:
        result = generate_heatmaps_from_wins(pgn_file, out_dir='analysis/heatmaps', pattern_set='pgn')
        print(f"✅ Successfully generated heatmaps from PGN!")
        print(f"Pattern sets: {list(result.keys())}")
        for pattern_set, heatmaps in result.items():
            print(f"  {pattern_set}: {list(heatmaps.keys())}")
        return True
    except Exception as e:
        print(f"❌ Error generating heatmaps from PGN: {e}")
        return False


def generate_from_runs(runs_dir):
    """Generate heatmaps from run data."""
    print(f"📊 Generating heatmaps from runs directory: {runs_dir}")
    
    if not Path(runs_dir).exists():
        print(f"❌ Runs directory not found: {runs_dir}")
        return False
    
    try:
        from scripts.generate_heatmaps_from_runs import main as generate_from_runs_main
        # This would need to be adapted to work as a function
        print("⚠️  Run data heatmap generation not yet implemented as a function")
        print("   You can use: python3 scripts/generate_heatmaps_from_runs.py --runs", runs_dir)
        return False
    except Exception as e:
        print(f"❌ Error generating heatmaps from runs: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Generate chess heatmaps for analysis")
    parser.add_argument("--sample", action="store_true", help="Generate sample heatmaps")
    parser.add_argument("--pgn", help="Generate heatmaps from PGN file")
    parser.add_argument("--runs", help="Generate heatmaps from runs directory")
    
    args = parser.parse_args()
    
    if not any([args.sample, args.pgn, args.runs]):
        print("🎯 No options specified. Generating sample heatmaps...")
        args.sample = True
    
    success = True
    
    if args.sample:
        success &= generate_sample_heatmaps()
    
    if args.pgn:
        success &= generate_from_pgn(args.pgn)
    
    if args.runs:
        success &= generate_from_runs(args.runs)
    
    if success:
        print("\n🎉 Heatmap generation completed successfully!")
        print("You can now run the UI viewer to see the heatmaps:")
        print("  python3 pyside_viewer.py")
    else:
        print("\n❌ Some heatmap generation failed. Check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()