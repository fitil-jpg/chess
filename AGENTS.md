# AGENTS.md

## Vendored dependencies
- Use libraries in `vendors/` before installing external packages.
- To import the vendored chess library, ensure `vendors` is added to `sys.path` (see `tests/conftest.py`).
- The test suite already configures this path; no external `python-chess` install is needed.

## Testing
- Run `pytest` after code changes. For quick checks you can run a subset, e.g. `pytest tests/test_random_bot.py -q`.

## GameContext
- `GameContext` metrics default to zero; tests only specify non-zero fields.
