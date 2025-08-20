# AGENTS.md

## Vendored dependencies
- `tests/conftest.py` automatically appends `vendors/` to `sys.path`. When running scripts outside the test suite, manually add `vendors/` to `sys.path`.
- If a required third-party library is missing, copy it into `vendors/` instead of installing it globally; adjust the `sys.path` update if necessary to import it correctly.

## Testing
- Run `pytest` after code changes. For quick checks you can run a subset, e.g. `pytest tests/test_random_bot.py -q`.

## GameContext
- `GameContext` metrics default to zero; tests only specify non-zero fields.
