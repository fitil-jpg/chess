# Chess AI

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

bot = DynamicBot(chess.WHITE, weights={"aggressive": 1.5, "fortify": 0.5})
```

### Example usage

```python
board = chess.Board()
move, score = bot.choose_move(board, debug=True)
```

The chosen move is the one with the highest total weighted confidence.

## HybridBot demo

A small demonstration script shows the hybrid MCTS/alpha-beta engine in action.
Run it directly from the repository root:

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

## Running Tests

Execute the entire test suite with `pytest`'s automatic discovery:

```bash
python tests.py
```

Running `pytest` directly works as well:

```bash
pytest
```

