# comb-the-desert

A Claude Code plugin for code review: a `/comb:review` → `/comb:plan` → `/comb:fix` pipeline with `/comb:the-desert` for the full sweep.

The plugin ships configurable reviewer agents, eight domain-neutral directives, and a layered config system that lets your project policy take precedence.

## What it does

- **`/comb:review`** — dispatches 1–5 reviewer agents over a PR / branch / file list / spec doc; right-sizes the apparatus based on what the diff is (code-shaped → full severity-ranked report with verdict and verification; non-code → condensed report with flat labelled findings)
- **`/comb:plan`** — turns each finding into a self-contained fix instruction
- **`/comb:fix`** — executes the instructions, with implementer + reviewer per item, parallel batching where safe; commits each item on reviewer PASS with `<code>: <title>` (opt out via `fix.commit_per_item: false`)
- **`/comb:the-desert`** — runs all three steps as one continuous sweep, opus everywhere, no pauses; short-circuits to review-only on non-code artifacts (findings go back to your design conversation, not an autonomous rewrite)
- **`/comb:patterns`** — scans the codebase and writes a PATTERNS manifest of concrete conventions (structure, naming, closed token sets, abstraction level, reuse points) with real `file:line` references; `/comb:review`, `/comb:plan`, and `/comb:fix` consume it as an observed baseline (a prior, not law)
- **`/comb:configure`** — edit `comb.config.json` conversationally: change paths, swap models, enable/disable agents, point at your directives
- **`/comb:help`** — overview and per-command details. `/comb:help <command>` for a deep dive

Each command accepts a free-form focus brief that biases agent picking and finding priorities:

```
/comb:review look for spec/plan misalignment
/comb:the-desert ensure simplicity, scope discipline, and TDD coverage
```

## Install

The plugin is distributed via [olioskar/claude-plugins](https://github.com/olioskar/claude-plugins)

1. Add the marketplace:

```
/plugin marketplace add olioskar/claude-plugins
```

2. Install the plugin:

```
/plugin install comb@olioskar-marketplace
```

For local development:

```bash
claude --plugin-dir /path/to/comb-the-desert-claude-plugin
```

## Quick start

After install, in a git repo with some changes:

```
/comb:review
```

The plugin picks an agent palette based on what's in the diff, runs the reviewers in parallel, and writes a report to `docs/combs/reviews/<derived-name>.md`. From there you can `/comb:plan` to generate fix instructions, then `/comb:fix` to execute them — or `/comb:the-desert` to do all three at once.

## Configuration

The plugin reads three layers of config, deep-merged in this order (later wins):

1. `${CLAUDE_PLUGIN_ROOT}/config/defaults.json` — shipped defaults
2. `~/.claude/comb.config.json` — global override
3. `<project-root>/.claude/comb.config.json` — project override

If you'd rather not hand-edit JSON, run `/comb:configure` and describe the change ("disable test-auditor", "use sonnet for plan", "look for my directives in `docs/our-rules`"). The skill picks the right scope file, shows a diff, and writes the merged result.

### Common overrides

**Use a project-specific writer for `/comb:fix` and `/comb:plan`:**

```json
{
  "agents": {
    "implementer": {
      "subagent_type": "your-org:implementer"
    }
  }
}
```

The default is `general-purpose` (Claude's built-in writer-capable subagent), which is suitable for most projects. Override only if you have a specialist implementer for your stack.

**Disable per-item commits**:

```json
{
  "fix": {
    "commit_per_item": false
  }
}
```

**Add your team's specialist agents** (e.g., a project-local `react-expert` defined in `.claude/agents/react-expert.md`):

```json
{
  "agents": {
    "react-expert": {
      "subagent_type": "react-expert",
      "when_to_use": "Diff includes React components, hooks, or JSX."
    }
  }
}
```

**Substitute a shipped role with a specialist plugin's agent:**

```json
{
  "agents": {
    "simplifier": {
      "subagent_type": "pr-review-toolkit:code-simplifier"
    }
  }
}
```

**Point at your team's directives:**

```json
{
  "directives": {
    "user_path": "docs/our-rules"
  }
}
```

### Removing a shipped role

Set the role's key to `null` in an override layer:

```json
{
  "agents": {
    "simplifier": null
  }
}
```

### Full schema

See `config/defaults.json` for every supported field. The skill bodies in `skills/*/SKILL.md` plus the shared contract blocks in `shared/*.md` are the runtime contract; `CHANGELOG.md` documents behavior changes per release.

## Directives

The plugin ships eight domain-neutral directives at `directives/`:

- `simplicity.md` — YAGNI, no overengineering, no speculative fixes
- `modularity.md` — composability, single-responsibility, clear interfaces
- `reusability.md` — DRY within reason, no copy-paste, no over-abstraction
- `maintainability.md` — naming, comment discipline, no dead code
- `quality.md` — correctness, error handling, no silent failures
- `consistency.md` — existing patterns, reference-impl alignment, spec/plan alignment
- `scope-discipline.md` — stay in the asked change, no drive-by refactors
- `testing.md` — TDD, real tests, cover changed behavior

A project's own directives at the configured `directives.user_path` (default `docs/directives/`) layer on top — both sets are authoritative at runtime, cited in findings as `<file>.md §N.N`.

Directives reach agents as file paths, never as embedded contents. Native `comb:*` agents already treat them as authoritative; any other agent type gets the same paths plus an explicit authority instruction (see `shared/dispatch-delivery.md`).

To opt out of the plugin's directives:

```json
{
  "directives": {
    "include_plugin_defaults": false
  }
}
```

## Subagents

The plugin registers five `comb:*` subagents — read-only reviewers (`disallowedTools: [Write, Edit, NotebookEdit]`):

- `comb:code-reviewer` — bugs, logic, contracts, data flow, security
- `comb:simplifier` — overengineering, dead code, naming, copy-paste
- `comb:silent-failure-hunter` — error handling, swallowed errors
- `comb:test-auditor` — coverage, real tests, behavior parity
- `comb:consistency-auditor` — patterns, reference impl, feature completeness (against a spec/plan, or against intent reconstructed from evidence when no spec exists)

The `disallowedTools` list blocks the file-editing tools; Bash stays available for git and read commands, so read-only is enforced by instruction, not by sandbox.

A sixth read-only subagent, `comb:pattern-scanner`, is **generation-only** — dispatched by `/comb:patterns` to map one codebase area, never part of the review/plan/fix palette.

You can invoke them directly via the Task tool or let the comb skills pick them automatically.

All five reviewers self-calibrate before publishing: each finding must reference a real cost — real failure mode, real complexity cost, real silence, real coverage gap, or real divergence with consequences. Ungrounded items get dropped. `LOOKS GOOD` on a clean diff is the expected outcome; padding the report with marginal items dilutes the signal of real findings. This keeps multi-round `/comb:the-desert` sweeps from drifting into diminishing-returns noise.

Each finding also carries a **Confidence** field, and `/comb:review` verifies before it promotes: it opens every cited line, recomputes every count, and refuses to state an untraced fix shape in the report's voice. Every finding in the report ends up with a `Verified:` line naming what was checked and what was not. `/comb:plan` reads that line and re-derives anything it names as unchecked.

### A note on skill `model` frontmatter

The seven `/comb:*` skills intentionally omit the `model:` frontmatter field. The orchestrator runs in the user's session model (whatever they invoked Claude Code with), and the skill body's logic dispatches subagents at the configured `models.<lane>` model (or `agents.<role>.model` when set), passed as the Task call's `model` parameter. Adding a `model:` field to a skill would only fix the orchestrator's model — it would have no effect on the dispatched agents, which is what actually matters for cost and quality.

## Development

The release gate, in order:

1. `claude plugin validate .` — structural lint of the manifest, skills, and agents.
2. `scripts/check-contract.sh` — deterministic greps: no dead spec citations, every `shared/` reference resolves, no shared block re-inlined into a skill, no `.DS_Store` tracked.
3. `claude plugin eval . --scaffold` — the behavioral suite in `evals/` (five cases covering the known regression classes). The eval feature is early access; until it is enabled for your account, run `scripts/smoke.sh` as the interim behavioral gate.

CI runs gates 1–2 on every push and PR; the eval suite runs as a manual workflow dispatch (it needs `ANTHROPIC_API_KEY`). `/skill-doctor` is a usage/cost report, useful for periodic monitoring — it is not a lint step and not part of the gate.

## Status

v0.9.0. See [CHANGELOG.md](CHANGELOG.md) for the full version history.

## License

MIT
