#!/usr/bin/env bash
set -euo pipefail

if ! command -v tesseract >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y tesseract-ocr
fi

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
