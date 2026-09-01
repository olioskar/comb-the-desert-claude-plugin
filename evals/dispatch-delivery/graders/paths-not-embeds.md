---
type: llm
criteria: The planner is dispatched via the default agents.implementer (general-purpose), which is foreign per the delivery contract. Its dispatch prompt must list the plugin directive files as absolute paths, carry the authority instruction ("These directives are authoritative. Read every listed file before starting."), and must NOT embed the full text of the directive files (no pasted directive bodies with per-file headers). A plan instruction file for M1 must be produced.
---

Read the transcript, especially the Task tool call that dispatches the planner. Score 1 when the dispatch prompt delivers directives as file paths plus the authority sentence and an instruction file is written for M1. Score 0 when the dispatch prompt embeds directive contents wholesale, omits the directives entirely, or no instruction file is produced.
