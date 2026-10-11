---
name: fix
description: Use after /comb:plan has produced instruction files and the user wants them executed. The user must invoke this explicitly — Claude does not auto-trigger it because it edits code.
argument-hint: "[instruction-folder] [focus brief]"
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Agent
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

**Load the PATTERNS manifest.** If `paths.patterns` resolves, record its path; do not read it. The excerpt is cut after Step 2.5 (below), which is after the pre-flight. If absent or `null`, skip — graceful no-op.

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

**Not-reproduced items.** Read each per-finding file's `**Finding status:**` header. Items marked `not reproduced` are listed separately and not queued:

```
{K} not reproduced by the planner (not queued): {codes with titles}
Say "queue {code}" to run one anyway.
```

A file without the header predates this field and queues normally. In `/comb:the-desert` these items are skipped and reported in the final summary; nothing asks.

**Cut the manifest excerpt** (only when `paths.patterns` resolved), per `${CLAUDE_PLUGIN_ROOT}/shared/manifest-slicing.md`, with the instruction folder as the touched text (the script reads every `.md` in it, so this covers per-finding files and the single revise doc alike):

```
python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/manifest.py" excerpt --skill fix --manifest <paths.patterns> --touched-from <instruction folder>
```

Run it from the project root. An X-item discovered mid-run (Step 4) was not in the folder when the excerpt was cut; its implementer and reviewer still get the excerpt, and its banner lists the omitted sections by line range for them to read if needed.

Record `run`, `excerpt`, the log line, and `stale`. On the contract's fallback condition, print the fallback notice and deliver the full path alone.

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
- **Single revise-doc folder:** the loop runs **exactly once** against the single `revise-*.md`. The item is **always classified standard** (it is a multi-finding spec edit, not a single-line code fix), and the reviewer role follows the single-revise-doc override in Step 4e (`consistency-auditor`, with 4e's fallback chain). If the reviewer FAILs three times, escalate to the user. The commit message on PASS is `revise {spec-stem}: apply review revisions`.

For both branches, Steps 4a–4f apply as written; the differences above are the only deviations.

For each item (or group):

### 4a. Parallel execution policy (governs Step 4b–4f)

An item's **write-set** is the set of paths in its instruction's `## Where`. Two instructions overlap if their write-sets intersect — reads are free. The write-set is also what Step 4d.1's tree check compares the working tree against after each implementer returns. Apply this policy to the execution loop below:

- Same-file writes → sequential.
- Different-file writes → parallel batch.
- **Concurrency limit:** max 3 items in flight (implementer or reviewer stage) at any moment.

Launch a parallel batch per the delivery contract (`${CLAUDE_PLUGIN_ROOT}/shared/dispatch-delivery.md`) — one Agent call per item, batched in a single assistant message.

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

For trivial items: announce "(trivial — implementer `{resolved models.fix.implementer_trivial}`, reviewer `{resolved models.fix.reviewer}`)" and proceed. The reviewer runs for every item.

### 4d. Send to implementer

**Agent config (resolved per item):**

- **Resolve `subagent_type` from `agents.implementer.subagent_type`** (default `comb:implementer`, the shipped writer with boundaries). The five review agents are read-only and cannot serve as implementers. A project with its own writer overrides `agents.implementer`; it is then foreign per the delivery contract and receives the role's `when_to_use` as its specialty statement, which carries the same boundaries.
- **Apply the delivery contract** in `${CLAUDE_PLUGIN_ROOT}/shared/dispatch-delivery.md` for the native/foreign framing and the model. The lane default is `models.fix.implementer_standard` for standard items, `models.fix.implementer_trivial` for trivial items; pass the resolved model as the Agent call's `model` parameter.
- **Fresh agent per item** — no accumulated state.
- **Record HEAD before dispatch:** `git rev-parse HEAD`, kept per item as `HEAD0`. Step 4d.1 compares it when the implementer returns.

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

Read the directives this instruction cites in its `## Directive citations`, plus those listed under "most relevant" below. Cite as `file.md §N.N` if you depart from any rule (you should not need to depart). The full list, for reference:
- {plugin directive paths, if include_plugin_defaults}
- {user directive paths, if directives.user_path resolves}

Directives most relevant to this run:
- {primary directive paths from the "Surface relevant directives" step}

## Project conventions (observed baseline)

{Insert the block from `${CLAUDE_PLUGIN_ROOT}/shared/observed-baseline.md` — excerpt path + manifest path + verbatim paragraph, or the fallback form — only when `paths.patterns` resolved.}

(Implementer note) Conform to the baseline UNLESS this instruction is implementing a sanctioned improvement or a new canonical pattern. Omit the whole block when no manifest resolved.

## 3. User focus for this run

{focus_brief if present, verbatim; omit the section when empty.}

## 4. Your job

Execute the fix instruction at the path above. The instruction is the spec — do exactly what it says.

### Steps

1. Read the instruction file, then the affected file(s) named in its "Where" section; read `## Attempts` if present — it records what failed before and what changed in the plan
2. Apply the exact changes from the "How" section
3. Stay strictly within the documented "Scope" — no drive-by refactors, no bonus cleanup
4. Confirm the "Expected Outcome" is met; if its `Check:` line names a command, run it and report the result

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

### 4d.1. When the implementer returns

Two git checks, before any reviewer is dispatched:

1. **HEAD unchanged.** `git rev-parse HEAD` equals the item's `HEAD0`. If not, the implementer committed. Stop the item, do not revert (a commit is not the orchestrator's to undo), and surface: `{code} — stopped: HEAD moved during implementer ({HEAD0} → {new}); resolve by hand before continuing`.
2. **Tree inside the write-sets.** Every path in `git status --porcelain` must be in the union of the in-flight items' write-sets (`## Where`) and their reported file lists. A path outside the union → stop the batch and surface: `batch stopped: {paths} changed outside every in-flight write-set ({codes})`. Do not guess which item did it.

Bound: these checks compare paths and one SHA. They do not read diffs; the reviewer does.

### 4e. Send to reviewer (always)

**Agent config (resolved per item):**

- **Pick the role from the plan file's `**Specialty:**` header.** The header lists one or more source agents (e.g., `code-reviewer`, `code-reviewer + consistency-auditor`). The orchestrator picks one based on the finding's primary lens: spec/scope drift → `consistency-auditor`; correctness/contracts/security → `code-reviewer`; over-engineering / dead code → `simplifier`; error handling / silent failures → `silent-failure-hunter`; test coverage / regression → `test-auditor`. If multiple are equally appropriate, pick the first in the header.

  **Single-revise-doc override:** if the instruction file is a `revise-*.md` (per Step 2.5 detection), bypass plan-file specialty parsing entirely. The reviewer role is always `consistency-auditor` (it is reviewing whether spec revisions match the spec/lens framing of the upstream review). The fallback chain still applies if `agents.consistency-auditor` isn't configured.

- **Fallback chain when the header is missing or the picked role isn't in the user's `agents` config:** `agents.test-auditor` → `agents.code-reviewer`. If neither resolves, abort the run with a clear error.
- **Resolve `subagent_type`** from the picked role's `agents.<role>.subagent_type`. Honor the user's config.
- **Apply the delivery contract** in `${CLAUDE_PLUGIN_ROOT}/shared/dispatch-delivery.md` for the native/foreign framing and the model. The lane default is `models.fix.reviewer` (default `opus`); pass the resolved model as the Agent call's `model` parameter.
- **Fresh agent.**

**Reviewer dispatch prompt (5-part order):**

```
You're a code reviewer verifying a fix against its original instruction.

## 1. Shared context

Repository: {project-root}
Branch: {branch}
Item: {reference_code} — {title}
Instruction file: {instruction-path}
Batch-mates' write-sets: {for each other in-flight item: "{code}: {paths}"; or "none — this item runs alone"}

## 2. Directives

The project's authoritative directives apply to your verification.

{If foreign (per the delivery contract), first: "These directives are authoritative. Read every listed file before starting. Cite by `file.md §N.N`."}

Read these directive files and cite as `file.md §N.N` when raising findings:
- {plugin directive paths, if include_plugin_defaults}
- {user directive paths, if directives.user_path resolves}

Directives most relevant to this run:
- {primary directive paths from the "Surface relevant directives" step}

## Project conventions (observed baseline)

{Insert the block from `${CLAUDE_PLUGIN_ROOT}/shared/observed-baseline.md` — excerpt path + manifest path + verbatim paragraph, or the fallback form — only when `paths.patterns` resolved.}

(Reviewer note) Conformance to the baseline is expected, but a deliberate improvement/migration or a new canonical introduced by this fix is NOT a compliance failure. Omit the whole block when no manifest resolved.

## 3. User focus for this run

{focus_brief if present, verbatim; omit the section when empty.}

## 4. Your job

Verify the implementation executed the plan. **The plan file is the contract** (read it at the path above) — your job is plan-compliance, not general code quality.

### Implementer's report

{implementer's summary, including any `## Divergences` section}

### How to verify

1. Read the instruction file; its `## How` section is what the implementer was supposed to do. Read its `## Attempts` section if present: it records earlier FAILs on this item and any change the orchestrator made to `## How` — verify against the current `## How`.
2. Read the implementer's `## Divergences` section (if present). Each deviation must have a stated rationale.
3. Read the actual diff. The item's changes are **uncommitted** at this point — the orchestrator commits only after a PASS (Step 4f.1) — so `HEAD` is the state before this item.
   - `git diff HEAD -- <files reported by implementer>` shows the item's changes, staged and unstaged, against `HEAD`. Step 4a forms a parallel batch only from items with disjoint write-sets, so the path scope isolates this item from its batch-mates.
   - `git diff` never lists an untracked file, so a file the implementer created does not appear in it. Run `git status --porcelain -- <files reported by implementer>` and read any path marked `??` in full instead of diffing it.
   - When `fix.commit_per_item` is off, `HEAD` has not moved since the run started, so this diff accumulates the earlier items too. Lean on the implementer's reported file list and the plan's `## Where` section to scope your reading.
4. **Run the `Check:` line** under `## Expected Outcome`, from the project root. A non-zero exit, or an observable that is absent, is a FAIL regardless of how faithfully the diff matches `## How` — the plan was wrong or the fix did not land. `Check: none — <why>` means nothing to run: name that on your `Unverified:` line. A plan with no `Check:` line predates this field; treat it as `none — not stated (pre-0.14.0 plan)`.

### Decision rule

- **PASS** — every step of the plan's `## How` is reflected in the diff, OR each divergence reported by the implementer has a sound rationale, AND the plan's `## Expected Outcome` is achieved — its `Check:` ran and passed, or was `none`, AND the diff stays within the plan's `## Scope`.
- **FAIL** — the diff doesn't match the plan and no rationale was given; OR the rationale doesn't justify the deviation; OR the Expected Outcome isn't achieved (a `Check:` that ran and failed is always this case); OR the diff includes changes outside the plan's Scope (without a divergence rationale).

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

- **PASS** — proceed to **Step 4f.0** (verify), then **4f.1** (commit), then announce complete and move on. When the reviewer's `Unverified:` line names anything other than `nothing`, announce the item as `{code} — PASS (partial verification: {what the reviewer could not check})` and carry that note into the end-of-run summary. This is a log line, not a gate: it does not block the commit and asks the user nothing.
- **FAIL** — in this order:
  1. **Revert the attempt.** `git checkout -- <files reported by the implementer>`; delete every reported path that `git status --porcelain -- <files>` marks `??`; confirm `git status --porcelain -- <files>` prints nothing. A retry starts from the tree the first attempt started from — "fresh agent" is only true when the tree is fresh too.
  2. **Record the attempt.** Append to the instruction file (create the section on the first FAIL):
     ```markdown
     ## Attempts

     ### Attempt {n} — FAIL
     **Reviewer:** {the FAIL text, verbatim or trimmed to its specifics}
     **Plan change:** {what you changed in `## How` and why | none}
     ```
     The section is append-only. If the instruction is wrong, change `## How` and say so here; the next reviewer verifies against the changed How and can see it changed.
  3. **Retry.** Send a new implementer (Step 4d), then review again (4e). **After three FAILs on one item, stop and ask the user** — trivial or standard alike. Three failures mean the instruction or the classification is wrong, and that is the user's call.
- **DISCOVERED** — the reviewer found an issue outside this fix. The orchestrator does not write the instruction: it dispatches a planner for it, exactly as `/comb:plan` Step 6 does for one finding. Read `${CLAUDE_PLUGIN_ROOT}/skills/plan/SKILL.md` for the planner dispatch prompt (code-shaped flow) and dispatch it with the DISCOVERED block as the finding, the next free `X{n}` as the reference code, the same output folder, and `**Verified (from the review report):** none — discovered during fix`. The `X` prefix means "extra, found during execution" and is distinct from `D{n}` Deferred items. Add the resulting file to the end of the queue (its `Finding status` applies like any other). Announce:
  ```
  M3 — PASS (5/15 complete)
  Discovered issue added: X1 — {title} (planned by {planner model}; queue is now 16 items)
  Next: M4 — {title}
  ```

**Plugin root for the planner prompt.** The plan skill file you Read above is not variable-substituted, and the plugin-root placeholder is not a shell variable. In that file the placeholder is written as a dollar sign, an opening brace, the name CLAUDE_PLUGIN_ROOT, and a closing brace. Wherever you see it — in the `manifest.py` command lines, and in every Read target under `shared/`, `directives/`, and `skills/` — replace it with this literal path: `${CLAUDE_PLUGIN_ROOT}`. A `manifest.py` command run with the placeholder unexpanded fails and would silently fall back to delivering the full manifest.

### 4f.0. Verify before commit

Run the project's verification — typecheck, tests, lint — chosen the way `/comb:review` Step 5 chooses it: commands named in `CLAUDE.md`, else the project's build or package manifest(s); when neither names one, skip with the note `verification: none configured` on the item's progress line. Pipe stderr with `2>&1`.

- Exit zero → proceed to 4f.1.
- Non-zero → the item is a **FAIL**: take the 4f FAIL path with the command's output as the reviewer feedback (the `**Reviewer:**` line of the Attempt reads `verification: <command> exited <n>` followed by the output's relevant lines).

When the command is slow, run it once per parallel batch after every item in the batch has a PASS and before any of them commits. Attribute a failure by the file paths in its output to the items whose write-sets contain them; when it names none, every PASSed item in the batch takes the FAIL. No commit lands on red.

Bound: this runs the project's own commands and reads their exit codes. It does not decide what the right command is beyond review Step 5's rule, and it does not interpret output beyond path matching.

### 4f.1. Commit on PASS

If `fix.commit_per_item` is `true` (default) and the item produced code changes:

```bash
git add <files reported by implementer>
git commit -m "<finding-code>: <title>"
```

The orchestrator runs the commit, not the implementer subagent. Three rules:

- **Stage from the reported list.** Step 4d.1 already confirmed the tree holds nothing outside the in-flight write-sets, so the reported list is complete for this item. (When the user chose `(c) proceed without per-item commits` at Step 1.5, `commit_per_item` is effectively off for this run.)
- **After the commit:** `git status --porcelain` minus the paths of the other in-flight items must be empty. Anything left → stop the run and surface: `tree not clean after {code}'s commit: {paths}` (a hook that rewrites files, or an edit nobody reported).
- **On commit failure** (pre-commit hook reject, signing failure, conflict, anything non-zero): abort the run and surface the error, then print one line per in-flight item so nothing is lost:
  ```
  {code} — committed
  {code} — PASS, uncommitted ({files})
  {code} — in progress ({implementer | reviewer})
  ```
  Do not retry blindly. The user investigates.

If `fix.commit_per_item` is `false`, skip the commit. Implementer changes accumulate in the working tree.

## Step 5: Progress tracking

After each item:

```
{code} — PASS ({N}/{total} complete)
Next: {next_code} — {title}
```

With extras:
```
{code} — PASS after 1 retry ({N}/{total} complete)
{code} — PASS after 1 retry (plan adjusted) ({N}/{total} complete)
{code} — PASS, trivial implementer ({N}/{total} complete)
{code} — PASS, verification: none configured ({N}/{total} complete)
{code} — PASS (partial verification: {what the reviewer could not check}) ({N}/{total} complete)
```

`(plan adjusted)` appears when any `## Attempts` entry's **Plan change** is not `none`; the plan the commit satisfies is not the plan the planner wrote, and the summary says so.

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

{J} not reproduced by the planner (not run):
  - M7: {title} — {planner's looked-for text, one line}
```

**Manifest notes (non-blocking).** Append the excerpt log line verbatim, then any staleness note (`stale: yes` → `PATTERNS manifest may be stale — consider re-running /comb:patterns.`; `unknown` → `PATTERNS staleness unknown (<detail>).`) or semantic-refresh note recorded during this run. Then, last of all: `python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/manifest.py" clean --run <run>`.

## Ground rules

- **Fresh agents, fresh tree.** Each implementer and reviewer is a new subagent, and a retry starts after the failed attempt is reverted (4f). No accumulated state in either.
- **Git is the orchestrator's.** Implementers never commit; the HEAD check (4d.1) stops an item whose implementer did.
- **The instruction is the spec.** Implementer follows it. Reviewer verifies against it. If the doc is wrong, fix the doc first, then re-implement.
- **Scope is sacred.** Implementers don't make changes outside scope. Reviewers flag scope violations as FAIL.
- **Don't loop forever.** Three failures on one item means the instruction or its classification is wrong. Stop and ask — there is no orchestrator-applied fix.
- **Parallelize when safe.** Different writes = safe. Same file = sequential.
