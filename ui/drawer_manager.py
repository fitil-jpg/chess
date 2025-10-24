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
        self.heatmap_sets = {}
        self.active_heatmap_set = "default"
        self.heatmaps = {}
        self.active_heatmap_piece = None
        self._load_heatmaps()
        self.agent_metrics = self._load_agent_metrics()
        # Staging for auxiliary overlays (tactical/blue, pruned/violet)
        self._tactical_cells: set[tuple[int, int]] = set()
        self._pruned_cells: set[tuple[int, int]] = set()

    # ------------------------------------------------------------------
    def _load_heatmaps(self):
        """Load heatmap sets from :mod:`analysis.heatmaps`.

        Heatmaps are organised in ``analysis/heatmaps/<set_name>`` directories.
        JSON files directly inside ``analysis/heatmaps`` are treated as the
        ``"default"`` set for backwards compatibility.
        """

        base = Path(__file__).resolve().parent.parent / "analysis" / "heatmaps"
        if not base.exists():
            logger.warning(
                "🔍 Heatmap data directory missing at %s. "
                "Heatmaps provide visual analysis of piece movement patterns. "
                "To generate: run utils.integration.generate_heatmaps() or execute analysis/heatmaps/generate_heatmaps.R. "
                "Requires R or Wolfram Engine installation.", base
            )
            self.heatmap_sets = {}
            self.heatmaps = {}
            self.active_heatmap_piece = None
            return

        heatmap_sets = {}

        def load_from_directory(path):
            mapping = {}
            for file in sorted(path.glob("*.json")):
                try:
                    with file.open("r", encoding="utf-8") as fh:
                        mapping[file.stem] = json.load(fh)
                except json.JSONDecodeError as exc:
                    logger.warning(f"Invalid JSON in heatmap file {file}: {exc}")
                except Exception as exc:
                    logger.warning(f"Failed to load heatmap file {file}: {exc}")
            return mapping

        for subdir in sorted(p for p in base.iterdir() if p.is_dir()):
            mapping = load_from_directory(subdir)
            if mapping:
                heatmap_sets[subdir.name] = mapping

        root_mapping = load_from_directory(base)
        if root_mapping:
            heatmap_sets.setdefault("default", {}).update(root_mapping)

        if not heatmap_sets:
            logger.warning(
                "🔍 No heatmap data found in %s. "
                "Heatmaps show strategic piece movement patterns. "
                "Generate them using: utils.integration.generate_heatmaps() or analysis/heatmaps/generate_heatmaps.R. "
                "Install R or Wolfram Engine first.", base
            )

        self.heatmap_sets = heatmap_sets

        if self.active_heatmap_set not in self.heatmap_sets:
            if "default" in self.heatmap_sets:
                self.active_heatmap_set = "default"
            elif self.heatmap_sets:
                self.active_heatmap_set = next(iter(self.heatmap_sets))
            else:
                self.active_heatmap_set = "default"

        self.heatmaps = self.heatmap_sets.get(self.active_heatmap_set, {})
        if self.active_heatmap_piece not in self.heatmaps:
            self.active_heatmap_piece = next(iter(self.heatmaps), None)

    # ------------------------------------------------------------------
    def _load_agent_metrics(self):
        """Read metrics from ``analysis/agent_metrics.json`` if present."""

        path = Path(__file__).resolve().parent.parent / "analysis" / "agent_metrics.json"
        if path.exists():
            try:
                with path.open("r", encoding="utf-8") as fh:
                    return json.load(fh)
            except json.JSONDecodeError as exc:
                logger.warning(f"Invalid JSON in agent metrics file {path}: {exc}")
                return {}
            except Exception as exc:
                logger.warning(f"Failed to load agent metrics from {path}: {exc}")
                return {}
        return {}

    # ------------------------------------------------------------------
    def collect_overlays(self, piece_objects, board):
        self.overlays.clear()
        self.scenarios.clear()
        self._tactical_cells.clear()
        self._pruned_cells.clear()
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
                try:
                    sq = chess.parse_square(sc.get("square"))
                    row = 7 - chess.square_rank(sq)
                    col = chess.square_file(sq)
                    color = sc.get("color", "purple")
                    self._add_overlay(row, col, "scenario", color)
                    self.scenarios.append({"row": row, "col": col, **sc})
                except Exception as exc:
                    logger.warning(f"Failed to process scenario {sc}: {exc}")
        except Exception as exc:
            logger.warning(f"Scenario detection failed: {exc}")

        self._apply_heatmaps()
        # Apply auxiliary channels last so they sit over gradients
        self._apply_tactical_overlays()
        self._apply_pruned_overlays()

    # ------------------------------------------------------------------
    def set_heatmap_set(self, name):
        """Select the active heatmap set and refresh overlays."""

        if not self.heatmap_sets:
            self.active_heatmap_set = "default"
            self.heatmaps = {}
            self.active_heatmap_piece = None
            self._refresh_heatmap_overlays()
            return

        if name not in self.heatmap_sets:
            name = "default" if "default" in self.heatmap_sets else next(iter(self.heatmap_sets))

        self.active_heatmap_set = name
        self.heatmaps = self.heatmap_sets.get(name, {})
        if self.active_heatmap_piece not in self.heatmaps:
            self.active_heatmap_piece = next(iter(self.heatmaps), None)
        self._refresh_heatmap_overlays()

    # ------------------------------------------------------------------
    def list_heatmap_sets(self):
        """Return available heatmap set names."""

        return sorted(self.heatmap_sets)

    # ------------------------------------------------------------------
    def _refresh_heatmap_overlays(self):
        """Remove existing gradient overlays and apply the active heatmap."""

        if not self.overlays:
            self._apply_heatmaps()
            return

        to_delete = []
        for key, items in list(self.overlays.items()):
            filtered = [item for item in items if item[0] != "gradient"]
            if filtered:
                self.overlays[key] = filtered
            else:
                to_delete.append(key)
        for key in to_delete:
            del self.overlays[key]
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
                except (TypeError, ValueError) as exc:
                    logger.warning(f"Invalid heatmap value at ({r}, {c}): {val} - {exc}")
                    continue
                self._add_gradient_overlay(r, c, v)

    # ------------------------------------------------------------------
    # Public API to feed blue and violet overlays from engines/evaluators
    def mark_tactical_cells(self, cells: list[tuple[int, int]] | set[tuple[int, int]]):
        """Mark cells as tactical (blue overlay).

        Cells are in board grid coordinates (row 0 is top). Duplicate inputs are ignored.
        Call :meth:`collect_overlays` or :meth:`_apply_tactical_overlays` afterwards to render.
        """
        self._tactical_cells.update((int(r), int(c)) for r, c in cells)

    def mark_pruned_cells(self, cells: list[tuple[int, int]] | set[tuple[int, int]]):
        """Mark cells as high-value candidates (violet overlay)."""
        self._pruned_cells.update((int(r), int(c)) for r, c in cells)

    def _apply_tactical_overlays(self):
        for r, c in sorted(self._tactical_cells):
            self._add_overlay(r, c, "tactical", "blue")

    def _apply_pruned_overlays(self):
        for r, c in sorted(self._pruned_cells):
            self._add_overlay(r, c, "pruned", "violet")

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
