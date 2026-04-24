#!/usr/bin/env python3
"""Run a local smoke test for the OCR preprocessing pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from law_llm.ocr_pipeline import extract_and_stitch_data, records_to_dataframe


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Law-LLM local OCR demo.")
    parser.add_argument(
        "--input-dir",
        default="sample_data/images",
        help="Directory containing sample images.",
    )
    parser.add_argument(
        "--output-csv",
        default="sample_data/output/final_training_dataset.csv",
        help="Where to write demo CSV output.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_dir = Path(args.input_dir)
    output_csv = Path(args.output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    records = extract_and_stitch_data(input_dir)
    if not records:
        raise RuntimeError(
            f"No OCR records were produced from input directory: {input_dir}"
        )

    df = records_to_dataframe(records)
    df.to_csv(output_csv, index=False)

    print(f"Input directory: {input_dir.resolve()}")
    print(f"Records generated: {len(records)}")
    print(f"Output CSV: {output_csv.resolve()}")
    print("\nSample rows:")
    print(df.head(5).to_string(index=False))


if __name__ == "__main__":
    main()
