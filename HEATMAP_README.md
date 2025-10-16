# Chess Heatmap Generation

This document explains how to generate and use heatmaps for chess analysis in this project.

## What are Heatmaps?

Heatmaps show the frequency of piece movements across the chess board, providing visual analysis of strategic patterns. They help identify:
- Common piece placements
- Opening patterns
- Tactical hotspots
- Positional preferences

## Quick Start

### Generate Sample Heatmaps

The easiest way to get started is to generate sample heatmaps:

```bash
python3 generate_heatmaps.py --sample
```

This will create heatmaps from common chess opening positions and save them to `analysis/heatmaps/sample/`.

### Generate Heatmaps from PGN Files

If you have chess games in PGN format:

```bash
python3 generate_heatmaps.py --pgn your_games.pgn
```

This will analyze winning games and generate heatmaps showing where pieces were most frequently placed.

### Generate Heatmaps from Run Data

If you have run data from chess bot games:

```bash
python3 generate_heatmaps.py --runs runs/
```

## Viewing Heatmaps

Once heatmaps are generated, you can view them in the UI:

```bash
python3 pyside_viewer.py
```

The UI will automatically detect available heatmap sets and allow you to:
- Switch between different heatmap sets
- View heatmaps for different piece types
- Analyze strategic patterns

## Technical Details

### File Structure

Heatmaps are stored in `analysis/heatmaps/<pattern_set>/`:
- `heatmap_pawn.json` - Pawn movement patterns
- `heatmap_rook.json` - Rook movement patterns  
- `heatmap_knight.json` - Knight movement patterns
- `heatmap_bishop.json` - Bishop movement patterns
- `heatmap_queen.json` - Queen movement patterns
- `heatmap_king.json` - King movement patterns

Each JSON file contains an 8x8 matrix where each cell represents the frequency of that piece type on that square.

### Dependencies

The heatmap generation requires:
- **R** - For statistical analysis and heatmap generation
- **R packages** - `jsonlite` and `readr` (installed automatically)
- **Python packages** - `python-chess` and other dependencies from `requirements.txt`

### Troubleshooting

#### "No heatmap data found" Warning

This means no heatmaps have been generated yet. Run:

```bash
python3 generate_heatmaps.py --sample
```

#### "Rscript not found" Error

Install R and required packages:

```bash
# On Ubuntu/Debian
sudo apt update && sudo apt install -y r-base
sudo Rscript -e "install.packages(c('jsonlite', 'readr'), repos='https://cran.rstudio.com/')"

# On macOS
brew install r
Rscript -e "install.packages(c('jsonlite', 'readr'), repos='https://cran.rstudio.com/')"
```

#### "No module named 'chess'" Error

Install Python dependencies:

```bash
pip3 install -r requirements.txt
```

## Advanced Usage

### Custom Heatmap Generation

You can generate heatmaps programmatically:

```python
from utils.integration import generate_heatmaps
import chess

# Create some FEN positions
board = chess.Board()
fens = [board.fen()]

# Make some moves
board.push_san('e4')
fens.append(board.fen())

# Generate heatmaps
result = generate_heatmaps(fens, out_dir='analysis/heatmaps', pattern_set='custom')
print(f"Generated heatmaps: {list(result.keys())}")
```

### Multiple Pattern Sets

You can create different heatmap sets for different analysis:

```python
# Generate heatmaps for different scenarios
generate_heatmaps(opening_fens, pattern_set='openings')
generate_heatmaps(endgame_fens, pattern_set='endgames')
generate_heatmaps(tactical_fens, pattern_set='tactics')
```

The UI will automatically detect all available pattern sets and allow switching between them.

## Examples

### Sample Output

After running `python3 generate_heatmaps.py --sample`, you should see:

```
🎯 Generating sample heatmaps...
Generated 8 sample positions
✅ Successfully generated heatmaps!
Pattern sets: ['sample']
  sample: ['queen', 'pawn', 'king', 'knight', 'bishop', 'rook']

🎉 Heatmap generation completed successfully!
```

### Heatmap Data Structure

Each heatmap file contains an 8x8 matrix. For example, `heatmap_pawn.json`:

```json
[
  [0, 0, 0, 0, 0, 0, 0, 0],
  [8, 8, 8, 8, 1, 8, 8, 8],
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 7, 0, 0, 0],
  [0, 0, 0, 0, 6, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0],
  [8, 8, 8, 8, 2, 8, 8, 8],
  [0, 0, 0, 0, 0, 0, 0, 0]
]
```

This shows pawn frequency across the board, with higher numbers indicating more frequent placement.

## Support

If you encounter issues:

1. Check that all dependencies are installed
2. Verify that the `analysis/heatmaps/` directory exists
3. Ensure you have write permissions in the project directory
4. Check the console output for specific error messages

The heatmap system is designed to be robust and provide helpful error messages to guide troubleshooting.