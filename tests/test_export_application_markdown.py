from __future__ import annotations

import pytest

from law_llm.ocr_pipeline import OCRRecord
from scripts import export_application_markdown as exporter


def test_validate_records_requires_expected_groups() -> None:
    records = [OCRRecord(id="original_Answer_01", content="one")]

    with pytest.raises(ValueError, match="missing groups: Answer_02"):
        exporter.validate_records(records, expected_count=2)


def test_validate_records_rejects_extra_groups() -> None:
    records = [
        OCRRecord(id="original_Answer_01", content="one"),
        OCRRecord(id="original_Answer_02", content="two"),
        OCRRecord(id="original_Answer_03", content="three"),
    ]

    with pytest.raises(ValueError, match="unexpected groups: Answer_03"):
        exporter.validate_records(records, expected_count=2)


def test_source_images_by_answer_keeps_natural_order(tmp_path) -> None:
    for name in ["Answer_01_page10.png", "Answer_01_page1.png", "Answer_01_page2.png"]:
        (tmp_path / name).write_text("x", encoding="utf-8")

    grouped = exporter.source_images_by_answer(tmp_path)

    assert [path.name for path in grouped["Answer_01"]] == [
        "Answer_01_page1.png",
        "Answer_01_page2.png",
        "Answer_01_page10.png",
    ]


def test_render_markdown_includes_title_sources_and_text(tmp_path) -> None:
    image_path = tmp_path / "Images" / "Answer_01_page1.png"
    image_path.parent.mkdir()
    image_path.write_text("x", encoding="utf-8")
    output_dir = tmp_path / "outputs" / "application_answers_markdown"
    record = OCRRecord(id="original_Answer_01", content="OCR text")

    markdown = exporter.render_markdown("Answer_01", record, [image_path], output_dir)

    assert markdown.startswith("# Answer 01")
    assert "Source images:" in markdown
    assert "## OCR Text" in markdown
    assert "OCR text" in markdown


def test_export_markdown_files_passes_paddle_options(tmp_path, monkeypatch) -> None:
    input_dir = tmp_path / "Images"
    input_dir.mkdir()
    (input_dir / "Answer_01_page1.png").write_text("x", encoding="utf-8")
    output_dir = tmp_path / "markdown"
    raw_output_dir = tmp_path / "raw_paddle"
    calls = []

    def fake_extract_and_stitch_data(*args, **kwargs):
        calls.append((args, kwargs))
        return [OCRRecord(id="original_Answer_01", content="one")]

    monkeypatch.setattr(exporter, "extract_and_stitch_data", fake_extract_and_stitch_data)

    written = exporter.export_markdown_files(
        input_dir,
        output_dir,
        expected_count=1,
        preserve_paddle_markdown=True,
        paddle_output_dir=raw_output_dir,
    )

    assert [path.name for path in written] == ["Answer_01.md"]
    assert calls[0][1]["preserve_markdown"] is True
    assert calls[0][1]["paddle_output_dir"] == raw_output_dir


def test_export_markdown_files_writes_expected_files(tmp_path, monkeypatch) -> None:
    input_dir = tmp_path / "Images"
    input_dir.mkdir()
    (input_dir / "Answer_01_page1.png").write_text("x", encoding="utf-8")
    (input_dir / "Answer_02_page1.png").write_text("x", encoding="utf-8")
    output_dir = tmp_path / "markdown"

    monkeypatch.setattr(
        exporter,
        "extract_and_stitch_data",
        lambda *args, **kwargs: [
            OCRRecord(id="original_Answer_01", content="one"),
            OCRRecord(id="original_Answer_02", content="two"),
        ],
    )

    written = exporter.export_markdown_files(input_dir, output_dir, expected_count=2)

    assert [path.name for path in written] == ["Answer_01.md", "Answer_02.md"]
    assert (output_dir / "Answer_01.md").read_text(encoding="utf-8").endswith("one\n")
    assert (output_dir / "Answer_02.md").read_text(encoding="utf-8").endswith("two\n")
