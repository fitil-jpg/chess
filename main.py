import chess
from metrics.attacked_squares import calculate_attacked_squares

def main():
    board = chess.Board()
    # Place a rook on E1
    board.set_piece_at(chess.E1, chess.Piece(chess.ROOK, chess.WHITE))
    
    # Calculate attacked squares
    rook = board.piece_at(chess.E1)
    attacked_squares = calculate_attacked_squares(rook, board)

    # Print out the results
    print("Attacked squares:")
    for square in attacked_squares:
        print(chess.square_name(square))

if __name__ == "__main__":
    main()
