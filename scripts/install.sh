#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required" >&2
  exit 1
fi

python3 - <<'PY'
import sys

if not ((3, 10) <= sys.version_info < (3, 13)):
    version = ".".join(map(str, sys.version_info[:3]))
    raise SystemExit(f"Python 3.10, 3.11, or 3.12 is required; found {version}")
PY

python3 -m venv .venv
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
