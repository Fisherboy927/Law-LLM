# Training Dataset Build Report

## Configuration

- Input directory: `D:\Projects\Law-LLM\data\augmentation`
- Batch files: `synthetic_answers_21to25_validated.jsonl`, `synthetic_answers_26to40_validated.jsonl`, `synthetic_answers_41to50_validated.jsonl`, `synthetic_answers_6to20_validated.jsonl`, `synthetic_answers_first5_validated.jsonl`
- Output format: `messages`
- Split strategy: `source` (val_fraction 0.1, seed 20260807)
- Quality filter: min_quality_score=8, drop_missing_score=True
- Strict cleaning: True (min_instruction_diversity 0.5)
- Metadata field: included

## Overall

- Records loaded: 492
- Records dropped by filters: 96
- Records kept: 396
- Source answers covered: 41

| batch | count |
|---|---:|
| `21to25` | 50 |
| `26to40` | 150 |
| `41to50` | 94 |
| `6to20` | 60 |
| `first5` | 42 |

| example_type | count |
|---|---:|
| `alternative_ordering_answer` | 40 |
| `application_heavy_answer` | 38 |
| `concise_strong_answer` | 39 |
| `detailed_model_answer` | 41 |
| `formal_exam_style_answer` | 41 |
| `irac_structured_answer` | 40 |
| `natural_student_style_answer` | 39 |
| `outline_then_answer` | 40 |
| `paraphrased_question_model_answer` | 39 |
| `principle_focused_answer` | 39 |

## Train split

- Rows: 357
- Source answers: 37 (1, 2, 4, 5, 11, 12, 14, 16, 18, 19, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 32, 34, 35, 36, 37, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50)
- Paraphrased-question rows: 35
- Scored rows: 357 (min 8, max 10, mean 8.846)
- Answer characters: 489482 total, 453/1273/3958 min/median/max

| batch | count |
|---|---:|
| `21to25` | 50 |
| `26to40` | 120 |
| `41to50` | 94 |
| `6to20` | 60 |
| `first5` | 33 |

| example_type | count |
|---|---:|
| `alternative_ordering_answer` | 36 |
| `application_heavy_answer` | 34 |
| `concise_strong_answer` | 35 |
| `detailed_model_answer` | 37 |
| `formal_exam_style_answer` | 37 |
| `irac_structured_answer` | 36 |
| `natural_student_style_answer` | 35 |
| `outline_then_answer` | 36 |
| `paraphrased_question_model_answer` | 35 |
| `principle_focused_answer` | 36 |

## Validation split

- Rows: 39
- Source answers: 4 (3, 31, 33, 38)
- Paraphrased-question rows: 4
- Scored rows: 39 (min 8, max 10, mean 8.974)
- Answer characters: 49295 total, 697/1291/2020 min/median/max

| batch | count |
|---|---:|
| `26to40` | 30 |
| `first5` | 9 |

| example_type | count |
|---|---:|
| `alternative_ordering_answer` | 4 |
| `application_heavy_answer` | 4 |
| `concise_strong_answer` | 4 |
| `detailed_model_answer` | 4 |
| `formal_exam_style_answer` | 4 |
| `irac_structured_answer` | 4 |
| `natural_student_style_answer` | 4 |
| `outline_then_answer` | 4 |
| `paraphrased_question_model_answer` | 4 |
| `principle_focused_answer` | 3 |

## Dropped records

| synthetic_id | reason |
|---|---|
| `answer_06__alternative_ordering_answer` | source_instruction_collapse |
| `answer_06__application_heavy_answer` | source_instruction_collapse |
| `answer_06__concise_strong_answer` | source_instruction_collapse |
| `answer_06__detailed_model_answer` | source_instruction_collapse |
| `answer_06__formal_exam_style_answer` | source_instruction_collapse |
| `answer_06__irac_structured_answer` | source_instruction_collapse |
| `answer_06__natural_student_style_answer` | source_instruction_collapse |
| `answer_06__outline_then_answer` | source_instruction_collapse |
| `answer_06__paraphrased_question_model_answer` | source_instruction_collapse |
| `answer_06__principle_focused_answer` | source_instruction_collapse |
| `answer_07__alternative_ordering_answer` | source_instruction_collapse |
| `answer_07__application_heavy_answer` | source_instruction_collapse |
| `answer_07__concise_strong_answer` | source_instruction_collapse |
| `answer_07__detailed_model_answer` | source_instruction_collapse |
| `answer_07__formal_exam_style_answer` | source_instruction_collapse |
| `answer_07__irac_structured_answer` | source_instruction_collapse |
| `answer_07__natural_student_style_answer` | source_instruction_collapse |
| `answer_07__outline_then_answer` | source_instruction_collapse |
| `answer_07__paraphrased_question_model_answer` | source_instruction_collapse |
| `answer_07__principle_focused_answer` | source_instruction_collapse |
| `answer_08__alternative_ordering_answer` | source_instruction_collapse |
| `answer_08__application_heavy_answer` | source_instruction_collapse |
| `answer_08__concise_strong_answer` | source_instruction_collapse |
| `answer_08__detailed_model_answer` | source_instruction_collapse |
| `answer_08__formal_exam_style_answer` | source_instruction_collapse |
| `answer_08__irac_structured_answer` | source_instruction_collapse |
| `answer_08__natural_student_style_answer` | source_instruction_collapse |
| `answer_08__outline_then_answer` | source_instruction_collapse |
| `answer_08__paraphrased_question_model_answer` | source_instruction_collapse |
| `answer_08__principle_focused_answer` | source_instruction_collapse |
| `answer_09__alternative_ordering_answer` | source_instruction_collapse |
| `answer_09__application_heavy_answer` | source_instruction_collapse |
| `answer_09__concise_strong_answer` | source_instruction_collapse |
| `answer_09__detailed_model_answer` | source_instruction_collapse |
| `answer_09__formal_exam_style_answer` | source_instruction_collapse |
| `answer_09__irac_structured_answer` | source_instruction_collapse |
| `answer_09__natural_student_style_answer` | source_instruction_collapse |
| `answer_09__outline_then_answer` | source_instruction_collapse |
| `answer_09__paraphrased_question_model_answer` | source_instruction_collapse |
| `answer_09__principle_focused_answer` | source_instruction_collapse |
| `answer_10__alternative_ordering_answer` | source_instruction_collapse |
| `answer_10__application_heavy_answer` | source_instruction_collapse |
| `answer_10__concise_strong_answer` | source_instruction_collapse |
| `answer_10__detailed_model_answer` | source_instruction_collapse |
| `answer_10__formal_exam_style_answer` | source_instruction_collapse |
| `answer_10__irac_structured_answer` | source_instruction_collapse |
| `answer_10__natural_student_style_answer` | source_instruction_collapse |
| `answer_10__outline_then_answer` | source_instruction_collapse |
| `answer_10__paraphrased_question_model_answer` | source_instruction_collapse |
| `answer_10__principle_focused_answer` | source_instruction_collapse |
| `answer_13__alternative_ordering_answer` | source_instruction_collapse |
| `answer_13__application_heavy_answer` | source_instruction_collapse |
| `answer_13__concise_strong_answer` | source_instruction_collapse |
| `answer_13__detailed_model_answer` | source_instruction_collapse |
| `answer_13__formal_exam_style_answer` | source_instruction_collapse |
| `answer_13__irac_structured_answer` | source_instruction_collapse |
| `answer_13__natural_student_style_answer` | source_instruction_collapse |
| `answer_13__outline_then_answer` | source_instruction_collapse |
| `answer_13__paraphrased_question_model_answer` | source_instruction_collapse |
| `answer_13__principle_focused_answer` | source_instruction_collapse |
| `answer_15__alternative_ordering_answer` | source_instruction_collapse |
| `answer_15__application_heavy_answer` | source_instruction_collapse |
| `answer_15__concise_strong_answer` | source_instruction_collapse |
| `answer_15__detailed_model_answer` | source_instruction_collapse |
| `answer_15__formal_exam_style_answer` | source_instruction_collapse |
| `answer_15__irac_structured_answer` | source_instruction_collapse |
| `answer_15__natural_student_style_answer` | source_instruction_collapse |
| `answer_15__outline_then_answer` | source_instruction_collapse |
| `answer_15__paraphrased_question_model_answer` | source_instruction_collapse |
| `answer_15__principle_focused_answer` | source_instruction_collapse |
| `answer_17__alternative_ordering_answer` | serialized_source_in_input |
| `answer_17__application_heavy_answer` | serialized_source_in_input |
| `answer_17__concise_strong_answer` | serialized_source_in_input |
| `answer_17__detailed_model_answer` | serialized_source_in_input |
| `answer_17__formal_exam_style_answer` | serialized_source_in_input |
| `answer_17__irac_structured_answer` | serialized_source_in_input |
| `answer_17__natural_student_style_answer` | serialized_source_in_input |
| `answer_17__outline_then_answer` | serialized_source_in_input |
| `answer_17__paraphrased_question_model_answer` | serialized_source_in_input |
| `answer_17__principle_focused_answer` | serialized_source_in_input |
| `answer_20__alternative_ordering_answer` | source_instruction_collapse |
| `answer_20__application_heavy_answer` | source_instruction_collapse |
| `answer_20__concise_strong_answer` | source_instruction_collapse |
| `answer_20__detailed_model_answer` | source_instruction_collapse |
| `answer_20__formal_exam_style_answer` | source_instruction_collapse |
| `answer_20__irac_structured_answer` | source_instruction_collapse |
| `answer_20__natural_student_style_answer` | source_instruction_collapse |
| `answer_20__outline_then_answer` | source_instruction_collapse |
| `answer_20__paraphrased_question_model_answer` | source_instruction_collapse |
| `answer_20__principle_focused_answer` | source_instruction_collapse |
| `answer_45__concise_strong_answer` | quality_score_below_8 |
| `answer_45__irac_structured_answer` | quality_score_below_8 |
| `answer_45__outline_then_answer` | quality_score_below_8 |
| `answer_45__paraphrased_question_model_answer` | quality_score_below_8 |
| `answer_46__concise_strong_answer` | quality_score_below_8 |
| `answer_46__paraphrased_question_model_answer` | quality_score_below_8 |
