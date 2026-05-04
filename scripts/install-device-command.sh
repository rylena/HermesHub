#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN_DIR="${HOME}/.local/bin"
mkdir -p "$BIN_DIR"

cat > "${BIN_DIR}/HermessHub" <<EOF
#!/usr/bin/env bash
set -euo pipefail
cd "$ROOT"
exec .venv/bin/hermeshub --config config.yaml run
EOF

chmod +x "${BIN_DIR}/HermessHub"

echo "Installed ${BIN_DIR}/HermessHub"
echo "Run: HermessHub"
