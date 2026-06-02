---
name: plan
description: Turn comb review findings into per-finding fix instructions. Use after a comb review when the user wants the findings translated into executable fix plans. Each finding gets its own instruction document an implementer can execute cold.
argument-hint: "[report-path] [focus brief]"
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Task
  - WebFetch
user-invocable: true
disable-model-invocation: false
---

You are running step 2 of the comb workflow: review → plan → fix.

You're a senior engineer turning review findings into crystal-clear fix instructions. Each finding gets its own specialist who reads the actual code and writes instructions good enough for any developer to execute cold.

## Inputs

1. **Report**: should be in conversation context, or user provides a path. Look in `<paths.plans>` parent directory or `<paths.reviews>` for the most recent report if not specified.
2. **Focus brief**: `$ARGUMENTS` — carries through from review when invoked via `/comb:the-desert`.

## Step 1: Load config

Same layered-merge as `/comb:review`. Project root is resolved with `git rev-parse --show-toplevel` (which handles git worktrees correctly). From it, take:
- `paths.plans` — output folder root
- `models.plan` — model for planner agents
- `directives` — for the planners' agent prompts
- `paths.patterns` — the PATTERNS manifest, if it resolves

**Load the PATTERNS manifest (decision §8).** If `paths.patterns` resolves, read it and run the commit-based staleness heuristic **exactly as defined in spec §10** (do not invent a variant): `cited` = the paths the manifest references, `touched` = the files referenced by the report's findings; flag if `git diff --name-only <Base commit> HEAD -- <cited ∩ touched>` is non-empty. Record any staleness note for presentation. If absent or `null`, skip — graceful no-op.

## Step 2: Surface relevant directives

Lowercase the focus brief and scan it for substring matches against the loaded directive filenames (both plugin defaults at `${CLAUDE_PLUGIN_ROOT}/directives/*.md` and the user's directives at `<project-root>/<directives.user_path>/*.md` if present). Strip the `.md` extension before matching, but match against the *full base name* — so `"scope"` matches `scope-discipline.md`, `"simplicity"` matches `simplicity.md`, and `"copy-paste"` would match a user directive named `copy-paste.md` if present (it doesn't match the shipped `reusability.md` — the matcher is a literal substring check, not a synonym mapper, per spec §8).

Record the matched directive paths. They will be flagged as **primary** in agent dispatch prompts under the heading "Directives most relevant to this run" so agents weight them first.

If the focus brief is empty, no directives are flagged primary; all directives still load normally.

## Step 2.5: Detect report shape

Read the report header. Determine the report shape:

- **Code-shaped report** — the report includes a `## Verdict:` block AND a `## Findings by Severity` section with C/H/M/L/T/D headings. This is the historical default. Use today's per-finding planning flow (Steps 3, 4, 5, 6 below).
- **Non-code report** — the report includes a `## Read` and `## Lens` section AND a `## Findings` section with flat labelled entries (no severity tiers). Use the non-code flow described in Step 6 below: a single consolidated `revise-{spec-stem}.md` file, no per-finding agents, no groupings.

Surface the detection to the user before proceeding:

```
Report shape: {code-shaped | non-code}
{Continue with per-finding plan files | Emit single revise-{spec-stem}.md}
```

The classification flows through the rest of this skill. Steps below note which shape they apply to.

## Step 3: Parse all findings

Extract every finding from the report:
- **Reference code**: C1, H2, M5, T1, D1, etc. Preserve exactly as the report uses them.
- **Title**: short description
- **Category** / **severity**: as the report uses
- **File(s)**: paths and line numbers
- **Description**: what's wrong, why
- **Suggested fix**: if the report includes one

**Include Deferred items.** Don't drop them. "Deferred" is *noted, explicitly out of scope for the current round* — but the user often picks them up while in the area. Each deferred item gets the same per-finding plan file as everything else. The user is the gate, not the planner.

If the Deferred section uses bullet points without codes (older review reports), assign `D1`, `D2`, … inline before dispatching agents, in the order they appear.

Count every code (C/H/M/L/T/D). Confirm the total with the user before sending agents.

**On a non-code report:** findings have plain labels (Ambiguity, Blind spot, Pattern-break, Reusability gap, Quality concern), not severity codes. Preserve the labels verbatim. The ordering for the consolidated revise-doc follows the report's order — no severity-based reshuffle. Skip the "confirm total with user" step; the count is just the number of findings.

## Step 4: Suggest groupings

**Skip this entire step on non-code reports.** A non-code report's findings all target the same spec file; there's no grouping concept — they're consolidated into one revise-doc in Step 6.

For code-shaped reports: scan findings for items that could be combined. Look for:
- Multiple findings touching the same file with small scope
- Findings on adjacent lines that share intent (e.g., 3 import fixes)
- Findings that depend on each other (don't split them across two instructions)

Suggest groupings to the user once:

```
L1, L2, L3 are all import fixes in ContactsGrid.tsx — group into one instruction?
M2 and M4 both touch the same hook's dependency array — combine?
```

The user decides. Grouped items share one .md file but list each sub-item explicitly so nothing gets lost.

**Group reference codes.** Each accepted group gets a `G{n}` code, sequential in the order the user accepts them: `G1`, `G2`, `G3`, …. The group's instruction file is named `G{n}-{title-slug}.md`, and the file's header block lists the source codes (e.g., `**Consolidates:** M4 + M5`). `G` is a separate sequence from C/H/M/L/T/D/X — collisions are not possible.

## Step 5: Determine output folder

Default: `<paths.plans>/plan-for-{report-stem}/`

For example, report at `docs/combs/reviews/pr-123-round1-report.md` → instructions at `docs/combs/plans/plan-for-pr-123-round1-report/`.

User may override.

## Step 6: Send one agent per finding (or group)

**Branch on report shape:**

- **Code-shaped report:** today's per-finding dispatch (see the rest of this step).
- **Non-code report:** a single planner agent emits one consolidated revise-doc. Skip per-finding dispatch entirely.

### Non-code report — single consolidated revise-doc

Dispatch one planner agent (resolved via `agents.implementer.subagent_type`, model per `models.plan`) with this prompt structure (same 5-part order, adapted):

````
You're a senior reviewer translating a spec/design-doc review into a single consolidated revision-instructions file.

## 1. Shared context

Repository: {project-root}
Branch: {branch}
Spec under revision: {spec_path}
Report: {report-path}
Output file: {output_folder}/revise-{spec-stem}.md

## 2. Directives

{Same directives block as the code-shaped flow.}

## Project conventions (observed baseline)

{Included only when `paths.patterns` resolved. Manifest path for native `comb:*` agents, embedded contents for foreign agents.}

This is the codebase's observed convention baseline as of its last generation — a prior, not the authority. Read the actual code around the diff; where it conflicts with the manifest, the live code wins. If the manifest has no entry for this area or theme, reconstruct the convention from the code — silence is neither a finding nor permission. Project directives outrank this manifest: a divergence that violates an up-to-date directive is drift no matter how widespread, and classifying it as a deliberate improvement or new canonical never excuses a directive violation. Before flagging a divergence, classify it: unjustified, inconsistent divergence is drift (a finding); a deliberate, consistently-applied improvement or migration, or the first canonical pattern for something genuinely new, is not a drift finding. When you judge a divergence to be an improvement/migration or a new canonical, say so explicitly so the orchestrator can emit the semantic refresh note. Cite manifest entries by area/section heading when raising conformance findings.

(Planner note) When you author the instruction for a finding the review classified as a deliberate improvement or a new canonical, reference the manifest but do not bend the instruction back to the baseline — that divergence is sanctioned. Omit the whole block when no manifest resolved.

## 3. User focus for this run

{focus_brief if present, verbatim.}

## 4. Your job

You are writing ONE consolidated revision-instructions file for the spec under review. The findings in the report are the spec for your work.

### Findings (full report body)

{Embed the full findings section of the report verbatim.}

### What to do

1. Read the spec file: {spec_path}
2. For each finding in the report, identify the exact section/line to revise.
3. Write a single file at `{output_folder}/revise-{spec-stem}.md` consolidating all revisions in the order findings appear in the report. Each revision is a section with the finding's original label and title.

## 5. Output format

A single markdown file at `{output_folder}/revise-{spec-stem}.md` with this shape:

```markdown
# Revise {spec-stem}

**Target spec:** `{spec_path}`
**Source report:** `{report_path}`
**Revisions:** {N} ({breakdown by label})

---

## {Label} — {finding title}

**Spec location:** `{spec_path}` § {section heading or line range}

**Current text:**
> {quote the relevant span of the spec, or describe its absence if the finding is a blind spot}

**Revision:**
{The exact text, paragraph, or section to add/replace/remove. For new prose, write the prose. For removals, name what to delete. For ambiguities, write the disambiguating clarification.}

**Reason:** {one sentence — quote the finding's "why it matters".}

(repeat per finding, in report order)

---

## Notes for the implementer

- All revisions target one file: `{spec_path}`.
- Apply revisions in order; later revisions assume earlier ones are in place.
- Cite directives where the original finding cited them (`file.md §N.N`).
```

Be concise and precise. The implementer applies these revisions cold; everything they need must be in this file.
````

### Code-shaped report — per-finding dispatch (existing behavior)

Launch all in parallel by issuing multiple Task tool calls in a single assistant message — one call per finding (or group). Do not use `run_in_background: true`; that is a Bash-tool parameter and has no effect on the Task tool.

**Agent config (resolved per finding):**

- **Pick a specialty lens.** For each finding, the orchestrator picks one role from `config.agents` whose `when_to_use` best matches the finding's specialty (general correctness → `code-reviewer`, simplification/abstraction concerns → `simplifier`, error-handling → `silent-failure-hunter`, test gaps → `test-auditor`, pattern/spec drift → `consistency-auditor`). When no role obviously matches, default to `code-reviewer`. `pattern-scanner` is generation-only and is never picked as a finding's lens. The lens informs the dispatch prompt's framing and is recorded in the plan file's `**Specialty:**` header — it is **not** the subagent_type that runs.
- **Resolve `subagent_type` from `agents.implementer.subagent_type`** (default `general-purpose`). The planner agent needs Write access to author the plan file; the comb:* review roles cannot write. The user's `agents.implementer` override (if present) is honored.
- **Resolve model** with this priority (per spec §4.3 / §7.6): `agents.<role>.model` if set; otherwise `models.plan` (default `opus`).
- **Allowlist match (not prefix check) — spec §5.4:** the shipped allowlist is exactly these five strings:
  - `comb:code-reviewer`
  - `comb:simplifier`
  - `comb:silent-failure-hunter`
  - `comb:test-auditor`
  - `comb:consistency-auditor`

  Compare the resolved `subagent_type` to the allowlist with literal string equality. A typo like `comb:my-typo` does **not** count as native. If the resolved type is in the allowlist, treat as native (supply directive paths only). Otherwise treat as foreign (embed full directive contents in the dispatch prompt — see §5.4).

**Planner dispatch prompt (5-part order per spec §7.1.5):**

```
You're a senior {specialization-derived-from-finding} developer. You've been assigned one review finding to write fix instructions for.

## 1. Shared context

Repository: {project-root}
Branch: {branch}
Base: {base}
Report under planning: {report-path}
Output folder: {output-folder}

Files referenced by the finding: {file-paths}
Adjacent files worth scanning: {2–3 nearest siblings the orchestrator picks}

## 2. Directives

The project's authoritative directives apply to your fix instruction.

{If native (resolved subagent_type IS in the allowlist):}
Read these directive files and cite them as `file.md §N.N` when your instruction references policy:
- {plugin directive paths, if include_plugin_defaults}
- {user directive paths, if directives.user_path resolves}

Directives most relevant to this run (matched against the focus brief):
- {primary directive paths from the "Surface relevant directives" step}

{If foreign (resolved subagent_type is NOT in the allowlist):}
These directives are authoritative. Cite by `file.md §N.N` when raising any policy-grounded instruction.

{Embed full contents of every loaded directive — both plugin defaults and user directives — verbatim, with `## File: <path>` headers between them.}

Directives most relevant to this run (matched against the focus brief):
- {primary directive paths from the "Surface relevant directives" step}

## Project conventions (observed baseline)

{Included only when `paths.patterns` resolved. Manifest path for native `comb:*` agents, embedded contents for foreign agents.}

This is the codebase's observed convention baseline as of its last generation — a prior, not the authority. Read the actual code around the diff; where it conflicts with the manifest, the live code wins. If the manifest has no entry for this area or theme, reconstruct the convention from the code — silence is neither a finding nor permission. Project directives outrank this manifest: a divergence that violates an up-to-date directive is drift no matter how widespread, and classifying it as a deliberate improvement or new canonical never excuses a directive violation. Before flagging a divergence, classify it: unjustified, inconsistent divergence is drift (a finding); a deliberate, consistently-applied improvement or migration, or the first canonical pattern for something genuinely new, is not a drift finding. When you judge a divergence to be an improvement/migration or a new canonical, say so explicitly so the orchestrator can emit the semantic refresh note. Cite manifest entries by area/section heading when raising conformance findings.

(Planner note) When you author the instruction for a finding the review classified as a deliberate improvement or a new canonical, reference the manifest but do not bend the instruction back to the baseline — that divergence is sanctioned. Omit the whole block when no manifest resolved.

## 3. User focus for this run

{focus_brief if present, verbatim, with framing:}

Findings matching this focus are highest priority. Surface other issues too, but do not let the user's stated concerns slip.

## 4. Your job

You are writing fix instructions for **one** review finding. Treat the finding as the spec for your work.

**Before recommending a fix, trace through its failure modes.** If correctness depends on a runtime invariant — closure state, async timing, render scheduling, lifecycle ordering, transaction isolation — simulate the failure path mentally and confirm the proposed fix breaks it. If you cannot, surface the structural concern in your output rather than recommend a flawed fix. The reviewer downstream is going to check plan-compliance, not re-design the fix; you owe future-you a sound recommendation.

### Finding

### {reference_code}. {title} ({severity})

{full_finding_description}

### What to do

1. Read the affected file(s): {file_paths}
2. Read 2–3 nearby files to understand the surrounding patterns
3. Write a fix instruction document at `{output_folder}/{reference_code}-{title-slug}.md`

## 5. Output format

Your output is a single markdown file at `{output_folder}/{reference_code}-{title-slug}.md`.

**File shape — H1 title, header block, six body sections in order, citations footer:**

```markdown
# {reference_code} — {one-line title}

**Severity:** {Critical | High | Medium | Low | Test gap | Deferred}
**File(s):** {primary repo-relative path(s), with line ranges}
**Specialty:** {source agent(s) from the review report's `*Source: <agent>*` line — comma-separated if multiple. For grouped findings, list the union across the group's source agents. /comb:fix uses this to route the fix-reviewer to the matching specialty.}
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
What's different after the fix. How to verify it worked.

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

Be concise and precise. No fluff. These instructions are the single source of truth for this fix.

File naming: `{reference-code}-{title-slug}.md`. Title kebab-case, 5–8 words max. For grouped findings, `{reference-code}` is `G{n}` per Step 4.
```

## Step 7: Collect results

**Code-shaped report — present the full list grouped by severity:**

```
All {N} instruction files ready:

Critical ({count}):
  - docs/combs/plans/plan-for-.../C1-stale-closure-in-hook.md
  - ...

High ({count}):
  - ...

Medium ({count}):
  - ...
```

**Non-code report — present the single revise-doc:**

```
Revision instructions ready: {output_folder}/revise-{spec-stem}.md

{N} revisions targeting `{spec_path}`: {breakdown by label}
```

**Manifest notes (non-blocking).** Append any commit-based staleness note (decision §10) or semantic-refresh note (decision §9) recorded during this run.

## Ground rules

- **Every item** in the report gets its own instruction file. Don't skip deferred items or test gaps — they all get documented.
- **Agents read source code.** They don't just parrot the review.
- **Instructions are self-contained.** Anyone picking up one file has everything they need to execute without reading the original report.
- **Scope boundaries are explicit.** Every instruction states what's in and out of scope.

## Edge case: focus brief contradicts shipped behavior

Same as `/comb:review`: surface and ask once.
