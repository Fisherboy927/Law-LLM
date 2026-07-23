from __future__ import annotations

import os
import re
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
_PAGE_SUFFIX_RE = re.compile(r"(?:[_-](?:page|p)[_-]?\d+)$", re.IGNORECASE)
_PADDLEOCR_PIPELINE: Any | None = None


@dataclass(frozen=True)
class OCRRecord:
    id: str
    content: str


def natural_sort_key(path: str | os.PathLike[str]) -> tuple[tuple[int, object], ...]:
    """Sort names in human page order, e.g. page2 before page10."""
    name = Path(path).name.lower()
    return tuple(
        (0, int(part)) if part.isdigit() else (1, part)
        for part in re.split(r"(\d+)", name)
    )


def _group_name_from_filename(filename: str) -> str:
    stem = Path(filename).stem
    return _PAGE_SUFFIX_RE.sub("", stem)


def normalize_ocr_text(text: str) -> str:
    return " ".join(text.split())


def iter_image_paths(folder_path: str | os.PathLike[str]) -> list[Path]:
    folder = Path(folder_path)
    if not folder.exists():
        raise FileNotFoundError(f"Input image folder not found: {folder}")
    if not folder.is_dir():
        raise NotADirectoryError(f"Input image path is not a directory: {folder}")

    return sorted(
        (
            entry
            for entry in folder.iterdir()
            if entry.is_file() and entry.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
        ),
        key=natural_sort_key,
    )


def _create_paddleocr_pipeline() -> Any:
    try:
        from paddleocr import PaddleOCRVL
    except ImportError as exc:
        raise ImportError(
            "PaddleOCR-VL is required for OCR. Install PaddlePaddle and PaddleOCR, "
            "for example: python -m pip install 'paddlepaddle>=3.2.1' "
            "'paddleocr[doc-parser]>=3.6.0'. GPU users may need the "
            "CUDA-specific PaddlePaddle package from Paddle's install guide."
        ) from exc

    return PaddleOCRVL(pipeline_version=os.environ.get("PADDLEOCR_PIPELINE_VERSION", "v1.6"))


def _get_paddleocr_pipeline() -> Any:
    global _PADDLEOCR_PIPELINE
    if _PADDLEOCR_PIPELINE is None:
        _PADDLEOCR_PIPELINE = _create_paddleocr_pipeline()
    return _PADDLEOCR_PIPELINE


def _get_mapping_value(value: Any, key: str) -> Any:
    if isinstance(value, dict):
        return value.get(key)
    return None


def _as_sequence(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _extract_text_from_json_payload(payload: Any) -> list[str]:
    text_parts: list[str] = []
    for item in _as_sequence(_get_mapping_value(payload, "parsing_res_list")):
        content = _get_mapping_value(item, "block_content")
        if content:
            text_parts.append(str(content))
    return text_parts


def _extract_text_from_markdown_payload(payload: Any) -> list[str]:
    markdown_texts = _get_mapping_value(payload, "markdown_texts")
    if not markdown_texts:
        return []
    return [str(part) for part in _as_sequence(markdown_texts) if str(part).strip()]


def _extract_text_from_single_paddle_result(result: Any) -> list[str]:
    text_parts: list[str] = []

    json_payload = getattr(result, "json", None)
    text_parts.extend(_extract_text_from_json_payload(json_payload))
    if text_parts:
        return text_parts

    markdown_payload = getattr(result, "markdown", None)
    text_parts.extend(_extract_text_from_markdown_payload(markdown_payload))
    if text_parts:
        return text_parts

    for attr_name in ("text", "content"):
        attr_value = getattr(result, attr_name, None)
        if attr_value:
            return [str(attr_value)]

    if isinstance(result, dict):
        nested_json_payload = result.get("json")
        text_parts.extend(_extract_text_from_json_payload(nested_json_payload))
        if text_parts:
            return text_parts

        nested_markdown_payload = result.get("markdown")
        text_parts.extend(_extract_text_from_markdown_payload(nested_markdown_payload))
        if text_parts:
            return text_parts

        text_parts.extend(_extract_text_from_json_payload(result))
        if text_parts:
            return text_parts

        text_parts.extend(_extract_text_from_markdown_payload(result))
        if text_parts:
            return text_parts

        for key in ("text", "content"):
            value = result.get(key)
            if value:
                return [str(value)]

    result_text = str(result).strip()
    if result_text and result_text != repr(result):
        return [result_text]
    return []


def _extract_text_from_paddle_result(output: Any) -> str:
    text_parts: list[str] = []
    for result in _as_sequence(output):
        text_parts.extend(_extract_text_from_single_paddle_result(result))
    return "\n".join(part.strip() for part in text_parts if part.strip())


def ocr_image(path: str | os.PathLike[str]) -> str:
    pipeline = _get_paddleocr_pipeline()
    output = pipeline.predict(str(path))
    return _extract_text_from_paddle_result(output)


def extract_and_stitch_data(
    folder_path: str | os.PathLike[str],
    *,
    min_content_length: int = 1,
    skip_bad_images: bool = True,
) -> list[OCRRecord]:
    grouped_text: dict[str, list[str]] = {}

    for entry in iter_image_paths(folder_path):
        group_name = _group_name_from_filename(entry.name)
        try:
            clean_text = normalize_ocr_text(ocr_image(entry))
        except Exception as exc:
            if not skip_bad_images:
                raise
            warnings.warn(f"Skipping unreadable image {entry}: {exc}", stacklevel=2)
            continue
        grouped_text.setdefault(group_name, []).append(clean_text)

    stitched: list[OCRRecord] = []
    for group_name, text_parts in grouped_text.items():
        full_text = " ".join(part for part in text_parts if part).strip()
        if len(full_text) >= min_content_length:
            stitched.append(OCRRecord(id=f"original_{group_name}", content=full_text))
    return stitched


def records_to_dataframe(records: Iterable[OCRRecord]) -> pd.DataFrame:
    return pd.DataFrame([{"ID": record.id, "content": record.content} for record in records])
