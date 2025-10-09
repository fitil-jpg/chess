# Tournament Mode

This document describes the current headless round‑robin tournament runner and how to compute Elo seeding. It also provides exact CLI usage and artifact examples.

## Formats

- Scoring: win=1.0, draw=0.5, loss=0.0
- Colors: alternate each game within a series
- Series length: either best‑of odd N (`--bo`, 1/3/5/7) with early stop, or a fixed number of games via `--games`
- Technical loss: illegal move, agent error, or returning `None` loses the game

## Time control (current)

- The headless runner does not track clocks yet. Use `--max-plies` (default 600) as a safety cap; exceeding the cap results in a draw.

## Participants and variants

We support running two tournaments:

- With DynamicBot: `DynamicBot, FortifyBot, AggressiveBot, EndgameBot, KingValueBot, PieceMateBot, RandomBot, ChessBot`
- Without DynamicBot: `FortifyBot, AggressiveBot, EndgameBot, KingValueBot, PieceMateBot, RandomBot, ChessBot, HybridBot`

For planned bracket play, seeds can be determined by the latest self‑play Elo ratings (see below).

## Elo seeding (artifact example)

Use the round‑robin Elo script to compute current ratings and seed the bracket accordingly:

```bash
python scripts/selfplay_elo.py \
  --agents DynamicBot,AggressiveBot,FortifyBot,EndgameBot,KingValueBot,PieceMateBot,RandomBot,ChessBot \
  --rounds 6 \
  --runs output
```

The script writes a JSON artifact at `output/selfplay_elo_YYYYmmdd_HHMMSS.json`. Minimal example:

```json
{
  "schema_version": 1,
  "task": "selfplay_elo",
  "timestamp": "20250101_120000",
  "agents": ["DynamicBot","FortifyBot","AggressiveBot"],
  "k_factor": 24.0,
  "ratings": {"DynamicBot": 1542.1, "FortifyBot": 1510.3, "AggressiveBot": 1447.6},
  "games": [
    {"white": "DynamicBot", "black": "FortifyBot", "result": "1-0", "round": 0, "color": "Awhite"}
  ]
}
```

## Running (current CLI)

Headless round‑robin runner is implemented at `scripts/tournament.py`.

Usage:

```bash
python scripts/tournament.py \
  --agents DynamicBot,FortifyBot,AggressiveBot \
  [--games 2 | --bo 3] \
  [--max-plies 600]
```

```bash
# With DynamicBot, Bo5
python scripts/tournament.py \
  --agents DynamicBot,FortifyBot,AggressiveBot,EndgameBot,KingValueBot,PieceMateBot,RandomBot,ChessBot \
  --bo 5

# Without DynamicBot
python scripts/tournament.py \
  --agents FortifyBot,AggressiveBot,EndgameBot,KingValueBot,PieceMateBot,RandomBot,ChessBot,HybridBot \
  --bo 5

# Quick smoke test: fixed 2 games per pairing, lower plies cap
python scripts/tournament.py \
  --agents DynamicBot,FortifyBot,AggressiveBot \
  --games 2 \
  --max-plies 300
```

Example live output (truncated):

```text
Учасники: DynamicBot, FortifyBot, AggressiveBot
Формат: Bo3 | Без потоків | Макс. пліїв: 600

=== Пара: DynamicBot vs FortifyBot | Серія: 3 ігор ===
Гра 1: DynamicBot (білі) — FortifyBot (чорні)
Результат: 1-0 (Перемога білих)
...
Поточна турнірна таблиця:
Місце  Гравець        Очки   W   D   L  Ігор
    1  DynamicBot      2.0   2   0   0    2
    2  FortifyBot      0.0   0   0   2    2
```

## Artifacts

- The tournament runner currently prints progress and standings to the terminal and does not write files.
- To persist logs, redirect output, for example:

```bash
ts=$(date +%Y%m%d_%H%M%S)
out_dir=output/tournaments/$ts
mkdir -p "$out_dir"
python scripts/tournament.py \
  --agents DynamicBot,FortifyBot,AggressiveBot \
  --bo 3 \
  --max-plies 600 | tee "$out_dir/summary.txt"
```

## Notes

- Colors alternate each game.
- Illegal move or invalid return results in a technical loss for that game.
- Exceeding `--max-plies` draws the game.
- For reproducibility, deterministic agents are preferred; stochastic agents should fix seeds.
