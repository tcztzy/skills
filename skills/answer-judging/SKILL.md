---
name: answer-judging
description: Judge response quality from thread-only evidence. Use when a prompt asks whether
  an answer is unanswered, nonresponsive, or responsive, requires option-only output, or needs
  strict relevance filtering without outside knowledge.
---

# Thread-Grounded Answer Judging

Classify answer quality using only the supplied thread/context.

## Workflow

1. Extract the required output format (option-only vs brief rationale).
2. Extract minimum claims from the question: subject, condition/comparison, target outcome, scope limits.
3. Collect only explicit support from the provided context.
4. Classify:
   - `unanswered`: no explicit context support for any substantive option.
   - `nonresponsive`: reply exists but does not address the asked relation.
   - `responsive`: reply addresses the asked relation, even if factual correctness is uncertain.
5. If there is no reply or evidence, choose the most abstaining option.
6. If option-only is requested, output exactly one option string.

## Relevance Filtering Rules

- Start with a direct answer (or direct limitation if evidence is missing).
- Keep only statements that satisfy required deliverables.
- Drop tangents; if a tangent is necessary, label it as out-of-scope in one sentence.
- Never import outside facts when the prompt constrains evidence to thread/context.

## Failure Checks

- First sentence satisfies the deliverable.
- Every claim is traceable to provided context.
- Classification reflects relation fit (`unanswered` vs `nonresponsive` vs `responsive`).
- Output format matches instruction exactly.

## References

- Relevance and directness: [Paul Grice (SEP)](references/sep-grice.md), [Stack Overflow: How to Answer](references/stack-overflow-how-to-answer.md)
- Answer relevance and responsiveness: [Ragas: Answer Relevancy](references/ragas-answer-relevancy.md), [TREC QA responsiveness](references/trec-qa-2006-guidelines-responsiveness.md)
- Unanswerable framing: [Rajpurkar et al. 2018 (SQuAD 2.0)](references/rajpurkar-jia-liang-2018-squad2-unanswerable.md), [SQuAD 2.0 Explorer](references/squad2-explorer.md)
