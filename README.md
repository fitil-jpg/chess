## Pattern JSON schema (user-extensible)

Store user patterns as standalone JSON files under `patterns/` for easy add/remove. A minimal schema aligns with `chess_ai.pattern_detector.ChessPattern.to_dict()`:

```json
{
  "version": "1.0",
  "patterns": [
    {
      "fen": "<full FEN before move>",
      "move": "<SAN or UCI>",
      "pattern_types": ["fork", "pin", "exchange", "tactical_moment", ...],
      "description": "free text",
      "influencing_pieces": [
        {"square":"e4","piece":"Knight","color":"white","relationship":"attacker"}
      ],
      "evaluation": {"before": {"total": 0}, "after": {"total": 50}, "change": 50},
      "metadata": {
        "focus_squares": ["e4","f6","d5"],
        "move_uci": "e4f6",
        "exchange_sequence": ["e4f6","g7f6"],
        "exchange_net": -100,
        "tags": ["capture","check"],
        "added_at": "2025-10-26T00:00:00"
      }
    }
  ]
}
```

The viewer will auto-focus on `metadata.focus_squares` and dim non-participating pieces.
# Chess AI

See [AGENTS.md](AGENTS.md) for an overview of the available bots. Development guidelines and testing instructions are in [CONTRIBUTING.md](CONTRIBUTING.md).


For a focused trapping strategy, see [docs/piece_mate_bot.md](docs/piece_mate_bot.md) describing `PieceMateBot` (UA).


## Meta Mode

The project includes a *meta* mode implemented by `DynamicBot`, which acts as an
aggregator for multiple sub-bots. Each sub-bot contributes a move suggestion
along with a confidence value.  The meta-agent multiplies each confidence by the
assigned weight and sums the results per move.

### Weight format

Weights are provided as a dictionary mapping agent names to floating point
values when creating `DynamicBot`:

```python
from chess_ai.dynamic_bot import DynamicBot
import chess

# RandomBot is disabled by default; pass a positive weight to enable it.
bot = DynamicBot(
    chess.WHITE, weights={"aggressive": 1.5, "fortify": 0.5, "random": 0.5}
)
```

### DynamicBot ensemble improvements

`DynamicBot` now supports advanced ensembling features:

- Phase-aware weights: provide different sub-agent weights per game phase (`opening`, `middlegame`, `endgame`).
- Diversity bonus: reward non-overlapping agent ideas to encourage coverage of alternative plans.
- Contextual bandit: adapt agent weights online per position-type bucket.

Usage examples:

```python
from chess_ai.dynamic_bot import DynamicBot
import chess

board = chess.Board()

# 1) Phase-aware weights (preferred)
bot = DynamicBot(
    color=chess.WHITE,
    phase_weights={
        "opening": {"aggressive": 1.5, "fortify": 0.7},
        "middlegame": {"critical": 1.2, "center": 1.0},
        "endgame": {"endgame": 1.6},
    },
)

# 2) Or pass a nested mapping via `weights`
bot = DynamicBot(
    color=chess.WHITE,
    weights={
        "opening": {"aggressive": 1.5},
        "middlegame": {"critical": 1.2},
        "endgame": {"endgame": 1.6},
        # fallback defaults used for other agents if not specified
    },
)

# 3) Configure diversity and bandit
bot = DynamicBot(
    color=chess.WHITE,
    enable_diversity=True,
    diversity_bonus=0.25,   # default 0.25
    enable_bandit=True,
    bandit_alpha=0.15,      # learning rate for online updates
)
```

Environment flags (override constructor defaults):

- `CHESS_DYNAMIC_DIVERSITY=1|0` – enable/disable diversity bonus (default: 1)
- `CHESS_DYNAMIC_DIVERSITY_BONUS=float` – per-pair bonus magnitude (default: 0.25)
- `CHESS_DYNAMIC_BANDIT=1|0` – enable/disable contextual bandit updates (default: 1)
- `CHESS_DYNAMIC_BANDIT_ALPHA=float` – bandit learning rate (default: 0.15)

Implementation notes:

- Position-type buckets are formed as `"{phase}|{tac|quiet}|{low|norm}"` using lightweight features and mobility. Bandit multipliers are updated only for agents that proposed the finally chosen move.
- The diversity idea overlap is approximated using from/to squares (and the first step along slider direction) and awards a bonus when overlap ≤ 25%.

By default all deterministic sub-bots have a weight of `1.0` while
`RandomBot` is assigned a weight of `0.0` and therefore excluded unless a
positive weight is supplied.

### Example usage

```python
board = chess.Board()
move, score = bot.choose_move(board, debug=True)
```

The chosen move is the one with the highest total weighted confidence.

## Search-based play

Two optional search engines complement the lightweight heuristics:

- [`chess_ai/decision_engine.py`](chess_ai/decision_engine.py) implements a
  selective alpha–beta search:

  ```python
  from chess_ai.decision_engine import DecisionEngine

  engine = DecisionEngine()
  best = engine.choose_best_move(board)
  ```

- [`chess_ai/batched_mcts.py`](chess_ai/batched_mcts.py) provides a minimal
  neural-network-guided Monte Carlo tree search (MCTS).

A small demonstration script combines both approaches:

```bash
python tests/run_hybrid_demo.py
```

The script starts from the initial position, lets the hybrid bot play a few
plies and prints the chosen move, raw MCTS/alpha-beta scores and the time spent
searching each move.

Example output::

```text
1. b2b4 | MCTS=0.000 AB=0.000 time=0.06s
2. g7g5 | MCTS=0.000 AB=-0.000 time=0.57s
```

## Piece-square tables

The lightweight evaluation in `evaluation.py` relies on layered piece-square
tables (PSTs) that distinguish between middlegame and endgame phases.  Each
phase blends three layers:

- **Base** – curated defaults tracked in `weights/pst_base_*.json`.
- **User** – optional adjustments in `weights/pst_user_*.json` (initially all
  zeroes).
- **Learned** – values produced by automated tuning in
  `weights/pst_learned_*.json`.

The loader in `pst_loader.py` combines the available layers and automatically
falls back to the base tables when custom files are missing.  To (re)create the
default files or reset local modifications run:

```bash
python scripts/generate_pst_defaults.py
```

Pass `--force` to overwrite existing files.  User-specific tweaks can be
applied by editing the appropriate `pst_user_*.json` file; the changes are picked
up automatically on the next evaluation call.

## Development setup

### Python version

- This project targets **Python 3.10** for local development.
- A `.python-version` file is included to help tools like `pyenv`/`asdf` select the
  correct interpreter.

### One-step bootstrap (recommended)

Create a local virtual environment and install dependencies with a single command:

```bash
bash scripts/bootstrap.sh --quick-test
```

- Use `SKIP_R=1` if you don't have R installed and don't need the R bridge right now:

```bash
SKIP_R=1 bash scripts/bootstrap.sh --quick-test
```

The script will:
- Create `.venv/`
- Upgrade `pip`/`setuptools`/`wheel`
- Install Python dependencies from `requirements.txt` (optionally skipping `rpy2`)
- Optionally run a quick import check for `chess`, `torch`, and `matplotlib`

Activate the environment afterwards:

```bash
source .venv/bin/activate
```

On Windows, run the script in Git Bash or WSL and activate with:

```bash
.venv\\Scripts\\activate
```

## Running Tests

Execute the entire test suite with `pytest`'s automatic discovery:

```bash
# Option A: via the helper
python tests.py

# Option B: run pytest directly
pytest -q
```

### Linting (basic)

We use Ruff for a fast, basic lint check (errors only). Install and run:

```bash
pip install ruff
ruff check . --select F --exclude vendors
```

To attempt auto-fixes where possible:

```bash
ruff check . --fix
```

### Run lint and tests together

```bash
ruff check . --select F --exclude vendors && pytest -q
```

### PR CI

All pull requests run GitHub Actions to execute the Python and R test suites and a basic Ruff lint.

### Запуск локально (UA)

```bash
pip install -r requirements.txt
pip install ruff
ruff check . --select F --exclude vendors
pytest -q
```

## Dependencies

If you prefer to install manually instead of using the bootstrap script:

```bash
pip install -r requirements.txt
```

R dependencies for the analysis scripts can be installed via:

```r
install.packages(c("jsonlite", "dplyr", "ggplot2"))
```

Run the dependency import test to verify optional libraries are available:

```bash
pytest tests/test_vendor_imports.py -q
```


## Bot usage statistics

Summarise how often each bot module appears in recorded runs:

```bash
python scripts/bot_usage_stats.py --runs runs/
```

The script outputs a JSON mapping of module names to their total usage counts.

## Usage log viewer

Inspect the recorded usage counters without launching the full GUI viewer:

```bash
python scripts/usage_log_viewer.py
```

The script prints a table showing each path and how often it has been used.

## Move heatmaps

Convert recorded run JSON files into a flat move table and generate per-piece
heatmaps:

```bash
python -m analysis.loader runs/ --csv analysis/heatmaps/moves.csv --rds analysis/heatmaps/moves.rds
Rscript analysis/heatmaps/generate_heatmaps.R analysis/heatmaps/moves.csv
# or using the Wolfram Language
wolframscript -file analysis/heatmaps/generate_heatmaps.wl \
  --palette Reds --bins 8 --resolution 300 analysis/heatmaps/moves.csv
```

### Wolfram Engine Integration

The project includes advanced integration with Wolfram Engine for mathematical analysis:

```python
from chess_ai.wolfram_bot import WolframBot
import chess

# Create a WolframBot for advanced position analysis
bot = WolframBot(
    color=chess.WHITE,
    evaluation_depth=3,
    use_pattern_analysis=True,
    use_tactical_analysis=True,
    use_strategic_analysis=True
)

# Use in a game
board = chess.Board()
move, confidence = bot.choose_move(board)
print(f"Best move: {move} (confidence: {confidence})")

# Get detailed position evaluation
evaluation = bot.get_position_evaluation(board)
print(f"Position score: {evaluation['total_score']}")
```

Generate heatmaps using Wolfram Engine:

```python
from utils.integration import generate_heatmaps

# Use Wolfram Engine for heatmap generation
heatmaps = generate_heatmaps(
    fens, 
    use_wolfram=True,
    pattern_set="wolfram_analysis"
)
```

See [WOLFRAM_SETUP.md](WOLFRAM_SETUP.md) for installation instructions and [examples/wolfram_example.py](examples/wolfram_example.py) for a complete demonstration.

Heatmap matrices are written as CSV and JSON files into the directory containing
`moves.csv` (such as `analysis/heatmaps/` in this example). When invoking the
Python helper ``utils.integration.generate_heatmaps`` the files are stored in the
``analysis/heatmaps/<pattern_set>`` subdirectory (``default`` by default).
The Wolfram variant requires the Wolfram Engine and exposes the same
`--palette`, `--bins` and `--resolution` options. From Python set
`use_wolfram=True` when calling `utils.integration.generate_heatmaps` to use
this script.

## Piece positions from FEN

Generate per-piece coordinates directly from a list of FEN strings using R:

```bash
Rscript analysis/extract_positions.R fens.txt analysis/positions.csv
```

From Python the same functionality is available via a small wrapper:

```python
from analysis.extract_positions import extract_positions

fens = ["rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"]
extract_positions(fens, "positions.csv")
```

The resulting CSV contains `file`, `rank`, and `piece` columns for each board
entry.


## FEN positions from PGN

Extract positions from PGN files directly as FEN strings:

```bash
python analysis/pgn_to_fen.py games.pgn > fens.txt
```

Filters allow narrowing down the output.  For example, only keep opening
positions where White is to move and the game is at move 10:

```bash
python analysis/pgn_to_fen.py games.pgn --player white --move 10 --phase opening
```

Each printed line is a FEN describing the board state before the corresponding
move.

