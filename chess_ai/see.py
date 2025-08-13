from __future__ import annotations
import chess

from .utility_bot import piece_value


def static_exchange_eval(board: chess.Board, move: chess.Move) -> int:
    """Perform a static exchange evaluation for ``move`` on ``board``.

    The function simulates the capture sequence on the destination square by
    alternating the least valuable attackers from each side.  The return value
    is the net material gain for the side to move.  A negative result indicates
    the capture sequence loses material."""
    if not board.is_capture(move):
        return 0

    tmp = board.copy(stack=False)
    to_sq = move.to_square
    captured = board.piece_at(to_sq)
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
