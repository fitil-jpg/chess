# Scenario Detection

The `scenarios` package detects tactical and structural patterns in a board
position.  Rules are defined in `scenarios/scenario_rules.json` and each entry
provides a unique `id`, a human readable `description` and a display `color`.

```json
{
  "rules": [
    {
      "id": "isolated_pawn",
      "description": "Pawn without friendly pawns on adjacent files.",
      "category": "structure",
      "color": "purple"
    }
  ]
}
```

## Usage

Call :func:`scenarios.detect_scenarios` with a FEN string.  The function
returns a list of dictionaries describing every detected scenario.

```python
from scenarios import detect_scenarios

fen = "8/3q1r2/8/4N3/8/8/8/8 w - - 0 1"
for sc in detect_scenarios(fen):
    print(sc["id"], sc["square"])
```

Each result includes the scenario `id`, the board `square` and the configured
`color`.  Additional fields may be present depending on the rule.
