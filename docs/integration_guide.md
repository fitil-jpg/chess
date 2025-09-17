# Integration Guide

This guide explains how external projects can interact with the chess
analysis tools of this repository.  The utilities expose functions for
FEN parsing, heatmap generation and metric calculation.

## API functions

```python
from utils.integration import parse_fen, generate_heatmaps, compute_metrics
```

* `parse_fen(fen)` – return an 8×8 board state representation.
* `generate_heatmaps(fens, out_dir="analysis/heatmaps", pattern_set="default")`
  – create heatmap JSON files inside ``<out_dir>/<pattern_set>`` and return
  them grouped by pattern-set name.
* `compute_metrics(fen)` – compute short‑ and long‑term metrics for a
  position.

## Data formats

### Heatmaps

Heatmaps are written as JSON files inside the selected pattern-set directory
(``analysis/heatmaps/default`` by default).  Each file contains an 8×8 matrix
of integers, e.g.

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
default_heatmaps = heatmaps["default"]
metrics = compute_metrics(fen)
```

The ``heatmaps`` dictionary maps pattern-set names to dictionaries of FEN
identifiers and their 8×8 matrices. ``default_heatmaps`` contains the
generated matrices for the default set, while
``metrics`` contains the derived evaluation numbers for the position.

### Generating heatmaps in R

You can render heatmaps in R using ``ggplot2``. First convert the JSON
matrix produced by ``generate_heatmaps`` into a data frame with columns
``x`` and ``y``. Then plot it with:

```r
ggplot(queen_moves, aes(x, y)) +
  geom_bin2d(bins = 8) +
  scale_fill_gradient(low = "white", high = "red") +
  coord_fixed()
```

Replace ``queen_moves`` with your own move data derived from the JSON
heatmap. Output files are saved alongside the CSV input or to the directory
given via ``--outdir`` (``analysis/heatmaps/`` by default).
