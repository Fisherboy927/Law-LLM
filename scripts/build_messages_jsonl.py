#!/usr/bin/env python3
"""Build OpenAI-style messages JSONL from Markdown answers and OpenAI rewrites."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from tqdm import tqdm

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from law_llm.openai_augmentation import (  # noqa: E402
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_USER_PROMPT_TEMPLATE,
    build_messages_record,
    generate_variations,
    get_openai_model,
    get_required_env,
)

DEFAULT_INPUT_DIR = REPO_ROOT / "outputs" / "application_answers_markdown"
DEFAULT_OUTPUT_JSONL = REPO_ROOT / "outputs" / "application_answers_messages.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate OpenAI messages JSONL from application-answer Markdown files."
    )
    parser.add_argument(
        "--input-dir",
        default=str(DEFAULT_INPUT_DIR),
        help="Directory containing Answer_XX.md files.",
    )
    parser.add_argument(
        "--output-jsonl",
        default=str(DEFAULT_OUTPUT_JSONL),
        help="Path where JSONL will be written.",
    )
    parser.add_argument(
        "--num-variations",
        type=int,
        default=3,
        help="Number of OpenAI-generated rewrites per Markdown file.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="OpenAI model name. Defaults to OPENAI_MODEL or gpt-4o-mini.",
    )
    parser.add_argument(
        "--system-prompt",
        default=DEFAULT_SYSTEM_PROMPT,
        help="System prompt stored in each training row.",
    )
    parser.add_argument(
        "--user-prompt-template",
        default=DEFAULT_USER_PROMPT_TEMPLATE,
        help="User prompt template. Use {answer_id} for the Markdown stem.",
    )
    parser.add_argument(
        "--include-original",
        dest="include_original",
        action="store_true",
        default=True,
        help="Include the original OCR Markdown text as one training row per answer.",
    )
    parser.add_argument(
        "--no-include-original",
        dest="include_original",
        action="store_false",
        help="Only include OpenAI-generated variations.",
    )
    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="Write rows containing only the messages field.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process only the first N Markdown files for low-cost smoke tests.",
    )
    return parser.parse_args()


def iter_markdown_files(input_dir: str | Path, limit: int | None = None) -> list[Path]:
    folder = Path(input_dir)
    if not folder.exists():
        raise FileNotFoundError(f"Input Markdown folder not found: {folder}")
    if not folder.is_dir():
        raise NotADirectoryError(f"Input Markdown path is not a directory: {folder}")

    files = sorted(path for path in folder.glob("Answer_*.md") if path.is_file())
    if limit is not None:
        if limit < 1:
            raise ValueError("limit must be at least 1 when provided")
        files = files[:limit]
    return files


def _metadata(answer_id: str, source: str, variation_index: int | None = None) -> dict[str, Any]:
    metadata: dict[str, Any] = {"answer_id": answer_id, "source": source}
    if variation_index is not None:
        metadata["variation_index"] = variation_index
    return metadata


def extract_ocr_text_from_markdown(markdown_text: str) -> str:
    marker = "## OCR Text"
    if marker not in markdown_text:
        return markdown_text.strip()
    return markdown_text.split(marker, 1)[1].strip()


def rows_for_markdown(
    markdown_path: Path,
    *,
    client: Any,
    model: str,
    num_variations: int,
    include_original: bool,
    include_metadata: bool,
    system_prompt: str,
    user_prompt_template: str,
) -> list[dict[str, Any]]:
    answer_id = markdown_path.stem
    markdown_text = markdown_path.read_text(encoding="utf-8").strip()
    if not markdown_text:
        raise ValueError(f"Markdown file is empty: {markdown_path}")
    ocr_text = extract_ocr_text_from_markdown(markdown_text)
    if not ocr_text:
        raise ValueError(f"Markdown file has no OCR text: {markdown_path}")

    rows: list[dict[str, Any]] = []
    if include_original:
        rows.append(
            build_messages_record(
                answer_id=answer_id,
                assistant_content=ocr_text,
                system_prompt=system_prompt,
                user_prompt_template=user_prompt_template,
                metadata=_metadata(answer_id, "original") if include_metadata else None,
            )
        )

    for index, variation in enumerate(
        generate_variations(
            client,
            answer_id=answer_id,
            markdown_text=ocr_text,
            num_variations=num_variations,
            model=model,
        ),
        start=1,
    ):
        rows.append(
            build_messages_record(
                answer_id=answer_id,
                assistant_content=variation,
                system_prompt=system_prompt,
                user_prompt_template=user_prompt_template,
                metadata=(
                    _metadata(answer_id, "openai_variation", index)
                    if include_metadata
                    else None
                ),
            )
        )
    return rows


def build_messages_jsonl(
    input_dir: str | Path,
    output_jsonl: str | Path,
    *,
    client: Any,
    model: str,
    num_variations: int = 3,
    include_original: bool = True,
    include_metadata: bool = True,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    user_prompt_template: str = DEFAULT_USER_PROMPT_TEMPLATE,
    limit: int | None = None,
) -> int:
    markdown_files = iter_markdown_files(input_dir, limit=limit)
    if not markdown_files:
        raise ValueError(f"No Answer_*.md files found in {input_dir}")

    output_path = Path(output_jsonl)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    row_count = 0
    with output_path.open("w", encoding="utf-8") as handle:
        for markdown_path in tqdm(markdown_files, desc="Building JSONL"):
            for row in rows_for_markdown(
                markdown_path,
                client=client,
                model=model,
                num_variations=num_variations,
                include_original=include_original,
                include_metadata=include_metadata,
                system_prompt=system_prompt,
                user_prompt_template=user_prompt_template,
            ):
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                row_count += 1
    return row_count


def main() -> None:
    args = parse_args()
    from openai import OpenAI

    client = OpenAI(api_key=get_required_env("OPENAI_API_KEY"))
    model = args.model or get_openai_model()
    row_count = build_messages_jsonl(
        args.input_dir,
        args.output_jsonl,
        client=client,
        model=model,
        num_variations=args.num_variations,
        include_original=args.include_original,
        include_metadata=not args.no_metadata,
        system_prompt=args.system_prompt,
        user_prompt_template=args.user_prompt_template,
        limit=args.limit,
    )
    print(f"Rows written: {row_count}")
    print(f"Output JSONL: {Path(args.output_jsonl).resolve()}")


if __name__ == "__main__":
    main()
