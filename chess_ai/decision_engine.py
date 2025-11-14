"""Alpha–beta search with selective extensions.

Used by :class:`chess_ai.dynamic_bot.DynamicBot` to deepen analysis.
For a Monte Carlo tree search counterpart see
:class:`chess_ai.batched_mcts.BatchedMCTS`.
"""

import logging
logger = logging.getLogger(__name__)

import chess
import time

from core.quiescence import quiescence
from .risk_analyzer import RiskAnalyzer
from .piece_values import dynamic_piece_value


class DecisionEngine:
    """Selective alpha–beta engine used by :class:`chess_ai.dynamic_bot.DynamicBot`.

    The Monte Carlo equivalent lives in :class:`chess_ai.batched_mcts.BatchedMCTS`.
    """

    def __init__(self, base_depth: int = 2, material_weight: int = 2):
        """Create a new decision engine.

        Parameters
        ----------
        base_depth:
            Minimum search depth for root moves before selective
            extensions are applied.
        material_weight:
            Multiplier used to emphasise material advantage in the
            evaluation.  Capturing valuable pieces should therefore
            outweigh sequences of repeated checks.
        """

        self.risk_analyzer = RiskAnalyzer()
        self.base_depth = base_depth
        self.material_weight = material_weight

    def _evaluate(self, board: chess.Board) -> int:
        """Проста матеріальна оцінка позиції з точки зору гравця, який ходить."""
        score = 0
        for _, piece in board.piece_map().items():
            val = dynamic_piece_value(piece, board)
            score += val if piece.color == board.turn else -val
        return score * self.material_weight

    def search(self, board: chess.Board, depth: int,
               alpha: int = -float("inf"), beta: int = float("inf"),
               deadline: float | None = None) -> int:
        """Alpha-beta negamax search with simple selective extensions and deadline."""
        if deadline is not None and time.monotonic() >= deadline:
            return self._evaluate(board)

        if depth == 0 or board.is_game_over() or board.is_repetition(3):
            # Scale the quiescence search to emphasise material balance
            # without distorting the alpha--beta window.
            scaled_alpha = alpha / self.material_weight
            scaled_beta = beta / self.material_weight
            return quiescence(board, scaled_alpha, scaled_beta) * self.material_weight

        best = float("inf") * -1
        for move in board.legal_moves:
            if deadline is not None and time.monotonic() >= deadline:
                break
            extension = 1 if board.is_capture(move) or board.gives_check(move) else 0
            board.push(move)
            score = -self.search(board, depth - 1 + extension, -beta, -alpha, deadline)
            board.pop()

            if score > best:
                best = score
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break
        if best == float("-inf"):
            return quiescence(board, alpha, beta)
        return best

    def choose_best_move(self, board: chess.Board, *, time_budget_s: float | None = None):
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None

        # Perform comprehensive analysis before move selection
        logger.info("Starting comprehensive move analysis...")
        
        # First prefer tactically safe moves; if none, consider all.
        safe_moves = [m for m in legal_moves if not self.risk_analyzer.is_risky(board, m)]
        moves_to_consider = safe_moves if safe_moves else legal_moves
        
        # Use the new comprehensive analysis system
        chosen_move = None
        if moves_to_consider:
            # If we have safe moves, pick the best one through normal analysis
            if safe_moves:
                chosen_move = self._analyze_and_choose_move(board, safe_moves, time_budget_s, chosen_by_bot=True)
            else:
                # All moves are risky, still need to pick the best one
                chosen_move = self._analyze_and_choose_move(board, legal_moves, time_budget_s, chosen_by_bot=True)
        
        # Generate comprehensive analysis summary
        analysis_summary = self.risk_analyzer.analyze_position(
            board, 
            depth=self.base_depth,
            chosen_move=chosen_move,
            chosen_by_bot=True
        )
        
        return chosen_move

    def _analyze_and_choose_move(self, board: chess.Board, moves: list, time_budget_s: float | None, chosen_by_bot: bool = False):
        """Analyze moves and choose the best one with detailed scoring."""
        # Score moves and annotate tactical features for pyramid ordering.
        # A small tolerance allows choosing a non-repetition move that is
        # slightly worse than the best repetition line.
        REPETITION_TOLERANCE = 60  # centipawns

        deadline: float | None = None
        if time_budget_s is not None:
            deadline = time.monotonic() + time_budget_s

        def _attack_count_after(move: chess.Move) -> int:
            tmp = board.copy(stack=False)
            tmp.push(move)
            to_sq = move.to_square
            enemy = not board.turn
            count = 0
            for sq in tmp.attacks(to_sq):
                p = tmp.piece_at(sq)
                if p and p.color == enemy:
                    count += 1
            return count

        annotated: list[tuple[int, int, bool, bool, int, bool, chess.Move]] = []
        # (score, capture_val, gives_check, is_capture, attack_cnt, repeats, move)
        for move in moves_to_consider:
            if deadline is not None and time.monotonic() >= deadline:
                break
            extension = 1 if board.is_capture(move) or board.gives_check(move) else 0
            capture_val = 0
            if board.is_capture(move):
                target = board.piece_at(move.to_square)
                capture_val = dynamic_piece_value(target, board) if target else 0
            board.push(move)
            # split remaining time across moves
            sub_deadline = None
            if deadline is not None:
                remaining = max(0.0, deadline - time.monotonic())
                sub_deadline = time.monotonic() + remaining / max(1, len(moves_to_consider))
            score = -self.search(board, self.base_depth + extension, deadline=sub_deadline)
            rep = board.is_repetition(3)
            gives_check = board.is_check()
            board.pop()
            score += capture_val * self.material_weight
            is_cap = board.is_capture(move)
            atk_cnt = _attack_count_after(move)
            annotated.append((score, capture_val, gives_check, is_cap, atk_cnt, rep, move))

        if not annotated:
            # fallback: best legal move by static eval within time
            best_mv = None
            best_sc = float("-inf")
            for mv in legal_moves:
                tmp = board.copy(stack=False)
                tmp.push(mv)
                sc = self._evaluate(tmp)
                if sc > best_sc:
                    best_sc = sc
                    best_mv = mv
            return best_mv

        # Compute the best score among repetition moves to gauge disadvantage.
        rep_scores = [sc for sc, _, _, _, _, rep, _ in annotated if rep]
        best_rep_score = max(rep_scores) if rep_scores else -float("inf")

        # Candidate non-repetition moves that are not materially/tactically worse.
        non_rep_good = [t for t in annotated if not t[5] and (t[0] >= best_rep_score - REPETITION_TOLERANCE)]

        # If we have acceptable non-repetition moves, pick by pyramid:
        # check > capture > attack count > score > capture_val deterministically.
        if non_rep_good:
            non_rep_good.sort(key=lambda t: (
                int(t[2]),               # gives_check
                int(t[3]),               # is_capture
                t[4],                    # attack count
                t[0],                    # score
                t[1],                    # capture value
            ), reverse=True)
            return non_rep_good[0][6]

        # Otherwise, if all acceptable alternatives either repeat or are too
        # disadvantageous, allow the best move even if it repeats.
        annotated.sort(key=lambda t: (t[0], t[1]), reverse=True)
        return annotated[0][6]