# Integration Guide

This guide explains how external projects can interact with the chess
analysis tools of this repository.  The utilities expose functions for
FEN parsing, heatmap generation and metric calculation.

## API functions

```python
from utils.integration import parse_fen, generate_heatmaps, compute_metrics
```

* `parse_fen(fen)` – return an 8×8 board state representation.
* `generate_heatmaps(fens, out_dir="analysis/heatmaps")` – create
  heatmap JSON files and return them as dictionaries.
* `compute_metrics(fen)` – compute short‑ and long‑term metrics for a
  position.

## Data formats

### Heatmaps

Heatmaps are written as JSON files inside ``analysis/heatmaps/``.  Each
file contains an 8×8 matrix of integers, e.g.

```json
[[0,1,0,0,0,0,0,0],
 [0,0,0,0,0,0,0,0],
 ...]
```

### Metrics

Metrics follow a nested JSON structure where scores are grouped into
``short_term`` and ``long_term`` categories:

```json
{
  "short_term": {"attacked_squares": 3, "defended_pieces": -1},
  "long_term": {"center_control": 2, "king_safety": 0,
                  "pawn_structure_stability": -1}
}
```

## Example usage

```python
from utils.integration import parse_fen, generate_heatmaps, compute_metrics

fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

board_state = parse_fen(fen)
heatmaps = generate_heatmaps([fen])
metrics = compute_metrics(fen)
```

The ``heatmaps`` dictionary maps FEN identifiers to 8×8 matrices, while
``metrics`` contains the derived evaluation numbers for the position.
