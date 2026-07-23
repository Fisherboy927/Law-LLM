#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

python scripts/export_application_markdown.py \
  --input-dir Images \
  --output-dir outputs/application_answers_markdown \
  --expected-count 50 \
  --min-content-length 50 \
  --device "${PADDLEOCR_DEVICE:-gpu:0}" \
  --require-gpu \
  "$@"
