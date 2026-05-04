#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ ! -x .venv/bin/python ]; then
  echo "Run scripts/install.sh first." >&2
  exit 1
fi

arch="$(uname -m)"
case "$arch" in
  armv7l|aarch64)
    if [ "${ALLOW_PARAKEET_ON_ARM:-0}" != "1" ]; then
      echo "Parakeet v2 is a large NeMo model and is not recommended locally on Raspberry Pi 4." >&2
      echo "Keep stt.engine: auto/vosk on Pi, or rerun with ALLOW_PARAKEET_ON_ARM=1 if you still want to try." >&2
      exit 1
    fi
    ;;
esac

. .venv/bin/activate

python -m pip install --upgrade pip wheel setuptools
if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1; then
  python -m pip install torch torchaudio
else
  python -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
fi
python -m pip install "nemo_toolkit[asr]>=2.2"

python - <<'PY'
import nemo.collections.asr as nemo_asr

model = nemo_asr.models.ASRModel.from_pretrained(model_name="nvidia/parakeet-tdt-0.6b-v2")
print(f"Parakeet ready: {model.__class__.__name__}")
PY
