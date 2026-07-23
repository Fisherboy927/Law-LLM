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
_PADDLEOCR_ENV_OPTIONS = {
    "PADDLEOCR_DEVICE": "device",
    "PADDLEOCR_ENGINE": "engine",
    "PADDLEOCR_LAYOUT_DETECTION_MODEL_NAME": "layout_detection_model_name",
    "PADDLEOCR_LAYOUT_DETECTION_MODEL_DIR": "layout_detection_model_dir",
    "PADDLEOCR_VL_REC_MODEL_NAME": "vl_rec_model_name",
    "PADDLEOCR_VL_REC_MODEL_DIR": "vl_rec_model_dir",
    "PADDLEOCR_VL_REC_BACKEND": "vl_rec_backend",
    "PADDLEOCR_VL_REC_SERVER_URL": "vl_rec_server_url",
    "PADDLEOCR_VL_REC_API_MODEL_NAME": "vl_rec_api_model_name",
    "PADDLEOCR_VL_REC_API_KEY": "vl_rec_api_key",
}
_PADDLEOCR_BOOL_ENV_OPTIONS = {
    "PADDLEOCR_USE_DOC_ORIENTATION_CLASSIFY": "use_doc_orientation_classify",
    "PADDLEOCR_USE_DOC_UNWARPING": "use_doc_unwarping",
    "PADDLEOCR_USE_LAYOUT_DETECTION": "use_layout_detection",
    "PADDLEOCR_USE_CHART_RECOGNITION": "use_chart_recognition",
    "PADDLEOCR_USE_SEAL_RECOGNITION": "use_seal_recognition",
    "PADDLEOCR_USE_OCR_FOR_IMAGE_BLOCK": "use_ocr_for_image_block",
    "PADDLEOCR_FORMAT_BLOCK_CONTENT": "format_block_content",
}


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


def normalize_ocr_markdown(text: str) -> str:
    lines = [" ".join(line.split()) for line in text.splitlines()]
    normalized_lines: list[str] = []
    previous_blank = False
    for line in lines:
        is_blank = not line
        if is_blank and previous_blank:
            continue
        normalized_lines.append(line)
        previous_blank = is_blank
    return "\n".join(normalized_lines).strip()


def _env_bool(name: str) -> bool | None:
    value = os.environ.get(name)
    if value is None or value == "":
        return None
    if value.lower() in {"1", "true", "yes", "y", "on"}:
        return True
    if value.lower() in {"0", "false", "no", "n", "off"}:
        return False
    raise ValueError(f"Environment variable {name} must be a boolean value, got {value!r}")


def _paddleocr_pipeline_kwargs() -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "pipeline_version": os.environ.get("PADDLEOCR_PIPELINE_VERSION", "v1.6")
    }
    for env_name, option_name in _PADDLEOCR_ENV_OPTIONS.items():
        value = os.environ.get(env_name)
        if value:
            kwargs[option_name] = value
    for env_name, option_name in _PADDLEOCR_BOOL_ENV_OPTIONS.items():
        value = _env_bool(env_name)
        if value is not None:
            kwargs[option_name] = value
    concurrency = os.environ.get("PADDLEOCR_VL_REC_MAX_CONCURRENCY")
    if concurrency:
        kwargs["vl_rec_max_concurrency"] = int(concurrency)
    return kwargs


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

    return PaddleOCRVL(**_paddleocr_pipeline_kwargs())


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


def _save_paddle_result(output: Any, output_dir: str | os.PathLike[str]) -> None:
    save_path = Path(output_dir)
    save_path.mkdir(parents=True, exist_ok=True)
    for result in _as_sequence(output):
        save_json = getattr(result, "save_to_json", None)
        if callable(save_json):
            save_json(save_path=save_path)
        save_markdown = getattr(result, "save_to_markdown", None)
        if callable(save_markdown):
            save_markdown(save_path=save_path)


def ocr_image(
    path: str | os.PathLike[str],
    *,
    paddle_output_dir: str | os.PathLike[str] | None = None,
) -> str:
    pipeline = _get_paddleocr_pipeline()
    output = pipeline.predict(str(path))
    if paddle_output_dir is not None:
        _save_paddle_result(output, paddle_output_dir)
    return _extract_text_from_paddle_result(output)


def extract_and_stitch_data(
    folder_path: str | os.PathLike[str],
    *,
    min_content_length: int = 1,
    skip_bad_images: bool = True,
    preserve_markdown: bool = False,
    paddle_output_dir: str | os.PathLike[str] | None = None,
) -> list[OCRRecord]:
    grouped_text: dict[str, list[str]] = {}

    normalize = normalize_ocr_markdown if preserve_markdown else normalize_ocr_text
    page_separator = "\n\n---\n\n" if preserve_markdown else " "

    for entry in iter_image_paths(folder_path):
        group_name = _group_name_from_filename(entry.name)
        try:
            raw_output_dir = Path(paddle_output_dir) / group_name if paddle_output_dir else None
            clean_text = normalize(
                ocr_image(entry, paddle_output_dir=raw_output_dir)
            )
        except Exception as exc:
            if not skip_bad_images:
                raise
            warnings.warn(f"Skipping unreadable image {entry}: {exc}", stacklevel=2)
            continue
        grouped_text.setdefault(group_name, []).append(clean_text)

    stitched: list[OCRRecord] = []
    for group_name, text_parts in grouped_text.items():
        full_text = page_separator.join(part for part in text_parts if part).strip()
        if len(full_text) >= min_content_length:
            stitched.append(OCRRecord(id=f"original_{group_name}", content=full_text))
    return stitched


def records_to_dataframe(records: Iterable[OCRRecord]) -> pd.DataFrame:
    return pd.DataFrame([{"ID": record.id, "content": record.content} for record in records])
