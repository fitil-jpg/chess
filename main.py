# main.py
import chess
from bot_agent import DynamicBot
from evaluation import evaluate
from pst_tables import PST_MG, PIECE_VALUES

def print_pst_summary():
    print("=== PST SUMMARY (midgame) ===")
    for pt, tbl in PST_MG.items():
        s = sum(tbl)
        mn = min(tbl)
        mx = max(tbl)
        print(f"PieceType {pt}: len={len(tbl)} sum={s} min={mn} max={mx}")
    print("Piece values:", PIECE_VALUES)
    print("=============================")

def run_match(max_plies: int = 40):
    board = chess.Board()
    white = DynamicBot("DynamicBot-White")
    black = DynamicBot("DynamicBot-Black")

    ply = 0
    print_pst_summary()
    print("Start FEN:", board.fen())
    print()

    while not board.is_game_over() and ply < max_plies:
        side = "White" if board.turn == chess.WHITE else "Black"
        bot = white if board.turn == chess.WHITE else black

        move, det = bot.select_move(board)
        board.push(move)
        ply += 1

        # Оцінка після зробленого ходу (позиція належить супернику):
        score, _ = evaluate(board)

        print(f"[Ply {ply:02d}] {side} {bot.name} played {board.peek().uci()}")
        print(f"  material={det['material']}  pst={det['pst']}  mobility={det['mobility']}  "
              f"att_w={det['attacks_white']} att_b={det['attacks_black']}  delta_att={det['delta_attacks']}")
        print(f"  eval_before_push(raw)≈{det['raw_score']}   eval_after={score}")
        print(f"  FEN: {board.fen()}")
        print("-")

    print("Result:", board.result(claim_draw=True))
    print("Game over reason:",
          "checkmate" if board.is_checkmate() else
          "stalemate" if board.is_stalemate() else
          "insufficient material" if board.is_insufficient_material() else
          "seventyfive-move" if board.is_seventyfive_moves() else
          "fivefold repetition" if board.is_fivefold_repetition() else
          "move limit reached"
    )

if __name__ == "__main__":
    # 40 плайів = 20 ходів кожної сторони. Зміни якщо треба.
    run_match(max_plies=40)
