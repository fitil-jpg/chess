# Sampling Run Data

Large collections of recorded games can consume significant memory when loaded
all at once.  The analysis tools therefore support sampling subsets of games
for offline processing.

## Random subset

To analyse a random subset of games, specify a sample size and random seed.
The seed makes the selection reproducible:

```bash
python -m analysis.loader runs/ --stats --sample-size 1000 --seed 42
```

This command processes up to **1000** randomly chosen games and prints
aggregated statistics.  If fewer games are available all of them are used.
Choose a sample size of at least 1000 games to obtain stable estimates.

## Sliding window

Omit the seed to read the first ``N`` games in sorted order, effectively
creating a sliding window over the dataset:

```bash
python -m analysis.loader runs/ --stats --sample-size 1000
```

This strategy is useful when the games are already shuffled externally.  As
with random sampling, ensure the window covers **≥1000** games for meaningful
results.
