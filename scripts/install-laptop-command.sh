#!/usr/bin/env bash
set -euo pipefail

BIN_DIR="${HOME}/.local/bin"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

mkdir -p "$BIN_DIR"

cat > "${BIN_DIR}/HermessHub" <<EOF
#!/usr/bin/env bash
set -euo pipefail

if [ "\$#" -eq 0 ]; then
  set -- run
fi

cd "$ROOT"
exec .venv/bin/hermeshub --config config.yaml "\$@"
EOF

chmod +x "${BIN_DIR}/HermessHub"

echo "Installed ${BIN_DIR}/HermessHub"
echo "Run: HermessHub"
