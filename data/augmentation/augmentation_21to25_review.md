# Augmentation Review: Answers 21–25

## Summary

- Markdown files processed: 5
- Source records created: 5
- Synthetic examples generated: 50
- Accepted examples: 50
- Rejected examples: 0
- Quality score range: 8–9
- Average quality score: 8.70
- Mean token Jaccard vs source: 0.344 (max 0.471)

## Source directory

Read-only source Markdown directory used for this batch:

```text
outputs/application_answers_markdown
```

The files selected by filename sort order (positions 21–25) were:

- `outputs/application_answers_markdown/Answer_21.md`
- `outputs/application_answers_markdown/Answer_22.md`
- `outputs/application_answers_markdown/Answer_23.md`
- `outputs/application_answers_markdown/Answer_24.md`
- `outputs/application_answers_markdown/Answer_25.md`

Original Markdown files were not modified.

## Files that could not be processed

- None.

## Files Processed

- `Answer_21.md` → `answer_21`
- `Answer_22.md` → `answer_22`
- `Answer_23.md` → `answer_23`
- `Answer_24.md` → `answer_24`
- `Answer_25.md` → `answer_25`

## Rejection Reasons

- None. All generated examples passed worker validation and parent-level fidelity checks.

Note: a parent automated check briefly flagged `answer_24__detailed_model_answer` for omitting the exact phrase “personal brand”; that was a false positive (the output used “distinctive professional identity” / reputation / profile for the same remote-working challenge). It was accepted after review.

## Source-Level Counts

| source_id | raw | accepted | rejected |
|---|---:|---:|---:|
| answer_21 | 10 | 10 | 0 |
| answer_22 | 10 | 10 | 0 |
| answer_23 | 10 | 10 | 0 |
| answer_24 | 10 | 10 | 0 |
| answer_25 | 10 | 10 | 0 |

## Example-Level Validation Table

| source_id | example_type | quality_score | status |
|---|---|---:|---|
| answer_21 | detailed_model_answer | 9 | accepted |
| answer_21 | concise_strong_answer | 9 | accepted |
| answer_21 | irac_structured_answer | 9 | accepted |
| answer_21 | natural_student_style_answer | 8 | accepted |
| answer_21 | formal_exam_style_answer | 9 | accepted |
| answer_21 | application_heavy_answer | 9 | accepted |
| answer_21 | principle_focused_answer | 8 | accepted |
| answer_21 | alternative_ordering_answer | 9 | accepted |
| answer_21 | paraphrased_question_model_answer | 9 | accepted |
| answer_21 | outline_then_answer | 9 | accepted |
| answer_22 | detailed_model_answer | 9 | accepted |
| answer_22 | concise_strong_answer | 8 | accepted |
| answer_22 | irac_structured_answer | 9 | accepted |
| answer_22 | natural_student_style_answer | 9 | accepted |
| answer_22 | formal_exam_style_answer | 9 | accepted |
| answer_22 | application_heavy_answer | 9 | accepted |
| answer_22 | principle_focused_answer | 8 | accepted |
| answer_22 | alternative_ordering_answer | 9 | accepted |
| answer_22 | paraphrased_question_model_answer | 9 | accepted |
| answer_22 | outline_then_answer | 9 | accepted |
| answer_23 | detailed_model_answer | 9 | accepted |
| answer_23 | concise_strong_answer | 9 | accepted |
| answer_23 | irac_structured_answer | 8 | accepted |
| answer_23 | natural_student_style_answer | 9 | accepted |
| answer_23 | formal_exam_style_answer | 8 | accepted |
| answer_23 | application_heavy_answer | 9 | accepted |
| answer_23 | principle_focused_answer | 8 | accepted |
| answer_23 | alternative_ordering_answer | 9 | accepted |
| answer_23 | paraphrased_question_model_answer | 9 | accepted |
| answer_23 | outline_then_answer | 9 | accepted |
| answer_24 | detailed_model_answer | 9 | accepted |
| answer_24 | concise_strong_answer | 9 | accepted |
| answer_24 | irac_structured_answer | 8 | accepted |
| answer_24 | natural_student_style_answer | 9 | accepted |
| answer_24 | formal_exam_style_answer | 8 | accepted |
| answer_24 | application_heavy_answer | 9 | accepted |
| answer_24 | principle_focused_answer | 8 | accepted |
| answer_24 | alternative_ordering_answer | 9 | accepted |
| answer_24 | paraphrased_question_model_answer | 9 | accepted |
| answer_24 | outline_then_answer | 8 | accepted |
| answer_25 | detailed_model_answer | 9 | accepted |
| answer_25 | concise_strong_answer | 9 | accepted |
| answer_25 | irac_structured_answer | 8 | accepted |
| answer_25 | natural_student_style_answer | 9 | accepted |
| answer_25 | formal_exam_style_answer | 9 | accepted |
| answer_25 | application_heavy_answer | 8 | accepted |
| answer_25 | principle_focused_answer | 8 | accepted |
| answer_25 | alternative_ordering_answer | 9 | accepted |
| answer_25 | paraphrased_question_model_answer | 9 | accepted |
| answer_25 | outline_then_answer | 8 | accepted |

## Dataset Quality Concerns

- These sources are law-firm **application** answers (DLA Piper / Fieldfisher motivations and training-programme challenges), not doctrinal IRAC problem questions. Keep them in a task-specific LoRA split rather than mixing blindly with black-letter law data.
- IRAC / principle / formal-exam variants are adapted application-style structures (issue framing + evaluation criteria + application of experience), not statute/case analysis.
- Answer 25 is character-limited (~800 characters); variants are intentionally compact and less expansive than Answers 21–24.
- Answer 22’s OCR answer body does not name a firm; synthetics correctly avoid inventing one.
- Validation is model-assisted plus light parent checks (issue anchors, authority allow-lists, similarity). Human spot checks are still needed before training use.

## Recommendations Before Scaling

- Keep range-specific output names (`21to25`) rather than the prompt template’s stale `first5` paths.
- Human-review at least one accepted variant per source and every `paraphrased_question_model_answer` before LoRA training.
- Prefer exact-phrase-agnostic issue checks (semantic anchors) over literal keyword gates to avoid false rejects on good paraphrases.
- Add a small schema checker / merge script in-repo so future batches do not depend on ad hoc assembly.
- Continue retaining `per_answer/` intermediates for audit even when the merged rejected file is empty.

## Output Artifacts

- `data/augmentation/source_answers_21to25.jsonl` (5 records)
- `data/augmentation/synthetic_answers_21to25_raw.jsonl` (50 records)
- `data/augmentation/synthetic_answers_21to25_validated.jsonl` (50 records)
- `data/augmentation/synthetic_answers_21to25_rejected.jsonl` (0 records)
- `data/augmentation/augmentation_21to25_review.md`
- Per-answer intermediates under `data/augmentation/per_answer/`

## Notes on Processing

- Selected files were sorted by filename; positions 21–25 correspond to `Answer_21.md`–`Answer_25.md`.
- Per-answer workers produced isolated raw/validation JSONL files; this review merges those into the canonical `21to25` artifacts.
- Prompt path placeholders saying `first5` were treated as template leftovers and remapped to `21to25`, consistent with the `6to20` batch convention.
