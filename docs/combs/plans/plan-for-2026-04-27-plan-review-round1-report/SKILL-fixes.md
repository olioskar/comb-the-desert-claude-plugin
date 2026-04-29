# SKILL-fixes — consolidated fix instructions

**Findings covered:** C1, C2, C3, H4, H5, H6, M2, M3, M5, M6, M9, L1, L2, L4, L5, L18
**Target file:** `docs/superpowers/plans/2026-04-27-comb-the-desert-plugin.md`
**Affected tasks:** 21 (review), 22 (plan), 23 (fix), 24 (the-desert)

## What

- **C1:** Replace hardcoded `subagent_type: general-purpose` in `/comb:plan` and `/comb:fix` with a `subagent_type` resolved from `agents.<role>` config; embed full directive contents whenever the resolved type is not in the shipped allowlist.
- **C2:** Insert the same model-resolution rule used in `/comb:review` (`agents.<role>.model` if set, else lane default) into `/comb:plan` and `/comb:fix`.
- **C3:** Add a "Surface relevant directives" sub-step to all four skill bodies that lowercases the focus brief and substring-matches against directive filenames, then flags the matches as primary in dispatch prompts.
- **H4:** Tighten the markdown-only palette restriction in `/comb:review` so it explicitly invokes `git diff --name-only` and triggers automatically rather than as user-instructed.
- **H5:** Mirror Task 21's allowlist enumeration into Tasks 22 and 23 so the foreign-vs-shipped check is an allowlist match (not a prefix check) wherever subagents are dispatched.
- **H6:** Restructure the planner / implementer / reviewer dispatch prompts in Tasks 22 and 23 into the spec §7.1.5 five-part order: shared context, directives, focus brief, agent-specific instructions, output format.
- **M2:** Replace `Agent` with `Task` in every `allowed-tools` list across all four skill bodies.
- **M3:** Replace every "in parallel using `run_in_background: true`" instruction with "in parallel by issuing multiple Task tool calls in a single assistant message."
- **M5:** Reframe the verification step in `/comb:review` from hardcoded `npx tsc`/`npx vitest` to project-appropriate detection.
- **M6:** Add a self-describing note to `/comb:review` Step 3 documenting the §7.1.4 contract (judgment-based picking, hard cap 5, soft floor 1) so the body itself states the verifiable rule.
- **M9:** Disambiguate the "max 3 pairs concurrent" sentence in `/comb:fix` to "max 3 implementer/reviewer pairs running concurrently — i.e., up to 3 items being implemented and verified at any given moment."
- **L1:** Add a one-line worktree note next to `git rev-parse --show-toplevel` in all four skill bodies.
- **L2:** Add the "judgment-based" framing to the triviality classification in `/comb:fix` Step 3b.
- **L4:** Add `WebFetch` to `/comb:plan` and `/comb:fix` `allowed-tools` lists for parity with `/comb:review` and `/comb:the-desert`.
- **L5:** Move the "Parallel execution" policy in `/comb:fix` into Step 3 (or before it) so it visibly governs the loop instead of trailing it.
- **L18:** No skill-body change. Add a CHANGELOG/README note that skills intentionally omit the `model:` frontmatter field so the user's session model runs the orchestrator while dispatched agents use `models.<lane>`.

## Why

The four skill bodies are the only place the orchestrator's runtime contract is encoded — the agent files describe specialty behavior, the directives describe policy, and the config carries data, but only the skill bodies tell Claude *how to assemble dispatches*. Most of these findings stem from the same root cause: contracts laid down in spec §4.3 (per-agent `model` override), §5.4 (allowlist match + full directive contents for foreign agents), §7.1.4 (judgment-based picking, hard cap 5), §7.1.5 (5-part dispatch prompt), §7.3 (markdown-only auto-detection), and §8 (focus-brief → directive substring matching) were captured in `/comb:review` (Task 21) but not propagated to `/comb:plan` (Task 22) and `/comb:fix` (Task 23). Plus a few correctness/terminology fixes (`Task` not `Agent`, Bash-tool parameter not Task-tool parameter, project-appropriate verification commands) that span all four bodies. Fixing these together keeps the four skills coherent: they all read the same config, build the same shape of prompt, and dispatch the same way.

## Where

**Task 21 (`skills/review/SKILL.md`)** — plan lines ~1647–1935. Edits in:
- Step 1 (Load config) — line ~1701: worthwhile add the worktree note.
- Step 2 (Gather context) — no behavioral change; spec-§7.1.5 alignment already roughly here.
- Step 3 (Pick agents) — lines ~1737–1789:
  - H4: replace the markdown-only sentence (line ~1750).
  - C3: add a "Surface relevant directives" sub-step before the dispatch block.
  - M6: add a self-describing rule line about hard cap 5 / soft floor 1 / judgment-based picking.
  - L1: confirm the worktree note covers Step 1's `git rev-parse` (already in Step 1).
- Dispatch block (still inside Step 3) — line ~1789: M3 fix on the "Launch all dispatches in parallel" sentence.
- Frontmatter — lines ~1661–1674: M2 fix on `allowed-tools` (`Agent` → `Task`).
- Step 4 (Run mechanical verification checks) — lines ~1791–1802: M5 reframe.

**Task 22 (`skills/plan/SKILL.md`)** — plan lines ~1939–2112. Edits in:
- Frontmatter — lines ~1953–1965:
  - M2: `allowed-tools` `Agent` → `Task`.
  - L4: add `WebFetch`.
- Step 1 (Load config) — line ~1976: add the worktree note (L1) and the model-resolution-priority bullet (C2).
- New step "Surface relevant directives" between Step 1 and Step 2 (C3).
- Step 5 (Send one agent per finding) — lines ~2019–2073:
  - C1: replace `subagent_type: general-purpose` with config-driven resolution; embed full directive contents when the resolved subagent_type is not in the allowlist.
  - C2: change the model line to follow the §7.6 priority.
  - H5: enumerate the shipped allowlist explicitly so the check is allowlist-match.
  - H6: restructure the planner prompt into §7.1.5's 5-part order.
  - M3: change "Launch all in parallel with `run_in_background: true`" to the multi-Task-tool-call wording.

**Task 23 (`skills/fix/SKILL.md`)** — plan lines ~2116–2343. Edits in:
- Frontmatter — lines ~2130–2142:
  - M2: `allowed-tools` `Agent` → `Task`.
  - L4: add `WebFetch`.
- Step 1 (Load config) — lines ~2154–2161: add the worktree note (L1) and the model-resolution-priority bullets (C2).
- New step "Surface relevant directives" between Step 1 and Step 2 (C3).
- Step 3 reorganization (L5): pull the "Parallel execution (where safe)" content from Step 4 to the head of Step 3 as Step 3a (or rename current Step 3a–3e to 3b–3f), so parallelization governs the loop rather than trailing it.
- Step 3b (Classify) — lines ~2182–2196: add "judgment-based by the orchestrator using this rubric" framing (L2).
- Step 3c (Send to implementer) — lines ~2198–2224:
  - C1: replace `subagent_type: general-purpose` with config-driven resolution.
  - C2: per-agent model override priority over `models.fix.implementer_*`.
  - H5: enumerate the shipped allowlist.
  - H6: restructure the implementer prompt into §7.1.5's 5-part order, including embedded directives (full contents when foreign).
- Step 3d (Send to reviewer) — lines ~2226–2267:
  - C1: replace `subagent_type: general-purpose` with `agents.test-auditor.subagent_type` (canonical fix-reviewer per spec §5.3).
  - C2: per-agent model override priority over `models.fix.reviewer`.
  - H5: enumerate the shipped allowlist.
  - H6: restructure the reviewer prompt into §7.1.5's 5-part order.
- Step 4 → Step 3a relocation (L5): see above. Inside the relocated text:
  - M3: `run_in_background: true` → multi-Task-tool-call wording.
  - M9: disambiguate "max 3 pairs concurrent."

**Task 24 (`skills/the-desert/SKILL.md`)** — plan lines ~2347–2490. Edits in:
- Frontmatter — lines ~2361–2374:
  - M2: `allowed-tools` `Agent` → `Task`.
- Step 1 (Load config) — lines ~2397–2403: confirm the worktree note (L1) is present (this skill defers to `/comb:review`'s loader; carrying the note here is informational).
- New step "Surface relevant directives" embedded in Step 1 (C3) — same algorithm as the other skills, so the carry-through to Steps 2/3/4 covers the whole pipeline.
- Step 2 / 3 / 4 (Run review / plan / fix) — lines ~2404–2447:
  - Confirm Step 4's "Every item gets a reviewer" note still routes to the canonical fix-reviewer subagent (per the C1 fix in Task 23).
  - M3: any references to `run_in_background: true` inside this skill's body get the multi-Task-tool-call wording. (Currently this skill delegates to the others, but be explicit.)

**No plan body changes (informational only):**
- L18: skills omit `model:` frontmatter on purpose. Add a one-line note in `CHANGELOG.md` (Task 1 / Phase 5) or in README §Configuration that documents this.

## How

Below are the precise before/after edits. Quoted "before" blocks are copied from the plan as it stands. Quoted "after" blocks are what the executor should write in their place.

---

### M2 — Replace `Agent` with `Task` in every `allowed-tools` list

**Affected:** Task 21 frontmatter, Task 22 frontmatter, Task 23 frontmatter, Task 24 frontmatter.

**Before** (Task 21, lines ~1665–1672):

```
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Agent
  - WebFetch
```

**After:**

```
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Task
  - WebFetch
```

**Before** (Task 22, lines ~1957–1962):

```
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Agent
```

**After** (also addresses L4 — adds `WebFetch`):

```
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Task
  - WebFetch
```

**Before** (Task 23, lines ~2134–2139):

```
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Agent
```

**After** (also addresses L4 — adds `WebFetch`):

```
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Task
  - WebFetch
```

**Before** (Task 24, lines ~2365–2371):

```
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Agent
  - WebFetch
```

**After:**

```
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Task
  - WebFetch
```

---

### L1 — Add the git-worktree note next to `git rev-parse --show-toplevel`

**Affected:** Task 21 Step 1, Task 22 Step 1, Task 23 Step 1, Task 24 Step 1.

**Before** (Task 21, line ~1701):

```
**Project root** is `git rev-parse --show-toplevel` (cwd fallback when not in git).
```

**After:**

```
**Project root** is `git rev-parse --show-toplevel` (which correctly returns the worktree path for git worktrees; cwd fallback when not in git).
```

**Tasks 22 / 23 / 24:** their Step 1 says "Same layered-merge as `/comb:review`." Add the same parenthetical immediately after that sentence:

**Before** (Task 22, line ~1978; Task 23, line ~2156; Task 24, line ~2399):

```
Same layered-merge as `/comb:review`.
```

**After:**

```
Same layered-merge as `/comb:review`. Project root is resolved with `git rev-parse --show-toplevel` (which handles git worktrees correctly).
```

---

### M5 — Reframe verification commands in `/comb:review` Step 4 as project-aware

**Affected:** Task 21 Step 4 (lines ~1791–1802).

**Before:**

```
## Step 4: Run mechanical verification checks

While agents work, in parallel:

```bash
npx tsc --noEmit 2>&1
npx vitest run <test_files> 2>&1
# Project-specific prohibited-import checks per CLAUDE.md, if applicable
```

Capture results for the verification table.
```

**After:**

```
## Step 4: Run mechanical verification checks

While agents work, in parallel, run project-appropriate verification (typecheck, tests, lint). Choose commands based on `CLAUDE.md` instructions and the project's manifest files (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, etc.). Examples:

```bash
# TypeScript / JavaScript
npx tsc --noEmit 2>&1
npx vitest run <test_files> 2>&1

# Python
ruff check . 2>&1
mypy . 2>&1
pytest 2>&1

# Rust
cargo check 2>&1
cargo test 2>&1

# Project-specific prohibited-import checks per CLAUDE.md, if applicable
```

If `CLAUDE.md` does not name a verification command and no manifest is recognised, skip the verification table row with a note rather than running unrelated tooling. Capture all results for the verification table.
```

---

### H4 — Markdown-only palette: explicit `git diff --name-only` detection

**Affected:** Task 21 Step 3 (line ~1750).

**Before:**

```
If scope is markdown-only (`.md` files), restrict palette to `code-reviewer` + `consistency-auditor` and note the limitation in the report header. Document-mode review is best-effort.
```

**After:**

```
**Markdown-only auto-detection.** Run `git diff --name-only <base>...<branch>` (or, for a PR, `gh pr diff <number> --name-only`) and check whether every returned path ends in `.md`. If yes — and even if the user did not explicitly say "markdown review" — automatically restrict the palette to `code-reviewer` + `consistency-auditor` and add a header note to the report: "Markdown-only diff — palette restricted to code-reviewer + consistency-auditor (document-mode review is best-effort, see spec §7.3)." Full document-mode review is future work.
```

---

### M6 — Self-describing rule for picking (judgment-based, hard cap 5, soft floor 1)

**Affected:** Task 21 Step 3, immediately above the existing "Hard cap" line (around line ~1746).

**Before:**

```
Pick 2–5 agents from `config.agents` based on:
- Diff content (what's actually in the files)
- Each agent's `when_to_use` (in config)
- The focus brief (required-include any agent matching it)

**Hard cap:** 5 agents. **Soft floor:** 1 (`code-reviewer` is `Always`, so it's always included).

If the focus brief required-includes more than 5, drop lower-priority required-includes by judgment.
```

**After:**

```
**Picking rule (spec §7.1.4 — judgment-based):** the orchestrator model itself picks the palette by reading the diff, weighing each agent's `when_to_use`, and applying the focus brief. There is no scoring algorithm — the picking is a judgment call you make explicitly and surface to the user.

Pick 2–5 agents from `config.agents` based on:
- Diff content (what's actually in the files)
- Each agent's `when_to_use` (in config)
- The focus brief (required-include any agent matching it)

**Hard cap:** 5 agents — never dispatch more than 5 in one run, even if both diff content and focus brief argue for more. If forced to choose, drop lower-priority required-includes by judgment.
**Soft floor:** 1 — `code-reviewer` is `when_to_use: "Always"`, so it is always included regardless of diff content.

These three rules (judgment-based, cap 5, floor 1) are the contract — verify them in your picking statement to the user (e.g., "Picking 4 of the 5 shipped agents — under the cap of 5; code-reviewer is always included").
```

---

### C3 — Add "Surface relevant directives" step to all four skill bodies

**Affected:** Task 21, Task 22, Task 23, Task 24.

This is a new sub-step. The exact wording is the same in all four skills; the placement differs.

**New text to insert (verbatim, identical across the four skills):**

```
## Step <N>: Surface relevant directives

Lowercase the focus brief and scan it for substring matches against the loaded directive filenames (both plugin defaults at `${CLAUDE_PLUGIN_ROOT}/directives/*.md` and the user's directives at `<project-root>/<directives.user_path>/*.md` if present). Strip the `.md` extension before matching, but match against the *full base name* — so `"scope"` matches `scope-discipline.md`, `"simplicity"` matches `simplicity.md`, and `"copy-paste"` would match a user directive named `copy-paste.md` if present (it doesn't match the shipped `reusability.md` — the matcher is a literal substring check, not a synonym mapper, per spec §8).

Record the matched directive paths. They will be flagged as **primary** in agent dispatch prompts under the heading "Directives most relevant to this run" so agents weight them first.

If the focus brief is empty, no directives are flagged primary; all directives still load normally.
```

**Placement:**
- **Task 21 (`/comb:review`):** insert as a new step between current Step 2 (Gather context) and Step 3 (Pick agents). Renumber the original Step 3 → Step 4 and so on through Step 8 → Step 9. Update internal references accordingly. Use heading `## Step 3: Surface relevant directives`.
- **Task 22 (`/comb:plan`):** insert as a new step between current Step 1 (Load config) and Step 2 (Parse all findings). Renumber the original Step 2 → Step 3, ..., Step 6 → Step 7. Use heading `## Step 2: Surface relevant directives`.
- **Task 23 (`/comb:fix`):** insert as a new step between current Step 1 (Load config) and Step 2 (Suggest groupings). Renumber Step 2 → Step 3, current Step 3 → Step 4 (the execution loop), and current Step 5 → Step 6 (progress tracking). Step 4-relocation note from L5 is handled separately. Use heading `## Step 2: Surface relevant directives`.
- **Task 24 (`/comb:the-desert`):** add as a new step between current Step 1 (Load config) and Step 2 (Run review). Use heading `## Step 2: Surface relevant directives`. Renumber Step 2 → Step 3 (Run review), Step 3 → Step 4 (Run plan), Step 4 → Step 5 (Run fix). Note that the matched-directive flagging then carries through review → plan → fix without re-computing.

**Reference in dispatch prompts:** every dispatch prompt (in Tasks 21 Step 3 dispatch block, Task 22 planner prompt, Task 23 implementer/reviewer prompts, Task 24 — via delegation) must include the matched-directives flag. See the H6 dispatch-prompt restructure for where this slots in.

---

### M3 — Replace `run_in_background: true` with multi-Task-tool-call wording

**Affected:** Task 21 dispatch block (line ~1789), Task 22 Step 5 lead-in (line ~2021), Task 23 Step 4 / relocated Step 3a (line ~2280–2289).

**Before** (Task 21, line ~1789):

```
Launch all dispatches in parallel using `run_in_background: true`.
```

**After:**

```
Launch all dispatches in parallel by issuing multiple Task tool calls in a single assistant message. (`run_in_background: true` is a Bash-tool parameter, not a Task-tool parameter; parallel agent dispatch happens via batched tool calls.)
```

**Before** (Task 22, line ~2021):

```
Launch all in parallel with `run_in_background: true`.
```

**After:**

```
Launch all in parallel by issuing multiple Task tool calls in a single assistant message — one call per finding (or group). Do not use `run_in_background: true`; that is a Bash-tool parameter and has no effect on the Task tool.
```

**Before** (Task 23, lines ~2280–2289 — current "Step 4: Parallel execution"; this content moves to Step 3a per L5, then this fix applies to the relocated text):

```
## Step 4: Parallel execution (where safe)

Two instructions overlap if their **write-sets** intersect. Reads are free.

When upcoming items don't overlap:
- Group into parallel batches
- Run each batch concurrently
- Max 3 pairs concurrent — keeps things trackable

Same-file writes: sequential. Different files: parallel.

Announce batches:
```
Running batch: L1, L2, L3 in parallel (no file overlap)
```
```

**After** (also addresses M9 and L5 — see those entries; combined here for one cohesive replacement):

```
## Step 3a: Parallel execution policy (governs Step 3b–3f)

Two instructions overlap if their **write-sets** intersect — reads are free. Apply this policy to the execution loop below:

- Same-file writes → sequential.
- Different-file writes → parallel batch.
- **Concurrency limit:** max 3 implementer/reviewer pairs running concurrently — i.e., up to 3 items being implemented and verified at any given moment (so up to 6 in-flight subagents at peak: 3 implementers running while 3 reviewers verify previous batches, or 3 implementer+reviewer pairs interleaved).

To launch a parallel batch, issue multiple Task tool calls in a single assistant message — one call per item in the batch. Do not use `run_in_background: true` (that is a Bash-tool parameter and has no effect on the Task tool).

Announce batches before launching:

```
Running batch: L1, L2, L3 in parallel (no file overlap, 3-pair concurrency)
```
```

**Note:** with this relocation, the old "Step 4" header in Task 23 is removed; "Step 5: Progress tracking" becomes "Step 4: Progress tracking" and the Ground rules / Edge cases sections shift up accordingly. (See L5 entry for the full step renumbering.)

---

### M9 — Disambiguate "3 pairs concurrent"

**Affected:** Task 23 (currently Step 4, relocated to Step 3a per L5).

Already covered in the M3 replacement above ("Concurrency limit: max 3 implementer/reviewer pairs running concurrently — i.e., up to 3 items being implemented and verified at any given moment").

---

### L5 — Move "Parallel execution" before the execution loop in `/comb:fix`

**Affected:** Task 23 — relocate current Step 4 content to a new Step 3a and renumber subsequent steps.

Before the relocation, the Task 23 step layout is:

- Step 1: Load config
- Step 2: Suggest groupings
- Step 3: Execution loop
  - 3a: Read the instruction
  - 3b: Classify: trivial or standard?
  - 3c: Send to implementer
  - 3d: Send to reviewer (standard only)
  - 3e: Handle the result
- Step 4: Parallel execution (where safe)
- Step 5: Progress tracking

After the relocation (and incorporating C3 which adds "Step 2: Surface relevant directives" before Suggest groupings):

- Step 1: Load config
- Step 2: Surface relevant directives (new — see C3)
- Step 3: Suggest groupings (was Step 2)
- Step 4: Execution loop (was Step 3)
  - 4a: Parallel execution policy (was Step 4 — relocated to head of loop)
  - 4b: Read the instruction (was 3a)
  - 4c: Classify: trivial or standard? (was 3b)
  - 4d: Send to implementer (was 3c)
  - 4e: Send to reviewer (standard only) (was 3d)
  - 4f: Handle the result (was 3e)
- Step 5: Progress tracking (unchanged number, but content now follows the renumbered loop)

Update all internal cross-references in the body to match. (E.g., the "(standard only)" phrase in Step 4e references Step 4c's classification; the "If 3 failures on one item" rule in Step 4f stays put.)

The renumbering is mechanical except for "Step 3a — Parallel execution policy" — that block's full text is given in the M3 entry above.

---

### L2 — "Judgment-based" framing in `/comb:fix` triviality classification

**Affected:** Task 23 Step 3b (becomes Step 4c after L5 renumbering, lines ~2182–2196).

**Before:**

```
### 3b. Classify: trivial or standard?

**Trivial:**
- Single-line edits
- Import reorders
- Comment fixes
- Lexical renames within a single file

**Standard:**
- Anything multi-file
- Anything that changes behavior
- Anything that introduces a new control-flow branch

The user can override the classification for any item.

For trivial items: announce "(trivial — sonnet implementer, no reviewer)" and proceed accordingly.
```

**After:**

```
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
```

> **Note on "no reviewer for trivial":** the original plan body announced "(trivial — sonnet implementer, no reviewer)". That contradicts spec §7.5 ("For each instruction: implementer (opus standard, sonnet trivial), then reviewer (opus)") — flagged separately as **H2** (out of this group's scope, handled in PROCESS-fixes). The After block above corrects the announcement wording while leaving the H2 substantive decision to that group. If H2 is resolved in favour of "always run a reviewer" before this group's edits land, the After block above is already consistent. If H2 lands in favour of "skip trivial review," update this block accordingly when both groups merge.

---

### C1 + C2 + H5 + H6 — Restructure dispatch prompts in `/comb:plan` (Task 22 Step 5)

**Affected:** Task 22 Step 5 — the planner agent config and prompt template (lines ~2019–2073).

**Before:**

```
## Step 5: Send one agent per finding (or group)

Launch all in parallel with `run_in_background: true`.

**Agent config:**
- `subagent_type`: `general-purpose` (planning is generic; specialty doesn't matter as much)
- `model`: `models.plan` (default opus)

**Agent prompt:**

```
You're a senior {specialization-derived-from-finding} developer. You've been assigned one review finding to write fix instructions for.

## Finding

### {reference_code}. {title} ({severity})

{full_finding_description}

## What to do

1. Read the affected file(s): {file_paths}
2. Read 2–3 nearby files to understand the surrounding patterns
3. Write a fix instruction document

## Save to

`{output_folder}/{reference_code}-{title-slug}.md`

## Document sections

### What
Exactly what needs to change. Name the exact code, lines, patterns.

### Why
Why this matters. What breaks or degrades if left unfixed.

### Where
Exact file path(s) and line number(s). Only include related files if they're part of the fix.

### How
The exact changes, with before/after code blocks. Precise enough to apply mechanically.

### Expected Outcome
What's different after the fix. How to verify it worked.

### Scope
What IS in scope. What is explicitly OUT of scope — no drive-by refactors, no bonus cleanup.

Be concise and precise. No fluff. These instructions are the single source of truth for this fix.

## User focus for this run

{focus_brief if present}
```

**File naming:** `{reference-code}-{title-slug}.md`. Title kebab-case, 5–8 words max.
```

**After** (post-C3 renumbering, this is Step 6; before C3 renumbering, it is still Step 5 — the executor applies whichever numbering matches their checkpoint):

```
## Step 6: Send one agent per finding (or group)

Launch all in parallel by issuing multiple Task tool calls in a single assistant message — one call per finding (or group). Do not use `run_in_background: true`; that is a Bash-tool parameter and has no effect on the Task tool.

**Agent config (resolved per finding):**

- **Pick the role.** For each finding, the orchestrator picks one role from `config.agents` whose `when_to_use` best matches the finding's specialty (general correctness → `code-reviewer`, simplification/abstraction concerns → `simplifier`, error-handling → `silent-failure-hunter`, test gaps → `test-auditor`, pattern/spec drift → `consistency-auditor`). When no role obviously matches, default to `code-reviewer`.
- **Resolve `subagent_type`** from the picked role's `agents.<role>.subagent_type`. **Do not hardcode `general-purpose`** — that bypasses both the user's `agents` config and the foreign-vs-shipped allowlist match.
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

### Finding

### {reference_code}. {title} ({severity})

{full_finding_description}

### What to do

1. Read the affected file(s): {file_paths}
2. Read 2–3 nearby files to understand the surrounding patterns
3. Write a fix instruction document at `{output_folder}/{reference_code}-{title-slug}.md`

## 5. Output format

Your output is a single markdown file at `{output_folder}/{reference_code}-{title-slug}.md` with these sections in order:

### What
Exactly what needs to change. Name the exact code, lines, patterns.

### Why
Why this matters. What breaks or degrades if left unfixed.

### Where
Exact file path(s) and line number(s). Only include related files if they're part of the fix.

### How
The exact changes, with before/after code blocks. Precise enough to apply mechanically.

### Expected Outcome
What's different after the fix. How to verify it worked.

### Scope
What IS in scope. What is explicitly OUT of scope — no drive-by refactors, no bonus cleanup.

Be concise and precise. No fluff. These instructions are the single source of truth for this fix.

File naming: `{reference-code}-{title-slug}.md`. Title kebab-case, 5–8 words max.
```
```

---

### C1 + C2 + H5 + H6 — Restructure implementer prompt in `/comb:fix` (Task 23 Step 3c → Step 4d)

**Affected:** Task 23 — implementer dispatch (lines ~2198–2224).

**Before:**

```
### 3c. Send to implementer

**Agent config:**
- `subagent_type`: `general-purpose`
- `model`: `models.fix.implementer_standard` for standard, `models.fix.implementer_trivial` for trivial
- Fresh agent per item — no accumulated state

**Implementer prompt:**

```
You're an implementer. Execute this fix instruction precisely and completely.

## Fix Instruction

{full instruction document content}

## Your job

1. Read the affected file(s)
2. Apply the exact changes from the "How" section
3. Stay strictly within the documented scope — no other changes
4. Report back: which files you changed, what changed, and confirm the expected outcome is met

## User focus for this run

{focus_brief if present}
```
```

**After** (post-L5 renumbering this is Step 4d; before L5 it is Step 3c — apply whichever matches the executor's checkpoint):

```
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
```

---

### C1 + C2 + H5 + H6 — Restructure reviewer prompt in `/comb:fix` (Task 23 Step 3d → Step 4e)

**Affected:** Task 23 — reviewer dispatch (lines ~2226–2267).

**Before:**

```
### 3d. Send to reviewer (standard only)

**Agent config:**
- `subagent_type`: `general-purpose`
- `model`: `models.fix.reviewer` (default opus)
- Fresh agent

**Reviewer prompt:**

```
You're a code reviewer. Verify this fix was done correctly.

## Original Instruction

{instruction document content}

## What the implementer changed

{implementer's summary}

## Check these things

1. The change from "How" was applied correctly
2. The "Expected Outcome" is satisfied
3. No unrelated changes were introduced
4. The fix stays within documented "Scope"

Report PASS or FAIL with specifics. If FAIL, explain exactly what's wrong.

## Discovered issues

If you spot a real problem in the same file(s) that's NOT part of this fix — a bug, type error, missing guard — report it under "DISCOVERED" with:
- Short title
- File path and line(s)
- Brief description and suggested fix

Only flag genuine issues, not style preferences. One or two max. If nothing stands out, skip this section.

## User focus for this run

{focus_brief if present}
```
```

**After** (post-L5 renumbering this is Step 4e; before L5 it is Step 3d):

```
### 4e. Send to reviewer (standard only)

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
```

---

### C1 + H6 — Add the same dispatch contract to `/comb:review` Step 3 (Task 21)

**Affected:** Task 21 — the existing dispatch block already has a 5-part structure, but several improvements should be folded in for consistency with the new Tasks 22/23 prompts and to surface the C3 "Directives most relevant to this run" flag.

**Before** (Task 21, dispatch block, lines ~1754–1789):

```
**Agent dispatch:**

For each picked role, construct the dispatch prompt:

1. **Shared context block:**
   ```
   Repository: <path>
   Branch: <name>
   Base: <base>

   Files in scope:
   <list>

   Commits under review:
   <list>

   Reference implementation: <path or "none">
   <prior review note if round N+1>
   ```

2. **Directives:**
   - For `comb:*` agents in the shipped allowlist (`comb:code-reviewer`, `comb:simplifier`, `comb:silent-failure-hunter`, `comb:test-auditor`, `comb:consistency-auditor`): supply directive **paths**. The agents know how to read them.
   - For substituted or extra agents (any subagent_type not in the allowlist): supply directive **full contents** verbatim, plus the explicit instruction "These directives are authoritative. Cite by `file.md §N.N` when raising findings."

3. **User focus brief**, under `## User focus for this run` heading, verbatim, with framing: "Findings matching this focus are highest priority. Surface other issues too, but do not let the user's stated concerns slip."

4. **Output format spec:**
   - Severity scale: Critical / High / Medium / Low / Test gaps / Deferred
   - Finding codes: placeholder (orchestrator renumbers)
   - File:line references
   - Directive citations
   - Read-only — no code changes

5. **Resolve model:** `agents.<role>.model` if set, else `models.review`. **Exception:** an `agents.<role>.model` user override always wins (per spec §7.6).

Launch all dispatches in parallel using `run_in_background: true`.
```

**After:**

```
**Agent dispatch:**

For each picked role, resolve and construct the dispatch prompt:

**Resolution (do this before assembling the prompt):**

- **Resolve `subagent_type`** from `agents.<role>.subagent_type` — never hardcode any value here.
- **Resolve model** with this priority (spec §4.3 / §7.6): `agents.<role>.model` if set; otherwise `models.review` (default `opus`). The per-agent override always wins.
- **Allowlist match (not prefix check) — spec §5.4:** the shipped allowlist is exactly:
  - `comb:code-reviewer`
  - `comb:simplifier`
  - `comb:silent-failure-hunter`
  - `comb:test-auditor`
  - `comb:consistency-auditor`

  Compare the resolved `subagent_type` with literal string equality. Native → directives by path. Foreign → full directive contents embedded.

**Dispatch prompt (5-part order per spec §7.1.5):**

1. **Shared context block:**
   ```
   Repository: <path>
   Branch: <name>
   Base: <base>

   Files in scope:
   <list>

   Commits under review:
   <list>

   Reference implementation: <path or "none">
   <prior review note if round N+1>
   ```

2. **Directives:**
   - **Native** (`comb:*` in the allowlist above): supply directive **paths**. The agents know how to read them.
     - List both plugin defaults (`${CLAUDE_PLUGIN_ROOT}/directives/*.md` if `include_plugin_defaults`) and user directives (`<project-root>/<directives.user_path>/*.md` if it resolves).
     - Append a `Directives most relevant to this run:` list with the primary matches from the "Surface relevant directives" step.
   - **Foreign** (subagent_type not in the allowlist): supply directive **full contents** verbatim with `## File: <path>` headers, plus the explicit instruction: "These directives are authoritative. Cite by `file.md §N.N` when raising findings." Then append the same `Directives most relevant to this run:` list.

3. **User focus brief**, under `## User focus for this run` heading, verbatim, with framing: "Findings matching this focus are highest priority. Surface other issues too, but do not let the user's stated concerns slip."

4. **Agent-specific instructions:** for native `comb:*` agents this is already in the agent file body. For foreign agents, supply a one-paragraph specialty statement derived from the role's `when_to_use` so the foreign agent knows what lens to apply.

5. **Output format spec:**
   - Severity scale: Critical / High / Medium / Low / Test gaps / Deferred
   - Finding codes: placeholder (orchestrator renumbers)
   - File:line references
   - Directive citations on every finding where applicable
   - Read-only — no code changes

Launch all dispatches in parallel by issuing multiple Task tool calls in a single assistant message — one call per picked role. (`run_in_background: true` is a Bash-tool parameter, not a Task-tool parameter; parallel agent dispatch happens via batched tool calls.)
```

---

### C1 + C2 + H5 + H6 — `/comb:the-desert` (Task 24)

**Affected:** Task 24 (lines ~2402–2447). The-desert delegates to `/comb:review`, `/comb:plan`, `/comb:fix`, so the dispatch-prompt restructure is inherited automatically once Tasks 21–23 are fixed. The only edits in Task 24:

**1. Confirm the model-coercion exception language is unchanged.** It already states: "explicit `agents.<role>.model` user overrides survive `the-desert` coercion (per spec §7.6). Only lane defaults are coerced." That is correct as written and aligns with C2 — leave it.

**2. Add the C3 "Surface relevant directives" step** (already covered in the C3 section above — placement: between Step 1 and Step 2, with subsequent steps renumbered).

**3. Confirm Step 4 (Run fix) routes to the canonical fix-reviewer.** The Step 4 bullet "Every item gets a reviewer — no 'trivial — skipped review'" remains; clarify which reviewer:

**Before** (Task 24 Step 4, line ~2443):

```
- **Every item gets a reviewer** — no "trivial — skipped review"
```

**After:**

```
- **Every item gets a reviewer** — no "trivial — skipped review". The reviewer is `agents.test-auditor.subagent_type` (default `comb:test-auditor`), per spec §5.3, with model coerced to `models.the_desert` unless an explicit `agents.test-auditor.model` user override is set.
```

---

### L18 — Note that skill bodies omit the `model:` frontmatter field (no plan body change)

**No changes to plan Tasks 21–24.**

Carry-forward as a note in `CHANGELOG.md` (under `[Unreleased]`, finalized at v0.1.0 release in Phase 5) or in `README.md` §Configuration:

```markdown
### A note on skill `model` frontmatter

The four `/comb:*` skills intentionally omit the `model:` frontmatter field. The orchestrator runs in the user's session model (whatever they invoked Claude Code with), and the skill body's logic dispatches subagents at the configured `models.<lane>` model (or `agents.<role>.model` when set). Adding a `model:` field to a skill would only fix the orchestrator's model — it would have no effect on the dispatched agents, which is what actually matters for cost and quality.
```

This is informational only; it documents intent so a future maintainer doesn't "fix" the missing field by adding one.

---

## Expected Outcome

After applying all fixes:

- All 4 skill bodies (Tasks 21–24) describe the **same dispatch-prompt structure** (the 5-part order from spec §7.1.5: shared context → directives → focus brief → agent-specific instructions → output format).
- Plan and fix dispatches resolve `subagent_type` from `agents.<role>` config, **not** hardcoded `general-purpose`. The fix-reviewer specifically resolves from `agents.test-auditor` per spec §5.3.
- All dispatches embed **full directive contents** for foreign agents (subagent_type not in the 5-string allowlist). Native agents receive paths. The check is literal string equality, not a `comb:*` prefix.
- Per-agent `agents.<role>.model` is honored in **all four** commands and survives the-desert coercion.
- Focus brief substring-matching against directive filenames (lowercased, full-base-name match) is implemented in all four skill bodies as a "Surface relevant directives" step, and the matched directives are flagged as primary in every dispatch prompt.
- All four skills' `allowed-tools` use the correct tool name (`Task`, not `Agent`). Task 22 and Task 23 also pick up `WebFetch` for parity.
- Parallelization mechanism is described as "multiple Task tool calls in a single assistant message," **not** `run_in_background: true`. The Bash-tool-vs-Task-tool distinction is called out wherever the wording appeared.
- Verification commands in `/comb:review` are project-aware — they detect the project's manifest and choose appropriate commands, with TS/Python/Rust examples and a "skip and note" fallback.
- The judgment-based / cap-5 / floor-1 picking contract is self-described in `/comb:review` Step 3, so the skill body itself is verifiable.
- "Max 3 pairs concurrent" is disambiguated to "max 3 implementer/reviewer pairs running concurrently — i.e., up to 3 items being implemented and verified at any given moment."
- The `/comb:fix` step order places the parallel-execution policy **before** the execution loop, where it visibly governs the loop.
- The triviality classification in `/comb:fix` carries the spec §7.5 "judgment-based by the orchestrator" framing.
- The git-worktree note is present in all four skill bodies' Step 1.
- The `model:`-frontmatter omission is documented in CHANGELOG/README so it's not "fixed" by accident later.

## Scope

**In scope:**

- Editing the 4 skill body content blocks in plan Tasks 21–24 (`skills/review/SKILL.md`, `skills/plan/SKILL.md`, `skills/fix/SKILL.md`, `skills/the-desert/SKILL.md`)
- Renumbering steps within those skill bodies as required by the C3 insertion and the L5 relocation, and updating any internal cross-references in the body text
- Adding a CHANGELOG/README note for L18 (informational)

**Out of scope:**

- Spec changes (handled separately in SPEC-DECISIONS group — including H2 "trivial reviewer skipped" and H3 "CLAUDE.md base-branch lookup" and M1 "round-N-aware prior report read")
- Agent file changes including `disallowedTools` form (handled separately in AGENT-fixes group — H1)
- Phase 0 / Task 25 / Task 28 / Task 29 / Task 30 changes (handled separately in PROCESS-fixes group — M4, M6's verification-side, M7, M8, M10, L3, L6, L7, L9, L10, L13, L14, L15, L16, L19, L21, TG1)
- Drive-by simplification or restructuring of skill bodies beyond what the listed findings require
- Any changes to `agents/*.md` body files (those describe specialty behavior; the dispatch contract is owned by the skill bodies covered here)
