#!/usr/bin/env bash
set -euo pipefail

if ! command -v sudo >/dev/null 2>&1; then
  echo "(!) Please run this script with sudo." >&2
  exit 1
fi

echo "[1/4] Installing system dependencies (Ubuntu)..."
sudo apt-get update -y
sudo apt-get install -y pipx libportaudio2 python3-tk

echo "[2/4] Configuring pipx PATH..."
pipx ensurepath >/dev/null 2>&1 || true

echo "[3/4] Installing application with pipx..."
pipx install . --force

echo "[4/4] Creating and activating .venv environment from requirements.txt..."
PY=${PYTHON:-python3}
if [ ! -d ".venv" ]; then
  $PY -m venv .venv
fi
source .venv/bin/activate
python -m pip install --upgrade pip
if [ -f "requirements.txt" ]; then
  pip install -r requirements.txt
fi
pip install -e .

echo
echo "- Application is installed with pipx: run 'voicechanger' from any directory."
echo "- Local environment is now ACTIVE (.venv)."
echo

exec $SHELL -i
