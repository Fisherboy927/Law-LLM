# Cursor Prompt: 26th to 40th Legal Answer Augmentation Pilot

```text
I want to run a small legal data augmentation pilot using the 26th to 40th Markdown files in:

D:\Projects\Law-LLM\Application_Images

Please do not modify the original Markdown files.

Goal:
Create synthetic training examples for LoRA fine-tuning, but avoid simply making 10 shallow paraphrases of the same answer. Use controlled task/style variation so the model does not see the exact same prompt with unexplained different outputs.

Please do the following:

1. Select the 26th to 40th `.md` files from the directory, sorted by filename.

2. Read each Markdown file and create a source record for each answer.

For each source record, extract:
- source_id
- source_path
- question text, if present
- sample_answer
- legal issues
- legal rules or principles
- application points
- authorities mentioned
- conclusion
- style profile
- facts or assumptions that must not be changed

Write these source records to:


data/augmentation/source_answers_26to40.jsonl

3. For each source answer, generate 10 derived training examples.

However, do not make all 10 examples the same instruction and same question. Use the following 10 derived example types:

1. detailed_model_answer
   - Same question.
   - Instruction: answer as a detailed high-quality model answer.

2. concise_strong_answer
   - Same question.
   - Instruction: answer concisely but completely.

3. irac_structured_answer
   - Same question.
   - Instruction: answer using a clear IRAC structure.

4. natural_student_style_answer
   - Same question.
   - Instruction: answer as a strong law student would in an exam.

5. formal_exam_style_answer
   - Same question.
   - Instruction: answer in a formal legal exam style.

6. application_heavy_answer
   - Same question.
   - Instruction: focus especially on applying the law to the facts.

7. principle_focused_answer
   - Same question.
   - Instruction: focus especially on explaining the legal principles clearly.

8. alternative_ordering_answer
   - Same question.
   - Instruction: answer the same legal problem but present the points in a different logical order.

9. paraphrased_question_model_answer
   - First create a safe paraphrase of the question that preserves the same facts, legal issues, and conclusion.
   - Then answer that paraphrased question as a model answer.

10. outline_then_answer
   - Same question.
   - Instruction: provide a brief answer outline followed by a polished final answer.

Rules for every synthetic example:
- Preserve the same legal issues and overall conclusion as the source answer.
- Do not introduce new facts.
- Do not invent cases, statutes, articles, regulations, or named authorities.
- Only mention authorities that appear in the source answer or question.
- If the source has no named authorities, do not add any.
- Do not copy distinctive phrases from the source answer.
- Vary wording, structure, and emphasis.
- Keep the answers legally accurate and useful for training.
- Do not make the answers artificially verbose.
- Do not include meta commentary inside the answer itself.

Each synthetic record should be a JSONL object with this shape:

{
  "synthetic_id": "...",
  "source_id": "...",
  "source_path": "...",
  "example_type": "...",
  "instruction": "...",
  "input": "...",
  "output": "...",
  "question_was_paraphrased": true_or_false,
  "paraphrased_question": null_or_string,
  "generation_notes": "brief note explaining how this variant differs from the source"
}

Write all generated examples to:


data/augmentation/synthetic_answers_first5_raw.jsonl

4. Validate the synthetic examples.

For each synthetic example, compare it against its source answer and check:
- same_conclusion
- preserves_key_issues
- no_new_facts
- no_hallucinated_authorities
- not_too_similar_to_source
- useful_for_lora_training
- quality_score from 1 to 10
- rejection_reason, if any

Accept examples only if they are legally faithful and useful for training.

Write accepted examples to:


data/augmentation/synthetic_answers_first5_validated.jsonl

Write rejected examples to:


data/augmentation/synthetic_answers_first5_rejected.jsonl

5. Create a human-readable review report at:


data/augmentation/augmentation_first5_review.md

The review report should include:
- number of Markdown files processed
- number of source records created
- number of synthetic examples generated
- number accepted
- number rejected
- rejection reasons grouped by type
- a short table showing source_id, example_type, quality_score, accepted/rejected
- any concerns about the dataset quality
- recommendations before scaling beyond the first 5 files

Important:
- Keep validation strict.
- Do not silently skip files. If a file cannot be processed, record it in the review report with the reason.
- Do not modify the original Markdown files.
- Keep all outputs machine-readable where JSONL is requested.

Finally, create a pull request in the corresponding github repo with appropriate comments.
```

  


