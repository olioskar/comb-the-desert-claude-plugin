---
name: plan
description: Use after a comb review when the user wants the findings translated into executable fix instructions.
argument-hint: "[report-path] [focus brief]"
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Agent
user-invocable: true
disable-model-invocation: false
---

You are running step 2 of the comb workflow: review → plan → fix.

You're a senior engineer turning review findings into crystal-clear fix instructions. Each finding gets its own specialist who reads the actual code and writes instructions good enough for any developer to execute cold.

## Inputs

1. **Report**: should be in conversation context, or user provides a path. Look in `<paths.plans>` parent directory or `<paths.reviews>` for the most recent report if not specified.
2. **Focus brief**: `$ARGUMENTS` — carries through from review when invoked via `/comb:the-desert`.

## Step 1: Load config

Load the merged config per `${CLAUDE_PLUGIN_ROOT}/shared/config-loading.md`:

```
python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/comb.py" config
```

Run it from the project root and read its JSON output; it is the merged config. A non-zero exit names the bad file — stop and show it.

From it, take:
- `paths.plans` — output folder root
- `models.plan` — model for planner agents
- `directives` — for the planners' agent prompts
- `paths.patterns` — the PATTERNS manifest, if it resolves

**Load the PATTERNS manifest.** If `paths.patterns` resolves, record its path; do not read it. The excerpt is cut after Step 3 (below). If absent or `null`, skip — graceful no-op.

## Step 2: Surface relevant directives

Apply the focus-brief matcher in `${CLAUDE_PLUGIN_ROOT}/shared/directive-matching.md`. It records the matched directive paths and flags them as **primary** in the run brief under "Directives most relevant to this run"; an empty focus brief flags nothing, and all directives still load normally.

```
python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/comb.py" directives --brief "<focus brief>"
```

Record the `plugin:` and `user:` paths and the `primary:` lines; `comb.py brief` renders them into every run brief.

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

Run the parser first:

```
python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/comb.py" findings --report <report path>
```

Its JSON lists every finding the template carries (`code`, `title`, `source`, `files`, `verified`) and its `shape` confirms Step 2.5. When it prints `count: 0` or `shape: unknown`, the report is not in the template shape: read it and extract by hand as below.

Each finding carries:
- **Reference code**: C1, H2, M5, T1, D1, etc. Preserve exactly as the report uses them.
- **Title**: short description
- **Category** / **severity**: as the report uses
- **File(s)**: paths and line numbers
- **Description**: what's wrong, why
- **Suggested fix**: if the report includes one
- **Verification status**: the finding's `Verified:` line. Preserve it verbatim. A report written before this field existed carries none — treat every particular in such a finding as unconfirmed.

**Include Deferred items.** Don't drop them. "Deferred" is *noted, explicitly out of scope for the current round* — but the user often picks them up while in the area. Each deferred item gets the same per-finding plan file as everything else. The user is the gate, not the planner.

If the Deferred section uses bullet points without codes (older review reports), assign `D1`, `D2`, … inline before dispatching agents, in the order they appear.

Count every code (C/H/M/L/T/D) — the script's `count` when it parsed. Confirm the total with the user before sending agents.

**On a non-code report:** findings have plain labels (Ambiguity, Blind spot, Pattern-break, Reusability gap, Quality concern), not severity codes. Preserve the labels verbatim. The ordering for the consolidated revise-doc follows the report's order — no severity-based reshuffle. Skip the "confirm total with user" step; the count is just the number of findings.

**Cut the manifest excerpt** (only when `paths.patterns` resolved), per `${CLAUDE_PLUGIN_ROOT}/shared/manifest-slicing.md`, with the report as the touched text:

```
python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/manifest.py" excerpt --skill plan --manifest <paths.patterns> --touched-from <the review report>
```

Run it from the project root.

Record `run`, `excerpt`, the log line, and `stale`. On the contract's fallback condition, print the fallback notice and deliver the full path alone.

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

Dispatch one planner agent, resolved and briefed exactly as the code-shaped flow below resolves and briefs its planners (`comb.py resolve --role implementer --lane plan`, then `comb.py brief --skill plan --role implementer …`), with this prompt structure (shared context, the run brief, then its own job and output format):

````
You're a senior reviewer translating a spec/design-doc review into a single consolidated revision-instructions file.

## 1. Shared context

Repository: {project-root}
Branch: {branch}
Spec under revision: {spec_path}
Report: {report-path}
Output file: {output_folder}/revise-{spec-stem}.md

Read first: {run brief path printed by `comb.py brief` (skill plan, role implementer)}

## 2. Your job

You are writing ONE consolidated revision-instructions file for the spec under review. The findings in the report are the spec for your work.

### What to do

1. Read the report at the path above (its `## Findings` section is your work list), then the spec file: {spec_path}
2. For each finding, open the spec at the cited section or line. Confirm the finding's quoted text and its anchor are accurate before you write the revision. Correct any anchor that does not resolve, and state the correction in that revision's **Reason** line. The finding's `Verified:` line states what the review confirmed; re-derive anything it names as unchecked. When a finding carries no `Verified:` line, treat its anchor and its quoted text as unconfirmed.
3. Identify the exact section or line to revise.
4. Write a single file at `{output_folder}/revise-{spec-stem}.md` consolidating all revisions in the order findings appear in the report. Each revision is a section with the finding's original label and title.

## 3. Output format

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

Launch all in parallel per the delivery contract (`${CLAUDE_PLUGIN_ROOT}/shared/dispatch-delivery.md`) — one Agent call per finding (or group), batched in a single assistant message.

**Agent config (resolved per finding):**

- **Pick a specialty lens.** For each finding, the orchestrator picks one role from `config.agents` whose `when_to_use` best matches the finding's specialty (general correctness → `code-reviewer`, simplification/abstraction concerns → `simplifier`, error-handling → `silent-failure-hunter`, test gaps → `test-auditor`, pattern/spec drift → `consistency-auditor`). When no role obviously matches, default to `code-reviewer`. The lens informs the dispatch prompt's framing and is recorded in the plan file's `**Specialty:**` header — it is **not** the subagent_type that runs.
- **Resolve the writer role** (the planner needs Write access; the `comb:*` review roles cannot write, and the user's `agents.implementer` override is honored):

  ```
  python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/comb.py" resolve --role implementer --lane plan
  ```

  Pass `model:` as the Agent call's `model` and `effort:` as `effort` unless `unset`; `native:` is the brief's form.
- **Write the run brief** once per run (every planner shares it):

  ```
  python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/comb.py" brief --skill plan --role implementer --run <run> --excerpt <excerpt> --manifest <paths.patterns> --brief "<focus brief>"
  ```

  Omit `--excerpt` and `--manifest` when no manifest resolved and `--brief` when the focus brief is empty. `<run>` is the stem the Step 3 excerpt printed. When no excerpt was cut this run, omit `--run` on the first `brief` call, record the `run:` it prints, and pass that stem as `--run` to every later `brief` call and to the final `clean`. Echo the four lines it prints; its `brief:` path goes into the prompt.
- **Delivery contract:** `${CLAUDE_PLUGIN_ROOT}/shared/dispatch-delivery.md`.

**Planner dispatch prompt (5-part order):**

```
You're a senior {specialization-derived-from-finding} developer. You've been assigned one review finding to write fix instructions for.

## 1. Shared context

Repository: {project-root}
Branch: {branch}
Base: {base}
Report under planning: {report-path}
Output folder: {output-folder}
Reference code: {reference_code}
Severity: {severity}
Specialty source: {source agent(s) from the finding's `*Source:*` line}
Output file: {output-folder}/{reference_code}-{title-slug}.md

Files referenced by the finding: {file-paths}
Adjacent files worth scanning: {2–3 nearest siblings the orchestrator picks}

Read these first, in order: ${CLAUDE_PLUGIN_ROOT}/shared/plan-brief.md, {run brief path printed by `comb.py brief`}

## Finding

### {reference_code}. {title} ({severity})

**Verified (from the review report):** {the finding's `Verified:` line, verbatim, or "none — the report predates this field"}

{full_finding_description}
```

## Step 7: Collect results

**Count before presenting (code-shaped only).** List `{output_folder}/*.md` and take each file's leading code (`C1`, `H2`, `G1`, …). Compare with the code list from Step 3 (groups replace their consolidated codes). A code with no file → re-dispatch that planner once; still missing → say so under the list as `Missing: {codes} — planner wrote no file`, and do not count it in `All {N}`. A file whose code is not in the list → report it as `Unexpected: {file}`. This is a listing comparison; it does not read the files.

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

Next: /comb:fix {output_folder}
```

**Non-code report — present the single revise-doc:**

```
Revision instructions ready: {output_folder}/revise-{spec-stem}.md

{N} revisions targeting `{spec_path}`: {breakdown by label}

Next: /comb:fix {output_folder}
```

The `Next:` line names `/comb:fix`, the command the user types. Never point the user at the `fix-auto` skill; it is model-only and cannot be typed.

**Manifest notes (non-blocking).** Append the excerpt log line verbatim, then any staleness note (`stale: yes` → `PATTERNS manifest may be stale — consider re-running /comb:patterns.`; `unknown` → `PATTERNS staleness unknown (<detail>).`) or semantic-refresh note recorded during this run. Then, last of all: `python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/manifest.py" clean --run <run>`.

## Ground rules

- **Every item** in the report gets its own instruction file. Don't skip deferred items or test gaps — they all get documented.
- **Agents read source code.** They don't just parrot the review.
- **Instructions are self-contained.** Anyone picking up one file has everything they need to execute without reading the original report.
- **Scope boundaries are explicit.** Every instruction states what's in and out of scope.

## Edge case: focus brief contradicts shipped behavior

Per `/comb:review`.
