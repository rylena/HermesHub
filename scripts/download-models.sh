#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

mkdir -p models voices /tmp/hermeshub-models

download() {
  local url="$1"
  local target="$2"
  if [ -f "$target" ]; then
    echo "exists: $target"
    return
  fi
  echo "downloading: $url"
  curl -L --fail --retry 3 -o "$target" "$url"
}

if [ ! -d models/vosk-model-en-us-0.22-lgraph ]; then
  download "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22-lgraph.zip" "/tmp/hermeshub-models/vosk-model-en-us-0.22-lgraph.zip"
  python3 - <<'PY'
from pathlib import Path
from zipfile import ZipFile

archive = Path("/tmp/hermeshub-models/vosk-model-en-us-0.22-lgraph.zip")
target = Path("models")
with ZipFile(archive) as zf:
    zf.extractall(target)
PY
else
  echo "exists: models/vosk-model-en-us-0.22-lgraph"
fi

download "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx" "voices/en_US-lessac-medium.onnx"
download "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json" "voices/en_US-lessac-medium.onnx.json"

if [ -x .venv/bin/python ]; then
  .venv/bin/python - <<'PY'
import openwakeword
from openwakeword.utils import download_models

download_models()
print("openWakeWord models downloaded")
PY
else
  echo "Skip openWakeWord model download: run scripts/install.sh first."
fi
