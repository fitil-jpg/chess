# UI Overlays

The viewer can render additional overlays on top of board cells using
`DrawerManager`.  It now understands two sources of analysis data:

* **Heatmaps** – JSON files in `analysis/heatmaps/` containing 8×8
  matrices of numbers in the range 0–1.  Each value is rendered as a
  translucent square with a colour gradient from green (`0.0`) to red
  (`1.0`).
* **Agent metrics** – key/value pairs stored in
  `analysis/agent_metrics.json`.  The file is loaded on start and the
  data is available through `DrawerManager.agent_metrics` for debugging
  or displaying aggregate numbers.

## Heatmap format

Example `analysis/heatmaps/example.json`:

```json
[
  [0.0, 0.2, 0.1, 0.0, 0.0, 0.1, 0.2, 0.0],
  [0.0, 0.3, 0.4, 0.0, 0.0, 0.4, 0.3, 0.0],
  [0.1, 0.4, 0.6, 0.0, 0.0, 0.6, 0.4, 0.1],
  [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
  [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
  [0.1, 0.4, 0.6, 0.0, 0.0, 0.6, 0.4, 0.1],
  [0.0, 0.3, 0.4, 0.0, 0.0, 0.4, 0.3, 0.0],
  [0.0, 0.2, 0.1, 0.0, 0.0, 0.1, 0.2, 0.0]
]
```

## Usage

```python
import chess
from ui.drawer_manager import DrawerManager

board = chess.Board()
drawer = DrawerManager()

drawer.collect_overlays({}, board)
# Access gradient overlays via drawer.overlays
metrics = drawer.agent_metrics
```

The `MiniBoard` automatically highlights the last move by colouring the
origin and destination squares as well as the piece symbols.

## Generating heatmaps from FEN strings

The loader can convert a collection of FEN positions into the move table
expected by the existing R heatmap script:

```python
from analysis.loader import export_fen_table

fens = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
]
export_fen_table(fens, csv_path="analysis/heatmaps/fens.csv")
```

Generate heatmaps by passing the resulting CSV to the R script:

```bash
Rscript analysis/heatmaps/generate_heatmaps.R analysis/heatmaps/fens.csv
```

The heatmaps are written back into `analysis/heatmaps/` and can then be
displayed by the viewer.

### Customising style

The script accepts options to tune the appearance of the generated
images.  For example:

```bash
Rscript analysis/heatmaps/generate_heatmaps.R \
  --palette Blues --theme classic --resolution 150 \
  analysis/heatmaps/fens.csv
```

* `--palette` – name of an RColorBrewer palette for the colour scale
  (default `Reds`).
* `--theme` – ggplot2 theme function such as `minimal` or `classic`
  (default `minimal`).
* `--resolution` – output image resolution in DPI (default `300`).

Run the script with `--help` to see all available options and defaults.
