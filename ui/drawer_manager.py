import json
import logging
from pathlib import Path

import chess

from scenarios import detect_scenarios

logger = logging.getLogger(__name__)


class DrawerManager:
    def __init__(self):
        self.overlays = {}
        self.scenarios = []
        self.heatmaps = self._load_heatmaps()
        self.agent_metrics = self._load_agent_metrics()
        # Currently selected heatmap piece name (e.g. "knight" or None)
        self.active_heatmap_piece = None

    # ------------------------------------------------------------------
    def _load_heatmaps(self):
        """Load all JSON heatmaps from :mod:`analysis.heatmaps`.

        Each file is expected to contain an 8×8 matrix of values between
        0 and 1.  The matrices are stored in a dict keyed by the file stem.
        Missing directories result in an empty mapping.
        """

        heatmaps = {}
        base = Path(__file__).resolve().parent.parent / "analysis" / "heatmaps"
        default_dir = base / "default"
        if default_dir.exists():
            search_dir = default_dir
        else:
            search_dir = base

        if not search_dir.exists():
            logger.warning(
                "Heatmap data missing – generate files via "
                "`utils.integration.generate_heatmaps` or "
                "`analysis/heatmaps/generate_heatmaps.R`."
            )
            return heatmaps

        files = list(search_dir.glob("*.json"))
        if not files:
            logger.warning(
                "Heatmap data missing – generate files via "
                "`utils.integration.generate_heatmaps` or "
                "`analysis/heatmaps/generate_heatmaps.R`."
            )
            return heatmaps

        for file in files:
            try:
                with file.open("r", encoding="utf-8") as fh:
                    heatmaps[file.stem] = json.load(fh)
            except Exception:
                continue
        return heatmaps

    # ------------------------------------------------------------------
    def _load_agent_metrics(self):
        """Read metrics from ``analysis/agent_metrics.json`` if present."""

        path = Path(__file__).resolve().parent.parent / "analysis" / "agent_metrics.json"
        if path.exists():
            try:
                with path.open("r", encoding="utf-8") as fh:
                    return json.load(fh)
            except Exception:
                return {}
        return {}

    # ------------------------------------------------------------------
    def collect_overlays(self, piece_objects, board):
        self.overlays.clear()
        self.scenarios.clear()
        for sq, obj in piece_objects.items():
            if hasattr(obj, "safe_moves"):
                for s in obj.safe_moves:
                    row = 7 - chess.square_rank(s)
                    col = chess.square_file(s)
                    self._add_overlay(row, col, "king_safe", "white" if obj.color else "black")
            if hasattr(obj, "attacked_moves"):
                for s in obj.attacked_moves:
                    row = 7 - chess.square_rank(s)
                    col = chess.square_file(s)
                    self._add_overlay(row, col, "king_attacked", "red")
            if hasattr(obj, "defended_moves"):
                for s in obj.defended_moves:
                    row = 7 - chess.square_rank(s)
                    col = chess.square_file(s)
                    self._add_overlay(row, col, "rook_defended", "blue")
            if hasattr(obj, "fork_moves"):
                for s in obj.fork_moves:
                    row = 7 - chess.square_rank(s)
                    col = chess.square_file(s)
                    self._add_overlay(row, col, "knight_fork", "magenta")
            if hasattr(obj, "hanging_targets"):
                for s in obj.hanging_targets:
                    row = 7 - chess.square_rank(s)
                    col = chess.square_file(s)
                    self._add_overlay(row, col, "queen_hanging", "orange")
            if hasattr(obj, "pin_moves"):
                for s in obj.pin_moves:
                    row = 7 - chess.square_rank(s)
                    col = chess.square_file(s)
                    self._add_overlay(row, col, "pin", "cyan")
            if hasattr(obj, "check_squares"):
                for s in obj.check_squares:
                    row = 7 - chess.square_rank(s)
                    col = chess.square_file(s)
                    self._add_overlay(row, col, "check", "yellow")
        # scenario detection on current board
        try:
            for sc in detect_scenarios(board.fen()):
                sq = chess.parse_square(sc.get("square"))
                row = 7 - chess.square_rank(sq)
                col = chess.square_file(sq)
                color = sc.get("color", "purple")
                self._add_overlay(row, col, "scenario", color)
                self.scenarios.append({"row": row, "col": col, **sc})
        except Exception:
            pass

        self._apply_heatmaps()

    # ------------------------------------------------------------------
    def _apply_heatmaps(self):
        """Convert selected heatmap into gradient overlays.

        Only the grid corresponding to ``active_heatmap_piece`` is applied.
        """

        if not self.active_heatmap_piece:
            return

        grid = self.heatmaps.get(self.active_heatmap_piece)
        if not grid:
            return

        for r, row in enumerate(grid):
            for c, val in enumerate(row):
                try:
                    v = float(val)
                except (TypeError, ValueError):
                    continue
                self._add_gradient_overlay(r, c, v)

    # ------------------------------------------------------------------
    def _add_overlay(self, row, col, overlay_type, color):
        if (row, col) not in self.overlays:
            self.overlays[(row, col)] = []
        self.overlays[(row, col)].append((overlay_type, color))

    def _add_gradient_overlay(self, row, col, value):
        value = max(0.0, min(1.0, value))
        r = int(value * 255)
        g = int((1 - value) * 255)
        color = f"#{r:02x}{g:02x}00"
        self._add_overlay(row, col, "gradient", color)

    # ------------------------------------------------------------------
    def get_cell_overlays(self, row, col):
        return self.overlays.get((row, col), [])

    # ------------------------------------------------------------------
    def export_ui_data(self):
        """Return overlays, heatmaps and metrics for front-end consumers.

        The overlays are returned as an 8×8 matrix where each entry is a list
        of ``(type, colour)`` tuples.  Heatmap values are also included so a
        web client can reconstruct the gradient if desired.  Agent metrics are
        relayed verbatim from :mod:`analysis.agent_metrics.json`.
        """

        grid = [[[] for _ in range(8)] for _ in range(8)]
        for (r, c), items in self.overlays.items():
            grid[r][c] = items
        return {
            "overlays": grid,
            "heatmaps": self.heatmaps,
            "agent_metrics": self.agent_metrics,
            "scenarios": self.scenarios,
        }
