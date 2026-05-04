#!/usr/bin/env bash
set -euo pipefail

if ! command -v apt-get >/dev/null 2>&1; then
  echo "This helper is for Ubuntu/Debian systems with apt-get." >&2
  exit 1
fi

sudo apt-get update
sudo apt-get install -y \
  alsa-utils \
  curl \
  libasound2-dev \
  libgl1 \
  libglib2.0-0 \
  libportaudio2 \
  portaudio19-dev \
  python3-pip \
  python3-venv \
  unzip \
  v4l-utils

echo "System dependencies installed."
