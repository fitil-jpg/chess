import logging
logger = logging.getLogger(__name__)

import chess

from core.evaluator import Evaluator
from utils import GameContext
from .risk_analyzer import RiskAnalyzer
from .piece_values import dynamic_piece_value
from core.shallow_search import ShallowSearch


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
        self._shallow = ShallowSearch()

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
        candidates: list[tuple[float, chess.Move, bool, bool, int]] = []
        # (score, move, gives_check, is_capture, attack_count)
        for move in board.legal_moves:
            score, _ = self.evaluate_move(board, move, context)
            tmp = board.copy(stack=False)
            tmp.push(move)
            score += evaluator.position_score(tmp, self.color)
            gives_check = tmp.is_check()
            is_cap = board.is_capture(move)
            atk_cnt = 0
            for sq in tmp.attacks(move.to_square):
                p = tmp.piece_at(sq)
                if p and p.color != self.color:
                    atk_cnt += 1
            # Tactical shallow search refinement where it likely pays
            if gives_check or is_cap or move.promotion or atk_cnt >= 2:
                depth = 3 if (gives_check or is_cap) else 2
                sscore, _ = self._shallow.search(tmp, depth=depth)
                # Negate because shallow returns score from opponent to move
                score += 0.25 * (-float(sscore))
            tmp.pop()
            candidates.append((float(score), move, gives_check, is_cap, atk_cnt))
            if score > best_score:
                best_score = float(score)

        # Prefer avoiding immediate threefold repetition when reasonable.
        REP_TOL = 60.0
        rep_best = -float("inf")
        for s, m, _, _, _ in candidates:
            tmp = board.copy(stack=False); tmp.push(m)
            if tmp.is_repetition(3):
                rep_best = max(rep_best, s)
            tmp.pop()

        non_rep_ok: list[tuple[float, chess.Move, bool, bool, int]] = []
        for item in candidates:
            s, m, *_ = item
            tmp = board.copy(stack=False); tmp.push(m)
            rep = tmp.is_repetition(3)
            tmp.pop()
            if not rep and (rep_best == -float("inf") or s >= rep_best - REP_TOL):
                non_rep_ok.append(item)

        chosen: chess.Move | None = None
        if non_rep_ok:
            # Pyramid preference: check > capture > attack_count > score > uci
            non_rep_ok.sort(key=lambda t: (int(t[2]), int(t[3]), t[4], t[0], -ord(t[1].uci()[0])), reverse=True)
            chosen = non_rep_ok[0][1]
            best_score = non_rep_ok[0][0]
        else:
            # Fall back to best score deterministically
            candidates.sort(key=lambda t: (t[0], t[1].uci()))
            chosen = candidates[-1][1]
            best_score = candidates[-1][0]

        return chosen, float(best_score)

    def evaluate_move(self, board, move, context: GameContext | None = None):
        if self.risk_analyzer.is_risky(board, move):
            return float('-inf'), "risky move"

        score = 0
        reasons = []
        opp_color = not self.color
        opp_king_sq = board.king(opp_color)
        repetition = board.is_repetition(2)
        evaluator = Evaluator(board)

        # --- контроль зони навколо нашого короля ДО ходу ---
        our_king_sq = board.king(self.color)
        before_unprotected = 0
        if our_king_sq is not None:
            zone = evaluator.piece_zone(board, our_king_sq, radius=2)
            for sq in zone:
                if board.is_attacked_by(opp_color, sq) and not board.is_attacked_by(self.color, sq):
                    before_unprotected += 1

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

        # --- покращення безпеки нашого короля ---
        after_unprotected = 0
        new_king_sq = temp.king(self.color)
        if new_king_sq is not None:
            zone = evaluator.piece_zone(temp, new_king_sq, radius=2)
            for sq in zone:
                if temp.is_attacked_by(opp_color, sq) and not temp.is_attacked_by(self.color, sq):
                    after_unprotected += 1
        if after_unprotected < before_unprotected:
            bonus = (before_unprotected - after_unprotected) * 30
            score += bonus
            reasons.append(
                f"improves king zone: {before_unprotected}→{after_unprotected} (+{bonus})"
            )

        # --- зменшення зони критичної фігури суперника ---
        critical = evaluator.criticality(board, self.color)
        if critical:
            crit_sq, _ = critical[0]
            crit_piece = board.piece_at(crit_sq)
            if crit_piece:
                if crit_piece.piece_type == chess.KNIGHT:
                    radius = 2
                elif crit_piece.piece_type == chess.KING:
                    radius = 3
                else:
                    radius = 1
                before_zone = evaluator.piece_zone(board, crit_sq, radius)
                before_safe = sum(
                    1 for sq in before_zone if not board.is_attacked_by(self.color, sq)
                )
                if temp.piece_at(crit_sq) is None:
                    after_safe = 0
                else:
                    after_zone = evaluator.piece_zone(temp, crit_sq, radius)
                    after_safe = sum(
                        1 for sq in after_zone if not temp.is_attacked_by(self.color, sq)
                    )
                if after_safe < before_safe:
                    bonus = (before_safe - after_safe) * 20
                    score += bonus
                    reasons.append(
                        f"limits enemy {crit_piece.symbol().upper()} zone: {before_safe}→{after_safe} (+{bonus})"
                    )

        # --- стандартна логіка:
        # 5. Захоплення фігури
        if board.is_capture(move):
            target_piece = board.piece_at(move.to_square)
            from_piece = board.piece_at(move.from_square)
            if target_piece and from_piece:
                # Evaluate pieces with dynamic king-aware values
                if target_piece.piece_type == chess.KING:
                    target_val = calculate_king_value(board, target_piece.color)
                else:
                    target_val = dynamic_piece_value(target_piece, board)
                if from_piece.piece_type == chess.KING:
                    from_val = calculate_king_value(board, from_piece.color)
                else:
                    from_val = dynamic_piece_value(from_piece, board)
                gain = target_val - from_val
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