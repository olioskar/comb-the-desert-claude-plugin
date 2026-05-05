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

## Step 2: Surface relevant directives

Lowercase the focus brief and scan it for substring matches against the loaded directive filenames (both plugin defaults at `${CLAUDE_PLUGIN_ROOT}/directives/*.md` and the user's directives at `<project-root>/<directives.user_path>/*.md` if present). Strip the `.md` extension before matching, but match against the *full base name* — so `"scope"` matches `scope-discipline.md`, `"simplicity"` matches `simplicity.md`, and `"copy-paste"` would match a user directive named `copy-paste.md` if present (it doesn't match the shipped `reusability.md` — the matcher is a literal substring check, not a synonym mapper, per spec §8).

Record the matched directive paths. They will be flagged as **primary** in agent dispatch prompts under the heading "Directives most relevant to this run" so agents weight them first.

If the focus brief is empty, no directives are flagged primary; all directives still load normally.

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

## Step 4: Suggest groupings

Scan findings for items that could be combined. Look for:
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

Launch all in parallel by issuing multiple Task tool calls in a single assistant message — one call per finding (or group). Do not use `run_in_background: true`; that is a Bash-tool parameter and has no effect on the Task tool.

**Agent config (resolved per finding):**

- **Pick a specialty lens.** For each finding, the orchestrator picks one role from `config.agents` whose `when_to_use` best matches the finding's specialty (general correctness → `code-reviewer`, simplification/abstraction concerns → `simplifier`, error-handling → `silent-failure-hunter`, test gaps → `test-auditor`, pattern/spec drift → `consistency-auditor`). When no role obviously matches, default to `code-reviewer`. The lens informs the dispatch prompt's framing and is recorded in the plan file's `**Specialty:**` header — it is **not** the subagent_type that runs.
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

Once all agents finish, present the full list grouped by severity:

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

## Ground rules

- **Every item** in the report gets its own instruction file. Don't skip deferred items or test gaps — they all get documented.
- **Agents read source code.** They don't just parrot the review.
- **Instructions are self-contained.** Anyone picking up one file has everything they need to execute without reading the original report.
- **Scope boundaries are explicit.** Every instruction states what's in and out of scope.

## Edge case: focus brief contradicts shipped behavior

Same as `/comb:review`: surface and ask once.
