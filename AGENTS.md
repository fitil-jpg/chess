# AGENTS.md

## Vendored dependencies
- `tests/conftest.py` automatically appends `vendors/` to `sys.path`. When running scripts outside the test suite, manually add `vendors/` to `sys.path`.

## Testing
- Run `pytest` after code changes. For quick checks you can run a subset, e.g. `pytest tests/test_random_bot.py -q`.

## GameContext
- `GameContext` metrics default to zero; tests only specify non-zero fields.
