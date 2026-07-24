# First 5 Legal Answer Augmentation Pilot Review

## Summary

- Markdown files processed: 5
- Source records created: 5
- Synthetic examples generated: 50
- Accepted examples: 42
- Rejected examples: 8

## Source directory

Read-only source Markdown directory used for this pilot:

```text
outputs/application_answers_markdown
```

The files selected by filename sort order were:

- outputs/application_answers_markdown/Answer_01.md
- outputs/application_answers_markdown/Answer_02.md
- outputs/application_answers_markdown/Answer_03.md
- outputs/application_answers_markdown/Answer_04.md
- outputs/application_answers_markdown/Answer_05.md

## Files that could not be processed

- None.

## Rejection reasons grouped by type

- preserves_key_issues: 8

## Validation table

| source_id | example_type | quality_score | status |
|---|---|---:|---|
| Answer_01 | detailed_model_answer | 10 | accepted |
| Answer_01 | concise_strong_answer | 10 | accepted |
| Answer_01 | irac_structured_answer | 10 | accepted |
| Answer_01 | natural_student_style_answer | 9 | rejected |
| Answer_01 | formal_exam_style_answer | 10 | accepted |
| Answer_01 | application_heavy_answer | 9 | rejected |
| Answer_01 | principle_focused_answer | 10 | accepted |
| Answer_01 | alternative_ordering_answer | 10 | accepted |
| Answer_01 | paraphrased_question_model_answer | 10 | accepted |
| Answer_01 | outline_then_answer | 10 | accepted |
| Answer_02 | detailed_model_answer | 10 | accepted |
| Answer_02 | concise_strong_answer | 10 | accepted |
| Answer_02 | irac_structured_answer | 10 | accepted |
| Answer_02 | natural_student_style_answer | 10 | accepted |
| Answer_02 | formal_exam_style_answer | 10 | accepted |
| Answer_02 | application_heavy_answer | 9 | rejected |
| Answer_02 | principle_focused_answer | 10 | accepted |
| Answer_02 | alternative_ordering_answer | 9 | rejected |
| Answer_02 | paraphrased_question_model_answer | 10 | accepted |
| Answer_02 | outline_then_answer | 10 | accepted |
| Answer_03 | detailed_model_answer | 10 | accepted |
| Answer_03 | concise_strong_answer | 10 | accepted |
| Answer_03 | irac_structured_answer | 10 | accepted |
| Answer_03 | natural_student_style_answer | 10 | accepted |
| Answer_03 | formal_exam_style_answer | 10 | accepted |
| Answer_03 | application_heavy_answer | 10 | accepted |
| Answer_03 | principle_focused_answer | 9 | rejected |
| Answer_03 | alternative_ordering_answer | 10 | accepted |
| Answer_03 | paraphrased_question_model_answer | 10 | accepted |
| Answer_03 | outline_then_answer | 10 | accepted |
| Answer_04 | detailed_model_answer | 10 | accepted |
| Answer_04 | concise_strong_answer | 10 | accepted |
| Answer_04 | irac_structured_answer | 10 | accepted |
| Answer_04 | natural_student_style_answer | 10 | accepted |
| Answer_04 | formal_exam_style_answer | 10 | accepted |
| Answer_04 | application_heavy_answer | 9 | rejected |
| Answer_04 | principle_focused_answer | 10 | accepted |
| Answer_04 | alternative_ordering_answer | 10 | accepted |
| Answer_04 | paraphrased_question_model_answer | 10 | accepted |
| Answer_04 | outline_then_answer | 10 | accepted |
| Answer_05 | detailed_model_answer | 10 | accepted |
| Answer_05 | concise_strong_answer | 10 | accepted |
| Answer_05 | irac_structured_answer | 10 | accepted |
| Answer_05 | natural_student_style_answer | 9 | rejected |
| Answer_05 | formal_exam_style_answer | 10 | accepted |
| Answer_05 | application_heavy_answer | 10 | accepted |
| Answer_05 | principle_focused_answer | 9 | rejected |
| Answer_05 | alternative_ordering_answer | 10 | accepted |
| Answer_05 | paraphrased_question_model_answer | 10 | accepted |
| Answer_05 | outline_then_answer | 10 | accepted |

## Dataset quality concerns

- The first five files are law-firm application answers rather than substantive legal problem answers, so legal rules/principles are interpreted as application-answer evaluation principles.
- Several source answers contain OCR artefacts, placeholders, and redactions such as [redacted], [xxx], and [firm]; these were preserved rather than normalised.
- This pilot uses controlled synthetic drafting without external authority expansion. That is useful for schema and quality testing, but a larger run should include human spot checks for naturalness and firm-specific nuance.

## Recommendations before scaling

- Replace the prompt placeholder <MARKDOWN_DIRECTORY> with outputs/application_answers_markdown or expose it as a script argument before scaling.
- Keep the strict no-new-authorities rule and maintain a per-source allow-list of named organisations extracted from each answer.
- Run human spot checks on at least one accepted variant per source and every paraphrased-question variant before producing a larger dataset.
- Consider adding a reusable pilot script so source extraction, generation, validation, and reporting can be rerun without manual prompting.
