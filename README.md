# Law-LLM
A Fine-Tuned LLM Intended for Law Firm Applications

## Local development setup

This repository currently contains a Colab-first notebook (`Law_LLM.ipynb`). For local
development and environment verification, use the scripts in `scripts/`.

### 1) Create and activate a virtual environment

Run the setup helper:

`./scripts/setup_env.sh`

This script creates `.venv`, upgrades pip, and installs dependencies from:

- `requirements.txt`
- `requirements-dev.txt`

### 2) Run a local smoke demo

The smoke demo exercises the OCR + dataset stitching workflow from the notebook using
local images.

Activate the virtual environment:

`source .venv/bin/activate`

Generate sample images:

`python scripts/create_demo_images.py --output-dir demo_images`

Run the demo:

`python scripts/demo_run.py --input-dir demo_images --output-csv demo_output/final_training_dataset.csv`

Expected output:

- Prints number of stitched OCR records.
- Writes a CSV with columns `ID` and `content`.

### Notes

- The notebook includes Google Colab and Google Drive-specific cells that are not required
  for local smoke testing.
- Training/inference cells depend on GPU resources and large model downloads; they are kept
  in the notebook and are not part of the local smoke demo.
