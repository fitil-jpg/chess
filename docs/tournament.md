# Tournament Mode

This document describes the headless tournament mode for internal agents, including formats, time control, seeding, and how to run two variants (with and without DynamicBot).

## Formats

- Match formats: Bo3, Bo5, Bo7 (first to 2 / 3 / 4 points).
- Scoring: win=1, draw=0.5, loss=0.
- Colors: alternate each game. For odd-length series, the higher seed has White in G1 and the last game if needed.
- Tie-breaks: if tied after all scheduled games:
  - Two extra blitz games 1|0 alternating colors.
  - If still tied, Armageddon: White 60s vs Black 45s, draw counts as a win for Black.
- Technical loss: illegal move or agent error/timeout loses the game.

## Time control (headless)

- Default: per-move timeout via `--time` (seconds). The default is 60s per move.
- Optional chess clock: pass `--clock M|inc` (minutes|increment seconds). This overrides `--time` and enables a per‑player clock where time spent inside `choose_move` is charged and increment is applied after each legal move. Flag‑fall loses the game.

## Bracket and live table

Example 8-player single-elimination bracket:

```text
Quarterfinals                      Semifinals                        Final
[QF1] (1) Seed1 ───────┐
                       ├─ [SF1] Winner QF1 ───┐
[QF2] (4) Seed4 ───┐   │                      ├─ [F] Champion
                   └───┤                      │
[QF3] (3) Seed3 ───┐   │   [SF2] Winner QF3 ──┘
                   └───┤
[QF4] (2) Seed2 ───────┘
```

Per‑match live card (updated after each game):

```text
[QF1] Seed1 vs Seed8  | Bo5 | Score: 2.0–1.0 | G4 next: Seed1 (Black)
  - G1: 1-0 (mate)     T: W 12.3s / B 3.2s
  - G2: ½-½ (repetition)  T: W 7.8s  / B 9.5s
  - G3: 1-0 (time)     T: W 4.1s  / B 0.0s
```

Summary table:

```text
Match   Format Result  Advances
QF1     Bo5    3–1     Seed1
QF2     Bo5    2.5–1.5 Seed4
QF3     Bo5    3–0     Seed3
QF4     Bo5    3–2     Seed2
SF1     Bo5    3–2     Seed1
SF2     Bo5    3–1     Seed2
Final   Bo7    4–2     Seed1 (Champion)
```

## Participants and variants

We support running two tournaments:

- With DynamicBot: `DynamicBot, NeuralBot, FortifyBot, AggressiveBot, EndgameBot, CriticalBot, KingValueBot, TrapBot`
- Without DynamicBot: `NeuralBot, FortifyBot, AggressiveBot, EndgameBot, CriticalBot, KingValueBot, TrapBot, RandomBot`

Tip: Use `--include-dynamic` or `--exclude-dynamic` to force inclusion/exclusion. If you omit `--agents`, the default set is `DynamicBot,FortifyBot,AggressiveBot,EndgameBot,KingValueBot,RandomBot`.

Seeds for single‑elimination are determined by the latest self‑play Elo ratings (see below). If no Elo file is found, input order is preserved. The chosen seed order is printed at start.

## Elo seeding

Use the round‑robin Elo script to compute current ratings used for single‑elimination seeding:

```bash
python scripts/selfplay_elo.py \
  --agents DynamicBot,AggressiveBot,FortifyBot,EndgameBot,KingValueBot,NeuralBot,TrapBot,RandomBot \
  --rounds 6 \
  --runs output
```

The script writes `output/selfplay_elo_YYYYmmdd_HHMMSS.json` containing a `ratings` map. The tournament runner will optionally look for the latest such file to build seeds automatically.

## CLI usage and examples

The headless runner lives in `scripts/tournament.py` and supports round‑robin and single‑elimination modes.

```bash
# Round‑robin, Bo5, chess clock 1|0, with DynamicBot
python scripts/tournament.py \
  --mode rr \
  --format bo5 \
  --clock 1|0 \
  --tiebreaks on \
  --agents DynamicBot,NeuralBot,FortifyBot,AggressiveBot,EndgameBot,CriticalBot,KingValueBot,TrapBot

# Round‑robin, fixed 2 games per pairing, per‑move timeout 30s, exclude DynamicBot
python scripts/tournament.py \
  --mode rr \
  --games 2 \
  --time 30 \
  --exclude-dynamic \
  --agents NeuralBot,FortifyBot,AggressiveBot,EndgameBot,CriticalBot,KingValueBot,TrapBot,RandomBot

# Single‑elimination, Bo3, chess clock 3|2, tag and custom output root
python scripts/tournament.py \
  --mode se \
  --format bo3 \
  --clock 3|2 \
  --tiebreaks on \
  --tag nightly \
  --out-root output/tournaments \
  --agents DynamicBot,NeuralBot,FortifyBot,AggressiveBot,EndgameBot,KingValueBot,TrapBot

# Notes
# - Use --include-dynamic or --exclude-dynamic to force adding/removing DynamicBot.
# - Use --bo (1,3,5,7) or --format (bo3|bo5|bo7), or set an exact --games count.
# - Use --max-plies to cap game length (default 600 plies).
```

Outputs:

- `output/tournaments/<timestamp>/bracket.json` — live tournament state.
  - Round‑robin: `type: "round_robin"`, `pairs` with series results and points.
  - Single‑elimination: `type: "single_elimination"`, `seeds`, and `rounds[*].matches[*]` with results and winners.
- `output/tournaments/<timestamp>/match_logs.jsonl` — one JSON per game with fields: `timestamp`, `pair` {`a`,`b`}, `game_index` (1‑based), `white`, `black`, `result` (`"1-0"|"0-1"|"1/2-1/2"`), `tiebreak` (bool), and optional `meta` (e.g., `kind: timeout|illegal_move|agent_error`, plus concise diagnostics like `elapsed`, `budget`, `move_uci`, `error`).
- `output/tournaments/<timestamp>/summary.txt` — final standings for round‑robin, or bracket summary and champion for single‑elimination.

### Artifact examples

Example `bracket.json` (round‑robin):

```json
{
  "type": "round_robin",
  "format": "Bo3",
  "agents": ["DynamicBot", "FortifyBot", "AggressiveBot"],
  "games_per_pair": 3,
  "tiebreaks": true,
  "max_plies": 600,
  "time_per_move": 60,
  "clock_initial": null,
  "clock_increment": null,
  "started_at": "2025-10-09T12:00:00Z",
  "updated_at": "2025-10-09T12:00:42Z",
  "tag": "nightly",
  "pairs": [
    {"a": "DynamicBot", "b": "FortifyBot", "results": ["1-0", "0-1", "1/2-1/2"], "points_a": 2.0, "points_b": 1.0}
  ],
  "seeds": [],
  "rounds": []
}
```

Example `bracket.json` (single‑elimination):

```json
{
  "type": "single_elimination",
  "format": "Bo5",
  "agents": ["DynamicBot", "FortifyBot", "AggressiveBot", "EndgameBot"],
  "tiebreaks": true,
  "max_plies": 600,
  "time_per_move": null,
  "clock_initial": 60.0,
  "clock_increment": 0.0,
  "started_at": "2025-10-09T12:05:00Z",
  "updated_at": "2025-10-09T12:07:30Z",
  "tag": null,
  "pairs": [],
  "seeds": ["DynamicBot", "FortifyBot", "AggressiveBot", "EndgameBot"],
  "rounds": [
    {
      "name": "Semifinals",
      "matches": [
        {"a": "DynamicBot", "b": "EndgameBot", "results": ["1-0", "0-1", "1-0"], "points_a": 2.0, "points_b": 1.0, "winner": "DynamicBot"}
      ]
    }
  ]
}
```

Example `match_logs.jsonl` line:

```json
{"timestamp":"2025-10-09T12:00:41.123456Z","pair":{"a":"DynamicBot","b":"FortifyBot"},"game_index":1,"white":"DynamicBot","black":"FortifyBot","result":"1-0","tiebreak":false}
```

Example `summary.txt` (round‑robin excerpt):

```text
Фінальна таблиця:
 Місце  Гравець        Очки    W   D   L  Ігор
----------------------------------------------
     1  DynamicBot      2.0    2   0   0    2
     2  FortifyBot      1.0    1   0   1    2
```

## Notes

- Matches alternate colors each game; Armageddon uses White 60s vs Black 45s, draw → Black.
- Illegal move, invalid return, or timeout results in a loss for that game.
- For reproducibility, deterministic agents are preferred; stochastic agents should fix seeds.
