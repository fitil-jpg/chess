# Sampling Strategy

The analysis utilities can process large collections of run JSON files without
loading every game into memory.  To keep analysis tractable while covering a
representative set of games, sample at least **1000** games from the archive.

## Random subset

Use the loader's sampling options to select a random subset of runs:

```bash
python analysis/loader.py runs/ --sample-size 1000 --seed 42
```

`--sample-size` limits the number of games processed and `--seed` controls the
random selection.  When fewer than ``sample-size`` files are available, all
files are used.

## Sliding window

Omitting ``--seed`` processes files in sorted order.  Limiting the sample size
then effectively yields a sliding window over the most recent games:

```bash
python analysis/loader.py runs/ --sample-size 1000
```

Both approaches guarantee that at least 1000 games are analysed when
``--sample-size`` is set to ``1000`` or higher.
