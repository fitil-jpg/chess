"""Generate heatmaps from winning games in a PGN file."""

from __future__ import annotations

from typing import List

from .pgn_loader import stream_pgn_games
from utils.integration import generate_heatmaps


_WIN_RESULTS = {"1-0", "0-1"}


def generate_heatmaps_from_wins(
    path: str,
    *,
    out_dir: str = "analysis/heatmaps",
    use_wolfram: bool = False,
):
    """Generate heatmaps for positions taken from decisive games.

    Parameters
    ----------
    path:
        Path to a PGN file.
    out_dir:
        Directory where the generated heatmaps should be written.  This is
        forwarded to :func:`utils.integration.generate_heatmaps`.
    use_wolfram:
        Whether to use the Wolfram implementation instead of the default R
        script when generating heatmaps.

    Returns
    -------
    Dict[str, List[List[int]]]
        The heatmaps produced by :func:`utils.integration.generate_heatmaps`.
    """

    winning_fens: List[str] = []
    for game in stream_pgn_games(path):
        metadata = game.get("metadata", {})
        result = metadata.get("Result")
        if result in _WIN_RESULTS:
            winning_fens.extend(game.get("fens", []))

    return generate_heatmaps(winning_fens, out_dir=out_dir, use_wolfram=use_wolfram)
