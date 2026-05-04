#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-}"
if [ -z "$PYTHON_BIN" ]; then
  for candidate in python3.12 python3.11 python3.10 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
      if "$candidate" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if (3, 10) <= sys.version_info < (3, 13) else 1)
PY
      then
        PYTHON_BIN="$candidate"
        break
      fi
    fi
  done
fi

if [ -z "$PYTHON_BIN" ]; then
  echo "Python 3.10, 3.11, or 3.12 is required." >&2
  exit 1
fi

"$PYTHON_BIN" - <<'PY'
import sys

if not ((3, 10) <= sys.version_info < (3, 13)):
    version = ".".join(map(str, sys.version_info[:3]))
    raise SystemExit(f"Python 3.10, 3.11, or 3.12 is required; found {version}")
PY

"$PYTHON_BIN" -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip wheel setuptools
python -m pip install -e .
python -m pip install "onnxruntime>=1.10,<2" "tqdm>=4,<5" "scipy>=1.3,<2" "scikit-learn>=1,<2"
python -m pip install --no-deps "openwakeword>=0.6,<0.7"

if [ ! -f config.yaml ]; then
  cp config.example.yaml config.yaml
fi

mkdir -p data/camera logs models voices

echo
echo "HermesHub installed."
echo "Next:"
echo "  scripts/download-models.sh"
echo "  .venv/bin/hermeshub doctor"
echo "  .venv/bin/hermeshub --config config.yaml run"
