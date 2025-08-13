from __future__ import annotations
import chess
from .utility_bot import piece_value


def static_exchange_eval(board: chess.Board, move: chess.Move) -> int:
    """Perform a simple Static Exchange Evaluation (SEE).

    The board is copied, ``move`` is applied and then a sequence of
    alternate captures on the destination square is simulated.  Each side
    always recaptures with its least valuable attacker.  The function
    returns the net material gain for the side to move.  Positive values
    indicate that the capture sequence is favorable, negative that it is
    unfavorable and zero that it is roughly balanced.
    """
    tmp = board.copy(stack=False)
    if not tmp.is_capture(move):
        return 0

    to_sq = move.to_square
    captured = tmp.piece_at(to_sq)
    if captured is None:
        return 0

    gain = [piece_value(captured)]
    side = board.turn
    tmp.push(move)
    side = not side

    while True:
        attackers = tmp.attackers(side, to_sq)
        if not attackers:
            break
        least_sq = min(attackers, key=lambda sq: piece_value(tmp.piece_at(sq)))
        least_piece = tmp.piece_at(least_sq)
        gain.append(piece_value(least_piece) - gain[-1])
        tmp.push(chess.Move(least_sq, to_sq))
        side = not side

    for i in range(len(gain) - 2, -1, -1):
        gain[i] = max(-gain[i + 1], gain[i])

    return gain[0]
