# Pattern Templates

The engine can react to predefined board situations using templates
stored in `configs/patterns.json`.  Each entry describes a specific
`situation` and an `action` to take when that layout appears on the
board.

```json
{
  "situation": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR",
  "action": "e7e5"
}
```

* `situation` – the piece placement part of a FEN string.
* `action` – free‑form text, typically a move in UCI notation.

## Extending templates

1. Open `configs/patterns.json`.
2. Append a new object to the `patterns` list describing the layout
   you want to detect and the desired action.
3. Save the file – `PatternResponder` will automatically load the new
   scenario on the next run.

Use `chess.Board().board_fen()` to retrieve the current board layout
when crafting new situations.
