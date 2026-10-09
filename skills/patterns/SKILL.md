---
name: patterns
description: Use when the user wants to set up, generate, or refresh comb's PATTERNS manifest — the project-specific record of concrete conventions (structure, naming, closed sets, abstraction, reuse, error handling, testing) that /comb:review, /comb:plan, and /comb:fix consume as an observed baseline — or wants to shave, shrink, or compress an existing manifest (`--shave`).
argument-hint: "[--shave] [focus brief]"
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

1. **Mode.** If `$ARGUMENTS` contains `--shave` anywhere, or the request is to shave, shrink, or compress the manifest, enter **Shave mode** (below) directly after Step 1 and skip Steps 2–8. Otherwise run the generate flow (Steps 2–9).
2. **Focus brief** — the rest of `$ARGUMENTS` (optional). In generate mode it biases which lenses the scanners weight; in shave mode it narrows which sections are dispatched (e.g. "only sections 16–18").

## Step 1: Load config

Load the merged config per `${CLAUDE_PLUGIN_ROOT}/shared/config-loading.md` (three layers, deep-merge; arrays replace; `null` deletes; invalid JSON is a hard error).

After merging, take:
- `paths.patterns` — where the manifest is written/read (default `docs/combs/PATTERNS.md`). If it is `null`, there is no write target (the key was deleted via merge semantics, so there is no default to fall back to): report that manifest consumption is disabled and stop. Do not generate to an undefined path.
- `models.patterns` — model for the scanner agents (default `opus`).
- `agents.pattern-scanner` — the scanner role (`subagent_type`, default `comb:pattern-scanner`).
- `directives` — the loaded directive set. Read each directive's name and its opening purpose line; you map directives to areas at the gate (Step 3) and dispatch each scanner only the directives relevant to its area (Step 5). **Authority is the user's call at the gate, never the scanner's** — every dispatched directive is authoritative unless the user down-weights it. If a directive's name or frontmatter self-marks as draft/WIP/superseded/non-authoritative, note it and pre-flag it at the gate as a *suggested* down-weight (the user confirms); a scanner is never told to disregard a directive on its own judgment.

## Step 2: Recon the codebase shape

Do a fast shape pass — **do not deep-read files yet**. Detect the codebase's regions from generic signals:

- **Manifest/build files** anywhere in the tree (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `composer.json`, `pom.xml`, `build.gradle`, `*.csproj`, `Gemfile`, `mix.exs`, `Package.swift`, `pubspec.yaml`, etc.).
- **Top-level and second-level directory structure.**
- **Language/extension mix** (e.g. `git ls-files` and tally extensions).

From these, propose a set of **scan areas**. Each area is a **label** + a **path scope** (paths/globs). Examples of areas, not a fixed list — derive them from what's actually present: "React frontend (`src/web/**`)", "Java API (`service/src/main/java/**`)", "Shared types (`packages/types/**`)", "Data layer (`**/repositories/**`, `**/migrations/**`)", "Infra (`deploy/**`, `*.tf`)".

Trust the model: detect shape from the signals above, not a hardcoded framework table.

**Also flag non-authoritative regions — do not propose them as scan areas.** A scanner that reads dead or vendored code launders stale patterns into the manifest (the same failure the directive-precedence rule guards against, one level up). Detect and set aside:

- **Generated / build output** — `_site/`, `dist/`, `build/`, `out/`, `coverage/`, `__generated__/`, anything a build step emits.
- **Vendored / third-party** — `node_modules/`, `vendor/`, bundled libraries.
- **Reference-only / legacy** — directories the project itself marks as not-in-build or superseded. Read `CLAUDE.md` (and obvious names like `mockup/`, `legacy/`, `deprecated/`, `archive/`, `examples/`) for explicit "reference-only", "not in the build", or "pre-<framework>" statements. When `CLAUDE.md` says a path is reference-only, that is authoritative — exclude it by default.

`git ls-files` already drops gitignored paths; this step catches the **tracked-but-non-authoritative** ones git won't. Carry the excluded list (one-line reason each) into the gate so the user can re-include any.

## Step 3: Confirm the scan plan (interactive gate)

This is the one hard stop. Present everything the user can steer in a **single batched prompt** — areas, excluded regions, the directive→area mapping, and directive currency — so they answer once and reply "go". Never drip these as separate questions.

For the mapping, match each directive to the areas it plausibly governs from its name and purpose line (e.g. a CSS/token directive → the styling area; an API-error directive → the service area). A directive may map to several areas; a broadly-applicable one (naming, simplicity) maps to all.

If Step 1 pre-flagged a directive as self-marked draft/WIP, show it in the AUTHORITATIVE list annotated `(looks draft — down-weight?)` so the user can accept with one word. It stays authoritative unless they down-weight it — the scanner never disregards it on its own.

```
Scan plan — adjust anything, then reply "go":

AREAS (one scanner each):
  1. {label} — {path scope}   ·  directives: {short names mapped here}
  2. {label} — {path scope}   ·  directives: {…}
  ...

EXCLUDED (non-authoritative — won't be scanned):
  - {path} — {build output | vendored | reference-only per CLAUDE.md | generated}
  (reply to re-include any, or name others to exclude)

DIRECTIVES treated as AUTHORITATIVE ({N}): {list short names}
  (flag any that are superseded/draft — down-weighting one stops a widespread
   practice that contradicts it from being recorded as drift)

Add / remove / rename / merge / rescope areas · fix the directive mapping ·
change exclusions · down-weight a stale directive · or "go" to accept all.
```

Defaults make "go" safe: the proposed areas, the exclusions, the mapping, and "all directives current" all apply as shown unless the user changes them. Apply edits and re-show only if the changes were non-trivial. **Nothing dispatches until the user confirms.**

## Step 4: Existing-manifest check

If `paths.patterns` resolves to an existing file, ask how to proceed **before** dispatching:

```
A manifest already exists at {paths.patterns} (generated {its Generated date}).
  (a) Regenerate — scan fresh, then show you a diff to approve/reject/cherry-pick per section
  (b) Cancel
Pick one:
```

Default is (a). Partial updates are handled by two explicit, user-driven mechanisms — the section-level cherry-pick at diff time and the single-area re-scan in the pre-write review (both in Step 8). Neither is automated merging.

## Step 5: Dispatch scanners

For each confirmed area, dispatch one scanner. **Launch them in parallel** per the delivery contract (`${CLAUDE_PLUGIN_ROOT}/shared/dispatch-delivery.md`) — one Task call per area, batched in a single assistant message.

**Resolution per scanner:**
- **`subagent_type`** from `agents.pattern-scanner.subagent_type` (default `comb:pattern-scanner`).
- **Model**: `agents.pattern-scanner.model` if set; otherwise `models.patterns` (default `opus`). Pass the resolved model as the Task call's `model` parameter, per the delivery contract.
- **Directives for this scanner = the subset mapped to its area at the gate (Step 3)** — not the full set. Send a scanner only the directives the gate mapped to its area; this keeps each scanner's lenses tight (a CSS scanner shouldn't carry an API-error directive). Any directive the user **down-weighted** at the gate that maps to this area is still sent, but marked `SUPERSEDED — treat as NON-authoritative`.
- **Delivery**: supply the mapped directives as absolute **paths** per the delivery contract; a foreign resolved `subagent_type` additionally gets the contract's authority sentence, never embedded contents.

**Scanner dispatch prompt:**

```
You're a read-only convention scanner. Map ONE area and report its concrete, established conventions with exact code references.

## 1. Shared context

Repository: {project-root}
Area: {area label}
Scope (paths/globs): {area path scope}
comb version: {version}

## 2. Directives for your area (your lenses AND your baseline)

These define the KINDS of conventions that matter AND set the authoritative baseline those conventions must respect. Find this codebase's CONCRETE answers *within* this framework — never record a deviation *from* an authoritative directive as if it were the convention. Directives outrank anything you observe.

{List ONLY the directive paths mapped to this area at the gate. If the scanner is foreign per the delivery contract, precede the list with the contract's authority sentence.}

{If any directive mapped to this area was down-weighted at the gate, list it under a "SUPERSEDED — treat as NON-authoritative" subheading: a widespread practice that conflicts with a superseded directive is the codebase's current norm — record it as the convention, do not treat it as drift or a conflict.}

## 3. User focus for this run

{focus_brief if present, verbatim. Otherwise: "None."}

## 4. Your job

Walk the files in your area's scope. For each thematic lens, extract the concrete convention this area actually follows — a fact with a real reference, not a restated principle. Omit any lens with no real convention. Cite `path:line` on every entry plus a canonical example.

Classify every candidate convention against the directives before recording it:
- Conforms to a directive, or no directive covers it (net-new) → record it.
- Conflicts with a directive but is a MINORITY in your area (the rest follows the directive) → drift, not a convention. Do not record it; record the directive-conforming norm instead.
- Conflicts with a directive but is the DOMINANT, consistent practice in your area → record the directive-conforming expectation in the manifest body, and report the conflict under `## Directive conflicts` (see Output format) for a human to reconcile. Never launder a deviation into "a new or improved pattern." **Dominance is measured area-wide:** the population is every instance of that lens across the whole area, never a single component. If every other instance of the lens follows the directive and only one component deviates, that is the MINORITY case (drift) no matter how consistent it is within that component — do not narrow the denominator to make it look dominant.

Lenses: Structural conventions; Naming & vocabulary; Closed sets (enumerate them); Abstraction calibration; Reuse points; Error handling & async; Testing conventions.

## 5. Output format

Markdown only, no preamble. One `## {area label}` block with only the non-empty `### ` thematic subsections, each a bulleted list of facts with `path:line` references.

Emit a `## Directive conflicts` section ONLY if at least one DOMINANT practice in your area conflicts with an authoritative directive — `{practice} conflicts with {directive}.md §{N} — dominant ({k}/{n} files), e.g. path:line; reconcile: update directive or treat as drift`. If you have no dominant conflict, emit NOTHING for this section — no heading, not even a parenthetical "(none — …)" explaining the absence. Do not narrate why there is no conflict; omit the section. A minority deviation is never placed under this heading in any form. "Dominant" = a clear majority of the area's instances of that lens, measured **area-wide** — never narrowed to one component where the deviation happens to be universal (that gerrymanders a minority into a false dominant). This section is NOT manifest content; the orchestrator extracts it.
```

## Step 6: Synthesize the manifest (in memory)

Assemble the manifest **in memory** — writing happens in Step 9, after the interactive review, so the file reflects any conflict resolutions and re-scans.

**Strip and filter the conflicts channel:**
1. Remove every `## Directive conflicts` section from each scanner's reply — never manifest content.
2. From the collected conflicts, **drop any item whose own text self-identifies as a minority / drift / "for awareness"** (a scanner may mis-place one under the heading despite the rule), and drop any that doesn't state clear dominance (a `{k}/{n}` majority). **Also drop any item whose own text reveals the rest of the area follows the directive** — phrases like "every other … uses the directive's form", "the lone exception", "while all other variants use …". That is a gerrymandered denominator (dominance scoped to one component), i.e. a misclassified minority, not a real dominant conflict. Only genuine *dominant* conflicts — a clear area-wide majority — survive to Step 7.

Assemble **area-major**: each area a top-level `##` section; within it the thematic `###` subsections returned (empty ones omitted). Deduplicate repeated entries within an area. The manifest body records only directive-conforming conventions.

Read the comb version from `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` (`version` field) and the base commit from `git rev-parse HEAD`. Render the manifest text in memory using this template:

```markdown
# PATTERNS — {repo name}

**Generated:** {YYYY-MM-DD}
**Base commit:** {sha}
**comb version:** {version}
**Scan areas:** {comma-separated confirmed area labels}

> Observed baseline, not law. comb's reviewers reconcile this against live code
> (live code wins), treat a silent area as a cue to read the code rather than
> permission to do anything, and classify divergence (drift vs. deliberate
> improvement vs. new canonical) before flagging. Project directives outrank
> this manifest. Refresh with `/comb:patterns`.

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

Hold this rendered text for Steps 7–8; you write it to `paths.patterns` (creating the directory if needed) in Step 9.

## Step 7: Reconcile dominant conflicts (interactive — only when Step 6 left any)

If no dominant conflict survived Step 6, skip this step.

For each surviving dominant conflict, walk the user through it and apply their choice to the in-memory manifest. Batch the questions — present them together, one decision each:

```
Dominant conflict in {area}:
  {practice} — used in {k}/{n} files (e.g. `path:line`)
  conflicts with {directive}.md §{N}, which prescribes {one-line restatement}.

How should the manifest treat this?
  (a) Directive is stale — record the practice as the new canonical norm
  (b) It's drift — keep the directive's expectation; list the offending files to fix
  (c) Skip — leave unresolved (surfaced as a note; manifest keeps the directive's expectation)
```

Apply each choice to the in-memory manifest:
- **(a) stale** → replace that area's directive-conforming entry with the actual practice as the convention, tagged `> supersedes {directive}.md §{N} (user-confirmed)`. Collect it for a "directives to update" line in Step 9.
- **(b) drift** → keep the directive-conforming entry unchanged; collect the offending `path:line`s for a "drift to fix" list in Step 9.
- **(c) skip** → no manifest change; the conflict carries to the ⚠ block in Step 9.

**Near-total conflicts (k ≈ n — the practice is essentially universal in the area).** Add a one-line note to that conflict's prompt surfacing the fork instead of guessing: **(a)** records reality (the directive is stale and nobody follows it); **(b)** keeps the directive's expectation as the recorded convention *even though no file currently follows it* — correct only if it is a new or aspirational standard the team is actively migrating toward, in which case the manifest entry is a target, not an observation. Make that consequence explicit so the user doesn't pick (b) and unknowingly write a convention the codebase doesn't exhibit.

This is the headline of the interactive flow: it resolves the stale-directive-vs-drift ambiguity at generation time, so the manifest is right immediately instead of after a human eventually circles back. Offer a single "skip all — reconcile later" escape that routes every conflict to (c).

## Step 8: Pre-write review (interactive)

Before writing, show a compact summary so the user can catch a mis-scoped area before it's baked in:

```
Scan summary — review before write:
  {area} — {entry count} entries across {lens count} lenses{ · ⚠ thin: only {lens} populated | · ⚠ empty}
  ...
  {if Step 7 ran: conflicts — X recorded as new norm / Y kept (drift) / Z skipped}

Reply "write" to save · "rescan {area} [new scope/notes]" to re-run one area · or adjust.
```

**Empty or thin areas are a mis-scope signal** — e.g. an "error-handling lens nearly empty" cue usually means that area's logic lives somewhere the scope missed. Flag them explicitly; don't make the user eyeball every long return to notice.

**Single-area re-scan.** If the user asks, re-dispatch exactly one scanner (Step 5 mechanics) for that area with any new scope/notes, replace that area's section in the in-memory manifest, and re-show this summary. Explicit, user-requested — not automated merging.

**Regenerate diff (only when Step 4 found an existing manifest).** Once the user is satisfied, show a diff of the new manifest against the existing file and let them cherry-pick **at the section level**: per changed section, keep existing or take regenerated. Explicit selection at diff time, not automated merge. The result is what gets written.

## Step 9: Write and present

Write the assembled (reconciled, re-scanned, cherry-picked) manifest text to `paths.patterns`, creating the directory if it doesn't exist. Then run `python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/manifest.py" index --manifest <paths.patterns>` for the size line (its last lines: total bytes, `~tokens (bytes/4)`, section counts, and the `Large manifest` notice above 100 KB), then present:

```
PATTERNS manifest written to {paths.patterns}

Areas: {N} ({labels})   ·   Excluded: {count} non-authoritative regions
Captured: {one-line summary, e.g. "structural + closed-set conventions for 3 areas, 27 entries"}
Size: {total bytes}B ~{tokens} tokens; {area} area, {global} global sections{ · Large manifest — consider /comb:patterns --shave}

Consumed automatically by /comb:review, /comb:plan, /comb:fix when present (as a per-run excerpt).
```

Then `python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/manifest.py" clean --run <run>` for the index run.

**Reconciliation outcomes (only when Step 7 ran).** Append whichever apply — these turn the old dead-end warning into an actionable result:

```
Directives to update ({count}) — the manifest now records the practice as canonical, but the directive text still says otherwise:
  - {directive}.md §{N}: "{practice}" is now the recorded norm in {area}

Drift to fix ({count}) — the manifest keeps the directive's expectation; these files diverge:
  - {directive}.md §{N} in {area}: {path:line}, {path:line}

⚠ Unresolved conflicts ({count}) — skipped for later reconciliation:
  - [{area}] {practice} vs `{directive}.md §{N}` — dominant ({k}/{n}), e.g. `path:line`
```

## Shave mode (`--shave`)

Reduce the manifest's token cost without changing what it asserts. Rules for everyone involved: `${CLAUDE_PLUGIN_ROOT}/shared/shave-rules.md`. Requires an existing manifest at `paths.patterns`; otherwise report `No manifest at {paths.patterns} — run /comb:patterns to generate one first.` and stop.

**S1. Index.** Run:

```
python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/manifest.py" index --manifest <paths.patterns>
```

Run every `manifest.py` command from the project root. It prints `run: <stem>`, `index: <path>`, one line per section (`<kind> <START>-<END> <bytes>B [<n>] <heading> edits=<path>`), and the totals. Record `run` and `index`. Show the per-section lines and totals to the user as the size table. Do not read the manifest or the index file.

**S2. Dispatch shavers.** If no area section is 4 KB or more (after any focus-brief narrowing), report `Nothing to shave: no area section is 4 KB or more` and stop with `clean`. Otherwise one shaver per **area** section of 4 KB or more, at most five at a time, per `${CLAUDE_PLUGIN_ROOT}/shared/dispatch-delivery.md`. Role: `agents.pattern-shaver` (`subagent_type`, default `comb:pattern-shaver`); model: `agents.pattern-shaver.model` if set, else `models.patterns`, passed as the Task call's `model` parameter. Header and global sections are never dispatched or edited. Dispatch prompt:

```
You shave ONE section of a PATTERNS manifest. You edit nothing except the one edit-script file named below. Rules: read ${CLAUDE_PLUGIN_ROOT}/shared/shave-rules.md first and follow it exactly.

Manifest: <absolute paths.patterns>
Index: <absolute index path>
Your section: "<heading>" — lines <START>-<END> (open with: sed -n START,ENDp <manifest>)
Write your edit script to: <absolute edits path from the index line>

Write that file with a Bash heredoc, then reply with its path and the edit count.
```

A foreign `subagent_type` gets the same prompt; the rules file carries the full contract.

**S3. Collect.** A reply that names no file, or names a file that is missing, is recorded as `section <heading>: no usable edit script, skipped`. A file that exists but is not valid JSON is reported by `verify` as `UNUSABLE` and skipped the same way. Nothing is merged or retyped by hand. If no shaver produced a file, report `Nothing to shave: no usable edit script` and stop with `clean`.

**S4. Verify.** Run, listing every edit file the shavers wrote:

```
python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/manifest.py" verify --manifest <paths.patterns> --index <index> --edits <edits-n.json ...> --out .comb/excerpts/<run>.passing.json
```

It prints one line per edit (`ok` or `FAIL … : <check>`), one `UNUSABLE <file>: <why>` line per edit file it could not parse, and a summary, and writes the passing set. A non-zero exit means some edits or files were rejected, not that the run failed; the passing set is always written. **Bound:** verify checks the mechanical properties in the rules file only; it does not judge whether a surviving anchor still supports its claim, does not open the codebase, and does not evaluate the shaver's comparison.

**S5. Gate** (shave mode's one hard stop; no default). Run:

```
python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/manifest.py" gate --edits .comb/excerpts/<run>.passing.json
```

Show its output verbatim: per section the counts by class and bytes removed, every `duplicate` in full (`old` → `new`, owner), every `anchor` as the dropped anchor and its line, every `fixed-drift` as the line, and the rejected edits with their checks; past 200 lines of full text the duplicates collapse to one line each. Replies: `apply`; `skip <class>` or `skip <section>` (run `python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/manifest.py" filter --edits <passing> --skip-class … --skip-section … --out .comb/excerpts/<run>.final.json`, then show the gate again for the final file); `show <section>` (run `gate … --show "<heading>"`). Nothing is applied until the user says `apply`.

**S6. Write.** Run:

```
python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/manifest.py" apply --manifest <paths.patterns> --index <index> --edits <final or passing file> --stamp
```

All-or-nothing: it re-verifies against the current text and refuses if anything no longer verifies. `--stamp` writes `**Shaved:** <date> (<before> → <after> bytes)` into the header (replacing an earlier one). It prints the applied count, the before/after bytes, and the token estimate; present them with the counts `verify` and `filter` printed:

```
Manifest shaved: {applied} edits applied ({skipped by the user} skipped, {rejected} rejected, {unusable} unusable files)
Size: {before}B → {after}B (~{tokens} tokens)
```

and finish with `python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/manifest.py" clean --run <run>`. Step 9's generate presentation does not apply to shave.

## Ground rules

- **Interactive before heavy work, but never naggy.** One hard stop per mode: the scan plan (Step 3) in generate mode, the shave gate in shave mode. In generate mode also confirm before overwriting an existing manifest (Steps 4, 8). Batch every gate into one prompt with safe "go"/"write" defaults — never drip questions one at a time, and never ask what recon already detected. The interactive steps that involve the user (3, 7, 8) only stop when there's a real decision to make: Step 7 fires only when dominant conflicts exist, Step 8's re-scan only when the user asks.
- **Scanners never edit; shavers write one file.** `comb:pattern-scanner` never edits. `comb:pattern-shaver` writes only the one edit-script file it is told to write, with a Bash heredoc. This orchestrator writes the manifest and, through `scripts/manifest.py`, the run's working files under `.comb/excerpts/`; nothing else.
- **Shave never rescans.** It reads code only to confirm two anchors pin one convention. In shave mode the orchestrator never reads the manifest; it reads the script's output and the shavers' replies.
- **Facts, not principles.** Every entry cites real code. Omit empty lenses rather than padding.
- **Full scan lives here only.** The consuming skills never re-scan the whole codebase; they read this manifest plus the files around their diff.
