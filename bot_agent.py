# bot_agent.py
import chess
from evaluation import evaluate
# Guardrails are optional in the lightweight DynamicBot used by tests.
# If importing the full module pulls heavy dependencies (or a stubbed
# chess module lacks constants), fall back to a no-op implementation.
try:  # pragma: no cover - exercised indirectly in tests
    from chess_ai.guardrails import Guardrails  # type: ignore
except Exception:  # pragma: no cover - graceful degradation in stub envs
    class Guardrails:  # type: ignore
        def is_legal_and_sane(self, board, move) -> bool:
            try:
                return move in getattr(board, "legal_moves", [])
            except Exception:
                return True

        def is_high_value_hang(self, board, move) -> bool:
            return False

        def is_blunder(self, board, move) -> bool:
            return False

# Optional metrics registry integration.  The registry is best-effort and
# must never affect move selection in this lightweight bot.
try:  # pragma: no cover - integration is optional for tests
    from metrics import registry as metrics_registry  # type: ignore
except Exception:  # pragma: no cover - missing optional dependency
    metrics_registry = None  # type: ignore

class DynamicBot:
    """
    Дуже простий динамічний бот: depth=1 (оцінює позицію після власного ходу).
    Мета — показати розкладку оцінки + увімкнути PST (не нулі).
    """

    def __init__(self, name: str = "DynamicBot"):
        self.name = name
        self.guardrails = Guardrails()

    def select_move(self, board: chess.Board) -> tuple[chess.Move, dict]:
        best_move = None
        best_score = -10**9
        best_details = {}

        for move in board.legal_moves:
            # Guardrails: skip illegal/insane and high-value hangs; penalize blunders
            if not self.guardrails.is_legal_and_sane(board, move):
                continue
            if self.guardrails.is_high_value_hang(board, move):
                continue
            mover = board.turn
            board.push(move)
            sc, det = evaluate(board)

            # Best-effort evaluator chain: compute auxiliary metrics for debug
            # logging without influencing the choice.
            metrics_summary = {}
            if metrics_registry is not None:
                try:  # pragma: no cover - side logging only
                    metrics_summary = metrics_registry.evaluate_all(board)
                except Exception:
                    metrics_summary = {}
            board.pop()
            # Compute side-aware score first, then apply penalty consistently
            side_factor = 1 if mover == chess.WHITE else -1
            sided_score = side_factor * sc
            if self.guardrails.is_blunder(board, move):
                sided_score -= 300  # penalty in centipawns
            # Якщо хід робить ЧОРНИЙ — загальна оцінка з точки зору БІЛИХ все ще sc,
            # але бот (за чорних) максимізує свою користь, тобто *мінімізує* sc.

            if sided_score > best_score:
                best_score = sided_score
                best_move = move
                best_details = det | {
                    "raw_score": sc,
                    "metrics": metrics_summary,
                }

        # Optional log for humans running the CLI: brief metrics summary.
        if metrics_registry is not None and best_details.get("metrics"):
            try:  # pragma: no cover - print-only
                pairs = ", ".join(f"{k}={v}" for k, v in sorted(best_details["metrics"].items()))
                print(f"[DynamicBot] metrics: {pairs}")
            except Exception:
                pass

        return best_move, best_details
