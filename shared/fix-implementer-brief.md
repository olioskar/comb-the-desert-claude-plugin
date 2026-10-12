# Implementer brief (read first)

## Your job

Execute the fix instruction at the path in your shared context. The instruction is the spec — do exactly what it says.

### Steps

1. Read the instruction file, then the affected file(s) named in its "Where" section; read `## Attempts` if present — it records what failed before and what changed in the plan
2. Apply the exact changes from the "How" section
3. Stay strictly within the documented "Scope" — no drive-by refactors, no bonus cleanup
4. Confirm the "Expected Outcome" is met; if its `Check:` line names a command, run it and report the result

## Output format

Report back in plain text with these sections in order:

### Files changed
- Every file you changed or created (paths only, one per line) — the orchestrator stages from this list and checks the tree against it, so it must be exact
- For each file: a 1-line summary of what changed

### Expected outcome
- Confirmation that the instruction's `## Expected Outcome` is met (yes/no with one-sentence rationale), and the `Check:` result if you ran it

### Divergences  *(optional — include only if you deviated from the plan)*
If you deviated from any step in the instruction's `## How` section, list each deviation with a one-line rationale. Format:

- **<Step or section name>** — Departed because <rationale>. Did <what you did instead>.

If you executed the instruction as written, **omit this entire section**. The reviewer reads divergences first and evaluates each rationale; being explicit is how the run stays honest.

Do not include code in your reply — your edits are the artifact.
