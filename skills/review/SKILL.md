---
name: review
description: Use when the user wants to review code for issues, audit a PR or branch, find bugs in a diff, comb through changes, or check a spec/plan against existing patterns. The user may provide a focus brief after the command (e.g., "/comb:review look for ambiguities and inconsistencies").
argument-hint: "[scope] [focus brief]"
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Agent
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

Load the merged config per `${CLAUDE_PLUGIN_ROOT}/shared/config-loading.md`:

```
python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/comb.py" config
```

Run it from the project root and read its JSON output; it is the merged config. A non-zero exit names the bad file — stop and show it.

From it, you have:
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
git merge-base origin/<base> <branch>   # record the SHA; agents and the report diff against it, not against a branch name
```

Read these:
- Project's `CLAUDE.md` for conventions and gotchas (do not read it for base-branch defaults — those come from `paths.base_branch` in merged config)
- Do **not** read the directive files. Step 3 lists them (`comb.py directives`); the matcher and the Step 7 gate need names and paths only, and every agent reads them itself from the run brief.
- Any plan/design doc the user points to in the focus brief
- A reference implementation, if the user names one or `CLAUDE.md` points to one

**Load the PATTERNS manifest.** If `paths.patterns` resolves to a file, record its path; do not read it. Once the diff's file names are gathered (above), pipe that same name list into the script to cut this run's excerpt per `${CLAUDE_PLUGIN_ROOT}/shared/manifest-slicing.md` — no intermediate file:

```
git diff --name-only origin/<base>...<branch> | python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/manifest.py" excerpt --skill review --manifest <paths.patterns> --touched-from -
```

(For a PR, pipe `gh pr diff <number> --name-only`; for a user-given file list, pipe `printf '%s\n' <files>`.) Run it from the project root.

Record `run`, `excerpt`, the log line, and `stale` from its output for the dispatch prompt and the presentation. On the contract's fallback condition, print the fallback notice and deliver the full path alone. If `paths.patterns` is absent or `null`, skip — manifest consumption is a graceful no-op.

## Step 3: Surface relevant directives

Apply the focus-brief matcher in `${CLAUDE_PLUGIN_ROOT}/shared/directive-matching.md`. It records the matched directive paths and flags them as **primary** in agent dispatch prompts under "Directives most relevant to this run"; an empty focus brief flags nothing, and all directives still load normally.

```
python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/comb.py" directives --brief "<focus brief>"
```

Record the `plugin:` and `user:` paths and the `primary:` lines; `comb.py brief` renders them into every run brief.

## Step 3.5: Read the work

Before picking agents, write a single short message that surfaces your read of the diff to the user. The read has two outputs and one classification bit. Treat this as a judgment call, not a file-extension lookup.

**1. Characterization** — one paragraph in plain language describing what the artifact is, how thick it is, and what's at stake. Examples:

- "60-line edit to `docs/spec.md` — prose iteration on a design doc, no executable changes; assess for ambiguities, pattern-breaking against the codebase, and reusability gaps the spec implicitly ignores."
- "3-line bump to `package.json` engines field — trivial config; check it doesn't conflict with declared CI matrix."
- "12 files, mixed React components + types + tests, 400 lines — substantive feature work."

**2. Lens to apply** — which questions the dispatched agent(s) should be answering. For code-shaped diffs the lens is the existing one (bugs, contracts, data flow, security, simplicity, error paths, test coverage, pattern conformity). For non-code artifacts the lens shifts to *ambiguities, blind spots, pattern-breaking against the codebase, reusability gaps, quality issues the artifact implicitly mandates*.

**3. Classification** — one of:

- **code-shaped** — the diff contains executable code as its primary content (any of: source files in a language the project builds/tests, config that materially changes runtime behavior, generated code regenerated by source changes, test files). The full review apparatus applies.
- **non-code** — the diff is prose/spec/design-doc/pure-docs as its primary content. The condensed apparatus applies (no verification table, no verdict, no severity tiers, flat findings list).

Trust the judgment, not the file extension. A `.ts` file with only TSDoc edits is non-code. A `.md` file that is documentation-as-code regenerated by a code change is code-shaped (the code drives it). A mixed diff with both spec edits and code is code-shaped (the code drives classification; the lens framing will mention both).

The user may override via focus brief on the same turn (e.g., "do a full pass on this spec", "treat as code review"). Honor the override and proceed.

Surface the read to the user in this shape, before picking agents:

```
Reading the work:
  {characterization paragraph}

Lens: {one-line statement of the lens}
Classification: {code-shaped | non-code}

Picking agents accordingly →
```

This classification bit drives Steps 4, 5, 7, 8, and 9 below.

## Step 4: Pick agents

Read the diff in detail. Understand what changed: hooks, CSS, types, tests, error handling, new components, refactors, abstractions, prose content, spec sections, configuration.

**Picking rule (judgment-based):** the orchestrator model itself picks the palette by reading the diff, weighing each agent's `when_to_use`, and applying the focus brief. There is no scoring algorithm — the picking is a judgment call you make explicitly and surface to the user.

Pick 1–5 agents from `config.agents` based on:
- Diff content (what's actually in the files)
- Each agent's `when_to_use` (in config)
- The focus brief (required-include any agent matching it)

**Hard cap:** 5 agents — never dispatch more than 5 in one run, even if both diff content and focus brief argue for more. If forced to choose, drop lower-priority required-includes by judgment.
**`pattern-scanner`, `pattern-shaver`, and `implementer` are never eligible.** The first two are generation-only (dispatched by `/comb:patterns`); the third is the writer role, and review is read-only. Exclude them from the palette regardless of diff content or focus brief.
**Soft floor:** 1 — the orchestrator always dispatches at least one agent for objectivity (self-review by the session that produced the artifact is biased). The anchor agent shifts with the Step 3.5 classification:

- **code-shaped** → `code-reviewer` is the anchor.
- **non-code** → `consistency-auditor` is the anchor; `code-reviewer` is NOT included on non-code diffs.

For non-code diffs, `silent-failure-hunter` and `test-auditor` are also typically excluded — their lanes (error handling, test coverage) don't apply to prose artifacts. `simplifier` may join if the artifact is proposing architecture worth challenging.

These three rules (judgment-based, cap 5, floor 1) are the contract — verify them in your picking statement to the user (e.g., "Code-shaped diff — picking 4 of 5 shipped agents, code-reviewer is the anchor", or "Non-code diff — picking consistency-auditor as anchor; skipping code-reviewer, silent-failure-hunter, test-auditor").

Briefly explain your picks: "Picking code-reviewer (always), simplifier (refactor in foo.ts), test-auditor (behavior change in bar.ts)." The user can override.

**Agent dispatch:**

For each picked role, resolve and construct the dispatch prompt:

**Resolution (do this before assembling the prompt):**

- **Resolve the role:**

  ```
  python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/comb.py" resolve --role <role> --lane review
  ```

  Pass `model:` as the Agent call's `model` and `effort:` as `effort` unless it is `unset`; `native:` is the form the brief takes (the script already chose it). Never hardcode a `subagent_type`.
- **Write the run brief:**

  ```
  python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/comb.py" brief --skill review --role <role> --run <run> --excerpt <excerpt> --manifest <paths.patterns> --brief "<focus brief>"
  ```

  Omit `--excerpt` and `--manifest` when no manifest resolved and `--brief` when the focus brief is empty. `<run>` is the stem the Step 2 excerpt printed, so one `clean` removes both. When no excerpt was cut this run, omit `--run` on the first `brief` call, record the `run:` it prints, and pass that stem as `--run` to every later `brief` call and to the final `clean`. Echo the four lines it prints; its `brief:` path goes into the prompt.
- **Delivery contract:** `${CLAUDE_PLUGIN_ROOT}/shared/dispatch-delivery.md` — the briefs, the native rule, and the model and effort parameters.

**Dispatch prompt (5-part order — Step 3.5 read framing is part 2):**

1. **Shared context block:**
   ```
   Repository: <path>
   Branch: <name>
   Base: <base>
   Merge-base: <sha>

   Files in scope:
   <list>

   Commits under review:
   <list>

   PR description: <body or "no PR — branch/file-list scope">

   Reference implementation: <path or "none">
   ```

2. **Lens framing (the orchestrator's read of the work):**
   ```
   Read of the work:
   <characterization paragraph from Step 3.5>

   Lens to apply:
   <lens statement from Step 3.5>

   Classification: <code-shaped | non-code>

   Bias guard: You are reviewing work produced in another session. Treat the artifact as the source of truth; do not assume intent you cannot verify from the text itself.
   ```

3. **Read first:** the line `Read first: <brief: path from comb.py brief>`. The run brief carries the directive paths (native or foreign form, with the primaries), the observed-baseline block, and the focus brief; the prompt repeats none of them.

4. **Agent-specific instructions:** for native `comb:*` agents this is already in the agent file body. For foreign agents the run brief's `Your lens:` line carries the role's `when_to_use`; add nothing else.

5. **Output format spec:**
   - **Native agents:** `Output format per your agent definition; finding codes are placeholders the orchestrator renumbers; include the Confidence line on every finding.`
   - **Foreign agents only** — the full spec:
     - Severity scale: Critical / High / Medium / Low / Test gaps / Deferred
     - Finding codes: placeholder (orchestrator renumbers)
     - File:line references
     - Directive citations on every finding where applicable
     - **Confidence** on every finding: `Verified` when you opened every cited file and confirmed every particular the finding asserts — the anchor, any count, and, for a suggested fix, that you traced the fix against the code. Otherwise `Unverified — <what you could not confirm>`, naming the specific gap (an inferred line range, an estimated count, an untraced fix shape, a file you could not open). This field is not optional.
     - Read-only — no code changes

Launch all dispatches in parallel per the delivery contract — one Agent call per picked role, batched in a single assistant message.

## Step 5: Run mechanical verification checks

**Conditional on classification (Step 3.5).** Skip this entire step if the classification is **non-code** — there is no executable artifact to verify. Omit the verification table from the report entirely (no "N/A" rows).

If the classification is **code-shaped**, run project-appropriate verification in parallel with agent dispatch (typecheck, tests, lint). Choose commands from `CLAUDE.md` instructions and the project's build or package manifest(s). Pipe stderr with `2>&1` so it lands in the verification table.

Project-specific prohibited-import or convention checks per `CLAUDE.md` come on top.

If `CLAUDE.md` does not name a verification command and the project's build or package manifest(s) name none, skip the verification table row with a note rather than running unrelated tooling. Capture all results for the verification table.

## Step 6: Wait and collect

Monitor agent completion. Don't consolidate until all agents report back. If one hangs over 10 minutes, note and proceed.

## Step 7: Consolidate

**Verify before promoting.** A finding becomes authoritative the moment it enters the report. Agent output is a proposal; the report is not. Before you write a finding, confirm the particulars it carries:

1. **Anchors.** Open each cited file at each cited line. Confirm the construct the finding describes is there. Take the line number from a numbered read, never by counting rows in a rendered block — an anchor derived by eye is unverified no matter how carefully you counted. Re-anchor a finding whose anchor does not resolve, or drop it. Never transcribe an anchor you did not open.
2. **Quantities.** Recompute every count, every ratio, and every all/none/only claim against the code — yours and the agents' alike.
3. **Suggested fixes.** A fix shape you have not traced is a proposal, not a recommendation. Trace it, or mark it unverified. Never promote an agent's untraced fix shape into the report's voice.
4. **Your own syntheses.** A merged description, a cross-agent count, or a combined severity rationale is new content that no agent wrote. It gets the same treatment.
5. **Directive citations.** For each `file.md §N` or `§N.N` a finding cites, confirm the file is among the loaded directives and has a heading numbered `N`. Correct or drop a citation that does not resolve; `/comb:plan` copies these into `## Directive citations` as policy.

Carry each agent's `Confidence` line forward. Where an agent reported `Unverified` and you did not close the gap yourself, the report says so. An agent that omitted the field confirmed nothing you can rely on — treat its particulars as unconfirmed until you check them.

**Bound.** This gate reads the cited locations, recomputes the stated quantities, and resolves the cited directive sections. It is not a second review. Do not re-derive findings, do not re-litigate severity, and do not hunt for issues the agents missed. The verdict inherits each agent's severity unchecked: one agent's over-rating can flip APPROVE to NEEDS WORK, and the report says which agent rated what in its `Sources:` line.

**Deduplication (both classifications).** When multiple agents flag the same issue:
- Keep the most detailed description
- Credit all agents that found it
- Use the highest severity (code-shaped) or preserve the first label (non-code)
- The merged finding's `Verified:` line covers the description you kept, not the ones you dropped. Re-check the particulars of the surviving text.

**Sources tally.** Count each agent's findings in and out: reported, kept under their own code, merged into another code, dropped at the gate (with the reason in one word: anchor, count, duplicate, calibration). An agent that never reported (Step 6 timeout) is `no report (timed out)`. This is bookkeeping, written once per agent; it makes a vanished finding visible.

**For non-code classification:** skip the C/H/M/L/T/D scale and the finding-code numbering. Preserve agent-supplied labels verbatim — typically one of *Ambiguity*, *Blind spot*, *Pattern-break*, *Reusability gap*, *Quality concern*. List findings as a flat collection; no tier grouping.

**For code-shaped classification: severity scale:**

| Level | Meaning |
|-------|---------|
| Critical | Production bugs, data loss, security |
| High | Significant quality issue, directive violation |
| Medium | Should improve, partial conformance, missing handling |
| Low | Minor style, naming, docs |
| Test gaps | Missing or weak coverage |
| Deferred | Noted, explicitly out of scope |

**Finding codes:** sequential by severity. C1, C2 / H1, H2 / M1, M2 / L1, L2 / T1, T2 / D1, D2. Every Deferred item gets a code too — `/comb:plan` plans them by code, so unnumbered bullets get dropped.

**Semantic refresh signal.** If any agent flagged a divergence as a *deliberate improvement / migration* or a *new canonical* pattern, record that the semantic refresh note should fire in the presentation. This is distinct from the commit-based staleness note.

## Step 8: Write the report

**Output path:**

```
python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/comb.py" report-name --reviews <paths.reviews> --pr <number>      # or: --branch <name>
```

Its `report:` line is the path to write (`pr-{number}-round{N}-report.md`, or `branch-{slug}-round{N}-report.md` with the branch name made path-safe). The script parses `N` out of the existing filenames with the same prefix and never counts files — after a deletion, a count collides with a surviving later round.

**Template selection.** Use the template that matches the Step 3.5 classification.

**Writing the `Verified:` line (both templates).** Name the check, not the act. `Read foo.ts:118-126; recomputed the count (4 of 5)` is a verification. `Verified against source` is not. State both halves — what you confirmed and what you did not. When nothing was confirmed, write `not independently verified — <what is unchecked>`. Every finding carries the line; there is no blank and no omission. The line reports on this finding's own particulars — never on the run's typecheck or test results, which belong in the Verification Summary table.

### Template — code-shaped:

```markdown
# {Title} — Round {N} Review Report

**Branch:** `{branch}` -> `{base}`
**Scope:** {file_count} files, +{insertions} / -{deletions} lines
**Reviewers:** {N} agents ({list types})
**Sources:** {agent}: {n} reported → {k} kept, {m} merged into {codes}, {d} dropped ({reasons}) · {agent}: no report (timed out) · …
**Date:** {date}

---

## Verification Summary

| Check | Result |
|---|---|
| {Typecheck / build command} | {Clean or N errors} |
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
**Verified:** {what you confirmed, and what you did not}

{What's wrong, why it matters, fix suggestion. Cite directives where applicable.}

### Low
{findings}

### Test Gaps
{findings or "None."}

### Deferred
**{code} — {title}**
*Source: {agent(s)}*
File(s): `{path}:{line}`
**Verified:** {what you confirmed, and what you did not}

{Why it's deferred, why it still matters, fix sketch.}

(or "None.")
```

### Template — non-code (condensed):

````markdown
# {Title} — Review

**Artifact:** `{path}` (or `{branch}` → `{base}` for diff-scoped)
**Scope:** {file_count} file(s), +{insertions} / -{deletions} lines
**Reviewers:** {N} agents ({list})
**Sources:** {agent}: {n} reported → {k} kept, {m} merged into {labels}, {d} dropped ({reasons}) · {agent}: no report (timed out) · …
**Date:** {date}

---

## Read

{Characterization paragraph from Step 3.5 — what the artifact is, what's at stake.}

## Lens

{Lens applied — the working questions agents were answering.}

---

## Findings

**{Label} — {title}**
*Source: {agent(s)}*
File(s): `{path}:{line-range or section heading}`
**Verified:** {what you confirmed, and what you did not}

{What's wrong, why it matters, suggested resolution. Cite directives where applicable.}

(repeat per finding)

(or "No findings — the artifact is clean against the loaded directives and codebase patterns.")
````

No verdict block. No verification table. No severity-tier headings.

## Step 9: Present

**For code-shaped classification:**

```
Review done — report saved to {path}

{verdict}

{count} findings: {N} critical, {N} high, {N} medium, {N} low, {N} test gaps, {N} deferred

Agents used: {list}
```

**For non-code classification:**

```
Review done — report saved to {path}

{count} findings: {breakdown by label, e.g., 2 ambiguities, 1 blind spot, 1 pattern-break}

Agents used: {list}
```

**Manifest notes (non-blocking).** Append, when recorded:
- The excerpt log line (`PATTERNS excerpt: …`) verbatim.
- Commit-based staleness (`stale: yes`): `PATTERNS manifest may be stale — consider re-running /comb:patterns.` When `stale: unknown`: `PATTERNS staleness unknown (<detail>).`
- Semantic refresh: `This diff evolves a convention not in the manifest — consider re-running /comb:patterns to capture it.`

Then, last of all, remove this run's excerpt and brief working files (they share the stem): `python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/manifest.py" clean --run <run>`.

## Ground rules

- **Read-only.** Nobody edits code. The only files created are the report and this run's excerpt and brief working files under `.comb/excerpts/`, which are removed at the end.
- **Agents read actual source code.** Not just filenames.
- **The report's voice is authoritative.** Step 7's verification gate is what earns it. A particular that survived no check is marked, not stated.
- **Project-aware.** Every agent gets the project's directives.
- **Severity is honest.** Critical means production bugs.
- **Round-aware.** The report filename includes round N, parsed from existing filenames by `comb.py report-name` (Step 8). Prior reports are not parsed for fixed-findings status — agents may flag items that already shipped in a prior round.

## Edge case: focus brief contradicts shipped behavior

If the brief implies altering shipped flow ("skip the report", "use only one agent", "write somewhere else"), surface the conflict and ask once before proceeding.
