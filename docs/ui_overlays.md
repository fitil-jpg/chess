# UI Overlays

The viewer can render additional overlays on top of board cells using
`DrawerManager`.  It now understands three sources of analysis data:

* **Heatmaps** – JSON files in the heatmap output directory (e.g.
  `analysis/heatmaps/`) containing 8×8 matrices of numbers in the range
  0–1.  Each value is rendered as a translucent square with a colour
  gradient from green (`0.0`) to red (`1.0`).
* **Agent metrics** – key/value pairs stored in
  `analysis/agent_metrics.json`.  The file is loaded on start and the
  data is available through `DrawerManager.agent_metrics` for debugging
  or displaying aggregate numbers.
* **Scenarios** – patterns detected by :func:`scenarios.detect_scenarios`
  and exposed via ``DrawerManager.scenarios``.  Scenario markers are
  included in :meth:`export_ui_data` and highlighted by the front-end.

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
scenarios = drawer.scenarios
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

The heatmaps are written back into the same directory as `fens.csv` (or
as specified via `--outdir`) and can then be displayed by the viewer.

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
* `--outdir` – directory for generated heatmap files (defaults to the
  directory of the moves CSV).

Run the script with `--help` to see all available options and defaults.

## Shiny heatmap explorer

A minimal Shiny application is provided in `analysis/shiny_app/app.R` for
interactive exploration of heatmaps and detected scenarios.  Start the app
from the repository root with:

```bash
R -e "shiny::runApp('analysis/shiny_app', host='0.0.0.0', port=8000)"
```

The interface lets you pick the piece heatmap to display and filter scenario
markers.  The board visualisation updates automatically to reflect the current
selection.

## Browser component

The repository ships with a lightweight JavaScript helper located at
`ui/fen_board.js`.  It renders a FEN position and applies the overlays and
agent metrics exported by `DrawerManager`.

### Exporting data

```python
import json
import chess
from ui.drawer_manager import DrawerManager

board = chess.Board()
drawer = DrawerManager()
drawer.collect_overlays({}, board)
data = drawer.export_ui_data()
data["fen"] = board.fen()
with open("output/ui_state.json", "w", encoding="utf-8") as fh:
    json.dump(data, fh, indent=2)
```

### Rendering in HTML

```html
<div id="board"></div>
<div id="metrics"></div>
<script type="module">
import {renderFenBoard, renderAgentMetrics} from './ui/fen_board.js';

fetch('output/ui_state.json').then(r => r.json()).then(data => {
  renderFenBoard('board', data.fen, data.overlays, {scenarios: data.scenarios});
  renderAgentMetrics('metrics', data.agent_metrics);
});
</script>
```

The board is drawn using Unicode characters and each overlay entry is
applied as a semi-transparent background colour to the respective cell.
