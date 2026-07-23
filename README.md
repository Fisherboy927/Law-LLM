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

`requirements-dev.txt` installs the CPU PaddlePaddle package through `requirements-cpu.txt`.

For GPU OCR, use the GPU dev requirements instead of `requirements-dev.txt`. For CUDA 12.6-compatible environments:

```bash
python -m pip uninstall -y paddlepaddle paddlepaddle-gpu
python -m pip install -r requirements-dev-gpu-cu126.txt
```

Verify that Paddle sees CUDA:

```bash
python -c "import paddle; print(paddle.__version__); print(paddle.is_compiled_with_cuda()); print(paddle.device.cuda.device_count())"
```

Expected GPU-capable output includes `True` for `is_compiled_with_cuda()` and at least `1` CUDA device. If your CUDA runtime differs from CUDA 12.6, use PaddlePaddle's official install selector and update the package index URL accordingly.

`requirements.txt` installs the shared data-stage dependencies:

- PaddleOCR-VL through `paddleocr[doc-parser]`
- OpenAI SDK
- `tqdm`
- `pandas` for compatibility with existing OCR record helpers

PaddlePaddle itself is selected by the environment-specific files:

- `requirements-cpu.txt` — CPU `paddlepaddle`
- `requirements-gpu-cu126.txt` — CUDA 12.6 `paddlepaddle-gpu`
- `requirements-dev.txt` / `requirements-dev-gpu-cu126.txt` — development/test variants

GPU users must replace the default CPU `paddlepaddle` package with the CUDA-specific `paddlepaddle-gpu` wheel that matches their machine. Follow the official PaddlePaddle/PaddleOCR installation guide if `requirements-gpu-cu126.txt` is not appropriate for your CUDA runtime.

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

The script auto-selects `gpu:0` when a CUDA-enabled PaddlePaddle install is available; otherwise it uses CPU.

For the normal GPU OCR run, use the one-command wrapper. It hard-codes the project defaults above and fails fast if the environment is still CPU-only:

```bash
bash scripts/run_gpu_ocr.sh
```

The wrapper uses `Images/`, writes to `outputs/application_answers_markdown/`, expects 50 answer groups, requires at least 50 OCR characters per stitched answer, and runs PaddleOCR-VL with `--device gpu:0 --require-gpu`.

To choose a different PaddleOCR GPU device while keeping the same project defaults:

```bash
PADDLEOCR_DEVICE=gpu:1 bash scripts/run_gpu_ocr.sh
```

Additional `export_application_markdown.py` flags can be appended to the wrapper command, for example:

```bash
bash scripts/run_gpu_ocr.sh \
  --preserve-paddle-markdown \
  --paddle-output-dir outputs/paddleocr_vl_raw
```

Watch GPU usage in another terminal with:

```bash
watch -n 1 nvidia-smi
```

To keep PaddleOCR-VL's Markdown structure and save the raw PaddleOCR JSON/Markdown `Result` outputs next to the stitched answer Markdown, run:

```bash
python scripts/export_application_markdown.py \
  --input-dir Images \
  --output-dir outputs/application_answers_markdown \
  --expected-count 50 \
  --min-content-length 50 \
  --preserve-paddle-markdown \
  --paddle-output-dir outputs/paddleocr_vl_raw
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
- `PADDLEOCR_DEVICE` — optional PaddleOCR-VL device, for example `cpu` or `gpu:0`; if unset, the script auto-selects `gpu:0` only when CUDA-enabled PaddlePaddle is installed and a GPU is visible.
- `PADDLEOCR_ENGINE` — optional PaddleOCR-VL engine, for example `paddle`, `paddle_static`, `paddle_dynamic`, or `transformers`.
- `PADDLEOCR_LAYOUT_DETECTION_MODEL_DIR` / `PADDLEOCR_VL_REC_MODEL_DIR` — optional local model directories for offline or pinned-model inference.
- `PADDLEOCR_VL_REC_BACKEND`, `PADDLEOCR_VL_REC_SERVER_URL`, `PADDLEOCR_VL_REC_API_MODEL_NAME`, `PADDLEOCR_VL_REC_MAX_CONCURRENCY` — optional remote VLM-recognition backend settings.
- `PADDLEOCR_USE_DOC_ORIENTATION_CLASSIFY`, `PADDLEOCR_USE_DOC_UNWARPING`, `PADDLEOCR_USE_LAYOUT_DETECTION`, `PADDLEOCR_USE_CHART_RECOGNITION`, `PADDLEOCR_USE_SEAL_RECOGNITION`, `PADDLEOCR_USE_OCR_FOR_IMAGE_BLOCK`, `PADDLEOCR_FORMAT_BLOCK_CONTENT` — optional boolean PaddleOCR-VL feature switches (`true`/`false`).

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
