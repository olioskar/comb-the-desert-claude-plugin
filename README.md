# comb-the-desert

A Claude Code plugin for code review. `/comb:review` finds issues, `/comb:plan` turns each one into a fix instruction, `/comb:fix` applies them, and `/comb:the-desert` runs all three in one go.

Reviewers follow eight shipped directives plus your own, and a layered config lets each project override the defaults.

## Commands

- **`/comb:review`** runs 1–5 reviewer agents over a PR, branch, file list, or spec. A code change gets a severity-ranked report with a verdict. A prose change (spec, design doc) gets a shorter report with labelled findings.
- **`/comb:plan`** writes one self-contained fix instruction per finding.
- **`/comb:fix`** applies the instructions. Each item gets an implementer and a reviewer, and items that touch different files run in parallel. Before each commit, the reviewer runs the plan's `Check:` line and the project's tests run. A failed attempt is reverted and recorded before the retry. Each passing item is committed as `<code>: <title>`. Only you can start it; see "Let Claude start fixes" below to change that.
- **`/comb:the-desert`** runs review, plan, and fix without pauses. On a prose change it stops after review.
- **`/comb:patterns`** scans the codebase and writes a PATTERNS manifest: the project's actual conventions, with `file:line` references. Review, plan, and fix give agents the relevant excerpt as a baseline. `--shave` shrinks an existing manifest without changing what it says.
- **`/comb:configure`** changes the config from a plain-language request.
- **`/comb:help`** prints an overview. `/comb:help <command>` shows one command in detail.

Every command takes a free-form focus brief that steers which agents run and what they prioritize:

```
/comb:review look for spec/plan misalignment
/comb:the-desert ensure simplicity, scope discipline, and TDD coverage
```

## Requirements

- `python3` 3.8 or later. Every command starts by running a bundled stdlib script and stops if it can't.
- `git`. `gh` is also needed to review a PR by number.
- Claude Code 2.1.292 or later, only if you configure an `effort` value.

## Install

```
/plugin marketplace add olioskar/claude-plugins
/plugin install comb@olioskar-marketplace
```

For local development:

```bash
claude --plugin-dir /path/to/comb-the-desert-claude-plugin
```

## Quick start

In a git repo with changes on a branch:

```
/comb:review
```

The report lands in `docs/combs/reviews/`. Run `/comb:plan` on it, then `/comb:fix`. Or run `/comb:the-desert` to do all three.

## Configuration

Three layers are deep-merged, with later layers winning:

1. `config/defaults.json` in the plugin
2. `~/.claude/comb.config.json` (global)
3. `<project-root>/.claude/comb.config.json` (project)

`/comb:configure` makes changes for you, for example "disable test-auditor" or "use sonnet for plan". It shows a diff, then writes the change to the global or project file.

`config/defaults.json` lists every key with its default. Three kinds of setting are absent by default: `effort.<lane>`, and the per-role `agents.<role>.model` and `agents.<role>.effort`.

### Models and effort

```json
{
  "models": { "plan": "sonnet" },
  "effort": { "review": "medium" },
  "agents": { "simplifier": { "model": "haiku" } }
}
```

- **Models** can be `sonnet`, `opus`, `haiku`, or `fable`. The agent dispatch rejects a full model ID.
- **Effort** can be `low`, `medium`, `high`, `xhigh`, or `max`. When it is unset, agents use your session's effort.
- **Per-role settings** beat the lane setting.

In one measured review run, `medium` found the same bugs as `high` for about 8% less.

### Turn off per-item commits

```json
{ "fix": { "commit_per_item": false } }
```

### Let Claude start fixes

```json
{ "fix": { "model_invocation": true } }
```

`/comb:fix` is user-only by default because it edits code and commits. With this flag, asking in your own words ("apply the fixes") runs the same workflow, with the same questions and commits. Without the flag, such a request gets a short reply naming `/comb:fix` and the flag.

### Use your own writer

```json
{ "agents": { "implementer": { "subagent_type": "your-org:implementer" } } }
```

The default writer, `comb:implementer`, edits only the files the instruction names, never commits, and reports every file it touched. A writer from outside this plugin gets an explicit instruction that the directives are authoritative. It also gets the same boundaries, and the same file and git checks after it returns.

### Add or swap reviewers

```json
{
  "agents": {
    "react-expert": {
      "subagent_type": "react-expert",
      "when_to_use": "Diff includes React components, hooks, or JSX."
    },
    "simplifier": { "subagent_type": "pr-review-toolkit:code-simplifier" },
    "test-auditor": null
  }
}
```

A new role needs `subagent_type` and `when_to_use`. Overriding a shipped role can set just the fields you change. `null` removes a role.

### Use your own directives

```json
{ "directives": { "user_path": "docs/our-rules" } }
```

## Directives

The plugin ships eight directives in `directives/`:

- `simplicity.md`: no overengineering or speculative fixes
- `modularity.md`: single responsibility, clear interfaces
- `reusability.md`: no copy-paste, no premature abstraction
- `maintainability.md`: naming, comments, no dead code
- `quality.md`: correctness, error handling
- `consistency.md`: follow existing patterns and the spec
- `scope-discipline.md`: stay inside the requested change
- `testing.md`: real tests that cover changed behavior

Your directives in `directives.user_path` (default `docs/directives/`) apply on top. Both sets are authoritative, and findings cite them as `<file>.md §N.N`. Agents get the files by path, not pasted into their prompt. To use only your own directives, set `"directives": { "include_plugin_defaults": false }`.

## Agents

Five read-only reviewers:

- `comb:code-reviewer`: bugs, logic, contracts, security
- `comb:simplifier`: overengineering, dead code, duplication
- `comb:silent-failure-hunter`: swallowed errors, hidden fallbacks
- `comb:test-auditor`: coverage and test quality
- `comb:consistency-auditor`: fit with existing patterns and with the spec or plan

Read-only is enforced by instruction. The edit tools are blocked, but Bash stays available for git.

Each finding must name a real cost, such as a failure mode, a coverage gap, or a maintenance burden. A clean diff should come back with few or no findings. `simplifier`, `silent-failure-hunter`, and `consistency-auditor` re-check their findings in a final step. `code-reviewer` and `test-auditor` dropped that step after an experiment showed it changed nothing.

Before a finding enters the report, `/comb:review` opens every cited line and recomputes every count. Each finding carries a `Verified:` line stating what was checked and what was not. `/comb:plan` re-checks anything marked unchecked.

Three more agents:

- **`comb:implementer`** is the writer for `/comb:fix` and `/comb:plan`.
- **`comb:pattern-scanner`** is used only by `/comb:patterns`.
- **`comb:pattern-shaver`** is used only by `/comb:patterns --shave`.

## How it works

- **Scripts do the bookkeeping.** `scripts/comb.py` merges config, resolves each agent's model and effort, matches directives to the focus brief, names reports, and batches fix items. Each dispatch prompt is a few lines plus the path to a per-run brief that the script writes. Planner and fix agents also get their role's brief in `shared/`. Working files live in `.comb/`, which ignores itself in git and is cleaned at the end of each run.
- **Agents get a manifest excerpt, not the whole file.** `scripts/manifest.py` cuts the PATTERNS manifest down to the sections whose scope matches the change, and lists the omitted sections by line range. The rules are in `shared/manifest-slicing.md`. Add a one-line `Home:` to a section if it is included too often.
- **The skills are the contract.** `skills/*/SKILL.md` and `shared/*.md` define the behavior, and `CHANGELOG.md` records every change to it. Skills run in your session's model; agents get the model from config on each dispatch.

## Development

[PLAYBOOK.md](PLAYBOOK.md) describes the workflow and design rules.

Release gate, in order:

1. `claude plugin validate .`
2. `scripts/check-contract.sh` runs the free checks:
   - The shared blocks are not copied into skills, and every reference resolves.
   - The help defaults match `config/defaults.json`.
   - The agent files are consistent.
   - The fixture tests for both scripts and the grader replay pass.
3. `claude plugin eval . --scaffold --ablation none --runs 1 --allow-tools Bash Write Edit` runs the eight behavioral cases in `evals/`, at about 5 USD per pass. On macOS it needs a standalone git, such as Homebrew's. `evals/README.md` explains the flags.

`scripts/smoke.sh` is the offline check. `scripts/replay-graders.py` re-scores a kept eval run for free. `experiments/` holds two-arm runs that test whether a prompt passage is still needed: run them with `--eval-dir experiments`, and see `experiments/README.md` for results.

CI runs gates 1 and 2 on every push. The eval suite runs on manual dispatch.

## Status

v0.15.3. See [CHANGELOG.md](CHANGELOG.md) for the full version history.

## License

MIT
