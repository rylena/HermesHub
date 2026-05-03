#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$HOME/.config/systemd/user"
sed "s|%h/hermeshub untyped|$ROOT|g" \
  "$ROOT/systemd/hermeshub.service" \
  > "$HOME/.config/systemd/user/hermeshub.service"

systemctl --user daemon-reload
systemctl --user enable hermeshub.service

echo "Installed user service. Start it with:"
echo "  systemctl --user start hermeshub"
