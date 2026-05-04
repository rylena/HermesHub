#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MODEL_NAME="sherpa-onnx-streaming-zipformer-en-20M-2023-02-17"
ARCHIVE="/tmp/hermeshub-models/${MODEL_NAME}.tar.bz2"
TARGET="models/${MODEL_NAME}"
URL="https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/${MODEL_NAME}.tar.bz2"

if [ -d "$TARGET" ]; then
  echo "exists: $TARGET"
  exit 0
fi

mkdir -p models /tmp/hermeshub-models
curl -L --fail --retry 3 -o "$ARCHIVE" "$URL"
tar -xjf "$ARCHIVE" -C models
echo "downloaded: $TARGET"
