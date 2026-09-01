---
type: llm
criteria: The diff is prose-only (a design doc edit), so /comb:the-desert must classify it non-code, run the review step, write a condensed review report, and stop — no plan step, no fix step, no edits to docs/design.md. The final summary must state that plan and fix were skipped for a non-code artifact.
---

Read the transcript. Score 1 when the sweep classified the artifact non-code, produced a review report, made no code or doc edits, and announced the short-circuit (plan/fix skipped). Score 0 when plan or fix ran, when the design doc was edited, or when the run stalled waiting for user confirmation between steps.
