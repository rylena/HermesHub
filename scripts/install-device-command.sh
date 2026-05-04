#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN_DIR="${HOME}/.local/bin"
mkdir -p "$BIN_DIR"

cat > "${BIN_DIR}/HermessHub" <<EOF
#!/usr/bin/env bash
set -euo pipefail
cd "$ROOT"
if [ "\$#" -eq 0 ]; then
  set -- run
fi
exec .venv/bin/hermeshub --config config.yaml "\$@"
EOF

chmod +x "${BIN_DIR}/HermessHub"

echo "Installed ${BIN_DIR}/HermessHub"
echo "Run: HermessHub"
