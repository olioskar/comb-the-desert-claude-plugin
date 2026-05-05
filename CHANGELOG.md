# Changelog

All notable changes to this plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] — 2026-05-05

### Added

- **`agents.implementer` config field.** New writer-capable agent slot used by `/comb:fix` and `/comb:plan` for any task that writes files. Defaults to `general-purpose` (Claude's built-in writer-capable subagent). User-overridable per-project. Replaces the broken v0.4.x picker that resolved to read-only `comb:*` review agents and caused real-world fix runs to fail (G4 implementer refused to write, G6 escalated, G8 applied inline by orchestrator without authorization, 2/9 plan agents returned content inline).
- **`fix.commit_per_item` config flag** (default `true`). Orchestrator commits each item's changes on reviewer PASS, with `<finding-code>: <title>` message. Solves the cumulative-diff false-positive problem (reviewer scope-creep flags from prior items leaking into the current diff). Opt out with `false` to keep the v0.4.x no-commits behavior.
- **Pre-flight check on dirty tree.** New Step 1.5 in `/comb:fix`. If the working tree is dirty when the run starts, a one-shot question asks: commit / stash / proceed-without-commits / abort. In `/comb:the-desert`, the question is the third allowed question (alongside scope-at-start and run-again-at-end), and only fires when dirty.
- **Specialty-matched fix-reviewer.** Plan files gain a `**Specialty:**` header line carrying the source-agent info from the review report. `/comb:fix` Step 4e routes the reviewer to the matching specialty (e.g., `consistency-auditor` for scope/pattern findings, `silent-failure-hunter` for error-handling findings) rather than always dispatching `test-auditor`. Fallback chain: `agents.test-auditor` → `agents.code-reviewer`.
- **`## Considered alternatives` section in plan files** (optional). ADR-style appendix listing rejected approaches with one-line "rejected because…" rationale. Main body remains the single executable path; alternatives are documentation only.
- **Trivial-only escape hatch.** After 3 implementer failures on an item classified trivial, the orchestrator may apply the fix inline. The reviewer step still runs. Standard items that hit 3 failures escalate to the user as before. Documents the prior undocumented G8 inline-edit behavior with safer bounds.

### Changed

- **`/comb:fix` reviewer's role is now strict plan-compliance.** The reviewer reads the plan, the implementer's report (including any new `## Divergences` section), and the actual diff; decides PASS/FAIL on whether the plan was executed (or whether reported divergences are justified). Was previously a more general "did the fix work and stay in scope" lens biased toward `test-auditor`'s specialty.
- **Implementer report format adds `## Divergences` section** (optional). Implementers list deviations from the plan's `## How` with one-line rationale per deviation. The reviewer evaluates each rationale rather than re-litigating the fix's design.
- **Planner-quality nudge.** `/comb:plan` dispatch prompt now asks the planner to mentally trace through the proposed fix's failure modes before recommending — particularly when correctness depends on a runtime invariant (closure state, async timing, render scheduling). Directly addresses the G6 case where Option A passed plan but failed structurally.
- **Picker default in `/comb:fix` Step 4d** changed from `code-reviewer` to `agents.implementer`. The role-from-config picker still picks a specialty *lens* for prompt framing, but the writer that actually runs is `agents.implementer`.

### Migration

All changes are additive at the config layer. Existing user configs deep-merge against the new defaults — no migration required. Users who explicitly worked around the v0.4.x bug by mapping `agents.<role>.subagent_type: "general-purpose"` should remove the override after upgrade; the new default kicks in cleanly. Users who prefer the v0.4.x no-commits behavior set `fix.commit_per_item: false`.

## [0.4.3] — 2026-05-05

### Fixed

- **`D`-code collision between Deferred (review) and Discovered (fix).** Both severities used `D1, D2, …` — a fix run that discovered new issues would have overwritten the review's deferred-item plan files. Discovered items now use `X{n}` ("extras found during execution"). Deferred items keep `D{n}`.
- **Branch slug for review filename.** Branches with `/`, whitespace, or other path-unsafe characters (e.g., `feature/foo bar`) would have written to a malformed report path (`branch-feature/foo bar-round1-report.md`). The Step 8 naming rule now slugifies the branch name (`/` and unsafe chars → `-`, collapse runs, trim trailing).

### Changed

- **Group naming convention codified.** `/comb:plan` Step 4 now specifies `G{n}` for grouped findings, sequential in user-acceptance order. Step 6 file-naming rule references this. Earlier versions left the group code as the planner's invention (your tero run picked `G1, G2, G4`); future runs will be deterministic.
- **`docs/superpowers/specs/2026-04-27-comb-the-desert-plugin-design.md` marked historical.** The spec was authoritative for v0.1.0; the plugin has evolved past it. Added an "Update 2026-05-05" note pointing readers to README/CHANGELOG/skill bodies as the current source of truth. The spec is retained for design rationale.

## [0.4.2] — 2026-05-05

### Changed

- **Trim 0.4.1's over-correction.** Replaced the per-language operator/syntax enumerations in `silent-failure-hunter.md` and the 13-row manifest+commands table in `/comb:review` Step 5 with abstract patterns and a flat manifest list. The model already knows that `?.` is JS/TS, `unwrap_or` is Rust, and `composer test` belongs to PHP — listing them inline added tokens without adding judgment. Same paradigm-spanning behavior, less prompt weight.

## [0.4.1] — 2026-05-04

### Changed

- **`silent-failure-hunter` is now language-neutral.** The agent prompt previously listed JS/TS-specific operators (`??`, `||`, `?.`, `.catch()`, "unhandled promise rejection", `console.error`) as fallback and async-error patterns. Generalized to span Rust (`?`, `unwrap_or`, `let _ = result`), Go (`_, err := …`, ignored returns), Python (`or`, `except: pass`), Java/C#/PHP (empty `catch {}`), and JS/TS (still covered). The agent will now reason about silent failures equally well across paradigms.
- **Review verification step recognizes more ecosystems.** The manifest list in `/comb:review` Step 5 was Node/Python/Rust/Go only. Extended to a tabular form covering PHP (`composer.json`), Ruby (`Gemfile`), Java/Kotlin (`pom.xml`, `build.gradle`), .NET (`*.csproj`), Elixir (`mix.exs`), Swift (`Package.swift`), Dart/Flutter (`pubspec.yaml`), and C/C++ (`Makefile`, `CMakeLists.txt`). The graceful-degrade fallback ("skip with a note rather than run unrelated tooling") still applies for unrecognized manifests.

## [0.4.0] — 2026-05-04

### Added

- `/comb:help` skill — overview of the plugin and command list. Pass a command name (e.g., `/comb:help fix`) for a per-command deep dive (inputs, what it does, where output lands, examples). Covers all six commands.

## [0.3.1] — 2026-05-04

### Changed

- **Generalize examples in directives and agents.** Three files used domain-specific examples that leaked from the originating codebase: `consistency.md` referenced "Jobs page" and "worksites"; `reusability.md` named `formatRowDateForGrid`; `consistency-auditor.md` repeated the "Jobs page" example. Replaced with universal SaaS placeholders (Customers page, customers/clients/accounts, `formatDateForCustomerList`) so the examples remain concrete and teachable without pinning to one project.

## [0.3.0] — 2026-05-04

### Changed

- **Plan output template** — every `/comb:plan` instruction file now leads with a header block (`**Severity:**`, `**File(s):**`, optional `**Consolidates:**` for groups) and ends with a `## Directive citations` footer that lists every plugin directive, user directive, and project-level authoritative doc (CLAUDE.md, MEMORY.md) the fix relies on. The six body sections (What / Why / Where / How / Expected Outcome / Scope) are unchanged but now use H2 headings to match the H1 file title. Real-world output from a v0.2.0 run already converged on this shape — codifying so it ships consistently.
- **Deferred items get plans.** `/comb:plan` no longer skips Deferred findings. They were already documented as "every item gets a file" in Ground rules, but the planner was reading the prose framing as out-of-scope. Step 3 is now explicit: include Deferred, auto-number with `D1`, `D2`, … if the report uses bullets without codes.
- **Review reports give Deferred items D-codes.** `/comb:review` now numbers Deferred entries (D1, D2, …) using the same `**{code} — {title}**` shape as other severities, so `/comb:plan` can hand each one to an agent without retrofitting codes.

## [0.2.0] — 2026-05-04

### Added

- `/comb:configure` skill — conversational editor for `comb.config.json`. Resolves the right scope file (project or global), shows the merged effective config, translates natural-language asks ("disable test-auditor", "use sonnet for plan") into the JSON edit, shows a diff, writes, and verifies. Honors the same merge semantics as the rest of the plugin (deep-merge, null-as-delete, hard-fail on bad JSON).

### Fixed

- `marketplace.json` `source` field: `"."` → `"./"`. The bare-string form was rejected by Claude Code as an unsupported source type; relative paths require the leading `./` per the plugin-marketplaces docs.

## [0.1.0] — 2026-04-27

### Added

- `/comb:review` skill — orchestrates 2–5 reviewer agents over a PR/branch/file list and produces a severity-ranked report
- `/comb:plan` skill — turns review findings into per-finding fix instructions
- `/comb:fix` skill — executes fix instructions with implementer + reviewer per item; parallel batching where safe
- `/comb:the-desert` skill — runs the full review→plan→fix sweep, opus everywhere, no pauses
- Five `comb:*` reviewer subagents: `code-reviewer`, `simplifier`, `silent-failure-hunter`, `test-auditor`, `consistency-auditor` — all read-only
- Eight domain-neutral directives: `simplicity.md`, `modularity.md`, `reusability.md`, `maintainability.md`, `quality.md`, `consistency.md`, `scope-discipline.md`, `testing.md`
- Layered config system (`project > global > shipped defaults`) supporting agent substitution, extensions, model lanes, and path overrides
- Same-repo marketplace manifest (`.claude-plugin/marketplace.json`) for `/plugin marketplace add` install path

### Notes

- The `marketplace.json` schema used here matches the conventional shape from `anthropics/claude-code` and was empirically verified during release via the Task 29 smoke test (`/plugin marketplace add` + `/plugin install`). The plugins-reference docs do not fully enumerate the schema, so any schema changes in future releases must re-run the marketplace install smoke test.
