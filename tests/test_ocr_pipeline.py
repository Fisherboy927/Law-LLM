from __future__ import annotations

from types import SimpleNamespace

import pytest

from law_llm import ocr_pipeline
from law_llm.ocr_pipeline import OCRRecord


def test_group_name_from_filename_handles_page_suffixes() -> None:
    assert ocr_pipeline._group_name_from_filename("Answer_20_page1.png") == "Answer_20"
    assert ocr_pipeline._group_name_from_filename("Answer_20_Page10.png") == "Answer_20"
    assert ocr_pipeline._group_name_from_filename("Answer_20-p2.jpg") == "Answer_20"


def test_iter_image_paths_uses_natural_order(tmp_path) -> None:
    for name in ["Answer_01_page10.png", "Answer_01_page2.png", "Answer_01_page1.png"]:
        (tmp_path / name).write_text("x", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("ignore", encoding="utf-8")

    assert [path.name for path in ocr_pipeline.iter_image_paths(tmp_path)] == [
        "Answer_01_page1.png",
        "Answer_01_page2.png",
        "Answer_01_page10.png",
    ]


def test_extract_text_from_paddle_json_payload() -> None:
    output = [
        SimpleNamespace(
            json={
                "parsing_res_list": [
                    {"block_content": "First block"},
                    {"block_content": "Second block"},
                ]
            }
        )
    ]

    assert ocr_pipeline._extract_text_from_paddle_result(output) == "First block\nSecond block"


def test_extract_text_from_paddle_markdown_payload() -> None:
    output = [SimpleNamespace(markdown={"markdown_texts": ["# Heading", "Body"]})]

    assert ocr_pipeline._extract_text_from_paddle_result(output) == "# Heading\nBody"


def test_extract_and_stitch_data_groups_pages_in_order(tmp_path, monkeypatch) -> None:
    for name in ["Answer_01_page2.png", "Answer_01_page1.png", "Answer_02_page1.png"]:
        (tmp_path / name).write_text("x", encoding="utf-8")

    text_by_name = {
        "Answer_01_page1.png": "first",
        "Answer_01_page2.png": "second",
        "Answer_02_page1.png": "other",
    }

    monkeypatch.setattr(
        ocr_pipeline,
        "ocr_image",
        lambda path: text_by_name[path.name],
    )

    assert ocr_pipeline.extract_and_stitch_data(tmp_path) == [
        OCRRecord(id="original_Answer_01", content="first second"),
        OCRRecord(id="original_Answer_02", content="other"),
    ]


def test_extract_and_stitch_data_can_skip_bad_images(tmp_path, monkeypatch) -> None:
    (tmp_path / "Answer_01_page1.png").write_text("x", encoding="utf-8")
    (tmp_path / "Answer_02_page1.png").write_text("x", encoding="utf-8")

    def fake_ocr(path):
        if path.name == "Answer_01_page1.png":
            raise RuntimeError("bad image")
        return "usable text"

    monkeypatch.setattr(ocr_pipeline, "ocr_image", fake_ocr)

    with pytest.warns(UserWarning, match="Skipping unreadable image"):
        records = ocr_pipeline.extract_and_stitch_data(tmp_path)

    assert records == [OCRRecord(id="original_Answer_02", content="usable text")]


def test_create_paddleocr_pipeline_has_actionable_import_error(monkeypatch) -> None:
    def fake_import(name, *args, **kwargs):
        if name == "paddleocr":
            raise ImportError("missing")
        return original_import(name, *args, **kwargs)

    original_import = __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__
    monkeypatch.setattr("builtins.__import__", fake_import)

    with pytest.raises(ImportError, match="PaddleOCR-VL is required"):
        ocr_pipeline._create_paddleocr_pipeline()
