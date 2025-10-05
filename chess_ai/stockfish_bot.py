from __future__ import annotations

import os
import logging
from typing import Optional, Tuple

import chess
try:
    import chess.engine
except Exception as exc:  # pragma: no cover - environments without engine support
    _ENGINE_IMPORT_ERROR = exc
else:
    _ENGINE_IMPORT_ERROR = None

logger = logging.getLogger(__name__)


class StockfishBot:
    """UCI-backed bot using a Stockfish-compatible engine.

    The bot spawns the engine process on first use and reuses it across calls.
    Engine executable path is taken from the ``STOCKFISH_PATH`` environment
    variable by default, falling back to ``stockfish`` on ``PATH``.
    """

    def __init__(
        self,
        color: bool,
        *,
        path: Optional[str] = None,
        think_time_ms: int = 200,
        skill_level: Optional[int] = None,
        uci_elo: Optional[int] = None,
        threads: int = 1,
        hash_mb: int = 128,
    ) -> None:
        self.color = color
        self.path = path or os.environ.get("STOCKFISH_PATH", "stockfish")
        self.think_time_ms = max(10, int(think_time_ms))
        self.skill_level = skill_level
        self.uci_elo = uci_elo
        self.threads = max(1, int(threads))
        self.hash_mb = max(16, int(hash_mb))

        self._engine: Optional["chess.engine.SimpleEngine"] = None

        if _ENGINE_IMPORT_ERROR is not None:  # pragma: no cover - graceful fallback
            logger.warning(
                "python-chess engine module unavailable: %s — StockfishBot will act random",
                _ENGINE_IMPORT_ERROR,
            )

    # --- lifecycle -----------------------------------------------------
    def _ensure_engine(self) -> None:
        if self._engine is not None:
            return
        if _ENGINE_IMPORT_ERROR is not None:
            return
        try:
            self._engine = chess.engine.SimpleEngine.popen_uci(self.path)
        except FileNotFoundError as exc:  # pragma: no cover - binary may be missing
            logger.error("Stockfish executable not found at '%s'", self.path)
            # Leave engine as None to allow graceful fallback in choose_move
            self._engine = None
            return
        except Exception:
            logger.exception("Failed to start UCI engine: %s", self.path)
            # Leave engine as None to allow graceful fallback
            self._engine = None
            return

        # Configure common options if supported
        try:
            opts = {}
            # Threads / Hash
            opts["Threads"] = self.threads
            opts["Hash"] = self.hash_mb
            # Strength controls
            if self.uci_elo is not None:
                # Not all engines support these; best-effort
                opts["UCI_LimitStrength"] = True
                # Clamp to typical Stockfish range [1320..3600]
                elo = int(self.uci_elo)
                if elo < 1000:
                    elo = 1000
                if elo > 3600:
                    elo = 3600
                opts["UCI_Elo"] = elo
            if self.skill_level is not None:
                opts["Skill Level"] = max(0, min(20, int(self.skill_level)))

            self._engine.configure(opts)
        except Exception:
            # Ignore unsupported options
            logger.debug("Some engine options not supported; continuing")

    def close(self) -> None:
        if self._engine is not None:
            try:
                self._engine.quit()
            except Exception:
                pass
            finally:
                self._engine = None

    def __del__(self) -> None:  # pragma: no cover - destructor semantics
        try:
            self.close()
        except Exception:
            pass

    # --- play ----------------------------------------------------------
    def choose_move(
        self,
        board: chess.Board,
        *,
        debug: bool = True,
        **_kwargs,
    ) -> Tuple[Optional[chess.Move], str]:
        """Return engine move for the given position.

        Returns (move, reason). When the engine is unavailable the bot picks a
        random legal move for robustness (and notes that in the reason).
        """
        # Engine-less fallback (keeps tests deterministic)
        if _ENGINE_IMPORT_ERROR is not None:
            moves = list(board.legal_moves)
            mv = min(moves, key=lambda m: m.uci()) if moves else None
            return mv, "STOCKFISH(STUB)"

        self._ensure_engine()
        if self._engine is None:
            moves = list(board.legal_moves)
            mv = min(moves, key=lambda m: m.uci()) if moves else None
            return mv, "STOCKFISH(FAILED)"

        limit = chess.engine.Limit(time=self.think_time_ms / 1000.0)
        try:
            res = self._engine.play(board, limit)
            move = res.move
        except Exception as exc:
            logger.exception("Engine error: %s", exc)
            move = None

        reason = (
            f"STOCKFISH | t={self.think_time_ms}ms"
            + (f" | skill={self.skill_level}" if self.skill_level is not None else "")
            + (f" | elo={self.uci_elo}" if self.uci_elo is not None else "")
        )
        return move, reason
