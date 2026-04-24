from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd
import pytesseract
from PIL import Image

SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


@dataclass(frozen=True)
class OCRRecord:
    id: str
    content: str


def _group_name_from_filename(filename: str) -> str:
    stem = Path(filename).stem
    if "_page" in stem:
        return stem.split("_page")[0]
    return stem


def extract_and_stitch_data(folder_path: str | os.PathLike[str]) -> list[OCRRecord]:
    folder = Path(folder_path)
    if not folder.exists():
        raise FileNotFoundError(f"Input image folder not found: {folder}")

    grouped_text: dict[str, list[str]] = {}

    for entry in sorted(folder.iterdir(), key=lambda p: p.name):
        if entry.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
            continue

        group_name = _group_name_from_filename(entry.name)
        text = pytesseract.image_to_string(Image.open(entry))
        clean_text = " ".join(text.split())
        grouped_text.setdefault(group_name, []).append(clean_text)

    stitched: list[OCRRecord] = []
    for group_name, text_parts in grouped_text.items():
        full_text = " ".join(part for part in text_parts if part).strip()
        if full_text:
            stitched.append(OCRRecord(id=f"original_{group_name}", content=full_text))
    return stitched


def records_to_dataframe(records: Iterable[OCRRecord]) -> pd.DataFrame:
    return pd.DataFrame([{"ID": record.id, "content": record.content} for record in records])
