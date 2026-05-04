---
name: review
description: Run a comb code review on a PR, branch, or file list. Use when the user wants to review code for issues, audit a PR, find bugs in a diff, comb through changes, or check a spec/plan against existing patterns. The user may provide a focus brief after the command (e.g., "/comb:review look for ambiguities and inconsistencies").
argument-hint: "[scope] [focus brief]"
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

You are running step 1 of the comb workflow: review → plan → fix.

You're a senior tech lead. You pick the right experts for the job, give them clear scope, and pull their findings into one honest report.

## Inputs

You need these before starting:

1. **Scope** — one of:
   - A PR number (`gh pr diff <number> --name-only` for files, `gh pr view <number>` for metadata)
   - A branch name (`git diff --name-only <base>...<branch>`)
   - An explicit list of files
2. **Base branch** — what to diff against. Default: `paths.base_branch` from merged config (ships as `main`). The user may override at invocation time; the override does not mutate config.
3. **Focus brief** — `$ARGUMENTS` (everything typed after the command). Optional but treated as authoritative when present.

If scope is ambiguous, ask once. Otherwise derive it from the current branch and proceed.

## Step 1: Load config

Read the layered config in this order, deep-merging each layer onto the previous:

1. `${CLAUDE_PLUGIN_ROOT}/config/defaults.json` — shipped defaults
2. `~/.claude/comb.config.json` — global override (skip if not present)
3. `<project-root>/.claude/comb.config.json` — project override (skip if not present)

**Project root** is `git rev-parse --show-toplevel` (which correctly returns the worktree path for git worktrees; cwd fallback when not in git).

**Merge rules:**
- Objects: deep-merged
- Arrays: replaced wholesale
- `null` at any depth: removes that key from the merged result
- Invalid JSON in any layer: hard error (abort with clear message)
- Schema violations (e.g., new role missing `subagent_type`): warn and skip the bad key, continue

After merging, you have:
- `paths.reviews` — where to write the report
- `paths.plans` — (used by /comb:plan, not now)
- `directives.include_plugin_defaults` (boolean) and `directives.user_path` (string)
- `agents.<role>` — palette of available reviewers
- `models.review` — model for reviewer agents in this step

## Step 2: Gather context

```bash
# From PR
gh pr diff <number> --name-only
gh pr view <number> --json title,body,baseRefName,headRefName

# From branch
git diff --name-only origin/<base>...<branch>
git log --oneline origin/<base>...<branch>
```

Read these:
- Project's `CLAUDE.md` for conventions and gotchas (do not read it for base-branch defaults — those come from `paths.base_branch` in merged config)
- The user's directives at `<project-root>/<directives.user_path>/*.md` (if directory exists)
- The plugin's directives at `${CLAUDE_PLUGIN_ROOT}/directives/*.md` (if `directives.include_plugin_defaults: true`)
- Any plan/design doc the user points to in the focus brief
- A reference implementation, if the user names one or `CLAUDE.md` points to one

## Step 3: Surface relevant directives

Lowercase the focus brief and scan it for substring matches against the loaded directive filenames (both plugin defaults at `${CLAUDE_PLUGIN_ROOT}/directives/*.md` and the user's directives at `<project-root>/<directives.user_path>/*.md` if present). Strip the `.md` extension before matching, but match against the *full base name* — so `"scope"` matches `scope-discipline.md`, `"simplicity"` matches `simplicity.md`, and `"copy-paste"` would match a user directive named `copy-paste.md` if present (it doesn't match the shipped `reusability.md` — the matcher is a literal substring check, not a synonym mapper, per spec §8).

Record the matched directive paths. They will be flagged as **primary** in agent dispatch prompts under the heading "Directives most relevant to this run" so agents weight them first.

If the focus brief is empty, no directives are flagged primary; all directives still load normally.

## Step 4: Pick agents

Read the diff. Understand what changed: hooks, CSS, types, tests, error handling, new components, refactors, abstractions.

**Picking rule (spec §7.1.4 — judgment-based):** the orchestrator model itself picks the palette by reading the diff, weighing each agent's `when_to_use`, and applying the focus brief. There is no scoring algorithm — the picking is a judgment call you make explicitly and surface to the user.

Pick 2–5 agents from `config.agents` based on:
- Diff content (what's actually in the files)
- Each agent's `when_to_use` (in config)
- The focus brief (required-include any agent matching it)

**Hard cap:** 5 agents — never dispatch more than 5 in one run, even if both diff content and focus brief argue for more. If forced to choose, drop lower-priority required-includes by judgment.
**Soft floor:** 1 — `code-reviewer` is `when_to_use: "Always"`, so it is always included regardless of diff content.

These three rules (judgment-based, cap 5, floor 1) are the contract — verify them in your picking statement to the user (e.g., "Picking 4 of the 5 shipped agents — under the cap of 5; code-reviewer is always included").

**Markdown-only auto-detection.** Run `git diff --name-only <base>...<branch>` (or, for a PR, `gh pr diff <number> --name-only`) and check whether every returned path ends in `.md`. If yes — and even if the user did not explicitly say "markdown review" — automatically restrict the palette to `code-reviewer` + `consistency-auditor` and add a header note to the report: "Markdown-only diff — palette restricted to code-reviewer + consistency-auditor (document-mode review is best-effort, see spec §7.3)." Full document-mode review is future work.

Briefly explain your picks: "Picking code-reviewer (always), simplifier (refactor in foo.ts), test-auditor (behavior change in bar.ts)." The user can override.

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

## Step 5: Run mechanical verification checks

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

## Step 6: Wait and collect

Monitor agent completion. Don't consolidate until all agents report back. If one hangs over 10 minutes, note and proceed.

## Step 7: Consolidate

**Deduplication.** When multiple agents flag the same issue:
- Keep the most detailed description
- Credit all agents that found it
- Use the highest severity any agent assigned

**Severity scale:**

| Level | Meaning |
|-------|---------|
| Critical | Production bugs, data loss, security |
| High | Significant quality issue, directive violation |
| Medium | Should improve, partial conformance, missing handling |
| Low | Minor style, naming, docs |
| Test gaps | Missing or weak coverage |
| Deferred | Noted, explicitly out of scope |

**Finding codes:** sequential by severity. C1, C2 / H1, H2 / M1, M2 / L1, L2 / T1, T2 / D1, D2. Every Deferred item gets a code too — `/comb:plan` plans them by code, so unnumbered bullets get dropped.

## Step 8: Write the report

**Output path:** `<paths.reviews>/<derived-name>.md`. Naming:
- PR → `pr-{number}-round{N}-report.md`
- Branch → `branch-{name}-round{N}-report.md`

**N is computed as `(count of existing files matching the prefix in paths.reviews) + 1`.**

**Template:**

```markdown
# {Title} — Round {N} Review Report

**Branch:** `{branch}` -> `{base}`
**Scope:** {file_count} files, +{insertions} / -{deletions} lines
**Reviewers:** {N} agents ({list types})
**Date:** {date}

---

## Verification Summary

| Check | Result |
|---|---|
| TypeScript (`tsc --noEmit`) | {Clean or N errors} |
| Tests | {pass}/{total} passing |
| {Project-specific check} | {result} |

---

## Verdict: **{APPROVE / NEEDS WORK}**

{1–2 sentence summary. APPROVE if no Critical or High items.}

---

## Findings by Severity

### Critical
{findings or "None."}

### High
{findings or "None."}

### Medium
**{code} — {title}**
*Source: {agent(s)}*
File(s): `{path}:{line}`

{What's wrong, why it matters, fix suggestion. Cite directives where applicable.}

### Low
{findings}

### Test Gaps
{findings or "None."}

### Deferred
**{code} — {title}**
*Source: {agent(s)}*
File(s): `{path}:{line}`

{Why it's deferred, why it still matters, fix sketch.}

(or "None.")
```

## Step 9: Present

```
Review done — report saved to {path}

{verdict}

{count} findings: {N} critical, {N} high, {N} medium, {N} low, {N} test gaps, {N} deferred

Agents used: {list}
```

## Ground rules

- **Read-only.** Nobody edits code. The only file created is the report.
- **Agents read actual source code.** Not just filenames.
- **Project-aware.** Every agent gets the project's directives.
- **Severity is honest.** Critical means production bugs.
- **Round-aware.** The report filename includes round N, computed by counting existing reports + 1. v1 does not parse prior reports for fixed-findings status — agents may flag items that already shipped in a prior round; deduplication against prior rounds is future work (spec §12).

## Edge case: focus brief contradicts shipped behavior

If the brief implies altering shipped flow ("skip the report", "use only one agent", "write somewhere else"), surface the conflict and ask once before proceeding.
