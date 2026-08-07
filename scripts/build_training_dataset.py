#!/usr/bin/env python3
"""Merge validated augmentation batches into train/validation JSONL for LoRA fine-tuning."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from law_llm.dataset_builder import (  # noqa: E402
    DEFAULT_TRAINING_SYSTEM_PROMPT,
    DEFAULT_VALIDATED_GLOB,
    OUTPUT_FORMATS,
    SPLIT_STRATEGIES,
    DatasetBuildError,
    filter_records,
    find_validated_files,
    load_validated_records,
    split_records,
    summarise,
    to_row,
    write_jsonl,
)

DEFAULT_INPUT_DIR = REPO_ROOT / "data" / "augmentation"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "data" / "training"
DEFAULT_SEED = 20260807


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Merge every synthetic_answers_*_validated.jsonl batch into a single "
            "training-ready dataset with a deterministic train/validation split."
        )
    )
    parser.add_argument(
        "--input-dir",
        default=str(DEFAULT_INPUT_DIR),
        help="Directory holding the validated augmentation batches.",
    )
    parser.add_argument(
        "--pattern",
        default=DEFAULT_VALIDATED_GLOB,
        help="Glob used to select validated batch files inside --input-dir.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory where merged dataset files are written.",
    )
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=OUTPUT_FORMATS,
        default="messages",
        help="Row layout: OpenAI chat 'messages' or Alpaca instruction/input/output.",
    )
    parser.add_argument(
        "--split-strategy",
        choices=SPLIT_STRATEGIES,
        default="source",
        help=(
            "'source' holds out whole answers so variants cannot leak, "
            "'random' splits individual rows, 'none' writes train only."
        ),
    )
    parser.add_argument(
        "--val-fraction",
        type=float,
        default=0.1,
        help="Fraction held out for validation. Use 0 to skip the split.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Seed making the split reproducible.",
    )
    parser.add_argument(
        "--min-quality-score",
        type=int,
        default=None,
        help="Drop scored records below this quality_score.",
    )
    parser.add_argument(
        "--drop-missing-score",
        action="store_true",
        help="Also drop records from batches that never stored quality_score.",
    )
    parser.add_argument(
        "--system-prompt",
        default=DEFAULT_TRAINING_SYSTEM_PROMPT,
        help="System message written into every messages-format row.",
    )
    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="Write rows without the provenance metadata field.",
    )
    return parser.parse_args(argv)


def _counts_table(title: str, counts: dict[str, int]) -> list[str]:
    lines = [f"| {title} | count |", "|---|---:|"]
    lines.extend(f"| `{key}` | {value} |" for key, value in counts.items())
    lines.append("")
    return lines


def _split_section(name: str, stats: dict[str, Any]) -> list[str]:
    if not stats["records"]:
        return [f"## {name}", "", "- Empty split.", ""]
    numbers = stats["answer_numbers"]
    return [
        f"## {name}",
        "",
        f"- Rows: {stats['records']}",
        f"- Source answers: {stats['sources']} ({', '.join(str(n) for n in numbers)})",
        f"- Paraphrased-question rows: {stats['paraphrased']}",
        f"- Scored rows: {stats['scored_records']} "
        f"(min {stats['quality_score_min']}, max {stats['quality_score_max']}, "
        f"mean {stats['quality_score_mean']})",
        f"- Answer characters: {stats['output_chars_total']} total, "
        f"{stats['output_chars_min']}/{stats['output_chars_median']}/{stats['output_chars_max']} "
        "min/median/max",
        "",
        *_counts_table("batch", stats["by_batch"]),
        *_counts_table("example_type", stats["by_example_type"]),
    ]


def render_report(report: dict[str, Any]) -> str:
    config = report["config"]
    overall = report["overall"]
    lines = [
        "# Training Dataset Build Report",
        "",
        "## Configuration",
        "",
        f"- Input directory: `{config['input_dir']}`",
        f"- Batch files: {', '.join(f'`{name}`' for name in config['batch_files'])}",
        f"- Output format: `{config['output_format']}`",
        f"- Split strategy: `{config['split_strategy']}` "
        f"(val_fraction {config['val_fraction']}, seed {config['seed']})",
        f"- Quality filter: min_quality_score={config['min_quality_score']}, "
        f"drop_missing_score={config['drop_missing_score']}",
        f"- Metadata field: {'omitted' if config['no_metadata'] else 'included'}",
        "",
        "## Overall",
        "",
        f"- Records loaded: {report['loaded']}",
        f"- Records dropped by filters: {len(report['dropped'])}",
        f"- Records kept: {overall['records']}",
        f"- Source answers covered: {overall['sources']}",
        "",
        *_counts_table("batch", overall["by_batch"]),
        *_counts_table("example_type", overall["by_example_type"]),
        *_split_section("Train split", report["train"]),
        *_split_section("Validation split", report["validation"]),
    ]

    if report["dropped"]:
        lines.extend(["## Dropped records", "", "| synthetic_id | reason |", "|---|---|"])
        lines.extend(
            f"| `{item['synthetic_id']}` | {item['reason']} |" for item in report["dropped"]
        )
        lines.append("")

    return "\n".join(lines)


def build_training_dataset(args: argparse.Namespace) -> dict[str, Any]:
    batch_files = find_validated_files(args.input_dir, args.pattern)
    records = load_validated_records(batch_files)
    kept, dropped = filter_records(
        records,
        min_quality_score=args.min_quality_score,
        drop_missing_score=args.drop_missing_score,
    )
    train, validation = split_records(
        kept,
        strategy=args.split_strategy,
        val_fraction=args.val_fraction,
        seed=args.seed,
    )

    output_dir = Path(args.output_dir)
    include_metadata = not args.no_metadata

    def rows(split: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            to_row(
                record,
                output_format=args.output_format,
                system_prompt=args.system_prompt,
                include_metadata=include_metadata,
            )
            for record in split
        ]

    written = {
        "train": write_jsonl(output_dir / "train.jsonl", rows(train)),
        "validation": write_jsonl(output_dir / "validation.jsonl", rows(validation)),
        "merged": write_jsonl(output_dir / "merged_records.jsonl", kept),
    }

    report = {
        "config": {
            "input_dir": str(Path(args.input_dir)),
            "batch_files": [path.name for path in batch_files],
            "output_format": args.output_format,
            "split_strategy": args.split_strategy,
            "val_fraction": args.val_fraction,
            "seed": args.seed,
            "min_quality_score": args.min_quality_score,
            "drop_missing_score": args.drop_missing_score,
            "no_metadata": args.no_metadata,
        },
        "loaded": len(records),
        "dropped": [
            {"synthetic_id": record["synthetic_id"], "reason": reason}
            for record, reason in dropped
        ],
        "written": written,
        "overall": summarise(kept),
        "train": summarise(train) if train else {"records": 0},
        "validation": summarise(validation) if validation else {"records": 0},
    }

    (output_dir / "dataset_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "dataset_report.md").write_text(
        render_report(report), encoding="utf-8", newline="\n"
    )
    return report


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = build_training_dataset(args)
    except DatasetBuildError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    written = report["written"]
    output_dir = Path(args.output_dir).resolve()
    print(f"Loaded {report['loaded']} validated records from {len(report['config']['batch_files'])} batches.")
    if report["dropped"]:
        print(f"Dropped {len(report['dropped'])} records by quality filters.")
    print(f"Train rows: {written['train']}")
    print(f"Validation rows: {written['validation']}")
    print(f"Merged records: {written['merged']}")
    print(f"Output directory: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
