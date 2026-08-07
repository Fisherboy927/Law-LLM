from __future__ import annotations

import json

import pytest

from law_llm import dataset_builder as builder
from scripts import build_training_dataset as cli


def make_record(number: int, example_type: str, **overrides):
    record = {
        "synthetic_id": f"answer_{number:02d}_{example_type}",
        "source_id": f"Answer_{number:02d}",
        "source_path": f"outputs/application_answers_markdown/Answer_{number:02d}.md",
        "example_type": example_type,
        "instruction": "Answer as a detailed high-quality model answer.",
        "input": "Why do you want to join this firm?",
        "output": f"Answer body {number} {example_type}",
        "question_was_paraphrased": False,
        "paraphrased_question": None,
        "generation_notes": "notes",
    }
    record.update(overrides)
    return record


def write_batch(directory, batch: str, records) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"synthetic_answers_{batch}_validated.jsonl"
    path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n",
        encoding="utf-8",
    )


def test_batch_name_from_path_strips_wrapper() -> None:
    assert builder.batch_name_from_path("a/synthetic_answers_41to50_validated.jsonl") == "41to50"
    assert builder.batch_name_from_path("a/other.jsonl") == "other"


def test_normalise_record_lowercases_source_id_and_fills_optionals() -> None:
    record = builder.normalise_record(
        make_record(1, "detailed_model_answer"), batch="first5", origin="test:1"
    )

    assert record["source_id"] == "answer_01"
    assert record["answer_number"] == 1
    assert record["batch"] == "first5"
    assert record["quality_score"] is None
    assert record["useful_for_lora_training"] is None


def test_normalise_record_rejects_blank_core_field() -> None:
    with pytest.raises(builder.DatasetBuildError, match="output"):
        builder.normalise_record(
            make_record(1, "detailed_model_answer", output="   "), batch="b", origin="test:1"
        )


def test_normalise_record_rejects_source_id_without_number() -> None:
    with pytest.raises(builder.DatasetBuildError, match="answer number"):
        builder.normalise_record(
            make_record(1, "detailed_model_answer", source_id="answer"), batch="b", origin="test:1"
        )


def test_load_validated_records_merges_and_sorts(tmp_path) -> None:
    write_batch(tmp_path, "first5", [make_record(2, "concise_strong_answer")])
    write_batch(tmp_path, "6to20", [make_record(1, "detailed_model_answer", quality_score=9)])

    records = builder.load_validated_records(builder.find_validated_files(tmp_path))

    assert [record["answer_number"] for record in records] == [1, 2]
    assert [record["batch"] for record in records] == ["6to20", "first5"]


def test_load_validated_records_rejects_duplicate_synthetic_id(tmp_path) -> None:
    write_batch(tmp_path, "first5", [make_record(1, "detailed_model_answer")])
    write_batch(tmp_path, "6to20", [make_record(1, "detailed_model_answer")])

    with pytest.raises(builder.DatasetBuildError, match="duplicate synthetic_id"):
        builder.load_validated_records(builder.find_validated_files(tmp_path))


def test_filter_records_applies_score_rules() -> None:
    scored = builder.normalise_record(
        make_record(1, "a", quality_score=7), batch="b", origin="o:1"
    )
    unscored = builder.normalise_record(make_record(2, "a"), batch="b", origin="o:2")
    good = builder.normalise_record(make_record(3, "a", quality_score=9), batch="b", origin="o:3")

    kept, dropped = builder.filter_records([scored, unscored, good], min_quality_score=8)
    assert [record["answer_number"] for record in kept] == [2, 3]
    assert dropped[0][1] == "quality_score_below_8"

    kept, dropped = builder.filter_records(
        [scored, unscored, good], min_quality_score=8, drop_missing_score=True
    )
    assert [record["answer_number"] for record in kept] == [3]
    assert {reason for _, reason in dropped} == {"quality_score_below_8", "missing_quality_score"}


def test_filter_records_rejects_empty_result() -> None:
    record = builder.normalise_record(make_record(1, "a", quality_score=5), batch="b", origin="o:1")
    with pytest.raises(builder.DatasetBuildError, match="filtered out"):
        builder.filter_records([record], min_quality_score=9)


def clean_record(number: int, example_type: str, **overrides):
    fields = {
        "quality_score": 9,
        "same_conclusion": True,
        "preserves_key_issues": True,
        "no_new_facts": True,
        "no_hallucinated_authorities": True,
        "not_too_similar_to_source": True,
        "useful_for_lora_training": True,
    }
    fields.update(overrides)
    return make_record(number, example_type, **fields)


def test_clean_filter_drops_sources_with_collapsed_instructions() -> None:
    records = [
        builder.normalise_record(
            clean_record(
                1,
                kind,
                instruction="Generic instruction",
                output=f"Distinct output {kind}",
            ),
            batch="b",
            origin=f"o:{kind}",
        )
        for kind in ("a", "b", "c")
    ]
    records.append(
        builder.normalise_record(
            clean_record(2, "a", instruction="Specific instruction"),
            batch="b",
            origin="o:good",
        )
    )

    kept, dropped = builder.filter_records(records, clean=True)

    assert [record["source_id"] for record in kept] == ["answer_02"]
    assert {reason for _, reason in dropped} == {"source_instruction_collapse"}


@pytest.mark.parametrize(
    ("input_text", "reason"),
    [
        ('{"question_text": "Why this firm?"}', "serialized_source_in_input"),
        ("Question: Why this firm?", "duplicated_question_label"),
        ("Why this firm?\nUse only these facts: facts", "embedded_facts_dump"),
    ],
)
def test_clean_filter_drops_malformed_inputs(input_text: str, reason: str) -> None:
    record = builder.normalise_record(
        clean_record(1, "a", input=input_text), batch="b", origin="o:1"
    )

    with pytest.raises(builder.DatasetBuildError, match="filtered out"):
        builder.filter_records([record], clean=True)

    record["input"] = "Why this firm?"
    good = builder.normalise_record(clean_record(2, "a"), batch="b", origin="o:2")
    kept, dropped = builder.filter_records([record, good], clean=True)
    assert [item["source_id"] for item in kept] == ["answer_01", "answer_02"]
    assert dropped == []

    malformed = builder.normalise_record(
        clean_record(3, "a", input=input_text), batch="b", origin="o:3"
    )
    kept, dropped = builder.filter_records([good, malformed], clean=True)
    assert kept == [good]
    assert dropped[0][1] == reason


def test_clean_filter_requires_validation_flags_and_score() -> None:
    missing_flag = builder.normalise_record(
        clean_record(1, "a", no_new_facts=None), batch="b", origin="o:1"
    )
    low_score = builder.normalise_record(
        clean_record(2, "a", quality_score=7), batch="b", origin="o:2"
    )
    good = builder.normalise_record(clean_record(3, "a"), batch="b", origin="o:3")

    kept, dropped = builder.filter_records(
        [missing_flag, low_score, good],
        clean=True,
        min_quality_score=8,
        drop_missing_score=True,
    )

    assert kept == [good]
    assert [reason for _, reason in dropped] == [
        "validation_not_passed:no_new_facts",
        "quality_score_below_8",
    ]


def test_split_by_source_keeps_variants_of_one_answer_together() -> None:
    records = [
        builder.normalise_record(make_record(number, kind), batch="b", origin=f"o:{number}")
        for number in range(1, 11)
        for kind in ("detailed_model_answer", "concise_strong_answer")
    ]

    train, validation = builder.split_by_source(records, val_fraction=0.2, seed=7)

    train_sources = {record["source_id"] for record in train}
    val_sources = {record["source_id"] for record in validation}
    assert len(val_sources) == 2
    assert not train_sources & val_sources
    assert len(train) + len(validation) == len(records)
    assert all(len(records) for records in (train, validation))


def test_split_by_source_is_deterministic() -> None:
    records = [
        builder.normalise_record(make_record(number, "a"), batch="b", origin=f"o:{number}")
        for number in range(1, 21)
    ]

    first = builder.split_by_source(records, val_fraction=0.1, seed=42)[1]
    second = builder.split_by_source(records, val_fraction=0.1, seed=42)[1]

    assert [record["synthetic_id"] for record in first] == [
        record["synthetic_id"] for record in second
    ]


def test_split_records_none_and_zero_fraction_skip_validation() -> None:
    records = [
        builder.normalise_record(make_record(number, "a"), batch="b", origin=f"o:{number}")
        for number in range(1, 6)
    ]

    assert builder.split_records(records, strategy="none")[1] == []
    assert builder.split_records(records, strategy="source", val_fraction=0.0)[1] == []
    assert builder.split_records(records, strategy="random", val_fraction=0.0)[1] == []


def test_split_records_rejects_unknown_strategy() -> None:
    with pytest.raises(builder.DatasetBuildError, match="Unknown split strategy"):
        builder.split_records([], strategy="stratified")


def test_to_messages_row_combines_instruction_and_question() -> None:
    record = builder.normalise_record(
        make_record(1, "detailed_model_answer", quality_score=9), batch="first5", origin="o:1"
    )

    row = builder.to_messages_row(record, system_prompt="System")

    assert [message["role"] for message in row["messages"]] == ["system", "user", "assistant"]
    assert row["messages"][1]["content"] == (
        "Answer as a detailed high-quality model answer.\n\n"
        "Question:\nWhy do you want to join this firm?"
    )
    assert row["messages"][2]["content"] == record["output"]
    assert row["metadata"]["quality_score"] == 9


def test_to_alpaca_row_can_omit_metadata() -> None:
    record = builder.normalise_record(make_record(1, "a"), batch="b", origin="o:1")

    row = builder.to_alpaca_row(record, include_metadata=False)

    assert set(row) == {"instruction", "input", "output"}


def test_to_row_rejects_unknown_format() -> None:
    record = builder.normalise_record(make_record(1, "a"), batch="b", origin="o:1")
    with pytest.raises(builder.DatasetBuildError, match="Unknown output format"):
        builder.to_row(record, output_format="sharegpt")


def test_summarise_reports_coverage() -> None:
    records = [
        builder.normalise_record(make_record(1, "a", quality_score=8), batch="b", origin="o:1"),
        builder.normalise_record(make_record(2, "b"), batch="c", origin="o:2"),
    ]

    stats = builder.summarise(records)

    assert stats["records"] == 2
    assert stats["sources"] == 2
    assert stats["by_batch"] == {"b": 1, "c": 1}
    assert stats["scored_records"] == 1
    assert stats["quality_score_mean"] == 8


def test_cli_writes_splits_and_reports(tmp_path) -> None:
    input_dir = tmp_path / "augmentation"
    output_dir = tmp_path / "training"
    write_batch(
        input_dir,
        "first5",
        [
            make_record(number, kind)
            for number in range(1, 6)
            for kind in ("detailed_model_answer", "concise_strong_answer")
        ],
    )
    write_batch(
        input_dir,
        "6to20",
        [
            make_record(number, kind, quality_score=9)
            for number in range(6, 16)
            for kind in ("detailed_model_answer", "concise_strong_answer")
        ],
    )

    exit_code = cli.main(
        [
            "--input-dir",
            str(input_dir),
            "--output-dir",
            str(output_dir),
            "--val-fraction",
            "0.2",
        ]
    )

    assert exit_code == 0
    train = [json.loads(line) for line in (output_dir / "train.jsonl").read_text("utf-8").splitlines()]
    validation = [
        json.loads(line) for line in (output_dir / "validation.jsonl").read_text("utf-8").splitlines()
    ]
    merged = [
        json.loads(line) for line in (output_dir / "merged_records.jsonl").read_text("utf-8").splitlines()
    ]

    assert len(train) + len(validation) == 30
    assert len(merged) == 30
    assert all(set(row) == {"messages", "metadata"} for row in train)
    train_sources = {row["metadata"]["source_id"] for row in train}
    val_sources = {row["metadata"]["source_id"] for row in validation}
    assert not train_sources & val_sources

    report = json.loads((output_dir / "dataset_report.json").read_text("utf-8"))
    assert report["loaded"] == 30
    assert report["written"]["train"] == len(train)
    assert "# Training Dataset Build Report" in (output_dir / "dataset_report.md").read_text("utf-8")


def test_cli_reports_error_for_missing_input(tmp_path, capsys) -> None:
    exit_code = cli.main(["--input-dir", str(tmp_path / "missing")])

    assert exit_code == 1
    assert "error:" in capsys.readouterr().err
