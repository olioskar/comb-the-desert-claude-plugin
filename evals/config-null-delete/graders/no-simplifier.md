---
type: llm
criteria: The project config sets agents.simplifier to null, and the merge rules say null deletes the key. The run must therefore never dispatch a simplifier agent (comb:simplifier), and the picked-palette announcement must not list simplifier as an available or picked role. Other reviewer agents may be dispatched normally, and a review report must be produced.
---

Read the transcript. Score 1 when no simplifier agent was dispatched and the palette announcement excludes it while the review still completes. Score 0 when a simplifier was dispatched, when simplifier is announced as part of the palette, or when the run aborted without producing a review.
