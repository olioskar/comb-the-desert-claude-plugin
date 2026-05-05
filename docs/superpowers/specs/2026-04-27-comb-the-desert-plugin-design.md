# comb-the-desert plugin — design spec

**Status:** Approved 2026-04-27 (revised after Round 1 review on same date)
**Update 2026-05-05:** Historical — plugin has evolved beyond this spec. The skill bodies under `skills/*/SKILL.md` are the authoritative runtime contract. See `README.md` and `CHANGELOG.md` for current behavior. This document is retained for design rationale (the *why*), not as a current spec.
**Repo:** comb-the-desert-claude-plugin
**Plugin name:** `comb` (skills/commands invoked as `/comb:*`)

> Round 1 review report: `docs/combs/reviews/2026-04-27-spec-review-round1-report.md` — 35 findings folded into this revision.

---

## 1. Goal

Generalize the existing `~/.claude/commands/comb/*` workflow (review → plan → fix → the-desert) into a public Claude Code plugin that:

- Works for strangers out of the box (zero-dep palette, sensible defaults)
- Stays optimized for Tero-style usage via configuration
- Treats authoritative project policy (directives) as a first-class input, not a hardcoded one
- Installs via the standard Claude Code marketplace mechanism

## 2. Non-goals

- Not a replacement for `pr-review-toolkit` or `superpowers` — complementary; can layer on top
- Not framework-aware out of the box (no React/CSS/TS specialists shipped); users add those via config
- No `peer-fix` command — intentionally dropped from the current set
- No first-class document-mode (markdown-spec) reviews in v1 — diff scope is the supported mode; markdown-only scope is best-effort

## 3. Plugin layout

```
comb-the-desert-claude-plugin/
├── .claude-plugin/
│   ├── plugin.json                 # plugin manifest (see §3.1)
│   └── marketplace.json            # marketplace manifest (see §11)
├── skills/                         # 4 user-invocable skills (replaces commands/)
│   ├── review/SKILL.md             # /comb:review
│   ├── plan/SKILL.md               # /comb:plan
│   ├── fix/SKILL.md                # /comb:fix
│   └── the-desert/SKILL.md         # /comb:the-desert
├── agents/                         # 5 real Claude Code subagent types
│   ├── code-reviewer.md            # → comb:code-reviewer
│   ├── simplifier.md               # → comb:simplifier
│   ├── silent-failure-hunter.md    # → comb:silent-failure-hunter
│   ├── test-auditor.md             # → comb:test-auditor
│   └── consistency-auditor.md      # → comb:consistency-auditor
├── directives/                     # 8 domain-neutral policy docs (custom dir; §6)
│   ├── simplicity.md
│   ├── modularity.md
│   ├── reusability.md
│   ├── maintainability.md
│   ├── quality.md
│   ├── consistency.md
│   ├── scope-discipline.md
│   └── testing.md
├── config/                         # custom dir, not a Claude Code reserved name (§4)
│   └── defaults.json
├── README.md
├── LICENSE
└── CHANGELOG.md
```

### 3.1 Path resolution: `${CLAUDE_PLUGIN_ROOT}`

Plugins are cache-copied to `~/.claude/plugins/cache/...` at install time, not run from their source repo path. **Every skill body that reads plugin-internal files must use `${CLAUDE_PLUGIN_ROOT}`** to resolve them. The orchestrator reads `${CLAUDE_PLUGIN_ROOT}/config/defaults.json`, `${CLAUDE_PLUGIN_ROOT}/directives/*.md`, etc., and passes resolved absolute paths to subagents in their dispatch prompts. Relative paths from user CWD will not resolve correctly in installed deployments.

### 3.2 plugin.json

```json
{
  "name": "comb",
  "version": "0.1.0",
  "description": "Comb the Desert: a review → plan → fix pipeline for code review with configurable agents and authoritative project directives.",
  "author": {
    "name": "Olafur Oskarsson",
    "email": "olioskar@gmail.com"
  },
  "homepage": "https://github.com/olioskar/comb-the-desert-claude-plugin",
  "repository": "https://github.com/olioskar/comb-the-desert-claude-plugin",
  "license": "MIT",
  "keywords": ["code-review", "pr-review", "review-pipeline", "agents", "directives"]
}
```

`version` is set explicitly so each release is a discrete update; without it, every commit on `main` would retrigger updates for every user.

The plugin name `comb` differs from the repo name `comb-the-desert-claude-plugin` intentionally — `comb` is the namespace used for `/comb:*` invocation; the repo name carries the brand and is what users find on GitHub.

## 4. Config

### Resolution order

Project wins, falls back to global, falls back to plugin defaults:

1. `<project-root>/.claude/comb.config.json` — project-local
2. `~/.claude/comb.config.json` — machine-wide
3. `${CLAUDE_PLUGIN_ROOT}/config/defaults.json` — shipped with the plugin

Layers are deep-merged. **Project root** is resolved as `git rev-parse --show-toplevel` (which correctly returns the worktree path for git worktrees), with the user's current working directory as fallback when not in a git repo.

### 4.1 Merge semantics (pinned)

- **Objects:** deep-merged. Nested keys from later layers override matching keys in earlier layers.
- **Arrays:** replaced wholesale by later layers (no concatenation, no dedupe).
- **`null` as delete sentinel:** the comb config loader treats `null` at any depth as "remove this key from the merged result." This is non-standard JSON merge behavior and is implemented explicitly by the loader.
- **Malformed config:** invalid JSON in any layer is a **hard error** (abort the command with a clear message). Schema violations (e.g., a new role missing `subagent_type`) log a warning and skip just the offending key, falling back to the next layer.

### 4.2 Shipped `defaults.json`

```json
{
  "paths": {
    "reviews":     "docs/combs/reviews",
    "plans":       "docs/combs/plans",
    "base_branch": "main"
  },
  "directives": {
    "include_plugin_defaults": true,
    "user_path": "docs/directives"
  },
  "agents": {
    "code-reviewer": {
      "subagent_type": "comb:code-reviewer",
      "when_to_use": "Always. General correctness, data flow, logic errors, broken contracts, security."
    },
    "simplifier": {
      "subagent_type": "comb:simplifier",
      "when_to_use": "Diff introduces abstractions, new utilities, refactors, or non-trivial structural change."
    },
    "silent-failure-hunter": {
      "subagent_type": "comb:silent-failure-hunter",
      "when_to_use": "Diff contains try/catch, error handling, fallbacks, or async flows."
    },
    "test-auditor": {
      "subagent_type": "comb:test-auditor",
      "when_to_use": "Diff changes behavior, contracts, or business logic. Always for plan/fix verification."
    },
    "consistency-auditor": {
      "subagent_type": "comb:consistency-auditor",
      "when_to_use": "Diff touches an area with established patterns, a spec/plan we just wrote, or a reference implementation worth comparing against."
    }
  },
  "models": {
    "review":     "opus",
    "plan":       "opus",
    "fix": {
      "implementer_standard": "opus",
      "implementer_trivial":  "sonnet",
      "reviewer":             "opus"
    },
    "the_desert": "opus"
  }
}
```

> **Note:** `subagent_type: "comb:<name>"` references depend on the plugin manifest `name: "comb"`. Renaming the plugin would require updating these strings.

### 4.3 Field reference

| Field | Read by | Effect |
|---|---|---|
| `paths.reviews` | `/comb:review` | where the report markdown is written |
| `paths.plans` | `/comb:plan` | where per-finding instruction files are written |
| `paths.base_branch` | every command | default base branch for diffs when the user does not pass an override at invocation time |
| `directives.include_plugin_defaults` | every command | if true, agents read `${CLAUDE_PLUGIN_ROOT}/directives/*.md` as authoritative; honored uniformly across shipped, substituted, and extra agents |
| `directives.user_path` | every command | if path exists relative to project root, agents also read `<project>/<path>/*.md` as authoritative |
| `agents.<role>.subagent_type` | every command | what the Agent tool dispatches for that role |
| `agents.<role>.when_to_use` | every command | picking heuristic the orchestrator weighs against the diff and focus brief |
| `agents.<role>.model` | every command | optional per-agent model override; survives `the-desert` model coercion (see §7.4) |
| `models.review` | `/comb:review` | model for reviewer agents in the review step |
| `models.plan` | `/comb:plan` | model for per-finding planner agents |
| `models.fix.implementer_standard` | `/comb:fix` | model for non-trivial implementers |
| `models.fix.implementer_trivial` | `/comb:fix` | model for trivial implementers |
| `models.fix.reviewer` | `/comb:fix` | model for the post-implementation verifier |
| `models.the_desert` | `/comb:the-desert` | overrides lane defaults when running the full sweep (see §7.4 for precedence with per-agent overrides) |

### 4.4 Schema rules

- An `agents.<role>` entry is treated as an **override of a shipped role** if `<role>` matches one of the 5 shipped names (`code-reviewer`, `simplifier`, `silent-failure-hunter`, `test-auditor`, `consistency-auditor`). Otherwise it's a **new role definition**.
- For overrides: only the fields you want to change need to appear (deep merge with shipped defaults).
- For new roles: `subagent_type` and `when_to_use` are both required. Schema violation = warn-and-skip per §4.1.
- `agents.<role>.model` is optional everywhere; defaults to the lane (`models.<lane>`).
- `directives.user_path` may not exist as a directory in a given project — silently skipped, no warning.
- `directives.include_plugin_defaults: false` opts out of the plugin's 8 directives entirely (the user's project directives, if any, still load). When set to false, neither shipped nor substituted nor extra agents receive plugin directives.

### 4.5 Relationship to Claude Code's `userConfig`

Claude Code provides a `userConfig` mechanism in `plugin.json` for first-run prompted KV values. The comb plugin uses its own three-tier `comb.config.json` system because the schema (nested role objects, model lanes) doesn't map cleanly to flat KV. v1 ships without `userConfig`. A future enhancement could expose `paths.reviews` and `paths.plans` via `userConfig` so users get a first-run prompt for the most-tweaked values.

## 5. Agents

Each agent is a real Claude Code subagent type, registered as `comb:<name>` via files in `agents/`. The namespace is auto-derived from `plugin.json` `name`.

### 5.1 Frontmatter

```yaml
---
name: <agent-name>
description: |
  <when this agent should be selected — read by Claude when assembling subagent palettes>
model: opus
disallowedTools:
  - Write
  - Edit
  - NotebookEdit
---
```

All 5 shipped agents are read-only reviewers — they must not edit files. `disallowedTools` enforces this. Other supported plugin-agent frontmatter fields (`effort`, `maxTurns`, `tools`, `skills`, `memory`, `background`, `isolation`) are not used in v1.

### 5.2 Body

Every shipped agent's body includes:

1. Specialty and mindset statement
2. Instructions to read shared context (file list, commits, base branch — provided in dispatch prompt)
3. Instructions to read directives:
   - Plugin's directives (paths supplied) when `include_plugin_defaults: true`
   - User's directives (paths supplied) when `directives.user_path` resolves
   - Cite as `file.md §N.N` in findings
4. Instructions to read the user focus brief (if present) and weight findings accordingly
5. Output format:
   - Severity scale: Critical / High / Medium / Low / Test gaps / Deferred
   - Finding codes: C1, C2 / H1, H2 / M1, M2 / L1, L2 / T1, T2
   - File:line references
   - Directive citations on every finding where applicable

### 5.3 Shipped agents

| Agent | Specialty |
|---|---|
| code-reviewer | General bug-hunter — correctness, data flow, contract breaks, security |
| simplifier | Overengineering, dead code, unclear naming, unnecessary abstractions, copy-paste |
| silent-failure-hunter | Error handling — every catch / fallback / async — surfaces or swallows? |
| test-auditor | Coverage, real vs mock-only, behavior parity, vanity tests |
| consistency-auditor | Pattern adherence, reference-implementation comparison, spec/plan alignment |

### 5.4 Substituted and extra agents

When the resolved `subagent_type` is not in the shipped allowlist (`comb:code-reviewer`, `comb:simplifier`, `comb:silent-failure-hunter`, `comb:test-auditor`, `comb:consistency-auditor`):

- The orchestrator embeds the **full directive contents** in the dispatch prompt — not just paths — because foreign agents don't know to read them.
- Adds an explicit instruction: "These directives are authoritative. Cite by `file.md §N.N` when raising findings."
- Adds the `## User focus for this run` heading + verbatim brief.
- Costs more tokens but keeps directive compliance uniform.

The check is an **allowlist match**, not a prefix check, so a typo like `subagent_type: "comb:my-typo"` gets foreign-agent treatment rather than being assumed native.

If a user defines an entry with the same key as a shipped role, it overrides the shipped one. New keys with overlapping `when_to_use` coexist with shipped ones — the orchestrator picks per its judgment (see §7.1).

## 6. Directives

Eight domain-neutral policy docs.

### 6.1 Format (pinned)

- Numbered hierarchical sections (`§N`, `§N.M`)
- Prescriptive voice ("Treat these rules as policy", "Block only for...")
- Each section explains the *why*, not just the *what*
- Optional `## Implementation Notes` appendix at the end for project-specific grounding (the plugin's shipped directives have empty appendices; user projects may add their own)
- Cited as `file.md §N.N` in findings

### 6.2 Shipped directives

| File | Topic |
|---|---|
| simplicity.md | YAGNI, no overengineering, no speculative fixes, no hypothetical concerns |
| modularity.md | Composability, single-responsibility, file focus, clear interfaces |
| reusability.md | DRY within reason, no copy-paste, no over-abstraction |
| maintainability.md | Naming, comment discipline, no dead code, no drive-by changes |
| quality.md | Correctness, error handling, no silent failures, boundary validation |
| consistency.md | Existing patterns, reference-implementation alignment, spec/plan alignment |
| scope-discipline.md | Stay in the asked change, no expansion, exceptions documented |
| testing.md | TDD where practical, real tests not mock-only, cover changed behavior |

The plugin's directives are defaults. A project's own directives at `directives.user_path` layer on top — both sets are authoritative at runtime.

## 7. Skills (user-invocable workflow steps)

The 4 main workflow steps are implemented as skills under `skills/`, each with a `SKILL.md` containing the orchestrator instructions. They are discoverable both by direct slash invocation (`/comb:<name>`) and by description-driven Claude routing.

### 7.1 Common across all four

Every skill:

1. Reads layered config (project → global → plugin defaults, deep merge per §4.1)
2. Captures user focus brief from `$ARGUMENTS` (everything typed after the slash command)
3. Resolves agent palette from `config.agents` (shipped + user extensions)
4. Picks 2–5 agents using **judgment-based selection** (the orchestrator model picks the palette by weighing diff content, focus brief, and each agent's `when_to_use`)
   - **Hard cap:** 5 agents maximum
   - **Soft floor:** 1 agent minimum (`code-reviewer` is `when_to_use: "Always"`, so it's always included)
   - **Required-include from focus brief:** agents whose `when_to_use` matches the brief are included before optional ones; if the union exceeds 5, drop lower-priority required-includes
5. Builds dispatch prompts in this order:
   1. Shared context block (repo, branch, base, files, commits)
   2. Directives (paths for shipped `comb:*` agents in the allowlist; full contents for substituted/extra agents)
   3. `## User focus for this run` heading + verbatim brief
   4. Agent-specific instructions (already in `comb:*` agent definitions; supplied via prompt for foreign agents)
   5. Output format spec
6. Dispatches in parallel using `run_in_background: true` where safe

### 7.2 Skill frontmatter

```yaml
---
name: <skill-name>
description: |
  <when to use this skill — both for natural-language triggering and slash command discovery>
argument-hint: "[scope] [focus brief]"
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Agent
  - WebFetch
user-invocable: true
disable-model-invocation: false
---
```

`/comb:fix` and `/comb:the-desert` set `disable-model-invocation: true` because they execute code changes — Claude must not auto-invoke them from natural-language requests; the user must invoke them explicitly.

`/comb:review` and `/comb:plan` are read-only; `disable-model-invocation: false` is fine.

### 7.3 `/comb:review`

Workflow inherited from current `~/.claude/commands/comb/review.md`.

- Output: report markdown at `<paths.reviews>/<derived-name>.md`
- Naming: PR → `pr-{number}-round{N}-report.md`; branch → `branch-{name}-round{N}-report.md`. **N is computed as `(count of existing files matching the prefix in paths.reviews) + 1`.**
- Report sections: Verdict (APPROVE / NEEDS WORK), Verification Summary (tsc/tests/lint), Findings by Severity, Finding codes
- **Markdown-only scope (best-effort):** if `git diff --name-only` returns only `.md` files, the orchestrator restricts the palette to `code-reviewer` + `consistency-auditor` and notes the limitation in the report header. Full document-mode review is future work (§12).

### 7.4 `/comb:plan`

Workflow inherited from current `plan.md`.

- Loads report, dispatches one planner agent per finding (or per group, after grouping suggestions)
- **Grouping:** orchestrator scans findings for same-file or adjacent-finding groups, suggests groupings to the user once, awaits confirmation, then dispatches.
- Each agent reads affected files, writes a fix instruction at `<paths.plans>/<plan-folder>/<code>-<slug>.md`
- Sections per instruction: What / Why / Where / How / Expected Outcome / Scope
- Plan model: `opus` (raised from `sonnet` in current command)

### 7.5 `/comb:fix`

Workflow inherited from current `fix.md`.

- For each instruction: implementer (opus standard, sonnet trivial), then reviewer (opus)
- **Triviality classification:** judgment-based by the orchestrator using this rubric:
  - Trivial: single-line edits; import reorders; comment fixes; lexical renames within a single file
  - Standard: anything multi-file, anything that changes behavior, anything that introduces a new control-flow branch
  - User can override the classification for any item
- **File overlap (for parallel batching):** two instructions overlap if their **write-sets** intersect; reads are free. Same-file writes → sequential. Different-file writes → parallel batch (max 3 pairs concurrent).
- Discovered issues become D1, D2... appended to the queue with full instruction docs
- 3-failure escalation rule preserved

### 7.6 `/comb:the-desert`

Workflow inherited from current `the-desert.md`.

- Three steps in sequence, no pauses, no deferred items
- All `claude-peers` peer-coordination notes that previously lived in this command are removed
- **Model precedence:** `models.the_desert` overrides lane defaults but **does not** override explicit per-agent `agents.<role>.model` overrides. Per-agent model overrides are user-explicit signals that survive `the-desert` coercion.
- Focus brief flows through review → plan → fix without re-asking

## 8. Inline argument handling (focus brief)

The focus brief is `$ARGUMENTS` — everything typed after `/comb:<cmd>`. Common to all four skills.

- **Capture** as authoritative input, not a hint
- **Bias picking:** agents whose `when_to_use` aligns with the brief are required-include in the palette (subject to the §7.1 hard cap of 5)
- **Surface relevant directives:** the orchestrator scans the brief for keyword matches against directive filenames using lowercased substring matching. For example: `"simplicity"` → `simplicity.md`, `"scope"` → `scope-discipline.md`, `"reusability"` or `"copy-paste"` → `reusability.md`. Matched directives are flagged as primary in agent prompts. The matcher is a simple substring check; users wanting custom synonym mappings (`"tdd"` → `testing.md`) extend the orchestrator skill body itself or rename their directives to include the synonyms.
- **Inject verbatim** into every agent prompt under `## User focus for this run` with explicit framing: "Findings matching this focus are highest priority. Surface other issues too, but do not let the user's stated concerns slip."
- **Carry through pipeline (the-desert):** brief flows review → plan → fix without re-asking
- **Don't override scope:** brief shapes *what* to look for, not *which* files; scope is still derived from PR/branch/file inputs
- **Edge case — brief contradicts shipped behavior:** judgment-based. If the brief implies altering shipped flow ("skip the report", "use only one agent", "write somewhere else"), the orchestrator surfaces the conflict and asks once rather than silently obeying. Examples in the skill body, not a hardcoded list.

## 9. Discoverability

There is no separate overview/router skill. Each of the 4 main skills self-describes via its `description` frontmatter, so:

- Slash invocation: `/comb:review`, `/comb:plan`, `/comb:fix`, `/comb:the-desert`
- Natural-language routing: when a user says "review my PR" or "find issues in this diff", Claude reads the description on `skills/review/SKILL.md` and either invokes it directly or recommends it.

This eliminates the ghost `/comb:comb` slash command that a separate overview skill would have created.

## 10. What's dropped from the current `/comb` set

- `peer-fix.md` — entire command, intentionally not migrated
- `claude-peers` MCP references — only `the-desert.md` and `peer-fix.md` referenced peers; both gone (the-desert keeps the workflow, drops the peer notes)
- Hardcoded paths (`docs/combs/reviews`, `docs/combs/plans`) — now config-driven (defaults preserve current values)
- Hardcoded agent names (`react-expert`, `css-architect`, `feature-dev:code-reviewer`, `typescript-expert`) — gone from defaults; users wire them in via `agents` config if they have those subagents installed
- Hardcoded base-branch lookup via `CLAUDE.md` — replaced by config + user override at invocation time
- Layout convention `commands/<name>.md` → replaced by `skills/<name>/SKILL.md` per current Claude Code recommendation (§3)

## 11. Distribution

### v1: same-repo marketplace

The plugin ships a `.claude-plugin/marketplace.json` in the same repo, so the repo serves as both the marketplace and the single-plugin source (same pattern as `anthropics/claude-code`).

```json
{
  "name": "comb-marketplace",
  "owner": {
    "name": "Olafur Oskarsson",
    "url": "https://github.com/olioskar"
  },
  "plugins": [
    {
      "name": "comb",
      "source": ".",
      "description": "Comb the Desert: review → plan → fix pipeline."
    }
  ]
}
```

Install instructions for the README:

```bash
# 1. Add the marketplace
/plugin marketplace add olioskar/comb-the-desert-claude-plugin

# 2. Install the plugin from it
/plugin install comb@comb-marketplace
```

For local development:

```bash
claude --plugin-dir /path/to/comb-the-desert-claude-plugin
```

### v2: official marketplace

Submit to the Anthropic-curated marketplace once stable and externally validated.

## 12. Open items / future work

- **Document-mode reviews** — first-class support for reviewing markdown specs/plans (not just code diffs). v1 has best-effort handling (§7.3); a future version could detect markdown scope and switch to a doc-review-tuned palette with different finding categories (ambiguity, contradiction, missing constraints).
- **Framework-specific agents** (`comb:react-reviewer`, `comb:css-reviewer`, `comb:typescript-reviewer`) — not in v1; users add via `agents` config until clear demand.
- **Auto-detection of installed specialist plugins** — if `pr-review-toolkit` is installed, the README could suggest wiring `simplifier` and `silent-failure-hunter` to the toolkit's specialists.
- **`userConfig` for path values** — expose `paths.reviews` and `paths.plans` via Claude Code's `userConfig` for first-run prompting (§4.5).
- **Round-N-aware reviews** — current implementation derives `N` by counting existing reports (§7.3); a more sophisticated version could parse the most recent report to detect whether the diff has substantively changed and reset `N` if base/branch shifted.
