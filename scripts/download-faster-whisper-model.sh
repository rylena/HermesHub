#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ ! -x .venv/bin/python ]; then
  echo "Run scripts/install.sh first." >&2
  exit 1
fi

MODEL="${1:-base.en}"

. .venv/bin/activate
python - "$MODEL" <<'PY'
import sys
from faster_whisper import WhisperModel

model_name = sys.argv[1]
WhisperModel(model_name, device="cpu", compute_type="int8", cpu_threads=2)
print(f"Faster Whisper model ready: {model_name}")
PY
