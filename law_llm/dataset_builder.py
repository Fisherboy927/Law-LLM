"""Merge validated augmentation batches into a training-ready dataset."""

from __future__ import annotations

import json
import random
import re
import statistics
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Sequence

DEFAULT_VALIDATED_GLOB = "synthetic_answers_*_validated.jsonl"
DEFAULT_TRAINING_SYSTEM_PROMPT = (
    "You are a legal application writing assistant. Produce clear, specific, "
    "professional law firm application answers while preserving the applicant's facts."
)

CORE_FIELDS = (
    "synthetic_id",
    "source_id",
    "source_path",
    "example_type",
    "instruction",
    "input",
    "output",
)
OPTIONAL_FIELDS = (
    "question_was_paraphrased",
    "paraphrased_question",
    "generation_notes",
    "same_conclusion",
    "preserves_key_issues",
    "no_new_facts",
    "no_hallucinated_authorities",
    "not_too_similar_to_source",
    "useful_for_lora_training",
    "quality_score",
    "rejection_reason",
)
METADATA_FIELDS = (
    "synthetic_id",
    "source_id",
    "example_type",
    "batch",
    "quality_score",
    "source_path",
)
OUTPUT_FORMATS = ("messages", "alpaca")
SPLIT_STRATEGIES = ("source", "random", "none")

_ANSWER_NUMBER = re.compile(r"(\d+)")
_BATCH_NAME = re.compile(r"synthetic_answers_(.+)_validated")


class DatasetBuildError(RuntimeError):
    """Raised when validated augmentation records cannot be merged."""


def batch_name_from_path(path: str | Path) -> str:
    stem = Path(path).stem
    match = _BATCH_NAME.fullmatch(stem)
    return match.group(1) if match else stem


def normalise_record(record: Any, *, batch: str, origin: str) -> dict[str, Any]:
    """Bring one validated record onto the canonical schema shared by every batch."""
    if not isinstance(record, dict):
        raise DatasetBuildError(f"{origin}: expected a JSON object, got {type(record).__name__}.")

    missing = [field for field in CORE_FIELDS if not str(record.get(field) or "").strip()]
    if missing:
        raise DatasetBuildError(f"{origin}: missing or blank required fields {missing}.")

    source_id = str(record["source_id"]).strip().lower()
    number_match = _ANSWER_NUMBER.search(source_id)
    if number_match is None:
        raise DatasetBuildError(f"{origin}: source_id {source_id!r} has no answer number.")

    normalised: dict[str, Any] = {field: str(record[field]).strip() for field in CORE_FIELDS}
    normalised["source_id"] = source_id
    normalised["answer_number"] = int(number_match.group(1))
    normalised["batch"] = batch
    for field in OPTIONAL_FIELDS:
        normalised[field] = record.get(field)
    return normalised


def sort_key(record: dict[str, Any]) -> tuple[int, str, str]:
    return record["answer_number"], record["example_type"], record["synthetic_id"]


def find_validated_files(
    input_dir: str | Path, pattern: str = DEFAULT_VALIDATED_GLOB
) -> list[Path]:
    folder = Path(input_dir)
    if not folder.is_dir():
        raise DatasetBuildError(f"Augmentation directory not found: {folder}")
    files = sorted(path for path in folder.glob(pattern) if path.is_file())
    if not files:
        raise DatasetBuildError(f"No files matching {pattern!r} in {folder}")
    return files


def load_validated_records(paths: Iterable[str | Path]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen_ids: dict[str, str] = {}

    for path in paths:
        file_path = Path(path)
        batch = batch_name_from_path(file_path)
        lines = file_path.read_text(encoding="utf-8").splitlines()
        for line_number, line in enumerate(lines, start=1):
            line = line.strip()
            if not line:
                continue
            origin = f"{file_path.name}:{line_number}"
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                raise DatasetBuildError(f"{origin}: invalid JSON.") from exc

            record = normalise_record(raw, batch=batch, origin=origin)
            synthetic_id = record["synthetic_id"]
            if synthetic_id in seen_ids:
                raise DatasetBuildError(
                    f"{origin}: duplicate synthetic_id {synthetic_id!r}, "
                    f"already defined in {seen_ids[synthetic_id]}."
                )
            seen_ids[synthetic_id] = origin
            records.append(record)

    if not records:
        raise DatasetBuildError("No validated records were loaded.")
    records.sort(key=sort_key)
    return records


def filter_records(
    records: Sequence[dict[str, Any]],
    *,
    min_quality_score: int | None = None,
    drop_missing_score: bool = False,
) -> tuple[list[dict[str, Any]], list[tuple[dict[str, Any], str]]]:
    """Split records into kept and dropped, using the batch-inconsistent quality_score field."""
    kept: list[dict[str, Any]] = []
    dropped: list[tuple[dict[str, Any], str]] = []

    for record in records:
        score = record.get("quality_score")
        if score is None:
            if drop_missing_score:
                dropped.append((record, "missing_quality_score"))
                continue
        elif min_quality_score is not None and score < min_quality_score:
            dropped.append((record, f"quality_score_below_{min_quality_score}"))
            continue
        kept.append(record)

    if not kept:
        raise DatasetBuildError("Every record was filtered out; relax the quality filters.")
    return kept, dropped


def _validation_size(total: int, val_fraction: float) -> int:
    if not 0.0 <= val_fraction < 1.0:
        raise DatasetBuildError("val_fraction must be in [0.0, 1.0).")
    if val_fraction == 0.0:
        return 0
    return min(max(1, round(total * val_fraction)), total - 1)


def split_by_source(
    records: Sequence[dict[str, Any]], *, val_fraction: float, seed: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Hold out whole source answers so near-duplicate variants cannot leak across the split."""
    sources = sorted({record["source_id"] for record in records})
    if len(sources) < 2:
        raise DatasetBuildError("Source-level splitting needs at least two source answers.")

    val_count = _validation_size(len(sources), val_fraction)
    if val_count == 0:
        return list(records), []

    val_sources = set(random.Random(seed).sample(sources, val_count))
    train = [record for record in records if record["source_id"] not in val_sources]
    validation = [record for record in records if record["source_id"] in val_sources]
    return train, validation


def split_random(
    records: Sequence[dict[str, Any]], *, val_fraction: float, seed: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ordered = sorted(records, key=lambda record: record["synthetic_id"])
    val_count = _validation_size(len(ordered), val_fraction)
    if val_count == 0:
        return list(records), []

    random.Random(seed).shuffle(ordered)
    validation = sorted(ordered[:val_count], key=sort_key)
    train = sorted(ordered[val_count:], key=sort_key)
    return train, validation


def split_records(
    records: Sequence[dict[str, Any]],
    *,
    strategy: str = "source",
    val_fraction: float = 0.1,
    seed: int = 20260807,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if strategy not in SPLIT_STRATEGIES:
        raise DatasetBuildError(f"Unknown split strategy {strategy!r}; expected {SPLIT_STRATEGIES}.")
    if strategy == "none":
        return list(records), []
    if strategy == "random":
        return split_random(records, val_fraction=val_fraction, seed=seed)
    return split_by_source(records, val_fraction=val_fraction, seed=seed)


def build_user_prompt(record: dict[str, Any]) -> str:
    return f"{record['instruction']}\n\nQuestion:\n{record['input']}"


def _metadata(record: dict[str, Any]) -> dict[str, Any]:
    return {field: record.get(field) for field in METADATA_FIELDS}


def to_messages_row(
    record: dict[str, Any],
    *,
    system_prompt: str = DEFAULT_TRAINING_SYSTEM_PROMPT,
    include_metadata: bool = True,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": build_user_prompt(record)},
            {"role": "assistant", "content": record["output"]},
        ]
    }
    if include_metadata:
        row["metadata"] = _metadata(record)
    return row


def to_alpaca_row(record: dict[str, Any], *, include_metadata: bool = True) -> dict[str, Any]:
    row: dict[str, Any] = {
        "instruction": record["instruction"],
        "input": record["input"],
        "output": record["output"],
    }
    if include_metadata:
        row["metadata"] = _metadata(record)
    return row


def to_row(
    record: dict[str, Any],
    *,
    output_format: str = "messages",
    system_prompt: str = DEFAULT_TRAINING_SYSTEM_PROMPT,
    include_metadata: bool = True,
) -> dict[str, Any]:
    if output_format == "messages":
        return to_messages_row(
            record, system_prompt=system_prompt, include_metadata=include_metadata
        )
    if output_format == "alpaca":
        return to_alpaca_row(record, include_metadata=include_metadata)
    raise DatasetBuildError(f"Unknown output format {output_format!r}; expected {OUTPUT_FORMATS}.")


def write_jsonl(path: str | Path, rows: Iterable[dict[str, Any]]) -> int:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            count += 1
    return count


def summarise(records: Sequence[dict[str, Any]]) -> dict[str, Any]:
    lengths = [len(record["output"]) for record in records]
    scores = [
        record["quality_score"] for record in records if record.get("quality_score") is not None
    ]
    return {
        "records": len(records),
        "sources": len({record["source_id"] for record in records}),
        "answer_numbers": sorted({record["answer_number"] for record in records}),
        "by_batch": dict(sorted(Counter(record["batch"] for record in records).items())),
        "by_example_type": dict(
            sorted(Counter(record["example_type"] for record in records).items())
        ),
        "paraphrased": sum(1 for record in records if record.get("question_was_paraphrased")),
        "scored_records": len(scores),
        "quality_score_min": min(scores) if scores else None,
        "quality_score_max": max(scores) if scores else None,
        "quality_score_mean": round(statistics.mean(scores), 3) if scores else None,
        "output_chars_total": sum(lengths),
        "output_chars_min": min(lengths),
        "output_chars_median": int(statistics.median(lengths)),
        "output_chars_max": max(lengths),
    }
