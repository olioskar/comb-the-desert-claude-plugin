# Changelog

All notable changes to this plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
