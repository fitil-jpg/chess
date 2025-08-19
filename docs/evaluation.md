# Evaluation Metrics

This project exposes a handful of helper functions that analyze pawn structure and overall position quality.
These metrics feed into the engine's evaluation and are available through `core.evaluator.Evaluator`.

## Setup

Some evaluation helpers rely on an optional R bridge and PyTorch‑based models. To enable these features install the following dependencies:

1. **R runtime**
   ```bash
   sudo apt-get update && sudo apt-get install -y r-base
   ```
2. **rpy2 Python package**
   ```bash
   pip install rpy2
   ```
3. **PyTorch and related packages**
   Visit <https://pytorch.org/get-started/locally/> for platform-specific commands or use the CPU wheels:
   ```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
   ```

After installing these packages the engine can call the R function `eval_position_complex` for advanced evaluation.
This function accepts an optional ``enemy_material`` argument, a mapping with
``"white"`` and ``"black"`` keys that scales king-attack penalties when the
opponent has lost major pieces such as the queen.

## Pawn structure helpers

- `is_isolated(board, square, files)` – checks whether a pawn has friendly pawns on adjacent files. An isolated pawn triggers `isolated_penalty` in [`pawn_structure_score`](../core/evaluator.py).
- `is_doubled(files, square)` – detects multiple friendly pawns on the same file and applies `doubled_penalty`.
- `is_passed(board, square, color, enemy_pawns)` – reports if no enemy pawn on the same or adjacent files is ahead of the pawn. See the implementation of `_is_passed_pawn` for details.

```python
from core.evaluator import Evaluator
import chess

board = chess.Board("8/8/2p5/8/2P5/8/8/8 w - - 0 1")
ev = Evaluator(board)
metrics = ev.compute_final_metrics()
print(metrics["position_score"])
```

In the position above the white pawn on c4 is isolated and blocked by a black pawn on c6.  `pawn_structure_score`
contributes `-10`, reducing the overall `position_score` accordingly.

If the black pawn is removed (`8/8/8/8/2P5/8/8/8 w - - 0 1`), the pawn becomes passed and earns a `+20` bonus – a net gain of
`+10` after the isolation penalty.

Doubled pawns forfeit `5` points per extra pawn.  Two white pawns on c4 and c3 with a black pawn on c6 are both isolated and
doubled, resulting in a `pawn_structure_score` of `-25` (`-10` for each isolated pawn and `-5` for doubling).

## `pawn_structure_score`

Calculates the net pawn-structure value using the three helpers above. Doubled pawns incur penalties, isolated pawns lose support,
and passed pawns receive a bonus.

## `position_score`

Combines material difference, piece–square table values, and `pawn_structure_score` into a single evaluation number.  Other modules
can retrieve this value via:

```python
metrics = ev.compute_final_metrics()
score = metrics["position_score"]
```

This allows bots in `chess_ai` to reuse the same metric without re‑evaluating the board.
