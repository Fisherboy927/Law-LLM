# Law-LLM

Data preparation pipeline for law firm application-answer fine-tuning.

The current local workflow focuses on the data stage only:

```text
Images/
  -> PaddleOCR-VL OCR and page stitching
  -> one Markdown file per Answer_XX group
  -> OpenAI data augmentation
  -> OpenAI-style messages JSONL
```

Local model loading and LoRA fine-tuning are intentionally out of scope for this stage.
The generated JSONL can be used as the input to a later local SFT/LoRA workflow.

## Security note

OpenAI credentials must come from `OPENAI_API_KEY` in your environment. Do **not** paste API keys into notebook source, scripts, Markdown files, or JSONL outputs.

If an API key was ever committed to this repository, treat it as compromised and revoke it in the OpenAI dashboard before creating a new one.

## Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

`requirements.txt` installs the data-stage dependencies:

- PaddleOCR-VL through `paddleocr[doc-parser]`
- PaddlePaddle
- OpenAI SDK
- `tqdm`
- `pandas` for compatibility with existing OCR record helpers

GPU users may need to install the PaddlePaddle package that matches their CUDA version before installing the rest of the requirements. Follow the official PaddlePaddle/PaddleOCR installation guide if the default CPU wheel is not appropriate for your machine.

## 1. Export application-answer Markdown

The source corpus is `Images/`, which contains image pages named like `Answer_01_page1.png`.
Multi-page answers are grouped by `Answer_XX` and stitched in natural page order.

Run:

```bash
python scripts/export_application_markdown.py \
  --input-dir Images \
  --output-dir outputs/application_answers_markdown \
  --expected-count 50 \
  --min-content-length 50
```

Expected result:

- `outputs/application_answers_markdown/Answer_01.md`
- `outputs/application_answers_markdown/Answer_02.md`
- ...
- `outputs/application_answers_markdown/Answer_50.md`

Each Markdown file contains source image links and the stitched PaddleOCR-VL text.
Generated files under `outputs/` are ignored by git.

## 2. Build OpenAI messages JSONL

For a low-cost smoke test, process only the first two Markdown files:

```bash
OPENAI_API_KEY=... python scripts/build_messages_jsonl.py \
  --input-dir outputs/application_answers_markdown \
  --output-jsonl outputs/application_answers_messages.jsonl \
  --num-variations 1 \
  --include-original \
  --limit 2
```

For a full data run, remove `--limit` and set the number of generated rewrites:

```bash
OPENAI_API_KEY=... python scripts/build_messages_jsonl.py \
  --input-dir outputs/application_answers_markdown \
  --output-jsonl outputs/application_answers_messages.jsonl \
  --num-variations 3 \
  --include-original
```

Each JSONL row uses OpenAI-style messages format:

```json
{"messages":[{"role":"system","content":"You are a legal application writing assistant..."},{"role":"user","content":"Write a polished law firm application answer for Answer_01."},{"role":"assistant","content":"..."}],"metadata":{"answer_id":"Answer_01","source":"openai_variation","variation_index":1}}
```

Use `--no-metadata` if the downstream trainer expects each row to contain only `messages`.

Useful environment variables:

- `OPENAI_API_KEY` — required for JSONL augmentation.
- `OPENAI_MODEL` — optional; defaults to `gpt-4o-mini`.
- `PADDLEOCR_PIPELINE_VERSION` — optional; defaults to `v1.6`.

## Verify outputs

Run unit tests:

```bash
python -m pytest
```

Check JSONL shape after generation:

```bash
python -c "import json; from pathlib import Path; rows=[json.loads(l) for l in Path('outputs/application_answers_messages.jsonl').open(encoding='utf-8')]; assert rows; assert all('messages' in r for r in rows); assert all([m['role'] for r in rows for m in r['messages']]); print(len(rows), rows[0]['messages'][0]['role'], rows[0]['messages'][-1]['role'])"
```

Expected roles are `system` then `assistant` for the first and last message in each row.

## Notebook status

`Law_LLM.ipynb` remains as a legacy Colab/training reference. The maintained local entry points for the current data stage are:

- `scripts/export_application_markdown.py`
- `scripts/build_messages_jsonl.py`
