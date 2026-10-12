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
- `models.plan` and `paths.base_branch` (for the X-item planner dispatch, Step 4f)
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

## Step 1.6: Record the run baseline

Three facts, recorded once here and compared against by Steps 4d.1, 4f.0, and 4f.1. Record them whether or not Step 1.5 ran.

- **Verification baseline** — run the project's verification once, chosen the way `/comb:review` Step 5 chooses it: commands named in `CLAUDE.md`, else the project's build or package manifest(s); pipe stderr with `2>&1`. Record the exit code and the failing lines. When neither names a command, record `verification: none configured` and 4f.0 skips. When it is red before any item runs, ask once: proceed (a 4f.0 failure whose failing lines are these is not the item's) or abort. In `/comb:the-desert` this is logged, not asked; the sweep proceeds.
- **Dirty baseline `D0`** — `git status --porcelain` as the tree stands after that run (so artefacts the verification wrote are in it). Paths in `D0` are the user's and are never re-examined by this run's checks. An item whose write-set intersects `D0` is not dispatched: announce `{code} — not dispatched: ## Where overlaps uncommitted changes ({paths}); commit or stash them first` and move on, so the revert and the stage never touch a user's edit.
- **`HEAD_expected`** — `git rev-parse HEAD`. Every commit this run makes (4f.1) advances it; any other movement is an implementer committing.

The **run's own paths** are everything under the instruction folder: `## Attempts` appends and X-item files land there. They are never counted by a check.

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

- **Per-finding folder:** today's execution loop (Steps 4a–4f below) runs once per instruction file.
- **Single revise-doc folder:** the loop runs **exactly once** against the single `revise-*.md`. The item is **always classified standard** (it is a multi-finding spec edit, not a single-line code fix), its write-set is the `**Target spec:**` path, and the reviewer role follows the single-revise-doc override in Step 4e (`consistency-auditor`, with 4e's fallback chain). If the reviewer FAILs three times, escalate to the user. The commit message on PASS is `revise {spec-stem}: apply review revisions`.

For both branches, Steps 4a–4f apply as written; the differences above are the only deviations.

For each item (or group):

### 4a. Parallel execution policy (governs Step 4b–4f)

An item's **write-set** is the set of file paths named in its instruction's `## Where`, line ranges dropped (a directory entry stands for everything under it). Two instructions overlap if their write-sets intersect — reads are free. Apply this policy to the execution loop below:

- Same-file writes → sequential.
- Different-file writes → parallel batch.
- **Concurrency limit:** max 3 items in flight at any moment.

Three terms the git checks use:

- An item is **in flight** from its implementer dispatch until its commit lands (4f.1) or, after a stop, until the user resolves it. Implementer stage, reviewer stage, PASS awaiting verification, and stopped all count; a committed item does not. When the run makes no commits (`commit_per_item` off, or option (c) at Step 1.5), an item leaves flight when it is announced complete, and its reported paths join `D0` at that moment.
- The **allowed set** is `D0` ∪ the run's own paths ∪ the write-sets of every in-flight item (Step 1.6 for the first two). It is what the working tree may contain at any moment.
- **Stop the item** means dispatch no further stage for it and leave its edits in place; its write-set stays in the allowed set until the user resolves it. **Stop the batch** means dispatch nothing further for any item in the batch, let the implementers already running return, print the per-item status list from 4f.1 for the batch, and hand the tree to the user. A HEAD stop (4d.1 check 1) stops the batch: `HEAD_expected` is stale for every batch-mate until the user resolves it. The orchestrator cannot interrupt a running agent; a stop is a promise about what it will not start.

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
- **HEAD is tracked per run, not per item:** `HEAD_expected` (Step 1.6) is what 4d.1 compares against when the implementer returns; this run's own commits advance it, so a batch-mate's commit is not mistaken for the implementer's.

**Implementer dispatch prompt (shared context + briefs):**

```
You're an implementer. Execute this fix instruction precisely and completely.

## 1. Shared context

Repository: {project-root}
Branch: {branch}
Item: {reference_code} — {title}
Instruction file: {instruction-path}

Read these first, in order: ${CLAUDE_PLUGIN_ROOT}/shared/fix-implementer-brief.md, {run brief path printed by `comb.py brief` (skill fix, role implementer)}
```

### 4d.1. When the implementer returns

Three git checks, before any reviewer is dispatched:

1. **HEAD unchanged.** `git rev-parse HEAD` equals `HEAD_expected` (Step 1.6, advanced only by this run's 4f.1 commits). If not, the implementer committed. Stop the batch (4a), do not revert (a commit is not the orchestrator's to undo), and surface: `{code} — stopped: HEAD moved during implementer ({HEAD_expected} → {new}); resolve by hand before continuing`.
2. **Reported list equals the tree inside the write-set.** `git status --porcelain -- <paths in ## Where>`, read as a set of paths, must equal the reported list. A dirty path inside `## Where` that was not reported, or a reported path that is not dirty → stop the item and surface which. A reported path outside `## Where` → stop the item; if that path lies inside a batch-mate's write-set → stop the batch. The reported list is what the reviewer scopes, the revert deletes, and the commit stages, so it must be exact; write-sets are disjoint within a batch, so attribution inside `## Where` is exact too.
3. **Tree inside the allowed set.** Every path in `git status --porcelain` must be in the allowed set (4a). A path outside → stop the batch and surface: `batch stopped: {paths} changed outside every in-flight write-set ({codes})`. Do not guess which item did it.

Bound: these checks compare paths and one SHA. They do not read diffs; the reviewer does. A write inside a batch-mate's `## Where` by the wrong implementer is indistinguishable by path from the batch-mate's own work; the batch-mate's reviewer sees it as a stray hunk, and its `Batch-mates' write-sets:` line is what lets it report a possible spill from `{code}` instead of failing on sight.

### 4e. Send to reviewer (always)

**Agent config (resolved per item):**

- **Pick the role from the plan file's `**Specialty:**` header.** The header lists one or more source agents (e.g., `code-reviewer`, `code-reviewer + consistency-auditor`). The orchestrator picks one based on the finding's primary lens: spec/scope drift → `consistency-auditor`; correctness/contracts/security → `code-reviewer`; over-engineering / dead code → `simplifier`; error handling / silent failures → `silent-failure-hunter`; test coverage / regression → `test-auditor`. If multiple are equally appropriate, pick the first in the header.

  **Single-revise-doc override:** if the instruction file is a `revise-*.md` (per Step 2.5 detection), bypass plan-file specialty parsing entirely. The reviewer role is always `consistency-auditor` (it is reviewing whether spec revisions match the spec/lens framing of the upstream review). The fallback chain still applies if `agents.consistency-auditor` isn't configured.

- **Fallback chain when the header is missing or the picked role isn't in the user's `agents` config:** `agents.test-auditor` → `agents.code-reviewer`. If neither resolves, abort the run with a clear error.
- **Resolve `subagent_type`** from the picked role's `agents.<role>.subagent_type`. Honor the user's config.
- **Apply the delivery contract** in `${CLAUDE_PLUGIN_ROOT}/shared/dispatch-delivery.md` for the native/foreign framing and the model. The lane default is `models.fix.reviewer` (default `opus`); pass the resolved model as the Agent call's `model` parameter.
- **Fresh agent.**

**Reviewer dispatch prompt (shared context + briefs + implementer's report):**

```
You're a code reviewer verifying a fix against its original instruction.

## 1. Shared context

Repository: {project-root}
Branch: {branch}
Item: {reference_code} — {title}
Instruction file: {instruction-path}
Batch-mates' write-sets: {for each other in-flight item: "{code}: {paths}"; or "none — this item runs alone"}

Read these first, in order: ${CLAUDE_PLUGIN_ROOT}/shared/fix-reviewer-brief.md, {run brief path printed by `comb.py brief` (skill fix, role = the picked reviewer role)}

### Implementer's report

{implementer's summary, including any `### Divergences` section}
```

### 4f. Handle the result

- **PASS** — proceed to **Step 4f.0** (verify), then **4f.1** (commit), then announce complete and move on. When the reviewer's `Unverified:` line names anything other than `nothing`, announce the item as `{code} — PASS (partial verification: {what the reviewer could not check})` and carry that note into the end-of-run summary. This is a log line, not a gate: it does not block the commit and asks the user nothing.
- **FAIL** — in this order:
  1. **Revert the attempt.** The reported list equals the item's dirty footprint inside `## Where` (4d.1 check 2), so: `git checkout -- <reported files>`; delete every reported path that `git status --porcelain -- <reported files>` marks `??`; confirm `git status --porcelain -- <paths in ## Where>` prints nothing. Never touch a path inside another in-flight item's write-set. A retry starts from the tree the first attempt started from — "fresh agent" is only true when the tree is fresh too.
  2. **Record the attempt.** Append to the instruction file (create the section on the first FAIL):
     ```markdown
     ## Attempts

     ### Attempt {n} — FAIL
     **Reviewer:** {the FAIL text, verbatim or trimmed to its specifics}
     **Plan change:** {what you changed in `## How` and why | none}
     ```
     The section is append-only. If the instruction is wrong, change `## How` and say so here; the next reviewer verifies against the changed How and can see it changed.
  3. **Retry.** Send a new implementer (Step 4d), then review again (4e). **After three FAILs on one item, stop and ask the user** — trivial or standard alike — printing the per-item status list from 4f.1 first, so the other in-flight items are not lost in the question. Three failures mean the instruction or the classification is wrong, and that is the user's call. A 4f.0 verification FAIL counts as one of the three.
- **DISCOVERED** — the reviewer found an issue outside this fix. The orchestrator does not write the instruction: it dispatches a planner for it, exactly as `/comb:plan` Step 6 does for one finding. Read `${CLAUDE_PLUGIN_ROOT}/skills/plan/SKILL.md` for the planner dispatch prompt (code-shaped flow) and dispatch it with the DISCOVERED block as the finding, the next free `X{n}` as the reference code, the same output folder, and `**Verified (from the review report):** none — discovered during fix`. The planner prompt's other inputs: `Base:` is `paths.base_branch`; `Report under planning:` is `none — discovered during fix by {code}'s reviewer`; the finding's severity is Medium unless the block says otherwise; its source agent (for the plan file's `**Specialty:**`) is the reviewing role; the model is `models.plan` (`models.the_desert` in a sweep). The file it writes lands in the instruction folder, which is the run's own. The `X` prefix means "extra, found during execution" and is distinct from `D{n}` Deferred items. Add the resulting file to the end of the queue (its `Finding status` applies like any other). Announce:
  ```
  M3 — PASS (5/15 complete)
  Discovered issue added: X1 — {title} (planned by {planner model}; queue is now 16 items)
  Next: M4 — {title}
  ```

**Plugin root for the planner prompt.** The plan skill file you Read above is not variable-substituted, and the plugin-root placeholder is not a shell variable. In that file the placeholder is written as a dollar sign, an opening brace, the name CLAUDE_PLUGIN_ROOT, and a closing brace. Wherever you see it — in the `manifest.py` command lines, and in every Read target under `shared/`, `directives/`, and `skills/` — replace it with this literal path: `${CLAUDE_PLUGIN_ROOT}`. A `manifest.py` command run with the placeholder unexpanded fails and would silently fall back to delivering the full manifest.

### 4f.0. Verify before commit

Run the verification command recorded at Step 1.6 (`2>&1`). When Step 1.6 recorded `none configured`, skip with the note `verification: none configured` on the item's progress line.

**When it runs.** Only when no implementer of the batch is in flight: reviewers are read-only, so the tree is quiescent then, and the suite does not see a batch-mate's half-written file. A PASSed item waits for that point before verifying and committing; a batch whose items all PASS is verified once, which is also the cheap choice when the command is slow.

**Reading the result.**

- Exit zero → every waiting item proceeds to 4f.1.
- Failing lines identical to the Step 1.6 baseline → not caused by this run; proceed as if green and carry `verification: red before the run (unchanged)` on the item's progress line.
- Otherwise the failing lines not in the baseline are the **new failure**. One that names a path inside an in-flight item's write-set → that item's **FAIL**: a PASSed item takes the 4f FAIL path now; an item still under review takes it when its reviewer returns, whatever the reviewer said. In both cases the Attempt's `**Reviewer:**` line reads `verification: <command> exited <n>` followed by the relevant lines.
- A new failure that names no in-flight write-set (test-file paths, or none) → every PASSed item waiting at this point takes the FAIL.
- After the attributed item's revert (4f step 1) and before its retry is dispatched, re-run this step for the items still waiting; they commit on green. The retry then starts, and later items wait for quiescence as before.

No commit lands on red.

Bound: this runs the project's own command and reads its exit code and output. It does not decide what the right command is beyond review Step 5's rule, does not map test files to the sources they cover, and does not interpret output beyond comparing lines with the baseline and matching paths against write-sets. When a suite reports test-file paths rather than sources, the last rule can fail a whole batch for one item's breakage; sequential items avoid that at the cost of one run per item.

### 4f.1. Commit on PASS

If `fix.commit_per_item` is `true` (default) and the item produced code changes:

```bash
git add <files reported by implementer>
git commit -m "<finding-code>: <title>"
```

The orchestrator runs the commit, not the implementer subagent. Three rules:

- **Stage from the reported list.** Step 4d.1 check 2 confirmed it equals the item's dirty footprint inside `## Where`, so it is complete for this item. (When the user chose `(c) proceed without per-item commits` at Step 1.5, `commit_per_item` is effectively off for this run.)
- **After the commit:** advance `HEAD_expected` to the new `git rev-parse HEAD`. Then `git status --porcelain` minus the allowed set (4a; this item is no longer in flight) must be empty. Anything left → stop the run and surface: `tree not clean after {code}'s commit: {paths}` (a hook that rewrites files, or an edit nobody reported).
- **On commit failure** (pre-commit hook reject, signing failure, conflict, anything non-zero): abort the run and surface the error, then print the per-item status list so nothing is lost (the same list a batch stop prints, 4a):
  ```
  {code} — committed
  {code} — PASS, uncommitted ({files})
  {code} — in progress ({implementer | reviewer})
  {code} — stopped ({why})
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
