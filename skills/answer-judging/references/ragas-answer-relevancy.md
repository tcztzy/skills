# Ragas: Answer Relevancy (Response/Answer Relevancy)

URL: https://docs.ragas.io/en/latest/concepts/metrics/available_metrics/answer_relevance/

Accessed: 2026-02-20

## Why This Source Matters

This documentation defines an *answer relevancy* metric for QA-style tasks, emphasizing that evaluation focuses on whether the answer is pertinent to the asked question (and penalizes incomplete/redundant answers). That supports treating "nonresponsive" as a *relevance/intent* failure rather than a factual-science dispute.

## Notes (Paraphrased)

- "Answer relevancy" measures how relevant an answer is to a question (not whether it is scientifically true).
- The metric uses the question and the generated answer to judge pertinence.

## Minimal Quotes (Verbatim, <= 25 words each)

- "This metric focuses on how well the answer matches the intent of the question, without evaluating factual accuracy."
- "An answer is considered relevant if it directly and appropriately addresses the original question."
