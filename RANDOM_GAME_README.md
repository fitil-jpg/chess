# Random Chess Bot Game Runner

This script runs chess games between two RandomBot agents with console output and pattern saving to a "random_games" catalog.

## Features

- **Two RandomBot agents**: Both white and black players use RandomBot with temperature-weighted move selection
- **Console output**: Shows game progress, move details, evaluation scores, and confidence levels
- **Pattern detection**: Automatically detects and saves chess patterns (development, center control, captures, checks, etc.)
- **Pattern storage**: Saves patterns to `patterns/random_games/` directory
- **Game data**: Saves complete game data as JSON files

## Usage

### Basic usage (single game):
```bash
python3 run_random_game.py
```

### With custom parameters:
```bash
python3 run_random_game.py --max-plies 20 --games 3
```

### Disable pattern saving:
```bash
python3 run_random_game.py --no-patterns
```

## Command Line Options

- `--max-plies N`: Maximum number of plies to play (default: 50)
- `--games N`: Number of games to play (default: 1)
- `--no-patterns`: Disable pattern detection and saving

## Output

### Console Output
For each move, the script displays:
- Ply number and side (White/Black)
- Move in UCI notation
- Evaluation details (material, PST, mobility, attacks)
- Pre/post evaluation scores
- Bot confidence level
- FEN position

### Files Generated
- `patterns/random_games/game_TIMESTAMP_N.json`: Complete game data
- `patterns/random_games/pattern_TIMESTAMP.json`: Individual detected patterns
- `patterns/random_games/summary_TIMESTAMP.json`: Summary of multiple games (if --games > 1)

## Pattern Types Detected

The simple pattern detector identifies:
- **Development**: Moving pieces from starting positions
- **Center Control**: Moving to center squares (e4, e5, d4, d5)
- **Captures**: Capturing opponent pieces
- **Checks**: Giving check to opponent king
- **Castling**: Kingside or queenside castling
- **Promotions**: Pawn promotions

## Example Output

```
=== RANDOM BOT GAME ===
Start FEN: rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1

[Ply 01] White played d2d3
  material=0  pst=20  mobility=14  att_w=27 att_b=22  delta_att=5
  eval_before≈0   eval_after=39   confidence=0.000
  FEN: rnbqkbnr/pppppppp/8/8/8/3P4/PPP1PPPP/RNBQKBNR b KQkq - 0 1
-

[Ply 02] Black played h7h6
  material=0  pst=20  mobility=16  att_w=27 att_b=23  delta_att=4
  eval_before≈39   eval_after=40   confidence=0.000
  FEN: rnbqkbnr/ppppppp1/7p/8/8/3P4/PPP1PPPP/RNBQKBNR w KQkq - 0 2
-

Result: *
Game over reason: move limit reached
Total plies: 6

✓ Saved 6 patterns to patterns/random_games/
✓ Game data saved to patterns/random_games/game_20251027_145239_1.json
```

## Dependencies

- `chess` library (installed automatically)
- `evaluation.py` (from the chess AI project)
- `chess_ai.random_bot` (from the chess AI project)

The script will work with or without the advanced pattern detection system, falling back to a simple pattern detector if needed.