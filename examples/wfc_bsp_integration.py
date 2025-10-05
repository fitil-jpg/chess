"""
Integration examples showing how WFC and BSP engines work with the chess AI system.

This demonstrates practical applications of Wave Function Collapse and Binary Space
Partitioning in chess AI development.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import chess
from chess_ai.wfc_engine import WFCEngine, create_chess_wfc_engine, PatternType
from chess_ai.bsp_engine import BSPEngine, create_chess_bsp_engine
from chess_ai.dynamic_bot import DynamicBot
from core.evaluator import Evaluator


def demonstrate_wfc_pattern_generation():
    """Demonstrate WFC for generating chess patterns."""
    print("=== WFC Pattern Generation Demo ===")
    
    # Create WFC engine
    wfc_engine = create_chess_wfc_engine()
    
    print("Generating opening patterns...")
    for i in range(3):
        board = wfc_engine.generate_pattern()
        if board:
            print(f"\nGenerated Pattern {i+1}:")
            print(board)
            print(f"FEN: {board.fen()}")
        else:
            print(f"Failed to generate pattern {i+1}")


def demonstrate_bsp_board_analysis():
    """Demonstrate BSP for chess board spatial analysis."""
    print("\n=== BSP Board Analysis Demo ===")
    
    # Create BSP engine
    bsp_engine = create_chess_bsp_engine()
    
    # Create a sample board with some pieces
    board = chess.Board()
    board.set_fen("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")  # King's Pawn Opening
    
    print("Analyzing board with BSP zones:")
    print(board)
    
    # Analyze the board
    zone_stats = bsp_engine.analyze_board(board)
    print("\nZone Statistics:")
    for zone_type, stats in zone_stats.items():
        print(f"{zone_type}: {stats['zones']} zones, {stats['total_pieces']} pieces")
    
    # Visualize zones
    print("\n" + bsp_engine.visualize_zones())
    
    # Calculate zone control
    white_control = bsp_engine.calculate_zone_control(board, chess.WHITE)
    black_control = bsp_engine.calculate_zone_control(board, chess.BLACK)
    
    print(f"\nWhite zone control: {white_control}")
    print(f"Black zone control: {black_control}")


def demonstrate_wfc_with_ai_evaluation():
    """Demonstrate WFC pattern generation with AI evaluation."""
    print("\n=== WFC + AI Evaluation Demo ===")
    
    # Create WFC engine and AI evaluator
    wfc_engine = create_chess_wfc_engine()
    
    print("Generating and evaluating patterns...")
    
    best_patterns = []
    for i in range(5):
        board = wfc_engine.generate_pattern()
        if board:
            # Evaluate the position using a simple material count
            score = sum(1 for square in chess.SQUARES if board.piece_at(square))
            
            pattern_info = {
                'board': board,
                'score': score,
                'fen': board.fen()
            }
            best_patterns.append(pattern_info)
            
            print(f"Pattern {i+1}: Score = {score:.2f}")
    
    # Sort by evaluation score
    best_patterns.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"\nBest pattern (Score: {best_patterns[0]['score']:.2f}):")
    print(best_patterns[0]['board'])


def demonstrate_bsp_with_ai_decision():
    """Demonstrate BSP analysis with AI decision making."""
    print("\n=== BSP + AI Decision Making Demo ===")
    
    # Create BSP engine and AI bot
    bsp_engine = create_chess_bsp_engine()
    bot = DynamicBot(chess.WHITE)
    
    # Create a complex position
    board = chess.Board()
    board.set_fen("r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1")
    
    print("Analyzing complex position:")
    print(board)
    
    # Analyze with BSP
    zone_stats = bsp_engine.analyze_board(board)
    print("\nZone Analysis:")
    for zone_type, stats in zone_stats.items():
        if stats['total_pieces'] > 0:
            print(f"{zone_type}: {stats['total_pieces']} pieces")
    
    # Get AI move recommendation
    move, diagnostics = bot.choose_move(board, debug=True)
    print(f"\nAI Recommended Move: {move}")
    
    # Analyze the move's impact on zones
    board.push(move)
    new_zone_stats = bsp_engine.analyze_board(board)
    
    print(f"\nAfter move {move}:")
    for zone_type, stats in new_zone_stats.items():
        if stats['total_pieces'] > 0:
            print(f"{zone_type}: {stats['total_pieces']} pieces")


def demonstrate_hybrid_approach():
    """Demonstrate combining WFC and BSP for advanced chess analysis."""
    print("\n=== Hybrid WFC + BSP Demo ===")
    
    # Create both engines
    wfc_engine = create_chess_wfc_engine()
    bsp_engine = create_chess_bsp_engine()
    
    print("Generating patterns and analyzing spatial structure...")
    
    pattern_analysis = []
    
    for i in range(3):
        # Generate pattern with WFC
        board = wfc_engine.generate_pattern()
        if not board:
            continue
            
        # Analyze with BSP
        zone_stats = bsp_engine.analyze_board(board)
        zone_control = bsp_engine.calculate_zone_control(board, chess.WHITE)
        
        # Evaluate position using simple material count
        score = sum(1 for square in chess.SQUARES if board.piece_at(square))
        
        # Calculate spatial complexity
        spatial_complexity = len([z for z in zone_stats.values() if z['total_pieces'] > 0])
        
        analysis = {
            'board': board,
            'score': score,
            'spatial_complexity': spatial_complexity,
            'zone_control': zone_control,
            'zone_stats': zone_stats
        }
        
        pattern_analysis.append(analysis)
        
        print(f"\nPattern {i+1}:")
        print(f"  Evaluation Score: {score:.2f}")
        print(f"  Spatial Complexity: {spatial_complexity} active zones")
        print(f"  Center Control: {zone_control.get('center', 0):.1f}")
    
    # Find most interesting pattern
    if pattern_analysis:
        best_pattern = max(pattern_analysis, key=lambda x: x['score'] + x['spatial_complexity'])
        print(f"\nMost interesting pattern:")
        print(best_pattern['board'])
        print(f"Score: {best_pattern['score']:.2f}, Complexity: {best_pattern['spatial_complexity']}")


def demonstrate_collision_detection_analogy():
    """Demonstrate how BSP can be used for 'collision detection' in chess."""
    print("\n=== Chess 'Collision Detection' with BSP ===")
    
    bsp_engine = create_chess_bsp_engine()
    
    # Create a position with potential piece interactions
    board = chess.Board()
    board.set_fen("r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1")
    
    print("Analyzing piece interactions (collision detection):")
    print(board)
    
    # Find all pieces
    pieces = []
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            zone = bsp_engine.get_zone_for_square(square)
            pieces.append({
                'piece': piece,
                'square': square,
                'zone': zone,
                'zone_type': zone.zone_type if zone else 'unknown'
            })
    
    # Group pieces by zone
    zone_groups = {}
    for piece_info in pieces:
        zone_type = piece_info['zone_type']
        if zone_type not in zone_groups:
            zone_groups[zone_type] = []
        zone_groups[zone_type].append(piece_info)
    
    print("\nPiece distribution by zone:")
    for zone_type, pieces_in_zone in zone_groups.items():
        print(f"{zone_type}: {len(pieces_in_zone)} pieces")
        for piece_info in pieces_in_zone:
            square_name = chess.square_name(piece_info['square'])
            piece_symbol = piece_info['piece'].symbol()
            print(f"  {piece_symbol} at {square_name}")
    
    # Find potential interactions (pieces in same or adjacent zones)
    print("\nPotential piece interactions:")
    for i, piece1 in enumerate(pieces):
        for j, piece2 in enumerate(pieces[i+1:], i+1):
            zone1 = piece1['zone']
            zone2 = piece2['zone']
            
            if zone1 and zone2:
                if zone1 == zone2:
                    # Same zone
                    square1 = chess.square_name(piece1['square'])
                    square2 = chess.square_name(piece2['square'])
                    print(f"  {piece1['piece'].symbol()} at {square1} and {piece2['piece'].symbol()} at {square2} in same {zone1.zone_type} zone")
                elif zone1 in bsp_engine.get_adjacent_zones(zone2):
                    # Adjacent zones
                    square1 = chess.square_name(piece1['square'])
                    square2 = chess.square_name(piece2['square'])
                    print(f"  {piece1['piece'].symbol()} at {square1} and {piece2['piece'].symbol()} at {square2} in adjacent zones")


def main():
    """Run all demonstration functions."""
    print("WFC and BSP Integration with Chess AI")
    print("=" * 50)
    
    try:
        demonstrate_wfc_pattern_generation()
        demonstrate_bsp_board_analysis()
        demonstrate_wfc_with_ai_evaluation()
        demonstrate_bsp_with_ai_decision()
        demonstrate_hybrid_approach()
        demonstrate_collision_detection_analogy()
        
        print("\n" + "=" * 50)
        print("All demonstrations completed successfully!")
        
    except Exception as e:
        print(f"Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()