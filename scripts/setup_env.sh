#!/usr/bin/env bash
set -euo pipefail

need_apt=false

if ! command -v tesseract >/dev/null 2>&1; then
  need_apt=true
fi

if ! python3 -m ensurepip --version >/dev/null 2>&1; then
  need_apt=true
fi

if [ "$need_apt" = true ]; then
  sudo apt-get update
  sudo apt-get install -y tesseract-ocr python3-venv
fi

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
