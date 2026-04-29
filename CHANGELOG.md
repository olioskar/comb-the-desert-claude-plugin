# Changelog

All notable changes to this plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
