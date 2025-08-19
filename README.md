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

