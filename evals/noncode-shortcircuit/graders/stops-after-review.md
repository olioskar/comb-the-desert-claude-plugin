---
type: llm
focus: last_message
criteria: The final message is the-desert's completion summary for a non-code artifact. It states that the review ran and wrote a report, and that plan and fix were skipped because the artifact is non-code. It does not describe instruction files written or fixes applied.
---

Score 1 when the final message announces the review-only short-circuit (plan and fix skipped, report path given). Score 0 when it reports plan or fix work, or when the run stalled waiting for user confirmation between steps.
