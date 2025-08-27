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
## Dependencies

The project relies on the following third-party libraries:

- `python-chess` – core chess logic.
- `PyYAML` – configuration file parsing.
- `torch` – neural network evaluation (optional).
- `matplotlib` – optional plotting for profiling stats.
- `rpy2` – optional bridge to R for advanced evaluation.
- `PySide6` – vendored GUI toolkit located in `vendors/`.
- `pytest` – test runner.

Install the main dependencies with:

```bash
python -m pip install -r requirements.txt
```

Optional features such as plotting or the R evaluator require the corresponding packages above and, for `rpy2`, an R runtime.


## Running Tests

Execute the entire test suite with `pytest`'s automatic discovery:

```bash
python tests.py
```

Running `pytest` directly works as well:

```bash
pytest
```

## Vendor Import Test

The project keeps third‑party libraries in the `vendors/` directory. To confirm
that these vendored packages can be imported, run the dedicated test:

```bash
pytest tests/test_vendor_imports.py
```

Optional arguments:

- Add `-q` for quieter output:

  ```bash
  pytest tests/test_vendor_imports.py -q
  ```
- Pass any other standard `pytest` flags as needed.

Expected failure modes:

- If a library is missing, the test will be skipped for that module.
- Import errors such as `ImportError: DLL load failed` indicate missing native
  dependencies or architecture mismatches. Ensure the required DLLs and the
  library itself are present in `vendors/`.

