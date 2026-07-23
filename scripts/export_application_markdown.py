#!/usr/bin/env python3
"""Export stitched OCR results to one Markdown file per application answer."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from law_llm.ocr_pipeline import (  # noqa: E402
    OCRRecord,
    _group_name_from_filename,
    extract_and_stitch_data,
    iter_image_paths,
    natural_sort_key,
)

DEFAULT_INPUT_DIR = REPO_ROOT / "Images"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "outputs" / "application_answers_markdown"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate one Markdown file per stitched application-answer OCR group."
    )
    parser.add_argument(
        "--input-dir",
        default=str(DEFAULT_INPUT_DIR),
        help="Directory containing Answer_XX_pageN image files.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory where Markdown files will be written.",
    )
    parser.add_argument(
        "--expected-count",
        type=int,
        default=50,
        help="Expected number of Answer_XX groups to export.",
    )
    parser.add_argument(
        "--min-content-length",
        type=int,
        default=50,
        help="Minimum stitched OCR text length required for an output file.",
    )
    parser.add_argument(
        "--fail-on-bad-images",
        action="store_true",
        help="Raise OCR errors instead of warning and skipping unreadable images.",
    )
    parser.add_argument(
        "--preserve-paddle-markdown",
        action="store_true",
        help="Preserve PaddleOCR-VL Markdown line breaks instead of flattening text.",
    )
    parser.add_argument(
        "--paddle-output-dir",
        help=(
            "Optional directory for raw PaddleOCR-VL outputs saved with "
            "Result.save_to_json() and Result.save_to_markdown()."
        ),
    )
    return parser.parse_args()


def answer_name_from_record(record: OCRRecord) -> str:
    prefix = "original_"
    if not record.id.startswith(prefix):
        raise ValueError(f"Unexpected OCR record ID format: {record.id}")
    answer_name = record.id[len(prefix) :]
    if not answer_name:
        raise ValueError(f"Unexpected empty answer name in OCR record ID: {record.id}")
    return answer_name


def expected_answer_names(expected_count: int) -> list[str]:
    if expected_count < 1:
        raise ValueError("expected_count must be at least 1")
    return [f"Answer_{index:02d}" for index in range(1, expected_count + 1)]


def source_images_by_answer(input_dir: str | Path) -> dict[str, list[Path]]:
    grouped: dict[str, list[Path]] = {}
    for image_path in iter_image_paths(input_dir):
        group_name = _group_name_from_filename(image_path.name)
        grouped.setdefault(group_name, []).append(image_path)
    for paths in grouped.values():
        paths.sort(key=natural_sort_key)
    return grouped


def validate_records(records: list[OCRRecord], expected_count: int) -> dict[str, OCRRecord]:
    records_by_answer = {answer_name_from_record(record): record for record in records}
    expected = expected_answer_names(expected_count)
    expected_set = set(expected)
    actual_set = set(records_by_answer)

    missing = sorted(expected_set - actual_set, key=natural_sort_key)
    extra = sorted(actual_set - expected_set, key=natural_sort_key)
    if missing or extra:
        details: list[str] = []
        if missing:
            details.append(f"missing groups: {', '.join(missing)}")
        if extra:
            details.append(f"unexpected groups: {', '.join(extra)}")
        raise ValueError(
            f"Expected exactly {expected_count} groups ({expected[0]} through {expected[-1]}), "
            + "; ".join(details)
        )

    if len(records_by_answer) != len(records):
        raise ValueError("Duplicate OCR record IDs detected; cannot safely export Markdown.")

    return records_by_answer


def markdown_source_link(image_path: Path, output_dir: Path) -> str:
    return os.path.relpath(image_path.resolve(), output_dir.resolve()).replace(os.sep, "/")


def render_markdown(
    answer_name: str,
    record: OCRRecord,
    image_paths: list[Path],
    output_dir: Path,
) -> str:
    title = answer_name.replace("_", " ")
    source_lines = [
        f"- {markdown_source_link(image_path, output_dir)}" for image_path in image_paths
    ]
    if not source_lines:
        source_lines = ["- No source images found"]

    content = record.content.strip()
    return "\n".join(
        [
            f"# {title}",
            "",
            "Source images:",
            "",
            *source_lines,
            "",
            "## OCR Text",
            "",
            content,
            "",
        ]
    )


def export_markdown_files(
    input_dir: str | Path,
    output_dir: str | Path,
    *,
    expected_count: int = 50,
    min_content_length: int = 50,
    skip_bad_images: bool = True,
    preserve_paddle_markdown: bool = False,
    paddle_output_dir: str | Path | None = None,
) -> list[Path]:
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    records = extract_and_stitch_data(
        input_path,
        min_content_length=min_content_length,
        skip_bad_images=skip_bad_images,
        preserve_markdown=preserve_paddle_markdown,
        paddle_output_dir=paddle_output_dir,
    )
    records_by_answer = validate_records(records, expected_count)
    images_by_answer = source_images_by_answer(input_path)

    output_path.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for answer_name in expected_answer_names(expected_count):
        record = records_by_answer[answer_name]
        markdown = render_markdown(
            answer_name,
            record,
            images_by_answer.get(answer_name, []),
            output_path,
        )
        output_file = output_path / f"{answer_name}.md"
        output_file.write_text(markdown, encoding="utf-8")
        written.append(output_file)
    return written


def main() -> None:
    args = parse_args()
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    image_count = len(iter_image_paths(input_dir))
    written = export_markdown_files(
        input_dir,
        output_dir,
        expected_count=args.expected_count,
        min_content_length=args.min_content_length,
        skip_bad_images=not args.fail_on_bad_images,
        preserve_paddle_markdown=args.preserve_paddle_markdown,
        paddle_output_dir=args.paddle_output_dir,
    )

    print(f"Input directory: {input_dir.resolve()}")
    print(f"Images processed: {image_count}")
    print(f"Markdown files written: {len(written)}")
    print(f"Output directory: {output_dir.resolve()}")
    if args.paddle_output_dir:
        print(f"Raw PaddleOCR-VL output directory: {Path(args.paddle_output_dir).resolve()}")


if __name__ == "__main__":
    main()
