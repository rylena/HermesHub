#!/usr/bin/env bash
set -euo pipefail

BIN_DIR="${HOME}/.local/bin"
KEY_PATH="${HOME}/.ssh/hermeshub_agent_key"
TARGET_HOST="${HERMESHUB_HOST:-192.168.70.60}"
TARGET_USER="${HERMESHUB_USER:-rylen}"
REMOTE_DIR="${HERMESHUB_REMOTE_DIR:-\$HOME/hermeshub untyped}"

mkdir -p "$BIN_DIR"

cat > "${BIN_DIR}/HermessHub" <<EOF
#!/usr/bin/env bash
set -euo pipefail

ssh -F /dev/null -i "$KEY_PATH" -o BatchMode=yes -o StrictHostKeyChecking=accept-new "$TARGET_USER@$TARGET_HOST" \\
  'cd "$REMOTE_DIR" && exec .venv/bin/hermeshub --config config.yaml run'
EOF

chmod +x "${BIN_DIR}/HermessHub"

echo "Installed ${BIN_DIR}/HermessHub"
echo "Run: HermessHub"
