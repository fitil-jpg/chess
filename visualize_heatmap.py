#!/usr/bin/env python3
"""
Visualize the generated heatmap data in a more readable format.
"""

import json
import os

def load_heatmap_data(heatmap_dir="heatmaps"):
    """Load heatmap data from JSON files."""
    heatmaps = {}
    
    for filename in os.listdir(heatmap_dir):
        if filename.startswith("heatmap_") and filename.endswith(".json"):
            piece_type = filename.replace("heatmap_", "").replace("_bins8.json", "")
            filepath = os.path.join(heatmap_dir, filename)
            
            with open(filepath, 'r') as f:
                heatmaps[piece_type] = json.load(f)
    
    return heatmaps

def print_heatmap(piece_type, heatmap_data):
    """Print a heatmap for a specific piece type."""
    print(f"\n{piece_type} Movement Heatmap:")
    print("=" * 40)
    print("    a  b  c  d  e  f  g  h")
    print("  +------------------------+")
    
    for rank in range(8):
        print(f"{8-rank} |", end="")
        for file in range(8):
            value = heatmap_data[rank][file]
            if value == 0:
                print(" . ", end="")
            else:
                print(f"{value:2d} ", end="")
        print(f"| {8-rank}")
    
    print("  +------------------------+")
    print("    a  b  c  d  e  f  g  h")
    
    total_moves = sum(sum(row) for row in heatmap_data)
    print(f"Total moves: {total_moves}")

def create_combined_heatmap(heatmaps):
    """Create a combined heatmap showing all pieces."""
    print("\nCombined Heatmap (All Pieces):")
    print("=" * 50)
    print("    a  b  c  d  e  f  g  h")
    print("  +------------------------+")
    
    # Create combined grid
    combined = [[0 for _ in range(8)] for _ in range(8)]
    
    for piece_type, heatmap_data in heatmaps.items():
        if isinstance(heatmap_data, list) and len(heatmap_data) >= 8:
            for rank in range(8):
                if isinstance(heatmap_data[rank], list) and len(heatmap_data[rank]) >= 8:
                    for file in range(8):
                        if isinstance(heatmap_data[rank][file], (int, float)):
                            combined[rank][file] += heatmap_data[rank][file]
    
    for rank in range(8):
        print(f"{8-rank} |", end="")
        for file in range(8):
            value = combined[rank][file]
            if value == 0:
                print(" . ", end="")
            else:
                print(f"{value:2d} ", end="")
        print(f"| {8-rank}")
    
    print("  +------------------------+")
    print("    a  b  c  d  e  f  g  h")
    
    total_moves = sum(sum(row) for row in combined)
    print(f"Total moves: {total_moves}")

def analyze_game_patterns(heatmaps):
    """Analyze patterns in the game."""
    print("\nGame Analysis:")
    print("=" * 30)
    
    # Count moves by piece type
    piece_counts = {}
    for piece_type, heatmap_data in heatmaps.items():
        total = sum(sum(row) for row in heatmap_data if isinstance(row, list))
        if total > 0:
            piece_counts[piece_type] = total
    
    # Sort by move count
    sorted_pieces = sorted(piece_counts.items(), key=lambda x: x[1], reverse=True)
    
    print("Move frequency by piece:")
    for piece_type, count in sorted_pieces:
        print(f"  {piece_type}: {count} moves")
    
    # Find most active squares
    all_squares = []
    for piece_type, heatmap_data in heatmaps.items():
        if isinstance(heatmap_data, list) and len(heatmap_data) >= 8:
            for rank in range(8):
                if isinstance(heatmap_data[rank], list) and len(heatmap_data[rank]) >= 8:
                    for file in range(8):
                        if isinstance(heatmap_data[rank][file], (int, float)):
                            value = heatmap_data[rank][file]
                            if value > 0:
                                square = f"{chr(ord('a') + file)}{8-rank}"
                                all_squares.append((square, value, piece_type))
    
    # Sort by activity
    all_squares.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\nMost active squares:")
    for square, count, piece in all_squares[:10]:  # Top 10
        print(f"  {square}: {count} moves ({piece})")

def main():
    """Main function to visualize heatmaps."""
    heatmaps = load_heatmap_data()
    
    if not heatmaps:
        print("No heatmap data found in 'heatmaps' directory")
        return
    
    # Print individual heatmaps for pieces with moves
    for piece_type, heatmap_data in heatmaps.items():
        total_moves = sum(sum(row) for row in heatmap_data if isinstance(row, list))
        if total_moves > 0:
            print_heatmap(piece_type, heatmap_data)
    
    # Create combined heatmap
    create_combined_heatmap(heatmaps)
    
    # Analyze patterns
    analyze_game_patterns(heatmaps)

if __name__ == "__main__":
    main()