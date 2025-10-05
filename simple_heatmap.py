#!/usr/bin/env python3
"""
Simple heatmap generator for chess games without external dependencies.
This script manually parses PGN moves and creates a heatmap.
"""

import json
import re
from collections import defaultdict

def parse_pgn_moves(pgn_text):
    """Extract moves from PGN text."""
    # Find the moves section (after the headers)
    lines = pgn_text.strip().split('\n')
    moves_section = []
    in_moves = False
    
    for line in lines:
        line = line.strip()
        if line.startswith('['):
            continue  # Skip headers
        if line and not line.startswith('['):
            in_moves = True
            moves_section.append(line)
    
    # Join all move lines and split by spaces
    moves_text = ' '.join(moves_section)
    
    # Remove result (1-0, 0-1, 1/2-1/2)
    moves_text = re.sub(r'\s+(1-0|0-1|1/2-1/2)\s*$', '', moves_text)
    
    # Split by move numbers and extract moves
    moves = []
    move_parts = re.split(r'\d+\.', moves_text)
    
    for part in move_parts[1:]:  # Skip first empty part
        part = part.strip()
        if part:
            # Split white and black moves
            white_black = part.split()
            if len(white_black) >= 1:
                moves.append(('white', white_black[0]))
            if len(white_black) >= 2:
                moves.append(('black', white_black[1]))
    
    return moves

def algebraic_to_coords(algebraic):
    """Convert algebraic notation to coordinates."""
    # Remove check/checkmate symbols
    algebraic = re.sub(r'[+#]', '', algebraic)
    
    # Handle castling
    if algebraic in ['O-O', '0-0']:
        return None  # Skip castling for now
    if algebraic in ['O-O-O', '0-0-0']:
        return None  # Skip castling for now
    
    # Handle pawn moves
    if len(algebraic) == 2:  # e4, d5, etc.
        file = ord(algebraic[0]) - ord('a')
        rank = int(algebraic[1]) - 1
        return (file, rank)
    
    # Handle piece moves (Nf3, Bxc5, etc.)
    if len(algebraic) >= 3:
        # Find the destination square (last 2 characters)
        dest = algebraic[-2:]
        if len(dest) == 2 and dest[0].islower() and dest[1].isdigit():
            file = ord(dest[0]) - ord('a')
            rank = int(dest[1]) - 1
            return (file, rank)
    
    return None

def create_heatmap_from_moves(moves):
    """Create heatmap data from moves."""
    # Initialize 8x8 grid for each piece type
    piece_heatmaps = {
        'P': [[0 for _ in range(8)] for _ in range(8)],  # White pawns
        'N': [[0 for _ in range(8)] for _ in range(8)],  # White knights
        'B': [[0 for _ in range(8)] for _ in range(8)],  # White bishops
        'R': [[0 for _ in range(8)] for _ in range(8)],  # White rooks
        'Q': [[0 for _ in range(8)] for _ in range(8)],  # White queen
        'K': [[0 for _ in range(8)] for _ in range(8)],  # White king
        'p': [[0 for _ in range(8)] for _ in range(8)],  # Black pawns
        'n': [[0 for _ in range(8)] for _ in range(8)],  # Black knights
        'b': [[0 for _ in range(8)] for _ in range(8)],  # Black bishops
        'r': [[0 for _ in range(8)] for _ in range(8)],  # Black rooks
        'q': [[0 for _ in range(8)] for _ in range(8)],  # Black queen
        'k': [[0 for _ in range(8)] for _ in range(8)],  # Black king
    }
    
    # Track piece positions (simplified)
    # This is a very basic implementation
    for color, move in moves:
        coords = algebraic_to_coords(move)
        if coords is None:
            continue
            
        file, rank = coords
        
        # Determine piece type based on move notation
        piece_type = 'P'  # Default to pawn
        if move[0].isupper():  # Piece move
            piece_type = move[0]
        
        # Adjust for color
        if color == 'black':
            piece_type = piece_type.lower()
        
        # Update heatmap
        if 0 <= file < 8 and 0 <= rank < 8:
            piece_heatmaps[piece_type][7-rank][file] += 1
    
    return piece_heatmaps

def generate_simple_heatmap(pgn_text, output_dir="heatmaps"):
    """Generate heatmap for the PGN game."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    moves = parse_pgn_moves(pgn_text)
    print(f"Parsed {len(moves)} moves")
    
    heatmaps = create_heatmap_from_moves(moves)
    
    # Save individual heatmaps as JSON
    for piece_type, heatmap in heatmaps.items():
        filename = f"{output_dir}/heatmap_{piece_type}_bins8.json"
        with open(filename, 'w') as f:
            json.dump(heatmap, f, indent=2)
        print(f"Saved {filename}")
    
    # Create a summary
    summary = {}
    for piece_type, heatmap in heatmaps.items():
        total_moves = sum(sum(row) for row in heatmap)
        if total_moves > 0:
            summary[piece_type] = {
                'total_moves': total_moves,
                'heatmap': heatmap
            }
    
    with open(f"{output_dir}/heatmap_summary.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Heatmap data saved to {output_dir}/")
    return heatmaps

if __name__ == "__main__":
    # The PGN game from the user
    pgn_game = """[Event "Viewer"]
[Site "Local"]
[White "DynamicBot"]
[Black "FortifyBot"]
[Result "1/2-1/2"]

1. e3 d6 2. Qe2 Qd7 3. d3 f6 4. Kd2 c6 5. a3 h6 6. c3 a6 7. f3 e5 8. Nh3 Ne7 9. Nf4 d5 10. h3 f5 11. b4 b5 12. e4 Rg8 13. Ke3 g5 14. Qd2 Rg7 15. Qe2 Ra7 16. Bd2 Qb7 17. g4 Qd7 18. Bg2 Rb7 19. Re1 Ng8 20. Rf1 Qe7 21. Rf2 Qd7 22. Rf1 Qe7 23. Re1 Qd7 24. Rf1 Qe7 25. Re1 Qd7 26. Rf1 Qe7 27. Re1 Qd7 28. Rf1 1/2-1/2"""
    
    heatmaps = generate_simple_heatmap(pgn_game)
    
    # Print a simple text representation
    print("\nHeatmap Summary:")
    print("=" * 50)
    for piece_type, heatmap in heatmaps.items():
        total = sum(sum(row) for row in heatmap)
        if total > 0:
            print(f"\n{piece_type} (total moves: {total}):")
            for i, row in enumerate(heatmap):
                print(f"Rank {8-i}: {' '.join(f'{cell:2d}' for cell in row)}")