# Planner brief (read first)

## 4. Your job

You are writing fix instructions for **one** review finding. Treat the finding as the spec for your work.

**Before recommending a fix, trace through its failure modes.** If correctness depends on a runtime invariant — closure state, async timing, render scheduling, lifecycle ordering, transaction isolation — simulate the failure path mentally and confirm the proposed fix breaks it. If you cannot, surface the structural concern in your output rather than recommend a flawed fix. The reviewer downstream is going to check plan-compliance, not re-design the fix; you owe future-you a sound recommendation.

**The finding's `Verified:` line states what the review actually confirmed.** Re-derive anything it names as unchecked — an anchor, a count, a fix shape — from the code before you build on it. A fix shape the review marked unverified is a proposal: evaluate it, do not transcribe it. When your instruction contradicts an unverified particular, say so in the instruction and give the corrected particular. When the finding carries no `Verified:` line at all, treat every particular as unconfirmed.

### What to do

1. Read the affected file(s) named in your shared context
2. Reproduce the finding: confirm the defect the finding describes is present in the code you read — the construct, the behaviour, the missing handling. Record the result in the header's `**Finding status:**` line. When you cannot reproduce it, say what you looked for; do not write a `## How` for a non-defect (see the template).
3. Read 2–3 nearby files to understand the surrounding patterns
4. Write a fix instruction document at the output file named in your shared context

## 5. Output format

Your output is a single markdown file at the output file named in your shared context (the output folder and reference code named there).

**File shape — H1 title, header block, six body sections in order, citations footer:**

```markdown
# {reference_code} — {one-line title}

**Severity:** {Critical | High | Medium | Low | Test gap | Deferred}
**File(s):** {primary repo-relative path(s), with line ranges}
**Specialty:** {source agent(s) from the review report's `*Source: <agent>*` line — comma-separated if multiple. For grouped findings, list the union across the group's source agents. /comb:fix uses this to route the fix-reviewer to the matching specialty.}
**Finding status:** {confirmed — <what you observed, with file:line> | not reproduced — <what you looked for and where>}
{For grouped items, also: }**Consolidates:** {comma-separated finding codes the group covers}

---

## What
Exactly what needs to change. Name the exact code, lines, patterns.

## Why
Why this matters. What breaks or degrades if left unfixed.

## Where
Exact file path(s) and line number(s). Only include related files if they're part of the fix.

## How
The exact changes, with before/after code blocks. Precise enough to apply mechanically.

## Expected Outcome
What's different after the fix. Then one required line:

Check: {a command the fix reviewer can run from the project root whose exit code or output confirms the outcome, or an observable it can read in the code | none — <why nothing runnable exists, e.g. "visual change; needs a browser">}

## Scope
**In scope:** what this fix covers.
**Out of scope:** what NOT to touch — no drive-by refactors, no bonus cleanup.

## Directive citations
Every directive (plugin or user) and any project-level authoritative doc (CLAUDE.md, MEMORY.md, etc.) the instruction relies on. One bullet per source, with a one-line reason it applies. If the fix doesn't lean on any, write `None — no policy citation needed.`

- `<file>.md §<section>` — one-line reason
- `CLAUDE.md` "<section heading>" — one-line reason

## Considered alternatives  *(optional — include only when meaningful alternatives were rejected)*
ADR-style: list alternatives you considered but rejected, one bullet each, with a one-line "rejected because…" rationale. The main body is the single executable path; this section is documentation, not a decision gate. /comb:fix never reads from this section.

- **<Alternative title>** — Rejected because <one-line rationale>
- **<Alternative title>** — Rejected because <one-line rationale>
```

**Not reproduced.** When `**Finding status:**` is `not reproduced`, `## What` states what the finding claimed and what you found instead, `## How` is the single line `No change — finding not reproduced (see Finding status).`, and `## Expected Outcome` has `Check: none — no change proposed`. `/comb:fix` lists such items separately and queues one only when the user asks.

Be concise and precise. No fluff. These instructions are the single source of truth for this fix.

File naming: `{reference-code}-{title-slug}.md`. Title kebab-case, 5–8 words max. For grouped findings, `{reference-code}` is `G{n}` per Step 4.
