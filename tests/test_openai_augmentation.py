from __future__ import annotations

from types import SimpleNamespace

import pytest

from law_llm.openai_augmentation import (
    OpenAIAugmentationError,
    build_messages_record,
    generate_variations,
    parse_variations,
)


def test_parse_variations_accepts_json_list() -> None:
    assert parse_variations('{"variations": ["one", "two"]}') == ["one", "two"]


def test_parse_variations_rejects_non_json() -> None:
    with pytest.raises(OpenAIAugmentationError, match="not valid JSON"):
        parse_variations("1. one\n2. two")


def test_parse_variations_rejects_empty_list() -> None:
    with pytest.raises(OpenAIAugmentationError, match="no non-empty variations"):
        parse_variations('{"variations": [""]}')


def test_build_messages_record_has_openai_messages_shape() -> None:
    row = build_messages_record(
        answer_id="Answer_01",
        assistant_content="Polished answer",
        metadata={"answer_id": "Answer_01", "source": "original"},
    )

    assert [message["role"] for message in row["messages"]] == [
        "system",
        "user",
        "assistant",
    ]
    assert row["messages"][1]["content"] == "Write a polished law firm application answer for Answer_01."
    assert row["messages"][2]["content"] == "Polished answer"
    assert row["metadata"] == {"answer_id": "Answer_01", "source": "original"}


def test_build_messages_record_can_omit_metadata() -> None:
    row = build_messages_record(answer_id="Answer_01", assistant_content="Text")

    assert set(row) == {"messages"}


class FakeCompletions:
    def __init__(self) -> None:
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content='{"variations": ["variation"]}')
                )
            ]
        )


class FakeClient:
    def __init__(self) -> None:
        self.completions = FakeCompletions()
        self.chat = SimpleNamespace(completions=self.completions)


def test_generate_variations_calls_openai_and_parses_response() -> None:
    client = FakeClient()

    variations = generate_variations(
        client,
        answer_id="Answer_01",
        markdown_text="# Answer 01\n\nText",
        num_variations=1,
        model="test-model",
    )

    assert variations == ["variation"]
    assert client.completions.kwargs["model"] == "test-model"
    assert client.completions.kwargs["messages"][0]["role"] == "system"
