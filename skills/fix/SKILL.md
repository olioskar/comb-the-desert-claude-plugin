---
name: fix
description: Execute comb fix instructions sequentially or in parallel batches. Use after /comb:plan has produced instruction files. Each instruction goes to an implementer; standard items also go to a verifier. The user must invoke this explicitly — Claude does not auto-trigger it because it edits code.
argument-hint: "[instruction-folder] [focus brief]"
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Task
  - WebFetch
user-invocable: true
disable-model-invocation: true
---

You are running step 3 of the comb workflow: review → plan → fix.

You're a team lead working through a stack of fix instructions. For each: hand it to an implementer, then hand the result to a reviewer. If it fails, adjust and retry. Track progress; don't let anything slip.

## Inputs

1. **Folder of instruction documents** — from `/comb:plan` or any structured fix instructions. User specifies, or default to most recent under `<paths.plans>`.
2. **Execution order** — user specifies (e.g., "C1 → H1-H3 → M1-M10"), or derive from filenames/categories (Critical → High → Medium → Low → Test gaps). Confirm with user. Exclude items the user marks deferred or out-of-scope.
3. **Focus brief** — `$ARGUMENTS` — carries through from review when invoked via `/comb:the-desert`.

## Step 1: Load config

Same layered-merge as `/comb:review`. Project root is resolved with `git rev-parse --show-toplevel` (which handles git worktrees correctly). From it:
- `models.fix.implementer_standard`
- `models.fix.implementer_trivial`
- `models.fix.reviewer`
- `directives` and `agents` (for verifier dispatch)

## Step 2: Surface relevant directives

Lowercase the focus brief and scan it for substring matches against the loaded directive filenames (both plugin defaults at `${CLAUDE_PLUGIN_ROOT}/directives/*.md` and the user's directives at `<project-root>/<directives.user_path>/*.md` if present). Strip the `.md` extension before matching, but match against the *full base name* — so `"scope"` matches `scope-discipline.md`, `"simplicity"` matches `simplicity.md`, and `"copy-paste"` would match a user directive named `copy-paste.md` if present (it doesn't match the shipped `reusability.md` — the matcher is a literal substring check, not a synonym mapper, per spec §8).

Record the matched directive paths. They will be flagged as **primary** in agent dispatch prompts under the heading "Directives most relevant to this run" so agents weight them first.

If the focus brief is empty, no directives are flagged primary; all directives still load normally.

## Step 3: Suggest groupings

Scan instruction files for items that touch the same file with trivial scope. Suggest combining:

```
L1, L2, L3 all touch imports in ContactsGrid.tsx — combine?
M2 and M4 both fix the same hook — combine?
```

The user decides. Grouped items share one implementation pass but each sub-item gets verified.

## Step 4: Execution loop

For each item (or group):

### 4a. Parallel execution policy (governs Step 4b–4f)

Two instructions overlap if their **write-sets** intersect — reads are free. Apply this policy to the execution loop below:

- Same-file writes → sequential.
- Different-file writes → parallel batch.
- **Concurrency limit:** max 3 implementer/reviewer pairs running concurrently — i.e., up to 3 items being implemented and verified at any given moment (so up to 6 in-flight subagents at peak: 3 implementers running while 3 reviewers verify previous batches, or 3 implementer+reviewer pairs interleaved).

To launch a parallel batch, issue multiple Task tool calls in a single assistant message — one call per item in the batch. Do not use `run_in_background: true` (that is a Bash-tool parameter and has no effect on the Task tool).

Announce batches before launching:

```
Running batch: L1, L2, L3 in parallel (no file overlap, 3-pair concurrency)
```

### 4b. Read the instruction

Read the full fix instruction file. Understand What, Why, Where, How, Expected Outcome, Scope.

### 4c. Classify: trivial or standard?

Triviality is **judgment-based by the orchestrator** using this rubric (spec §7.5):

**Trivial:**
- Single-line edits
- Import reorders
- Comment fixes
- Lexical renames within a single file

**Standard:**
- Anything multi-file
- Anything that changes behavior
- Anything that introduces a new control-flow branch

This is a judgment call — borderline cases lean **standard**, because the cost of a needless reviewer is small but the cost of a missed regression is high. The user can override the classification for any item.

For trivial items: announce "(trivial — sonnet implementer per `models.fix.implementer_trivial`, reviewer per `models.fix.reviewer`)" and proceed. Note that the reviewer is **not** skipped for trivial items in the standard `/comb:fix` flow — that skip-trivial-review behavior only happens if the user explicitly authorises it for a given run, and is overridden in `/comb:the-desert` where every item gets a reviewer regardless.

### 4d. Send to implementer

**Agent config (resolved per item):**

- **Pick the role.** Implementer roles aren't restricted — pick whichever shipped role best matches the instruction's domain. When no domain match is clear, default to `code-reviewer`.
- **Resolve `subagent_type`** from the picked role's `agents.<role>.subagent_type`. **Do not hardcode `general-purpose`** — honor the user's `agents` config.
- **Resolve model** with this priority (spec §4.3 / §7.6): `agents.<role>.model` if set; otherwise `models.fix.implementer_standard` for standard items, `models.fix.implementer_trivial` for trivial items.
- **Allowlist match (not prefix check) — spec §5.4:** the shipped allowlist is exactly:
  - `comb:code-reviewer`
  - `comb:simplifier`
  - `comb:silent-failure-hunter`
  - `comb:test-auditor`
  - `comb:consistency-auditor`

  Compare the resolved `subagent_type` to this list with literal string equality. Native → supply directive paths only. Foreign → embed full directive contents.
- **Fresh agent per item** — no accumulated state.

**Implementer dispatch prompt (5-part order per spec §7.1.5):**

```
You're an implementer. Execute this fix instruction precisely and completely.

## 1. Shared context

Repository: {project-root}
Branch: {branch}
Item: {reference_code} — {title}
Instruction file: {instruction-path}

## 2. Directives

The project's authoritative directives apply to this fix.

{If native:}
Read these directive files and cite as `file.md §N.N` if you depart from any rule (you should not need to depart):
- {plugin directive paths, if include_plugin_defaults}
- {user directive paths, if directives.user_path resolves}

Directives most relevant to this run:
- {primary directive paths from the "Surface relevant directives" step}

{If foreign:}
These directives are authoritative. Cite by `file.md §N.N` if you depart from any rule.

{Embed full contents of every loaded directive verbatim with `## File: <path>` headers between them.}

Directives most relevant to this run:
- {primary directive paths from the "Surface relevant directives" step}

## 3. User focus for this run

{focus_brief if present, verbatim, with framing:}

Findings matching this focus are highest priority. Surface other issues too, but do not let the user's stated concerns slip.

## 4. Your job

Execute the fix instruction below. The instruction is the spec — do exactly what it says.

### Fix Instruction

{full instruction document content}

### Steps

1. Read the affected file(s) named in the instruction's "Where" section
2. Apply the exact changes from the "How" section
3. Stay strictly within the documented "Scope" — no drive-by refactors, no bonus cleanup
4. Confirm the "Expected Outcome" is met

## 5. Output format

Report back in plain text:

- Files you changed (paths)
- What changed in each (1-line summary)
- Confirmation that the "Expected Outcome" is met (yes/no with rationale)

Do not include code in your reply — your edits are the artifact.
```

### 4e. Send to reviewer (always)

**Agent config (resolved per item):**

- **Pick the role.** The fix-reviewer is **always `test-auditor`** — that is the canonical fix-verifier role per spec §5.3 ("`test-auditor` … Always for plan/fix verification."). Do not pick another role here unless the user has remapped `agents.test-auditor` in their config.
- **Resolve `subagent_type`** from `agents.test-auditor.subagent_type`. **Do not hardcode `general-purpose`** — honor the user's `agents.test-auditor` config (which defaults to `comb:test-auditor`).
- **Resolve model** with this priority (spec §4.3 / §7.6): `agents.test-auditor.model` if set; otherwise `models.fix.reviewer` (default `opus`).
- **Allowlist match (not prefix check) — spec §5.4:** the shipped allowlist is exactly:
  - `comb:code-reviewer`
  - `comb:simplifier`
  - `comb:silent-failure-hunter`
  - `comb:test-auditor`
  - `comb:consistency-auditor`

  Compare with literal string equality. Native (the default) → supply directive paths. Foreign (user remapped `agents.test-auditor.subagent_type` to something else) → embed full directive contents.
- **Fresh agent.**

**Reviewer dispatch prompt (5-part order per spec §7.1.5):**

```
You're a code reviewer verifying a fix against its original instruction.

## 1. Shared context

Repository: {project-root}
Branch: {branch}
Item: {reference_code} — {title}
Instruction file: {instruction-path}
Implementer summary: {implementer's reply}

## 2. Directives

The project's authoritative directives apply to your verification.

{If native:}
Read these directive files and cite as `file.md §N.N` when raising findings:
- {plugin directive paths, if include_plugin_defaults}
- {user directive paths, if directives.user_path resolves}

Directives most relevant to this run:
- {primary directive paths from the "Surface relevant directives" step}

{If foreign:}
These directives are authoritative. Cite by `file.md §N.N` when raising findings.

{Embed full contents of every loaded directive verbatim with `## File: <path>` headers between them.}

Directives most relevant to this run:
- {primary directive paths from the "Surface relevant directives" step}

## 3. User focus for this run

{focus_brief if present, verbatim, with framing:}

Findings matching this focus are highest priority. Surface other issues too, but do not let the user's stated concerns slip.

## 4. Your job

Verify the fix below was done correctly.

### Original Instruction

{instruction document content}

### What the implementer changed

{implementer's summary}

### Check these things

1. The change from "How" was applied correctly
2. The "Expected Outcome" is satisfied
3. No unrelated changes were introduced
4. The fix stays within documented "Scope"

## 5. Output format

Report `PASS` or `FAIL` on the first line with specifics:

- **PASS** — single line plus a 1–2-sentence confirmation of what you verified.
- **FAIL** — explain exactly what's wrong, with file:line citations.

### Discovered issues (optional)

If you spot a real problem in the same file(s) that's NOT part of this fix — a bug, type error, missing guard — report it under a `DISCOVERED` heading with:
- Short title
- File path and line(s)
- Brief description and suggested fix

Only flag genuine issues, not style preferences. One or two max. If nothing stands out, omit this heading.
```

### 4f. Handle the result

- **PASS** — log it, announce complete, move on.
- **FAIL** — read feedback. Adjust instructions if needed. Send a new implementer. Review again. **If 3 failures on one item, stop and ask the user.**
- **DISCOVERED** — write a new instruction document in the same folder using the next available code (`D1`, `D2`...). Same format as all other items. Add to the end of the queue. Announce:
  ```
  M3 — PASS (5/15 complete)
  Discovered issue added: D1 — {title} (queue is now 16 items)
  Next: M4 — {title}
  ```

## Step 5: Progress tracking

After each item:

```
{code} — PASS ({N}/{total} complete)
Next: {next_code} — {title}
```

With extras:
```
{code} — PASS after 1 retry ({N}/{total} complete)
{code} — PASS, trivial implementer ({N}/{total} complete)
```

At the end:

```
All {N} items complete:
  - C1: PASS
  - H1: PASS
  - H2: PASS (1 retry)
  - L1-L3: PASS (parallel batch, trivial implementer)
  - D1: PASS (discovered during H2 review)
  - ...

{M} items deferred:
  - X1-X6: {reason}

{K} discovered during execution:
  - D1: {title} (found reviewing H2) — PASS
```

## Ground rules

- **Fresh agents.** Each implementer and reviewer is a new subagent. No accumulated state.
- **The instruction is the spec.** Implementer follows it. Reviewer verifies against it. If the doc is wrong, fix the doc first, then re-implement.
- **Scope is sacred.** Implementers don't make changes outside scope. Reviewers flag scope violations as FAIL.
- **Don't loop forever.** Three failures means something's structurally wrong. Stop and ask.
- **Parallelize when safe.** Different writes = safe. Same file = sequential.
