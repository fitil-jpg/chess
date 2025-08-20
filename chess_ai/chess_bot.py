import chess

from core.evaluator import Evaluator
from utils import GameContext
from .risk_analyzer import RiskAnalyzer
from .piece_values import dynamic_piece_value


_SHARED_EVALUATOR: Evaluator | None = None

CENTER_SQUARES = [chess.E4, chess.D4, chess.E5, chess.D5]

# Additional score applied for each point of material deficit when
# considering capturing moves.  Encourages material recovery when behind.
MATERIAL_DEFICIT_BONUS = 10


def calculate_king_value(board: chess.Board, color: chess.Color | None = None) -> int:
    """Return a dynamic material value for the king.

    The king's value scales with the material of its own side to roughly
    reflect how difficult it is to checkmate.  It is computed as::

        8*P + 2*B + 2*N + 2*R + Q

    where ``P`` is the number of allied pawns and so on.  If the opponent has
    no queen the king is considered slightly safer and its value is reduced by
    15%.

    Parameters
    ----------
    board:
        Current position to evaluate.
    color:
        Side for which to compute the king's value.  Defaults to the side to
        move.
    """

    if color is None:
        color = board.turn

    value = (
        8 * len(board.pieces(chess.PAWN, color))
        + 2 * len(board.pieces(chess.BISHOP, color))
        + 2 * len(board.pieces(chess.KNIGHT, color))
        + 2 * len(board.pieces(chess.ROOK, color))
        + len(board.pieces(chess.QUEEN, color))
    )

    if not board.pieces(chess.QUEEN, not color):
        value = int(value * 0.85)

    return value

class ChessBot:
    def __init__(self, color: bool):
        self.color = color
        self.risk_analyzer = RiskAnalyzer()

    def choose_move(
        self,
        board: chess.Board,
        context: GameContext | None = None,
        evaluator: Evaluator | None = None,
        debug: bool = False,
    ):
        """Return the move with the highest evaluation score.

        Parameters
        ----------
        board: chess.Board
            Position to analyse.
        context: GameContext | None, optional
            Shared positional context used for additional heuristics such as
            material-deficit bonuses.
        evaluator: Evaluator | None, optional
            Reusable evaluator instance.  A shared one is created if ``None``.
        debug: bool, optional
            Unused flag retained for compatibility.

        Returns
        -------
        tuple[chess.Move | None, float]
            Chosen move and its evaluation score.
        """

        global _SHARED_EVALUATOR
        evaluator = evaluator or _SHARED_EVALUATOR
        if evaluator is None:
            evaluator = _SHARED_EVALUATOR = Evaluator(board)

        best_score = float("-inf")
        best_moves = []
        for move in board.legal_moves:
            score, _ = self.evaluate_move(board, move, context)
            tmp = board.copy(stack=False)
            tmp.push(move)
            score += evaluator.position_score(tmp, self.color)
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)
        # Pick a deterministic move to keep tests stable.  When multiple
        # moves share the best score, choose the one with the smallest UCI
        # string so that results are reproducible.
        move = min(best_moves, key=lambda m: m.uci()) if best_moves else None
        return move, float(best_score if best_moves else 0.0)

    def evaluate_move(self, board, move, context: GameContext | None = None):
        if self.risk_analyzer.is_risky(board, move):
            return float('-inf'), "risky move"

        score = 0
        reasons = []
        opp_color = not self.color
        opp_king_sq = board.king(opp_color)
        repetition = board.is_repetition(2)

        # 1. Кількість safe square у суперника ДО ходу
        before_safe = []
        for m in board.legal_moves:
            if m.from_square == opp_king_sq:
                to_sq = m.to_square
                if not board.is_attacked_by(self.color, to_sq):
                    before_safe.append(to_sq)

        # 2. Кількість safe square у суперника ПІСЛЯ ходу
        temp = board.copy()
        temp.push(move)
        after_safe = []
        opp_king_sq_after = temp.king(opp_color)
        for m in temp.legal_moves:
            if m.from_square == opp_king_sq_after:
                to_sq = m.to_square
                if not temp.is_attacked_by(self.color, to_sq):
                    after_safe.append(to_sq)

        # 3. Якщо safe square стало менше — бонус
        if len(after_safe) < len(before_safe):
            bonus = 100 + (len(before_safe) - len(after_safe)) * 20
            score += bonus
            reasons.append(f"reduced enemy king safe squares: {len(before_safe)}→{len(after_safe)} (+{bonus})")

        # 4. Якщо цей хід атакує нову safe square і під захистом
        if opp_king_sq is not None and move.to_square in before_safe:
            defenders = temp.attackers(self.color, move.to_square)
            attackers = temp.attackers(opp_color, move.to_square)
            if defenders and not attackers:
                score += 40
                reasons.append("attacks king's safe square under protection (+40)")

        # --- стандартна логіка:
        # 5. Захоплення фігури
        if board.is_capture(move):
            target_piece = board.piece_at(move.to_square)
            from_piece = board.piece_at(move.from_square)
            if target_piece and from_piece:
                gain = dynamic_piece_value(target_piece, board) - dynamic_piece_value(from_piece, board)
                score += gain
                if context and context.material_diff < 0:
                    bonus = abs(context.material_diff) * MATERIAL_DEFICIT_BONUS
                    score += bonus
                    reasons.append(f"material deficit capture bonus (+{bonus})")
                defenders = board.attackers(not board.turn, move.to_square)
                if not defenders:
                    score += 100
                    reasons.append(
                        f"capture hanging {target_piece.symbol().upper()} (+{100 + gain})"
                    )
                else:
                    reasons.append(
                        f"capture defended {target_piece.symbol().upper()} (+{gain})"
                    )
                if repetition and gain > 0:
                    score += 150
                    reasons.append(
                        "avoid repetition: capture bonus (+150)"
                    )
        # 6. Центр
        if move.to_square in CENTER_SQUARES:
            score += 30
            reasons.append("center control")
        # 7. Розвиток
        from_sq = move.from_square
        piece = board.piece_at(from_sq)
        if piece and piece.piece_type in [chess.KNIGHT, chess.BISHOP] and (from_sq in [chess.B1, chess.G1, chess.B8, chess.G8]):
            score += 10
            reasons.append("develop piece")
        # 8. Promotion
        if move.promotion:
            score += 90
            reasons.append("promotion")
        # Avoid random noise to make evaluations deterministic for tests.
        return score, " | ".join(reasons)
