#!/usr/bin/env bash
set -euo pipefail

show_help() {
  cat <<'EOF'
Usage: scripts/bootstrap.sh [options]

Create a local Python virtual environment and install project dependencies.

Options:
  --python <cmd>   Python interpreter to use (default: auto-detect)
  --force          Recreate the virtual environment if it already exists
  --skip-r         Skip installing rpy2 (R integration) if not needed
  --no-install     Create venv and upgrade pip, but skip installing deps
  --quick-test     After install, verify key imports (chess, torch, matplotlib)
  -h, --help       Show this help and exit

Environment variables:
  PYTHON           Overrides Python interpreter detection
  SKIP_R=1         Same as --skip-r

Examples:
  bash scripts/bootstrap.sh
  SKIP_R=1 bash scripts/bootstrap.sh --quick-test
  bash scripts/bootstrap.sh --python python3.10 --force
EOF
}

ROOT_DIR="$(cd -- "$(dirname -- "$0")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
PYTHON_CMD="${PYTHON:-}"
FORCE_RECREATE=0
SKIP_R=${SKIP_R:-0}
DO_INSTALL=1
DO_QUICK_TEST=0

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --python)
      PYTHON_CMD="$2"; shift 2;;
    --force)
      FORCE_RECREATE=1; shift;;
    --skip-r)
      SKIP_R=1; shift;;
    --no-install)
      DO_INSTALL=0; shift;;
    --quick-test)
      DO_QUICK_TEST=1; shift;;
    -h|--help)
      show_help; exit 0;;
    *)
      echo "Unknown option: $1" >&2
      show_help >&2
      exit 2;;
  esac
done

# Auto-detect Python if not provided
if [[ -z "$PYTHON_CMD" ]]; then
  for candidate in python3.10 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
      PYTHON_CMD="$candidate"; break
    fi
  done
fi

if [[ -z "$PYTHON_CMD" ]]; then
  echo "Error: Could not find a Python interpreter (looked for python3.10, python3, python)." >&2
  exit 1
fi

# Ensure Python version >= 3.10
PY_VER="$($PYTHON_CMD -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
PY_MAJ=${PY_VER%%.*}
PY_MIN=${PY_VER#*.}
if [[ "$PY_MAJ" -lt 3 || "$PY_MIN" -lt 10 ]]; then
  echo "Error: Python >= 3.10 required. Found $PY_VER from '$PYTHON_CMD'." >&2
  exit 1
fi

echo "Using Python $PY_VER at: $(command -v "$PYTHON_CMD")"

# Create or recreate venv
if [[ -d "$VENV_DIR" && "$FORCE_RECREATE" -eq 1 ]]; then
  echo "Recreating virtual environment at $VENV_DIR ..."
  rm -rf "$VENV_DIR"
fi

if [[ ! -d "$VENV_DIR" ]]; then
  echo "Creating virtual environment at $VENV_DIR ..."
  "$PYTHON_CMD" -m venv "$VENV_DIR"
else
  echo "Reusing existing virtual environment at $VENV_DIR"
fi

VENV_PY="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"

# Upgrade packaging tools
"$VENV_PY" -m pip install --upgrade pip setuptools wheel >/dev/null

echo "pip version: $($VENV_PIP --version)"

if [[ "$DO_INSTALL" -eq 1 ]]; then
  REQ_FILE="$ROOT_DIR/requirements.txt"
  if [[ ! -f "$REQ_FILE" ]]; then
    echo "Error: requirements.txt not found at repo root ($ROOT_DIR)." >&2
    exit 1
  fi

  if [[ "$SKIP_R" -eq 1 ]]; then
    echo "Installing Python dependencies (skipping rpy2) ..."
    TMP_REQ="$(mktemp)"
    grep -i -v '^rpy2\b' "$REQ_FILE" > "$TMP_REQ"
    "$VENV_PIP" install -r "$TMP_REQ"
    rm -f "$TMP_REQ"
  else
    echo "Installing Python dependencies from requirements.txt ..."
    "$VENV_PIP" install -r "$REQ_FILE"
  fi

  # Ensure pytest is available for local runs
  "$VENV_PIP" install -U pytest >/dev/null

  if [[ "$DO_QUICK_TEST" -eq 1 ]]; then
    echo "Running quick import test (chess, torch, matplotlib) ..."
    "$VENV_PY" - "$@" <<'PY'
import importlib, sys
mods = ["chess", "torch", "matplotlib"]
missing = []
for m in mods:
    try:
        importlib.import_module(m)
    except Exception as exc:
        missing.append((m, str(exc)))
if missing:
    for m, err in missing:
        print(f"[FAIL] import {m}: {err}")
    sys.exit(1)
print("All quick imports succeeded.")
PY
  fi
fi

echo
echo "Done. To start using this environment run:"
if [[ "$(uname -s)" == "Darwin" || "$(uname -s)" == "Linux" ]]; then
  echo "  source .venv/bin/activate"
else
  echo "  .venv\\Scripts\\activate"
fi

echo
if [[ "$SKIP_R" -eq 1 ]]; then
  echo "Note: rpy2 installation was skipped. R-based features will be unavailable until R and rpy2 are installed."
fi
