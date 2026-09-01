---
name: fix
description: Use after /comb:plan has produced instruction files and the user wants them executed. The user must invoke this explicitly — Claude does not auto-trigger it because it edits code.
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

Load the merged config per `${CLAUDE_PLUGIN_ROOT}/shared/config-loading.md`. From it:
- `models.fix.implementer_standard`
- `models.fix.implementer_trivial`
- `models.fix.reviewer`
- `directives` and `agents` (for verifier dispatch)
- `paths.patterns` — the PATTERNS manifest, if it resolves

**Load the PATTERNS manifest.** If `paths.patterns` resolves, read it and run the commit-based staleness heuristic (do not invent a variant): `cited` = the paths the manifest references, `touched` = the files referenced by the instruction set; flag if `git diff --name-only <Base commit> HEAD -- <cited ∩ touched>` is non-empty. Record any staleness note for presentation. If absent or `null`, skip — graceful no-op.

## Step 1.5: Pre-flight — check for an unrelated dirty tree

Skip this entire step if `fix.commit_per_item` is `false` in merged config.

Run `git status --porcelain`. If the output is empty, the tree is clean — proceed.

If non-empty, surface a one-shot question with these options:

```
Working tree has uncommitted changes before /comb:fix starts:
  <git status --porcelain output>

Pick one:
  (a) Commit existing changes now (suggest a message)
  (b) Stash and restore at the end of the run
  (c) Proceed without per-item commits for this run only
  (d) Abort
```

Honor the user's choice and proceed. In `/comb:the-desert`, this question is the third allowed question (alongside scope-at-start and run-again-at-end), and only fires when the tree is dirty.

## Step 2: Surface relevant directives

Apply the focus-brief matcher in `${CLAUDE_PLUGIN_ROOT}/shared/directive-matching.md`. It records the matched directive paths and flags them as **primary** in agent dispatch prompts under "Directives most relevant to this run"; an empty focus brief flags nothing, and all directives still load normally.

## Step 2.5: Detect folder shape

List the instruction folder. Determine the shape:

- **Per-finding folder** — multiple files matching the per-finding naming pattern (`{C|H|M|L|T|D|X}{n}-*.md`, optionally also `G{n}-*.md` for groups). This is the historical default. Use Steps 3–4 below as today.
- **Single revise-doc folder** — the folder contains exactly one file matching `revise-*.md` (and no per-finding files). This means the upstream `/comb:plan` ran against a non-code review report. Use the single-revise flow described in Step 4 below.

Surface the detection to the user before proceeding:

```
Instruction folder shape: {per-finding | single revise-doc}
{N items to process | 1 consolidated revise-doc: revise-{spec-stem}.md}
```

## Step 3: Suggest groupings

**Skip this entire step on a single-revise-doc folder.** There's nothing to group — there's already exactly one work item.

For per-finding folders: scan instruction files for items that touch the same file with trivial scope. Suggest combining:

```
L1, L2, L3 all touch imports in ContactsGrid.tsx — combine?
M2 and M4 both fix the same hook — combine?
```

The user decides. Grouped items share one implementation pass but each sub-item gets verified.

## Step 4: Execution loop

**Branch on folder shape (Step 2.5):**

- **Per-finding folder:** today's execution loop (Steps 4a–4g below) runs once per instruction file.
- **Single revise-doc folder:** the loop runs **exactly once** against the single `revise-*.md`. The item is **always classified standard** (it is a multi-finding spec edit, not a single-line code fix), and the reviewer is **always** `agents.consistency-auditor` (the same anchor that produced the upstream review). The escape hatch (4g) does not apply — there is only one item, and if the reviewer FAILs three times, escalate to the user. The commit message on PASS is `revise {spec-stem}: apply review revisions`.

For both branches, Steps 4a–4f apply as written; the differences above are the only deviations.

For each item (or group):

### 4a. Parallel execution policy (governs Step 4b–4f)

Two instructions overlap if their **write-sets** intersect — reads are free. Apply this policy to the execution loop below:

- Same-file writes → sequential.
- Different-file writes → parallel batch.
- **Concurrency limit:** max 3 implementer/reviewer pairs running concurrently — i.e., up to 3 items being implemented and verified at any given moment (so up to 6 in-flight subagents at peak: 3 implementers running while 3 reviewers verify previous batches, or 3 implementer+reviewer pairs interleaved).

Launch a parallel batch per the delivery contract (`${CLAUDE_PLUGIN_ROOT}/shared/dispatch-delivery.md`) — one Task call per item, batched in a single assistant message.

Announce batches before launching:

```
Running batch: L1, L2, L3 in parallel (no file overlap, 3-pair concurrency)
```

### 4b. Read the instruction

Read the full fix instruction file. Understand What, Why, Where, How, Expected Outcome, Scope.

### 4c. Classify: trivial or standard?

Triviality is **judgment-based by the orchestrator** using this rubric:

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

- **Resolve `subagent_type` from `agents.implementer.subagent_type`** (default `general-purpose`). The shipped `comb:*` review agents are read-only (`disallowedTools: Write, Edit, NotebookEdit`) and cannot serve as implementers. Users who want a project-specific writer override `agents.implementer` in their config.
- **Apply the delivery contract** in `${CLAUDE_PLUGIN_ROOT}/shared/dispatch-delivery.md` for the native/foreign framing and the model. The lane default is `models.fix.implementer_standard` for standard items, `models.fix.implementer_trivial` for trivial items; pass the resolved model as the Task call's `model` parameter.
- **Fresh agent per item** — no accumulated state.

**Implementer dispatch prompt (5-part order):**

```
You're an implementer. Execute this fix instruction precisely and completely.

## 1. Shared context

Repository: {project-root}
Branch: {branch}
Item: {reference_code} — {title}
Instruction file: {instruction-path}

## 2. Directives

The project's authoritative directives apply to this fix.

{If foreign (per the delivery contract), first: "These directives are authoritative. Read every listed file before starting. Cite by `file.md §N.N`."}

Read these directive files and cite as `file.md §N.N` if you depart from any rule (you should not need to depart):
- {plugin directive paths, if include_plugin_defaults}
- {user directive paths, if directives.user_path resolves}

Directives most relevant to this run:
- {primary directive paths from the "Surface relevant directives" step}

## Project conventions (observed baseline)

{Insert the block from `${CLAUDE_PLUGIN_ROOT}/shared/observed-baseline.md` — manifest path + verbatim paragraph — only when `paths.patterns` resolved.}

(Implementer note) Conform to the baseline UNLESS this instruction is implementing a sanctioned improvement or a new canonical pattern. Omit the whole block when no manifest resolved.

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

Report back in plain text with these sections in order:

### Files changed
- Files you changed (paths only, one per line)
- For each file: a 1-line summary of what changed

### Expected outcome
- Confirmation that the instruction's `## Expected Outcome` is met (yes/no with one-sentence rationale)

### Divergences  *(optional — include only if you deviated from the plan)*
If you deviated from any step in the instruction's `## How` section, list each deviation with a one-line rationale. Format:

- **<Step or section name>** — Departed because <rationale>. Did <what you did instead>.

If you executed the instruction as written, **omit this entire section**. The reviewer reads divergences first and evaluates each rationale; being explicit is how the run stays honest.

Do not include code in your reply — your edits are the artifact.
```

### 4e. Send to reviewer (always)

**Agent config (resolved per item):**

- **Pick the role from the plan file's `**Specialty:**` header.** The header lists one or more source agents (e.g., `code-reviewer`, `code-reviewer + consistency-auditor`). The orchestrator picks one based on the finding's primary lens: spec/scope drift → `consistency-auditor`; correctness/contracts/security → `code-reviewer`; over-engineering / dead code → `simplifier`; error handling / silent failures → `silent-failure-hunter`; test coverage / regression → `test-auditor`. If multiple are equally appropriate, pick the first in the header.

  **Single-revise-doc override:** if the instruction file is a `revise-*.md` (per Step 2.5 detection), bypass plan-file specialty parsing entirely. The reviewer role is always `consistency-auditor` (it is reviewing whether spec revisions match the spec/lens framing of the upstream review). The fallback chain still applies if `agents.consistency-auditor` isn't configured.

- **Fallback chain when the header is missing or the picked role isn't in the user's `agents` config:** `agents.test-auditor` → `agents.code-reviewer`. If neither resolves, abort the run with a clear error. `pattern-scanner` is generation-only and is never selected as the reviewer role.
- **Resolve `subagent_type`** from the picked role's `agents.<role>.subagent_type`. Honor the user's config.
- **Apply the delivery contract** in `${CLAUDE_PLUGIN_ROOT}/shared/dispatch-delivery.md` for the native/foreign framing and the model. The lane default is `models.fix.reviewer` (default `opus`); pass the resolved model as the Task call's `model` parameter.
- **Fresh agent.**

**Reviewer dispatch prompt (5-part order):**

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

{If foreign (per the delivery contract), first: "These directives are authoritative. Read every listed file before starting. Cite by `file.md §N.N`."}

Read these directive files and cite as `file.md §N.N` when raising findings:
- {plugin directive paths, if include_plugin_defaults}
- {user directive paths, if directives.user_path resolves}

Directives most relevant to this run:
- {primary directive paths from the "Surface relevant directives" step}

## Project conventions (observed baseline)

{Insert the block from `${CLAUDE_PLUGIN_ROOT}/shared/observed-baseline.md` — manifest path + verbatim paragraph — only when `paths.patterns` resolved.}

(Reviewer note) Conformance to the baseline is expected, but a deliberate improvement/migration or a new canonical introduced by this fix is NOT a compliance failure. Omit the whole block when no manifest resolved.

## 3. User focus for this run

{focus_brief if present, verbatim, with framing:}

Findings matching this focus are highest priority. Surface other issues too, but do not let the user's stated concerns slip.

## 4. Your job

Verify the implementation executed the plan. **The plan file is the contract** — your job is plan-compliance, not general code quality.

### Original Instruction

{instruction document content}

### Implementer's report

{implementer's summary, including any `## Divergences` section}

### How to verify

1. Read the plan's `## How` section. This is what the implementer was supposed to do.
2. Read the implementer's `## Divergences` section (if present). Each deviation must have a stated rationale.
3. Read the actual diff. The item's changes are **uncommitted** at this point — the orchestrator commits only after a PASS (Step 4f.1) — so `HEAD` is the state before this item.
   - `git diff HEAD -- <files reported by implementer>` shows the item's changes, staged and unstaged, against `HEAD`. Step 4a forms a parallel batch only from items with disjoint write-sets, so the path scope isolates this item from its batch-mates.
   - `git diff` never lists an untracked file, so a file the implementer created does not appear in it. Run `git status --porcelain -- <files reported by implementer>` and read any path marked `??` in full instead of diffing it.
   - When `fix.commit_per_item` is off, `HEAD` has not moved since the run started, so this diff accumulates the earlier items too. Lean on the implementer's reported file list and the plan's `## Where` section to scope your reading.

### Decision rule

- **PASS** — every step of the plan's `## How` is reflected in the diff, OR each divergence reported by the implementer has a sound rationale, AND the plan's `## Expected Outcome` is achieved, AND the diff stays within the plan's `## Scope`.
- **FAIL** — the diff doesn't match the plan and no rationale was given; OR the rationale doesn't justify the deviation; OR the Expected Outcome isn't achieved; OR the diff includes changes outside the plan's Scope (without a divergence rationale).

**A step you could not verify is not a FAIL on its own.** FAIL means you found a mismatch. When you could not confirm a step — the outcome needs a browser, the invariant needs a runtime, the artifact needs a rebuild — report the verdict your actual evidence supports and name the gap on the `Unverified:` line below. Do not convert a limit of your own into a FAIL.

You are **not** auditing for general code quality. You are **not** re-litigating the fix's design. The plan is the spec. Stay narrow.

## 5. Output format

Report `PASS` or `FAIL` on the first line with specifics:

- **PASS** — single line plus a 1–2-sentence confirmation of what you verified.
- **FAIL** — explain exactly what's wrong, with file:line citations.

Every verdict then carries a second line naming what you could **not** check, in the form `Unverified: {the step, outcome, or scope claim you could not confirm, and why}`. Write `Unverified: nothing — every step of the How was confirmed against the diff` when you confirmed all of it. The line is required; there is no blank and no omission. Name the specific gap: an Expected Outcome that needs a browser or a manual check, a runtime invariant you could not exercise, a generated artifact you could not rebuild, a file you could not open. This is not a third verdict — you still report PASS or FAIL.

### Discovered issues (optional)

If you spot a real problem in the same file(s) that's NOT part of this fix — a bug, type error, missing guard — report it under a `DISCOVERED` heading with:
- Short title
- File path and line(s)
- Brief description and suggested fix

Only flag genuine issues, not style preferences. One or two max. If nothing stands out, omit this heading.
```

### 4f. Handle the result

- **PASS** — proceed to **Step 4f.1** (commit), then announce complete and move on. When the reviewer's `Unverified:` line names anything other than `nothing`, announce the item as `{code} — PASS (partial verification: {what the reviewer could not check})` and carry that item into the end-of-run summary with the same note. This is a log line, not a gate: it does not block the commit, does not trigger a retry, and asks the user nothing.
- **FAIL** — read feedback. Adjust instructions if needed. Send a new implementer. Review again. **If 3 failures on one item:** if the item is classified trivial (per Step 4c), proceed to **Step 4g** (orchestrator escape hatch). Otherwise stop and ask the user.
- **DISCOVERED** — write a new instruction document in the same folder using the next available code (`X1`, `X2`...). The `X` prefix means "extra, found during execution" and is distinct from `D{n}` Deferred items emitted by review. Same format as all other items. Add to the end of the queue. Announce:
  ```
  M3 — PASS (5/15 complete)
  Discovered issue added: X1 — {title} (queue is now 16 items)
  Next: M4 — {title}
  ```

### 4f.1. Commit on PASS

If `fix.commit_per_item` is `true` (default) and the item produced code changes:

```bash
git add <files reported by implementer>
git commit -m "<finding-code>: <title>"
```

The orchestrator runs the commit, not the implementer subagent. Two safety rules:

- **Pre-flight already happened** at Step 1.5 — the only changes in the working tree at this point are the implementer's. (Or: the user chose `(c) proceed without per-item commits` and `commit_per_item` is effectively off for this run.)
- **On commit failure** (pre-commit hook reject, signing failure, conflict, anything non-zero): abort the run, surface the error, name the affected item. Do not retry blindly. The user investigates.

If `fix.commit_per_item` is `false`, skip the commit. Implementer changes accumulate in the working tree.

### 4g. Trivial escape hatch (orchestrator-applied fix after 3 failures)

If an item has failed 3 times AND was classified trivial at Step 4c (single-line edits, import reorders, comment fixes, lexical renames), the orchestrator may apply the fix inline rather than re-dispatch a fourth implementer. The escape hatch is **trivial only** — standard items that hit 3 failures escalate to the user as before.

When taking the escape hatch:

1. **Announce:**
   ```
   {code} — escape: orchestrator applying inline (3 implementer failures, trivial item)
   ```
2. **Apply the change directly** using `Edit` / `Write` tools, exactly per the plan's `## How` section.
3. **Run the reviewer step (4e) anyway.** The reviewer is the safety net; bypassing it because the orchestrator made the edit erodes the contract. The reviewer reads the same plan, the same diff, and applies the same plan-compliance decision rule. The implementer's report is replaced with a one-paragraph "Orchestrator applied inline. No divergences from plan."
4. **Commit on PASS per Step 4f.1.** Failure handling is the same — abort and surface to user if the commit fails.

If the reviewer FAILs on the orchestrator's inline application, escalate to the user. Do not retry inline a second time. (At that point you've burned 4 attempts on the same item; escalate.)

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
{code} — PASS (partial verification: {what the reviewer could not check}) ({N}/{total} complete)
```

At the end:

```
All {N} items complete:
  - C1: PASS
  - H1: PASS
  - H2: PASS (1 retry)
  - M4: PASS (partial verification: Expected Outcome needs a browser check)
  - L1-L3: PASS (parallel batch, trivial implementer)
  - X1: PASS (discovered during H2 review)
  - ...

{M} items deferred:
  - (deferred items listed by their review code, e.g., D1-D4)

{K} discovered during execution:
  - X1: {title} (found reviewing H2) — PASS
```

**Manifest notes (non-blocking).** Append any commit-based staleness note or semantic-refresh note recorded during this run.

## Ground rules

- **Fresh agents.** Each implementer and reviewer is a new subagent. No accumulated state.
- **The instruction is the spec.** Implementer follows it. Reviewer verifies against it. If the doc is wrong, fix the doc first, then re-implement.
- **Scope is sacred.** Implementers don't make changes outside scope. Reviewers flag scope violations as FAIL.
- **Don't loop forever.** Three failures means something's structurally wrong. Stop and ask.
- **Parallelize when safe.** Different writes = safe. Same file = sequential.
