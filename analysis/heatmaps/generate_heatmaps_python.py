#!/usr/bin/env python3
"""
Python fallback script for heatmap generation.
This script reads FEN data from a CSV file and generates heatmaps for each piece type.
"""

import sys
import json
import csv
from pathlib import Path
from collections import defaultdict

def square_to_coords(square):
    """Convert chess square notation (e.g., 'e4') to 0-based coordinates."""
    file = ord(square[0]) - ord('a')  # 0-7
    rank = int(square[1]) - 1  # 0-7
    return (file, rank)

def coords_to_matrix_index(file, rank):
    """Convert coordinates to matrix indices (8x8 grid with rank 8 at top)."""
    # Rank 8 should be at row 0, rank 1 at row 7
    row = 7 - rank  # 7 - rank (0-7) = 7-0
    col = file      # file (0-7) = 0-7
    return (row, col)

def generate_heatmaps(csv_path, output_dir="."):
    """Generate heatmaps from CSV data."""
    csv_path = Path(csv_path)
    output_dir = Path(output_dir)
    
    if not csv_path.exists():
        print(f"Error: Input CSV file not found: {csv_path}", file=sys.stderr)
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Read CSV data
    piece_counts = defaultdict(lambda: [[0 for _ in range(8)] for _ in range(8)])
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                piece = row['piece']
                square = row['to']
                
                # Convert square to coordinates
                file, rank = square_to_coords(square)
                row_idx, col_idx = coords_to_matrix_index(file, rank)
                
                # Increment count for this piece at this square
                piece_counts[piece][row_idx][col_idx] += 1
                
    except Exception as e:
        print(f"Error reading CSV file: {e}", file=sys.stderr)
        sys.exit(1)
    
    if not piece_counts:
        print("No data found in CSV file")
        return
    
    # Generate heatmap files for each piece
    piece_types = sorted(piece_counts.keys())
    print(f"Processing {len(piece_types)} piece types: {', '.join(piece_types)}")
    
    for piece in piece_types:
        heatmap_matrix = piece_counts[piece]
        
        # Save as JSON
        output_file = output_dir / f"heatmap_{piece}.json"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(heatmap_matrix, f, indent=2)
            print(f"Saved heatmap for {piece} to {output_file}")
        except Exception as e:
            print(f"Error saving heatmap for {piece}: {e}", file=sys.stderr)
    
    print("Heatmap generation completed successfully")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_heatmaps_python.py <input_csv> [output_dir]", file=sys.stderr)
        sys.exit(1)
    
    csv_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "."
    
    generate_heatmaps(csv_path, output_dir)

if __name__ == "__main__":
    main()