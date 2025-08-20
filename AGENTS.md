# AGENTS.md

## Vendored dependencies
- `tests/conftest.py` automatically appends `vendors/` to `sys.path`. When running scripts outside the test suite, manually add `vendors/` to `sys.path`.
- If a required third-party library is missing, copy it into `vendors/` instead of installing it globally; adjust the `sys.path` update if necessary to import it correctly.

## Testing
- Run `pytest` after code changes. For quick checks you can run a subset, e.g. `pytest tests/test_random_bot.py -q`.

## GameContext
- `GameContext` metrics default to zero; tests only specify non-zero fields.

## Sync with remote
- Before starting development, run `git fetch origin`.
- Verify your branch is not behind `origin/main` with `git status -uno` or `git rev-list origin/main...HEAD`.
- If your branch is behind, run `git pull --rebase origin main` (or merge) before proceeding.

## Pull requests
- Before calling `make_pr`, ensure your branch is synchronized with `origin/main`:
  - Run `git fetch origin` and confirm your branch is not behind using `git status -uno` or `git rev-list origin/main...HEAD`.
  - If it is behind, run `git pull --rebase origin main` (or merge) and resolve conflicts.
- Run `pytest` (e.g., `pytest tests/test_random_bot.py -q`) and address any failures before creating the PR.
