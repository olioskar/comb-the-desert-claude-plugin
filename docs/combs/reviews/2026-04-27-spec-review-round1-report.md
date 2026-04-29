# comb-the-desert plugin spec — Round 1 Review Report

**Scope:** `docs/superpowers/specs/2026-04-27-comb-the-desert-plugin-design.md` (the design spec, not code)
**Reviewers:** 2 agents (ambiguity-hunter, plugin-compliance) + skill-creator validation + orchestrator self-pass
**Date:** 2026-04-27
**Focus brief:** ambiguities + compliance with `code.claude.com/docs/en/plugins-reference`, `/plugins`, `/skills` + `/skill-creator` validation

---

## Verification Summary

| Check | Result |
|-------|--------|
| Spec file exists at canonical path | ✓ |
| Working copy at root present + gitignored | ✓ |
| Claude Code official docs fetched | 4/4 pages reachable (plugins, plugins-reference, skills, discover-plugins) |
| Skill format check vs installed plugins | confirmed `skills/<name>/SKILL.md` convention |

---

## Verdict: **NEEDS WORK**

3 Critical findings make v1 non-installable as specified. 11 High findings would cause visible breakage or wrong behavior. The architecture is sound but the spec was written without verifying against Claude Code's actual install/distribution mechanics or the `${CLAUDE_PLUGIN_ROOT}` cache-copy model. Resolve Critical + High findings before plan phase.

---

## Findings by Severity

### Critical

**C1 — `claude plugin install <repo-url>` is not a real command**
*Source: plugin-compliance*
File: §11 Distribution

Claude Code installs plugins from *marketplaces*, not bare repo URLs. CLI form is `/plugin install <plugin>@<marketplace>`. Users first add a marketplace (`/plugin marketplace add <owner/repo>`), then install. Without a `.claude-plugin/marketplace.json` in the repo, no one can install this plugin via the documented mechanism — only via `--plugin-dir` for local dev.

Fix: ship `.claude-plugin/marketplace.json` in the same repo (the repo can be both marketplace and single-plugin source), and rewrite §11 to document the two-step install. Drop the fictional `claude plugin install <repo-url>`.

**C2 — Agent picking algorithm is undefined**
*Source: ambiguity-hunter*
File: §7 (common workflow step 4), §8 (focus brief biasing)

Spec says "picks 2–5 agents based on diff content + focus brief + each agent's `when_to_use`" but never defines selection mechanics. Two implementers would build different things — one a deterministic scorer (tokenize, count overlaps, top-N), one a meta-prompt asking the orchestrator model to "use judgment." Drives the core behavior of every command.

Fix: state explicitly. Recommendation: judgment-based (LLM picks the palette in the orchestrator prompt) since the heuristic space is too varied for a deterministic algorithm, but pin that decision in the spec.

**C3 — 2–5 cap vs "required-include" conflict undefined**
*Source: ambiguity-hunter*
File: §7 step 4 vs §8 "Bias picking"

§7 says 2–5 agents. §8 says aligned agents are "required-include." If a focus brief aligns with 6 agents, or a tiny diff matches 0, the spec doesn't say which constraint wins. Hard cap or soft floor?

Fix: state explicitly. Recommendation: hard cap of 5 (truncate required-includes by `when_to_use` priority); minimum 1 (code-reviewer is always included as it's marked "Always" in defaults).

---

### High

**H1 — `/comb:comb` ghost skill in the slash menu**
*Source: plugin-compliance, skill-creator*
File: §9 Overview skill

Skill invocation name in plugins is `<plugin-name>:<skill-directory>`. So `skills/comb/SKILL.md` inside plugin `comb` invokes as `/comb:comb` — a confusing duplicate next to `/comb:review`, `/comb:plan`, etc. The frontmatter `name: comb` field is cosmetic for plugin skills (doc says: "If omitted, uses the directory name").

Fix: either (a) remove the skill entirely and put routing content in `README.md` and the plugin's `CLAUDE.md` (cleaner), or (b) rename the skill directory to something not stuttery (e.g., `skills/router/` → `/comb:router`) AND set `user-invocable: false` so it doesn't appear in the slash menu — its only purpose is description-driven Claude routing, not user invocation.

**H2 — Commands missing `$ARGUMENTS`, `argument-hint`, `disable-model-invocation`**
*Source: plugin-compliance*
File: §7 Commands, §8 Inline argument handling

Without `$ARGUMENTS` placeholder in command bodies, the focus brief is appended as `ARGUMENTS: <value>` rather than injected at a specific point — implementing §8's "User focus for this run" section becomes awkward. `argument-hint` is needed for autocomplete. Most importantly, `/comb:fix` and `/comb:the-desert` execute code changes; without `disable-model-invocation: true`, Claude could auto-trigger them from natural-language requests, which is dangerous.

Fix: spec should explicitly state command frontmatter requirements. At minimum:
- All 4 commands: `$ARGUMENTS` in body, `argument-hint`
- `/comb:fix` and `/comb:the-desert`: `disable-model-invocation: true`

**H3 — Subagent frontmatter underspecified**
*Source: plugin-compliance*
File: §5 Agents

Spec says agents have frontmatter `name`, `description`, `model: opus`. Plugins-reference lists more supported fields: `effort`, `maxTurns`, `tools`, `disallowedTools`, `skills`, `memory`, `background`, `isolation`. Reviewers should be denied `Write`/`Edit` (they're read-only) — that needs `disallowedTools` or `tools` allowlist. Worth verifying `model: opus` is the canonical alias.

Fix: pin the full frontmatter schema for shipped agents, including `disallowedTools: ["Write", "Edit", "NotebookEdit"]` for all 5 reviewers.

**H4 — `${CLAUDE_PLUGIN_ROOT}` is not mentioned anywhere in the spec**
*Source: plugin-compliance*
File: §3, §4, §5, §6 (cross-cutting)

Plugins are copied to `~/.claude/plugins/cache/...` at install time. The spec uses placeholders like `<plugin>/directives/*.md` but never resolves them. Any orchestrator code that reads `config/defaults.json` or hands directive paths to subagents must use `${CLAUDE_PLUGIN_ROOT}` substitution. Relative paths from user CWD won't resolve in installed deployments.

Fix: add a §3.1 or §4.1 subsection: "All plugin-internal file references use `${CLAUDE_PLUGIN_ROOT}` to resolve to the actual cache path. The orchestrator passes resolved absolute paths to subagents in dispatch prompts."

**H5 — `null` as delete sentinel is non-standard JSON merge**
*Source: orchestrator self-pass, ambiguity-hunter*
File: §4 Resolution order ("To remove a shipped role, set its key to `null`")

Standard JSON deep-merge sets the value to `null`, doesn't remove the key. The spec needs to either name a config-loader library that supports null-as-delete (rare), or explicitly state that the comb config loader treats `null` as a delete sentinel — and define which keys it applies to (only `agents.<role>`, or universally?).

Fix: pin to "the comb config loader treats top-level and nested `null` values as 'remove this key from the merged config'" — and write tests for it during plan phase.

**H6 — Substring/keyword matching example fails its own rule**
*Source: ambiguity-hunter*
File: §8 "Surface relevant directives"

Spec says "simple substring/keyword matching" with example "tdd" → `testing.md`. But "tdd" has no shared substring with "testing.md" — pure substring match cannot satisfy the example. So the matcher must be either a synonym table or fuzzy/semantic, neither of which is "simple substring."

Fix: either (a) name the actual mechanism (hand-curated synonym table embedded in the orchestrator command, growing with each shipped directive) or (b) replace the example with a true substring match ("simplicity" → `simplicity.md`, "scope" → `scope-discipline.md`), and drop the synonym examples.

**H7 — Project root resolution for `directives.user_path` is underspecified**
*Source: ambiguity-hunter*
File: §4 field reference

"Repo root, or cwd if not in a git repo" — but what about submodules, worktrees, or sibling repos? Different `git rev-parse` answers exist. Affects which directives load, so this matters.

Fix: pin to `git rev-parse --show-toplevel` (with cwd fallback), and explicitly handle the worktree case (worktree root is fine — shares `.git/worktrees/<name>` but `--show-toplevel` returns the worktree path, which is what we want).

**H8 — Deep-merge semantics for arrays unspecified**
*Source: ambiguity-hunter*
File: §4 "Resolution order"

"Layers are deep-merged" is well-defined for objects, ambiguous for arrays. Schema doesn't currently use arrays much, but extension points (future list fields, user-added arrays under `agents.<role>`) need a defined behavior: replace wholesale, or concatenate, or dedupe?

Fix: state "arrays are replaced wholesale by later layers" — simplest and most predictable.

**H9 — "Trivial" classification is fuzzy**
*Source: ambiguity-hunter*
File: §7 `/comb:fix`

"Single-line changes, import reorders, comment fixes, simple renames" — but "simple rename" is undefined (lexical text-replace? or semantic with all call-site updates? a rename touching 40 files — still simple?). Drives model selection (sonnet vs opus), so cost/quality impact is real.

Fix: pin trivial = "diff is purely additive/structural with ≤1 line of net logic change OR the implementer agent's own classification (judgment-based)." Lean toward judgment with explicit override.

**H10 — `comb:*` prefix detection is strict vs allowlist**
*Source: ambiguity-hunter*
File: §5 substituted/extra agents

"When the resolved `subagent_type` is not `comb:*`" — strict prefix means a user typing `subagent_type: "comb:my-typo"` would be treated as native (paths only) even if the agent doesn't exist. Should be checked against the actual shipped agents list.

Fix: pin to "if subagent_type matches one of the 5 shipped agents (`comb:code-reviewer` etc.), supply paths only; otherwise embed full directive contents." Allowlist beats prefix-check.

**H11 — Marketplace requirement (extension of C1)**
*Source: plugin-compliance*
File: §11 Distribution

Same issue as C1 from a different angle. There is no "install from raw repo" path. Even for v1's "manual GitHub install only," the spec needs a `marketplace.json` so users can use `/plugin install` at all.

Fix: same as C1.

---

### Medium

**M1 — `plugin.json` missing recommended fields**
*Source: plugin-compliance*
File: §3 / §4

Spec only specifies `name: "comb"`. Should include `version`, `description`, `author`, `homepage`, `repository`, `license`, `keywords`. Without `version`, every commit on `main` retriggers an update for every user. Without `description`/`keywords`, marketplace discoverability is poor.

**M2 — Custom config layer should acknowledge it's outside Claude Code's `userConfig`**
*Source: plugin-compliance*
File: §4

Claude Code has `userConfig` in `plugin.json` for first-run prompted values, stored in `settings.json`. Spec's three-tier `comb.config.json` system is reasonable for the nested structures (`userConfig` is flat KV), but should:
- Acknowledge the divergence in §4
- Consider exposing `paths.reviews` and `paths.plans` via `userConfig` so users get a first-run prompt for the most-tweaked values

**M3 — SKILL.md description undertriggering + missing synonyms**
*Source: skill-creator*
File: §9

Description starts with passive "Use when..." rather than the recommended pushy "Make sure to use this skill whenever...". Missing natural-language synonyms ("find issues in my PR", "look for bugs", "comb through these commits"). Body is descriptive rather than imperative. No disambiguation from generic "review my code" requests. Together these reduce trigger reliability.

Fix (if skill is kept): rewrite description and body to be more emphatic and synonym-rich, OR remove the skill entirely (per H1 fix option a).

**M4 — Document-mode reviews are silent on v1 behavior**
*Source: orchestrator self-pass*
File: §7 `/comb:review`, §12 (open items)

You actually use `/comb:review the spec we just wrote` against markdown files. Spec lists this as future work but says nothing about what v1 should do when scope is markdown. `gh pr diff` and `git diff` will work on .md files but the agent palette (simplifier, silent-failure-hunter) doesn't apply. Risk: v1 review of a spec produces nonsensical findings.

Fix: at minimum, state "v1 supports diff scope only; markdown-only scope falls back to code-reviewer + consistency-auditor only, with explicit notice." Or punt formally to v2 by stating the limitation in §11/§12.

**M5 — Edge-case conflict resolution underspecified**
*Source: ambiguity-hunter*
File: §8

"If brief contradicts shipped behavior, ask once" — what counts as a contradiction? Only "skip the report" is given as example. Hardcoded list, or LLM judgment?

Fix: judgment-based with examples — "contradictions include directives like 'skip the report,' 'use only one agent,' 'write somewhere else'."

**M6 — Multiple agents with overlapping `when_to_use` is unaddressed**
*Source: ambiguity-hunter*
File: §4/§5/§7

If a user adds an agent with broader `when_to_use` than a shipped one, both are eligible. Picker behavior is unspecified (pick both, prefer user, dedupe?).

Fix: state "user-defined entries with the same role-key override shipped ones; otherwise both coexist; the orchestrator picks the most relevant per its judgment."

**M7 — Malformed config behavior unspecified**
*Source: ambiguity-hunter*
File: §4 Schema rules

Invalid JSON, missing required fields — hard error or silent skip?

Fix: state "invalid JSON in any layer is a hard error; schema violations log a warning and skip just the offending key, falling back to the next layer."

**M8 — `the-desert` model override vs per-agent `model` precedence**
*Source: ambiguity-hunter*
File: §4 + §7 `/comb:the-desert`

§7 says `the-desert` "overrides every other model setting." Does that include explicit `agents.<role>.model` user overrides? Could read either way.

Fix: state "in `/comb:the-desert`, `models.the_desert` overrides lane defaults but NOT explicit per-agent `agents.<role>.model` overrides — those are user-explicit signals that survive."

**M9 — Round N detection algorithm**
*Source: ambiguity-hunter*
File: §7 `/comb:review`, §12

How is `{N}` derived? Counting existing files? Reading the prior report? §12 acknowledges this as needing work.

Fix: pin to "N = (count of existing files matching prefix in `paths.reviews`) + 1." Simple and predictable.

**M10 — Parallel batching read/write conflict semantics**
*Source: ambiguity-hunter*
File: §7 `/comb:fix`

"Files don't overlap" — overlap on writes only, or reads too?

Fix: state "two instructions overlap if their write-sets intersect; reads are free."

**M11 — `include_plugin_defaults: false` interaction with substituted agents**
*Source: ambiguity-hunter*
File: §4 + §5

If a user opts out of plugin directives but uses a substituted agent, does the orchestrator still embed plugin directives in the substituted-agent dispatch?

Fix: state "`include_plugin_defaults: false` is honored uniformly — neither shipped nor substituted agents receive plugin directives when set to false; only user directives are passed/embedded."

**M12 — Implicit "new vs override" rule in agents config**
*Source: orchestrator self-pass*
File: §4 schema rules

"Required for new roles" — but the rule for distinguishing new from override is implicit (key matches one of the 5 shipped names → override; else → new).

Fix: state explicitly: "If `agents.<role>` key matches one of the 5 shipped role names, it's treated as an override (deep-merged with shipped defaults). Otherwise it's a new role definition and `subagent_type` + `when_to_use` are required."

**M13 — §10 "scrubbed from all remaining commands" inconsistency**
*Source: ambiguity-hunter*
File: §10 vs §7 `/comb:the-desert`

§10 says `claude-peers` references scrubbed from all remaining commands; §7 mentions removal only for `the-desert`. Either the other commands had no peers refs (so §10 is a no-op generalization) or they did and §7 is silently incomplete.

Fix: confirm — looking at current `~/.claude/commands/comb/*`, only `the-desert.md` and `peer-fix.md` reference `claude-peers`. So §10's "scrubbed" is technically accurate but slightly misleading. Tighten: "the-desert had peer-coordination notes; those are removed."

**M14 — Directive structure not pinned**
*Source: orchestrator self-pass*
File: §6

"Format follows the tero-app `docs/directives/*.md` convention" — but nothing about whether numbered sections are required, whether the "Tero Implementation Notes" appendix is part of the convention, etc.

Fix: pin the structure: "numbered hierarchical sections (§N → §N.M), prescriptive voice, optional 'Implementation Notes' appendix at the end." Plan phase will use this.

---

### Low

**L1 — Plugin name "comb" vs repo "comb-the-desert-claude-plugin" divergence**
*Source: plugin-compliance*

Manifest name and repo name differ. Works as designed (the marketplace entry maps them) but worth noting for users who search by repo. Also: "comb" is short/generic, could collide in a marketplace.

**L2 — `config/` folder is not a reserved Claude Code folder**
*Source: plugin-compliance*

Works fine — Claude Code doesn't reserve `config/`. Just confirming the spec doesn't accidentally trip on a reserved name.

**L3 — Agent namespace is auto-derived; renaming plugin would silently break references**
*Source: plugin-compliance*

If `plugin.json` `name` changes, every `subagent_type: "comb:*"` in `defaults.json` becomes invalid. Worth a comment in `defaults.json` noting the dependency.

**L4 — Plan grouping criteria undefined**
*Source: ambiguity-hunter*

Who proposes plan groups? When? Spec is hand-wavy.

Fix: state "the orchestrator scans findings for same-file or adjacent-finding groups, suggests groupings to the user once, awaits confirmation, then dispatches one planner agent per finding or group."

**L5 — User focus brief ordering for substituted agents undefined**
*Source: ambiguity-hunter*

Foreign agents get full directive contents inlined plus the focus brief. Ordering is undefined.

Fix: pin order: "1) shared context block, 2) directives (paths or contents), 3) `## User focus for this run` heading + verbatim brief, 4) output format spec."

---

### Test Gaps

None applicable — spec is a design document, not testable code. Plan phase should produce an implementation plan that defines test cases for:
- Config layer merge semantics (especially null-as-delete)
- Agent palette picking (deterministic test inputs → expected palette)
- Path resolution (`${CLAUDE_PLUGIN_ROOT}` substitution, `directives.user_path` resolution edge cases)
- Focus brief injection at the right point in dispatch prompts

### Deferred

None.

---

## Notes

- The 4 Critical/High items concentrated on Claude Code distribution mechanics (C1, H1, H2, H4) are non-obvious from the docs unless you read all four pages carefully — the brainstorm conversation didn't surface these because we were building from the existing /comb commands' working assumptions, not from the public plugin docs.
- Several findings (H6, H10, M11) are about the spec contradicting its own examples or rules — these are fixable by tightening the prose, not rethinking the design.
- The spec's architecture (plugin layout, agents-as-subagents, layered config, focus brief flow) holds up well under both reviews. The breakage is in mechanics and underspecification, not in the design's bones.
