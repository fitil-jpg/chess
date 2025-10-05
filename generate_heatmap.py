#!/usr/bin/env python3
"""
Generate a heatmap for a chess game without requiring R.
This script parses a PGN game and creates a heatmap showing piece movement patterns.
"""

import chess
import chess.pgn
import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
from io import StringIO

def parse_pgn_game(pgn_string):
    """Parse a PGN game string and return the game object."""
    pgn_io = StringIO(pgn_string)
    game = chess.pgn.read_game(pgn_io)
    return game

def extract_piece_movements(game):
    """Extract piece movements from a chess game."""
    board = game.board()
    movements = defaultdict(list)
    
    for move in game.mainline_moves():
        # Get the piece that moved
        piece = board.piece_at(move.from_square)
        if piece:
            piece_symbol = piece.symbol()
            # Convert square to file (a-h) and rank (1-8)
            from_file = chess.square_file(move.from_square)
            from_rank = chess.square_rank(move.from_square)
            to_file = chess.square_file(move.to_square)
            to_rank = chess.square_rank(move.to_square)
            
            movements[piece_symbol].append({
                'from': (from_file, from_rank),
                'to': (to_file, to_rank)
            })
        
        board.push(move)
    
    return movements

def create_heatmap_data(movements, piece_type):
    """Create heatmap data for a specific piece type."""
    if piece_type not in movements:
        return np.zeros((8, 8))
    
    # Create 8x8 grid (files a-h, ranks 1-8)
    heatmap = np.zeros((8, 8))
    
    for move in movements[piece_type]:
        to_file, to_rank = move['to']
        # Convert to array indices (0-7)
        heatmap[7-to_rank, to_file] += 1
    
    return heatmap

def generate_heatmap(pgn_string, output_dir="heatmaps"):
    """Generate heatmaps for all piece types in the game."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    game = parse_pgn_game(pgn_string)
    if not game:
        print("Failed to parse PGN game")
        return
    
    movements = extract_piece_movements(game)
    
    # Define piece types to analyze
    piece_types = ['P', 'N', 'B', 'R', 'Q', 'K', 'p', 'n', 'b', 'r', 'q', 'k']
    
    # Create a figure with subplots for each piece type
    fig, axes = plt.subplots(3, 4, figsize=(16, 12))
    fig.suptitle('Chess Piece Movement Heatmap', fontsize=16)
    
    for i, piece_type in enumerate(piece_types):
        row = i // 4
        col = i % 4
        ax = axes[row, col]
        
        heatmap_data = create_heatmap_data(movements, piece_type)
        
        if np.sum(heatmap_data) > 0:  # Only plot if there are movements
            sns.heatmap(heatmap_data, 
                       annot=True, 
                       fmt='d', 
                       cmap='Reds',
                       ax=ax,
                       cbar_kws={'shrink': 0.8})
            ax.set_title(f'{piece_type} movements')
        else:
            ax.set_title(f'{piece_type} (no movements)')
            ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
        
        # Set labels
        ax.set_xlabel('File (a-h)')
        ax.set_ylabel('Rank (1-8)')
        ax.set_xticklabels(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'])
        ax.set_yticklabels(['8', '7', '6', '5', '4', '3', '2', '1'])
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/chess_heatmap.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Also save individual heatmaps as JSON
    heatmap_data = {}
    for piece_type in piece_types:
        heatmap_data[piece_type] = create_heatmap_data(movements, piece_type).tolist()
    
    with open(f'{output_dir}/heatmap_data.json', 'w') as f:
        json.dump(heatmap_data, f, indent=2)
    
    print(f"Heatmap saved to {output_dir}/chess_heatmap.png")
    print(f"Heatmap data saved to {output_dir}/heatmap_data.json")

if __name__ == "__main__":
    # The PGN game from the user
    pgn_game = """[Event "Viewer"]
[Site "Local"]
[White "DynamicBot"]
[Black "FortifyBot"]
[Result "1/2-1/2"]

1. e3 d6 2. Qe2 Qd7 3. d3 f6 4. Kd2 c6 5. a3 h6 6. c3 a6 7. f3 e5 8. Nh3 Ne7 9. Nf4 d5 10. h3 f5 11. b4 b5 12. e4 Rg8 13. Ke3 g5 14. Qd2 Rg7 15. Qe2 Ra7 16. Bd2 Qb7 17. g4 Qd7 18. Bg2 Rb7 19. Re1 Ng8 20. Rf1 Qe7 21. Rf2 Qd7 22. Rf1 Qe7 23. Re1 Qd7 24. Rf1 Qe7 25. Re1 Qd7 26. Rf1 Qe7 27. Re1 Qd7 28. Rf1 1/2-1/2"""
    
    generate_heatmap(pgn_game)