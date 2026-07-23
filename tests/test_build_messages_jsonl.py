from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import build_messages_jsonl as builder


class DummyClient:
    pass


def test_iter_markdown_files_filters_and_limits(tmp_path) -> None:
    for name in ["Answer_02.md", "notes.md", "Answer_01.md"]:
        (tmp_path / name).write_text("text", encoding="utf-8")

    files = builder.iter_markdown_files(tmp_path, limit=1)

    assert [path.name for path in files] == ["Answer_01.md"]


def test_rows_for_markdown_includes_original_and_variations(tmp_path, monkeypatch) -> None:
    markdown_path = tmp_path / "Answer_01.md"
    markdown_path.write_text(
        "# Answer 01\n\nSource images:\n\n- image.png\n\n## OCR Text\n\nOriginal text",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        builder,
        "generate_variations",
        lambda *args, **kwargs: ["Variation one", "Variation two"],
    )

    rows = builder.rows_for_markdown(
        markdown_path,
        client=DummyClient(),
        model="test-model",
        num_variations=2,
        include_original=True,
        include_metadata=True,
        system_prompt="System",
        user_prompt_template="Prompt {answer_id}",
    )

    assert len(rows) == 3
    assert rows[0]["metadata"] == {"answer_id": "Answer_01", "source": "original"}
    assert rows[0]["messages"][2]["content"] == "Original text"
    assert rows[1]["metadata"] == {
        "answer_id": "Answer_01",
        "source": "openai_variation",
        "variation_index": 1,
    }
    assert rows[2]["messages"][2]["content"] == "Variation two"


def test_rows_for_markdown_can_omit_metadata(tmp_path, monkeypatch) -> None:
    markdown_path = tmp_path / "Answer_01.md"
    markdown_path.write_text("Original text", encoding="utf-8")
    monkeypatch.setattr(builder, "generate_variations", lambda *args, **kwargs: [])

    rows = builder.rows_for_markdown(
        markdown_path,
        client=DummyClient(),
        model="test-model",
        num_variations=0,
        include_original=True,
        include_metadata=False,
        system_prompt="System",
        user_prompt_template="Prompt {answer_id}",
    )

    assert set(rows[0]) == {"messages"}


def test_build_messages_jsonl_writes_valid_jsonl(tmp_path, monkeypatch) -> None:
    input_dir = tmp_path / "markdown"
    input_dir.mkdir()
    (input_dir / "Answer_01.md").write_text("Answer one", encoding="utf-8")
    (input_dir / "Answer_02.md").write_text("Answer two", encoding="utf-8")
    output_jsonl = tmp_path / "out" / "messages.jsonl"

    monkeypatch.setattr(builder, "generate_variations", lambda *args, **kwargs: ["Variation"])

    row_count = builder.build_messages_jsonl(
        input_dir,
        output_jsonl,
        client=DummyClient(),
        model="test-model",
        num_variations=1,
        include_original=True,
        include_metadata=False,
    )

    rows = [json.loads(line) for line in output_jsonl.read_text(encoding="utf-8").splitlines()]
    assert row_count == 4
    assert len(rows) == 4
    assert all(set(row) == {"messages"} for row in rows)
    assert all([message["role"] for row in rows for message in row["messages"]])


def test_build_messages_jsonl_rejects_missing_input(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        builder.iter_markdown_files(tmp_path / "missing")
