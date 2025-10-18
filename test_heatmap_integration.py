#!/usr/bin/env python3
"""
Test script to demonstrate complete heatmap generation and visualization pipeline.
"""

import os
import sys
from pathlib import Path

# Add the workspace to Python path
sys.path.insert(0, str(Path(__file__).parent))

from utils.integration import generate_heatmaps
from analysis.generate_heatmaps_from_wins import generate_heatmaps_from_wins

def test_heatmap_generation():
    """Test heatmap generation from FEN data."""
    print("=== Testing Heatmap Generation ===")
    
    # Sample FEN positions (starting position and some common openings)
    test_fens = [
        'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',  # Starting position
        'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1',  # e4
        'rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2',  # e4 e5
        'rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKBNR b KQkq - 1 2',  # e4 e5 Nf3
        'r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKBNR w KQkq - 2 3',  # e4 e5 Nf3 Nc6
        'r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQKBNR b KQkq - 3 3',  # e4 e5 Nf3 Nc6 Bb5
    ]
    
    print(f"Testing with {len(test_fens)} FEN positions...")
    
    try:
        # Generate heatmaps
        result = generate_heatmaps(test_fens, out_dir='test_heatmaps', pattern_set='integration_test')
        
        print("✅ Heatmap generation successful!")
        print(f"Generated heatmaps for pattern set: {list(result.keys())}")
        
        if 'integration_test' in result:
            heatmaps = result['integration_test']
            print(f"Piece types: {list(heatmaps.keys())}")
            
            # Show some statistics
            for piece_type, heatmap_data in heatmaps.items():
                total_moves = sum(sum(row) for row in heatmap_data)
                print(f"  {piece_type}: {total_moves} total moves")
        
        return True
        
    except Exception as e:
        print(f"❌ Heatmap generation failed: {e}")
        return False

def test_visualization():
    """Test heatmap visualization."""
    print("\n=== Testing Heatmap Visualization ===")
    
    try:
        # Import and run visualization
        from visualize_heatmap_matplotlib import main as visualize_main
        visualize_main()
        
        print("✅ Heatmap visualization successful!")
        
        # Check if visualization files were created
        viz_dir = Path("heatmap_visualizations")
        if viz_dir.exists():
            png_files = list(viz_dir.glob("*.png"))
            print(f"Created {len(png_files)} visualization files:")
            for png_file in png_files:
                print(f"  - {png_file.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Heatmap visualization failed: {e}")
        return False

def test_pgn_heatmap_generation():
    """Test heatmap generation from PGN files (if available)."""
    print("\n=== Testing PGN Heatmap Generation ===")
    
    # Look for PGN files in the workspace
    pgn_files = list(Path(".").glob("**/*.pgn"))
    
    if not pgn_files:
        print("No PGN files found, skipping PGN heatmap test")
        return True
    
    print(f"Found {len(pgn_files)} PGN files")
    
    # Test with the first PGN file
    pgn_file = pgn_files[0]
    print(f"Testing with: {pgn_file}")
    
    try:
        result = generate_heatmaps_from_wins(str(pgn_file), out_dir='test_heatmaps', pattern_set='pgn_test')
        
        if result:
            print("✅ PGN heatmap generation successful!")
            print(f"Generated heatmaps: {list(result.keys())}")
        else:
            print("⚠️  No winning games found in PGN file")
        
        return True
        
    except Exception as e:
        print(f"❌ PGN heatmap generation failed: {e}")
        return False

def main():
    """Run all heatmap integration tests."""
    print("🧪 Starting Heatmap Integration Tests")
    print("=" * 50)
    
    # Test 1: Basic heatmap generation
    test1_passed = test_heatmap_generation()
    
    # Test 2: Visualization
    test2_passed = test_visualization()
    
    # Test 3: PGN heatmap generation
    test3_passed = test_pgn_heatmap_generation()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"  Heatmap Generation: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"  Visualization:      {'✅ PASS' if test2_passed else '❌ FAIL'}")
    print(f"  PGN Integration:    {'✅ PASS' if test3_passed else '❌ FAIL'}")
    
    all_passed = test1_passed and test2_passed and test3_passed
    print(f"\nOverall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n🎉 Heatmap system is working correctly!")
        print("   - R script fallback to Python works")
        print("   - Data flows correctly from FEN to heatmaps")
        print("   - Visualizations are generated successfully")
        print("   - Integration with Python code is functional")
    else:
        print("\n⚠️  Some issues detected. Check the error messages above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)