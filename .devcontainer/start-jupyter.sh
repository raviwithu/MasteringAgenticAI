#!/usr/bin/env bash
# Launch JupyterLab so it is reachable on the forwarded port 8888.
#
# --ip=0.0.0.0 binds to all interfaces (required so the forwarded/public port
#   reaches the server inside the container).
# In Codespaces, port 8888 is published with "visibility": "public" (see
#   devcontainer.json), so the forwarded URL is accessible without auth.
#
# SECURITY NOTE: a public, token-less Jupyter server lets anyone with the URL
# run code. This is convenient for a training lab but do NOT expose real
# secrets/keys while it is public. Remove the --ServerApp.token/password flags
# below to re-enable the login token.
set -euo pipefail

# pip installs console scripts (jupyter) into the user bin, which is not always
# on PATH in the non-interactive shell that runs postStartCommand. Add it so the
# `jupyter` entry point resolves regardless of how this script is invoked.
export PATH="$HOME/.local/bin:$PATH"

PORT="${JUPYTER_PORT:-8888}"

# Idempotent: if a server is already serving this port, don't start a second one.
# (jupyter lab server list prints "http://...:PORT/" for each running server.)
if jupyter server list 2>/dev/null | grep -q ":${PORT}/"; then
  echo "JupyterLab already running on port ${PORT}; nothing to do."
  exit 0
fi

exec jupyter lab \
  --ip=0.0.0.0 \
  --port="${PORT}" \
  --no-browser \
  --allow-root \
  --ServerApp.token='' \
  --ServerApp.password='' \
  --ServerApp.allow_origin='*' \
  --notebook-dir=/workspaces
