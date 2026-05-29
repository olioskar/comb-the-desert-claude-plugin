---
name: patterns
description: Scan the codebase and generate or refresh the PATTERNS manifest — a project-specific record of concrete conventions (structural patterns, naming & vocabulary, closed token/enum sets, abstraction calibration, reuse points, error/async patterns, testing conventions) with real code references. The manifest feeds /comb:review, /comb:plan, and /comb:fix as an observed-baseline context block. Use when the user wants to set up, generate, or refresh comb's project conventions manifest.
argument-hint: "[focus brief]"
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Task
user-invocable: true
disable-model-invocation: false
---

You generate or refresh the **PATTERNS manifest** — a persisted, project-specific record of the codebase's *concrete, observed conventions with references to real code*. The manifest is the concrete instantiation of comb's directive principles: a directive says *use the codebase's vocabulary*; the manifest records *the vocabulary is `worksite`, `job`, `crew`, canonical at `src/domain/Worksite.ts:1`*.

This is an **interactive** command. You do recon, propose scan areas, and wait for the user to confirm before dispatching any agents.

## Inputs

1. **Focus brief** — `$ARGUMENTS` (optional). Biases which lenses the scanners weight.

## Step 1: Load config

Read the layered config, deep-merging each layer onto the previous:

1. `${CLAUDE_PLUGIN_ROOT}/config/defaults.json` — shipped defaults
2. `~/.claude/comb.config.json` — global override (skip if absent)
3. `<project-root>/.claude/comb.config.json` — project override (skip if absent)

**Project root** is `git rev-parse --show-toplevel` (cwd fallback when not in git). Merge rules are the same as `/comb:review` (objects deep-merge; arrays replace; `null` deletes; invalid JSON is a hard error).

After merging, take:
- `paths.patterns` — where the manifest is written/read (default `docs/combs/PATTERNS.md`). If it is `null`, there is no write target (the key was deleted via merge semantics, so there is no default to fall back to): report that manifest consumption is disabled and stop. Do not generate to an undefined path.
- `models.patterns` — model for the scanner agents (default `opus`).
- `agents.pattern-scanner` — the scanner role (`subagent_type`, default `comb:pattern-scanner`).
- `directives` — the scanners use the directive set as their lenses.

## Step 2: Recon the codebase shape

Do a fast shape pass — **do not deep-read files yet**. Detect the codebase's regions from generic signals:

- **Manifest/build files** anywhere in the tree (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `composer.json`, `pom.xml`, `build.gradle`, `*.csproj`, `Gemfile`, `mix.exs`, `Package.swift`, `pubspec.yaml`, etc.).
- **Top-level and second-level directory structure.**
- **Language/extension mix** (e.g. `git ls-files` and tally extensions).

From these, propose a set of **scan areas**. Each area is a **label** + a **path scope** (paths/globs). Examples of areas, not a fixed list — derive them from what's actually present: "React frontend (`src/web/**`)", "Java API (`service/src/main/java/**`)", "Shared types (`packages/types/**`)", "Data layer (`**/repositories/**`, `**/migrations/**`)", "Infra (`deploy/**`, `*.tf`)".

Trust the model: detect shape from the signals above, not a hardcoded framework table.

## Step 3: Propose areas and confirm (interactive gate)

Present the detected areas and their path scopes, and ask the user to adjust:

```
Detected scan areas:
  1. {label} — {path scope}
  2. {label} — {path scope}
  ...

Add, remove, rename, merge, or rescope any area. Reply "go" to scan as-is.
```

**Nothing dispatches until the user confirms.** This is the only hard stop in the flow. Apply their edits and re-show if they made non-trivial changes.

## Step 4: Existing-manifest check

If `paths.patterns` resolves to an existing file, ask how to proceed **before** dispatching:

```
A manifest already exists at {paths.patterns} (generated {its Generated date}).
  (a) Regenerate — scan fresh, then show you a diff to approve/reject/cherry-pick per section
  (b) Cancel
Pick one:
```

Default is (a). Partial updates are handled by section-level cherry-pick at diff time (Step 7), not a separate per-area re-scan branch (kept out per spec §5).

## Step 5: Dispatch scanners

For each confirmed area, dispatch one scanner. **Launch them in parallel** by issuing multiple Task tool calls in a single assistant message — one per area. (Do not use `run_in_background: true`; that is a Bash-tool parameter and has no effect on the Task tool.)

**Resolution per scanner:**
- **`subagent_type`** from `agents.pattern-scanner.subagent_type` (default `comb:pattern-scanner`).
- **Model**: `agents.pattern-scanner.model` if set; otherwise `models.patterns` (default `opus`).
- **Allowlist match (literal string equality):** `comb:pattern-scanner` is native — supply directive **paths**. Any other resolved `subagent_type` is foreign — embed full directive **contents** with `## File: <path>` headers.

**Scanner dispatch prompt:**

```
You're a read-only convention scanner. Map ONE area and report its concrete, established conventions with exact code references.

## 1. Shared context

Repository: {project-root}
Area: {area label}
Scope (paths/globs): {area path scope}
comb version: {version}

## 2. Directives (your lenses)

These define the KINDS of conventions that matter. Find this codebase's CONCRETE answers within your area.

{If native: list directive paths — plugin defaults if include_plugin_defaults, plus user directives if directives.user_path resolves.}
{If foreign: embed full directive contents verbatim with `## File: <path>` headers.}

## 3. User focus for this run

{focus_brief if present, verbatim. Otherwise: "None."}

## 4. Your job

Walk the files in your area's scope. For each thematic lens, extract the concrete convention this area actually follows — a fact with a real reference, not a restated principle. Omit any lens with no real convention. Cite `path:line` on every entry plus a canonical example.

Lenses: Structural conventions; Naming & vocabulary; Closed sets (enumerate them); Abstraction calibration; Reuse points; Error handling & async; Testing conventions.

## 5. Output format

Markdown only, no preamble. One `## {area label}` block with only the non-empty `### ` thematic subsections, each a bulleted list of facts with `path:line` references.
```

## Step 6: Synthesize and write

Collect the scanner outputs. Assemble an **area-major** manifest: each area is a top-level `##` section; within it, the thematic `###` subsections returned for that area (empty ones omitted). Deduplicate repeated entries within an area.

Read the comb version from `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` (`version` field) and the base commit from `git rev-parse HEAD`.

Write to `paths.patterns` using this template:

```markdown
# PATTERNS — {repo name}

**Generated:** {YYYY-MM-DD}
**Base commit:** {sha}
**comb version:** {version}
**Scan areas:** {comma-separated confirmed area labels}

> Observed baseline, not law. comb's reviewers reconcile this against live code
> (live code wins), treat a silent area as a cue to read the code rather than
> permission to do anything, and classify divergence (drift vs. deliberate
> improvement vs. new canonical) before flagging. Refresh with `/comb:patterns`.

---

## {Area label}

_Scope: {path scope}_

### Structural conventions
- {convention} — `path:line` (canonical: `path:line`)

### Closed sets
- {set name}: `{value}`, `{value}`, … — `path:line`

(…only the non-empty thematic subsections, in lens order…)

## {Next area label}
…
```

If `paths.patterns` is in a directory that doesn't exist yet, create it.

## Step 7: Diff and confirm (only when a manifest already existed)

If Step 4 found an existing manifest and the user chose regenerate, do **not** overwrite silently. Show a diff of the freshly synthesized manifest against the existing file and let the user cherry-pick **at the section level**: for each changed section, keep the existing text or take the regenerated text. This is explicit user selection at diff time, not automated merging. Write the result. (If no manifest existed, just write.)

## Step 8: Present

```
PATTERNS manifest written to {paths.patterns}

Areas: {N} ({labels})
Captured: {one-line summary, e.g. "structural + closed-set conventions for 3 areas, 27 entries"}

Consumed automatically by /comb:review, /comb:plan, /comb:fix when present.
```

## Ground rules

- **Interactive before heavy work.** Always confirm areas (Step 3) before dispatching scanners. Always confirm before overwriting an existing manifest (Steps 4, 7).
- **Read-only scanners.** `comb:pattern-scanner` never edits. Only this orchestrator writes, and only the manifest file.
- **Facts, not principles.** Every entry cites real code. Omit empty lenses rather than padding.
- **Full scan lives here only.** The consuming skills never re-scan the whole codebase; they read this manifest plus the files around their diff.
