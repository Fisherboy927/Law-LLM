from __future__ import annotations

import json
import os
from typing import Any

DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_SYSTEM_PROMPT = (
    "You are a legal application writing assistant. Produce clear, specific, "
    "professional application answers while preserving the applicant's facts."
)
DEFAULT_USER_PROMPT_TEMPLATE = "Write a polished law firm application answer for {answer_id}."


class OpenAIAugmentationError(RuntimeError):
    """Raised when OpenAI data augmentation cannot produce usable variations."""


def get_required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise OpenAIAugmentationError(f"Environment variable {name} is required.")
    return value


def get_openai_model(default: str = DEFAULT_OPENAI_MODEL) -> str:
    return os.environ.get("OPENAI_MODEL", default)


def _message_content(response: Any) -> str:
    try:
        content = response.choices[0].message.content
    except (AttributeError, IndexError, TypeError) as exc:
        raise OpenAIAugmentationError("OpenAI response did not include message content.") from exc
    if not content or not content.strip():
        raise OpenAIAugmentationError("OpenAI response content was empty.")
    return content.strip()


def parse_variations(text: str) -> list[str]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise OpenAIAugmentationError(
            "OpenAI response was not valid JSON. Expected: {\"variations\": [\"...\"]}."
        ) from exc

    variations = payload.get("variations") if isinstance(payload, dict) else None
    if not isinstance(variations, list):
        raise OpenAIAugmentationError(
            "OpenAI response JSON must contain a 'variations' list."
        )

    cleaned = [str(item).strip() for item in variations if str(item).strip()]
    if not cleaned:
        raise OpenAIAugmentationError("OpenAI response contained no non-empty variations.")
    return cleaned


def build_variation_prompt(answer_id: str, markdown_text: str, num_variations: int) -> str:
    return f"""Create {num_variations} rewritten training variations from this law-firm application answer.

Rules:
- Preserve the applicant's facts, chronology, legal context, and achievements.
- Do not invent new employers, schools, grades, cases, deals, awards, identities, or experiences.
- Improve clarity, structure, specificity, and professional tone.
- Each variation should be a complete answer, not notes.
- Return JSON only in this exact shape: {{"variations": ["answer 1", "answer 2"]}}

Answer ID: {answer_id}

Source Markdown:
{markdown_text}
"""


def generate_variations(
    client: Any,
    *,
    answer_id: str,
    markdown_text: str,
    num_variations: int,
    model: str = DEFAULT_OPENAI_MODEL,
) -> list[str]:
    if num_variations < 1:
        return []

    prompt = build_variation_prompt(answer_id, markdown_text, num_variations)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You generate faithful, JSON-only legal application answer rewrites.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.8,
    )
    return parse_variations(_message_content(response))


def build_messages_record(
    *,
    answer_id: str,
    assistant_content: str,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    user_prompt_template: str = DEFAULT_USER_PROMPT_TEMPLATE,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    assistant_text = assistant_content.strip()
    if not assistant_text:
        raise ValueError(f"Assistant content for {answer_id} is empty.")

    record: dict[str, Any] = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": user_prompt_template.format(answer_id=answer_id),
            },
            {"role": "assistant", "content": assistant_text},
        ]
    }
    if metadata is not None:
        record["metadata"] = metadata
    return record
