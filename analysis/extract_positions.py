from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Iterable


def extract_positions(fens: Iterable[str], csv_path: str) -> None:
    """Call the R script to extract piece coordinates from *fens*.

    Parameters
    ----------
    fens:
        Iterable of FEN strings.
    csv_path:
        Output CSV path that will contain columns ``file``, ``rank`` and ``piece``.
    """

    script = Path(__file__).with_name("extract_positions.R")
    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as tmp:
        for fen in fens:
            tmp.write(f"{fen}\n")
        tmp_path = tmp.name

    subprocess.run(["Rscript", str(script), tmp_path, csv_path], check=True)
