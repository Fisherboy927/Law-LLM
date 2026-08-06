# Augmentation Review: Answers 41–50

## Summary

- Markdown files processed: 10
- Source records created: 10
- Synthetic examples generated: 100
- Accepted examples: 100
- Rejected examples: 0
- Quality score range: 7–9
- Average quality score: 8.65
- Mean token Jaccard vs source: 0.358 (max 0.534)

## Source directory

Read-only source Markdown directory used for this batch:

```text
outputs/application_answers_markdown
```

Note: The prompt referenced `Application_Images`, but that directory holds page PNGs. Consistent with prior pilots (21–25, 26–40), this batch used the OCR-exported Markdown under `outputs/application_answers_markdown`.

The files selected by filename sort order (positions 41–50) were:

- `outputs/application_answers_markdown/Answer_41.md`
- `outputs/application_answers_markdown/Answer_42.md`
- `outputs/application_answers_markdown/Answer_43.md`
- `outputs/application_answers_markdown/Answer_44.md`
- `outputs/application_answers_markdown/Answer_45.md`
- `outputs/application_answers_markdown/Answer_46.md`
- `outputs/application_answers_markdown/Answer_47.md`
- `outputs/application_answers_markdown/Answer_48.md`
- `outputs/application_answers_markdown/Answer_49.md`
- `outputs/application_answers_markdown/Answer_50.md`

Original Markdown files were not modified.

## Output path note

The prompt template still named outputs `synthetic_answers_first5_*.jsonl` / `augmentation_first5_review.md`. This batch used `41to50` naming to match prior pilots and avoid overwriting earlier datasets.

## Files that could not be processed

- None.

## Files Processed

- `Answer_41.md` → `answer_41`
- `Answer_42.md` → `answer_42`
- `Answer_43.md` → `answer_43`
- `Answer_44.md` → `answer_44`
- `Answer_45.md` → `answer_45`
- `Answer_46.md` → `answer_46`
- `Answer_47.md` → `answer_47`
- `Answer_48.md` → `answer_48`
- `Answer_49.md` → `answer_49`
- `Answer_50.md` → `answer_50`

## Rejection Reasons

- None. All generated examples passed worker validation and parent-level fidelity checks (issue anchors, placeholder preservation where applicable, authority allow-list extras, Jaccard similarity ≤ 0.72).

## Source-Level Counts

| source_id | raw | accepted | rejected |
|---|---:|---:|---:|
| answer_41 | 10 | 10 | 0 |
| answer_42 | 10 | 10 | 0 |
| answer_43 | 10 | 10 | 0 |
| answer_44 | 10 | 10 | 0 |
| answer_45 | 10 | 10 | 0 |
| answer_46 | 10 | 10 | 0 |
| answer_47 | 10 | 10 | 0 |
| answer_48 | 10 | 10 | 0 |
| answer_49 | 10 | 10 | 0 |
| answer_50 | 10 | 10 | 0 |

## Per-Example Review Table

| source_id | example_type | quality_score | status | similarity_jaccard |
|---|---|---:|---|---:|
| answer_41 | detailed_model_answer | 9 | accepted | 0.426 |
| answer_41 | concise_strong_answer | 9 | accepted | 0.422 |
| answer_41 | irac_structured_answer | 8 | accepted | 0.392 |
| answer_41 | natural_student_style_answer | 9 | accepted | 0.396 |
| answer_41 | formal_exam_style_answer | 9 | accepted | 0.5 |
| answer_41 | application_heavy_answer | 9 | accepted | 0.361 |
| answer_41 | principle_focused_answer | 8 | accepted | 0.419 |
| answer_41 | alternative_ordering_answer | 9 | accepted | 0.424 |
| answer_41 | paraphrased_question_model_answer | 9 | accepted | 0.444 |
| answer_41 | outline_then_answer | 8 | accepted | 0.394 |
| answer_42 | detailed_model_answer | 9 | accepted | 0.429 |
| answer_42 | concise_strong_answer | 9 | accepted | 0.323 |
| answer_42 | irac_structured_answer | 8 | accepted | 0.371 |
| answer_42 | natural_student_style_answer | 9 | accepted | 0.378 |
| answer_42 | formal_exam_style_answer | 9 | accepted | 0.418 |
| answer_42 | application_heavy_answer | 9 | accepted | 0.326 |
| answer_42 | principle_focused_answer | 8 | accepted | 0.306 |
| answer_42 | alternative_ordering_answer | 9 | accepted | 0.353 |
| answer_42 | paraphrased_question_model_answer | 9 | accepted | 0.338 |
| answer_42 | outline_then_answer | 8 | accepted | 0.32 |
| answer_43 | detailed_model_answer | 9 | accepted | 0.404 |
| answer_43 | concise_strong_answer | 9 | accepted | 0.404 |
| answer_43 | irac_structured_answer | 8 | accepted | 0.363 |
| answer_43 | natural_student_style_answer | 9 | accepted | 0.382 |
| answer_43 | formal_exam_style_answer | 9 | accepted | 0.476 |
| answer_43 | application_heavy_answer | 9 | accepted | 0.36 |
| answer_43 | principle_focused_answer | 9 | accepted | 0.343 |
| answer_43 | alternative_ordering_answer | 9 | accepted | 0.423 |
| answer_43 | paraphrased_question_model_answer | 9 | accepted | 0.342 |
| answer_43 | outline_then_answer | 8 | accepted | 0.379 |
| answer_44 | detailed_model_answer | 9 | accepted | 0.381 |
| answer_44 | concise_strong_answer | 9 | accepted | 0.374 |
| answer_44 | irac_structured_answer | 8 | accepted | 0.32 |
| answer_44 | natural_student_style_answer | 9 | accepted | 0.323 |
| answer_44 | formal_exam_style_answer | 9 | accepted | 0.269 |
| answer_44 | application_heavy_answer | 9 | accepted | 0.298 |
| answer_44 | principle_focused_answer | 9 | accepted | 0.282 |
| answer_44 | alternative_ordering_answer | 9 | accepted | 0.428 |
| answer_44 | paraphrased_question_model_answer | 9 | accepted | 0.343 |
| answer_44 | outline_then_answer | 8 | accepted | 0.348 |
| answer_45 | detailed_model_answer | 9 | accepted | 0.334 |
| answer_45 | concise_strong_answer | 7 | accepted | 0.254 |
| answer_45 | irac_structured_answer | 7 | accepted | 0.279 |
| answer_45 | natural_student_style_answer | 9 | accepted | 0.266 |
| answer_45 | formal_exam_style_answer | 9 | accepted | 0.399 |
| answer_45 | application_heavy_answer | 9 | accepted | 0.255 |
| answer_45 | principle_focused_answer | 9 | accepted | 0.267 |
| answer_45 | alternative_ordering_answer | 9 | accepted | 0.319 |
| answer_45 | paraphrased_question_model_answer | 7 | accepted | 0.271 |
| answer_45 | outline_then_answer | 7 | accepted | 0.247 |
| answer_46 | detailed_model_answer | 9 | accepted | 0.416 |
| answer_46 | concise_strong_answer | 7 | accepted | 0.386 |
| answer_46 | irac_structured_answer | 9 | accepted | 0.317 |
| answer_46 | natural_student_style_answer | 9 | accepted | 0.252 |
| answer_46 | formal_exam_style_answer | 9 | accepted | 0.434 |
| answer_46 | application_heavy_answer | 9 | accepted | 0.263 |
| answer_46 | principle_focused_answer | 9 | accepted | 0.295 |
| answer_46 | alternative_ordering_answer | 9 | accepted | 0.352 |
| answer_46 | paraphrased_question_model_answer | 7 | accepted | 0.378 |
| answer_46 | outline_then_answer | 9 | accepted | 0.327 |
| answer_47 | detailed_model_answer | 9 | accepted | 0.325 |
| answer_47 | concise_strong_answer | 9 | accepted | 0.419 |
| answer_47 | irac_structured_answer | 8 | accepted | 0.37 |
| answer_47 | natural_student_style_answer | 9 | accepted | 0.3 |
| answer_47 | formal_exam_style_answer | 9 | accepted | 0.34 |
| answer_47 | application_heavy_answer | 9 | accepted | 0.315 |
| answer_47 | principle_focused_answer | 8 | accepted | 0.27 |
| answer_47 | alternative_ordering_answer | 9 | accepted | 0.398 |
| answer_47 | paraphrased_question_model_answer | 9 | accepted | 0.36 |
| answer_47 | outline_then_answer | 8 | accepted | 0.383 |
| answer_48 | detailed_model_answer | 9 | accepted | 0.401 |
| answer_48 | concise_strong_answer | 9 | accepted | 0.317 |
| answer_48 | irac_structured_answer | 8 | accepted | 0.313 |
| answer_48 | natural_student_style_answer | 9 | accepted | 0.337 |
| answer_48 | formal_exam_style_answer | 9 | accepted | 0.335 |
| answer_48 | application_heavy_answer | 9 | accepted | 0.26 |
| answer_48 | principle_focused_answer | 8 | accepted | 0.265 |
| answer_48 | alternative_ordering_answer | 9 | accepted | 0.442 |
| answer_48 | paraphrased_question_model_answer | 9 | accepted | 0.313 |
| answer_48 | outline_then_answer | 8 | accepted | 0.287 |
| answer_49 | detailed_model_answer | 9 | accepted | 0.355 |
| answer_49 | concise_strong_answer | 9 | accepted | 0.391 |
| answer_49 | irac_structured_answer | 8 | accepted | 0.338 |
| answer_49 | natural_student_style_answer | 9 | accepted | 0.379 |
| answer_49 | formal_exam_style_answer | 9 | accepted | 0.39 |
| answer_49 | application_heavy_answer | 9 | accepted | 0.307 |
| answer_49 | principle_focused_answer | 8 | accepted | 0.327 |
| answer_49 | alternative_ordering_answer | 9 | accepted | 0.392 |
| answer_49 | paraphrased_question_model_answer | 9 | accepted | 0.395 |
| answer_49 | outline_then_answer | 8 | accepted | 0.346 |
| answer_50 | detailed_model_answer | 9 | accepted | 0.471 |
| answer_50 | concise_strong_answer | 9 | accepted | 0.388 |
| answer_50 | irac_structured_answer | 8 | accepted | 0.35 |
| answer_50 | natural_student_style_answer | 9 | accepted | 0.41 |
| answer_50 | formal_exam_style_answer | 8 | accepted | 0.534 |
| answer_50 | application_heavy_answer | 9 | accepted | 0.353 |
| answer_50 | principle_focused_answer | 8 | accepted | 0.344 |
| answer_50 | alternative_ordering_answer | 9 | accepted | 0.47 |
| answer_50 | paraphrased_question_model_answer | 9 | accepted | 0.446 |
| answer_50 | outline_then_answer | 8 | accepted | 0.371 |


## Dataset Quality Concerns

- Application/competency answers (not doctrinal IRAC exams): IRAC variants are adapted Issue/Rule/Application/Conclusion scaffolds; still useful for style diversity but slightly less natural than for problem questions.
- Several sources rely on `[redacted]` placeholders (answers 43, 45, 50). Synthetics preserve them; training pipelines should treat placeholders as intentional.
- Answer 42 OCR has `C+` for Unity’s language; synthetics kept source wording rather than inventing corrections.
- Prompt copy-paste still points at `first5` output filenames; recommend fixing future prompt templates before scaling.

## Recommendations Before Scaling Beyond This Batch

1. Fix prompt output paths to the batch range (e.g. `41to50`) instead of leftover `first5` names.
2. Point prompts at `outputs/application_answers_markdown` (or auto-resolve PNG→MD) to avoid ambiguity with `Application_Images`.
3. Keep parent-level anchor + Jaccard checks; they caught nothing this batch but remain valuable.
4. Consider a shared schema/validator script rather than per-batch merge scripts as coverage grows past 50.
5. Monitor redacted-heavy answers separately so LoRA training does not learn to invent filled names.

## Artifacts

- `data/augmentation/source_answers_41to50.jsonl`
- `data/augmentation/synthetic_answers_41to50_raw.jsonl`
- `data/augmentation/synthetic_answers_41to50_validated.jsonl`
- `data/augmentation/synthetic_answers_41to50_rejected.jsonl` (empty)
- `data/augmentation/per_answer/answer_{41..50}_{raw,validation}.jsonl`
- `data/augmentation/per_answer/_merge_41to50.ps1`