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

- Default tournament control: 1|0 (60 seconds per player, no increment).
- The framework tracks per-agent remaining time; the time spent inside `choose_move` is charged against the agent's clock. Hitting 0 seconds loses on time.

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

Seeds are determined by the latest self-play Elo ratings (see below).

## Elo seeding

Use the round‑robin Elo script to compute current ratings and seed the bracket accordingly:

```bash
python scripts/selfplay_elo.py \
  --agents DynamicBot,AggressiveBot,FortifyBot,EndgameBot,KingValueBot,NeuralBot,TrapBot,RandomBot \
  --rounds 6 \
  --runs output
```

The script writes `output/selfplay_elo_YYYYmmdd_HHMMSS.json` containing a `ratings` map. The tournament runner will optionally look for the latest such file to build seeds automatically.

## Running (planned interface)

Headless tournament runner (to be added under `scripts/tournament.py`):

```bash
# With DynamicBot, Bo5, 1|0
python scripts/tournament.py \
  --format bo5 \
  --time 60 \
  --agents DynamicBot,NeuralBot,FortifyBot,AggressiveBot,EndgameBot,CriticalBot,KingValueBot,TrapBot

# Without DynamicBot
python scripts/tournament.py \
  --format bo5 \
  --time 60 \
  --agents NeuralBot,FortifyBot,AggressiveBot,EndgameBot,CriticalBot,KingValueBot,TrapBot,RandomBot
```

Outputs:

- `output/tournaments/<timestamp>/bracket.json` — bracket with per‑match results and seeds.
- `output/tournaments/<timestamp>/match_logs.jsonl` — per‑game results, times, SAN snippets.
- `output/tournaments/<timestamp>/summary.txt` — final standings and results.

## Notes

- Matches alternate colors each game; Armageddon uses White 60s vs Black 45s, draw → Black.
- Illegal move, invalid return, or timeout results in a loss for that game.
- For reproducibility, deterministic agents are preferred; stochastic agents should fix seeds.
