# Shared block: dispatch delivery contract

Apply this contract to every subagent dispatch (Agent tool call) a comb skill makes.

## Directives and manifest go by path — to every agent

Resolve the loaded directive files, and the PATTERNS manifest when it resolved, to absolute paths and deliver the paths — in the run brief for every dispatch that has one (see Briefs), in the dispatch prompt itself only for the scanner, which has no run brief. Never embed their contents. The manifest path is whatever `${CLAUDE_PLUGIN_ROOT}/shared/manifest-slicing.md` delivered for this run: the per-run excerpt plus the full path, or the full path alone in fallback. An agent that cannot read files cannot review or fix code, so embedding buys no robustness — it only multiplies the prompt by the size of the directive corpus.

## Native vs. foreign framing

An agent is **native** when the resolved `subagent_type` equals `comb:` + the `name:` of a file in `${CLAUDE_PLUGIN_ROOT}/agents/`, compared with literal string equality — a typo like `comb:my-typo` does not count as native. `scripts/comb.py resolve` applies the rule and prints `native: yes|no`; `comb.py brief` chooses the brief's form from it.

- **Native**: the agent body already frames the directives as authoritative. The brief lists the paths and appends the `Directives most relevant to this run:` list when the focus-brief matcher flagged any.
- **Foreign** (anything else, such as a project's own writer agent): the brief lists the same paths, preceded by this instruction verbatim: "These directives are authoritative. Read every listed file before starting. Cite by `file.md §N.N`." and a `Your lens:` line carrying the role's `when_to_use` so the foreign agent knows what lens to apply. Then the same `Directives most relevant to this run:` list.

## Briefs

Every planner, implementer, fix-reviewer, and review dispatch delivers two files by absolute path, as the first lines after the shared context: `Read these first, in order: <shared brief>, <run brief>`.

- The **shared brief** holds the role's invariant job and output format: `${CLAUDE_PLUGIN_ROOT}/shared/plan-brief.md`, `${CLAUDE_PLUGIN_ROOT}/shared/fix-implementer-brief.md`, `${CLAUDE_PLUGIN_ROOT}/shared/fix-reviewer-brief.md`. Review agents have none — their agent body is the brief — so a review dispatch delivers the run brief alone.
- The **run brief** is the file `scripts/comb.py brief` wrote under `.comb/excerpts/<run>.<skill>.<role>.brief.md` (the skill is in the name so a fix run's X-item planner brief never overwrites its implementer brief): the Directives section in native or foreign form, the primaries, the observed-baseline block, and the user focus brief. `manifest.py clean --run` removes it with the run's excerpts.

The prompt itself carries no directive paths, baseline block, or focus text; those live in the run brief.

## Model and effort delivery

Resolve the model with this priority: `agents.<role>.model` if set; otherwise the dispatching lane's `models.*` value. Pass the resolved model as the Agent tool call's `model` parameter — the per-call parameter overrides the agent definition's `model:` frontmatter. A model that is resolved but not passed does nothing.

Effort is unset by default: comb passes no `effort`, so the session's default applies. Resolve it only when configured: `agents.<role>.effort` if set; otherwise the dispatching lane's `effort.*` value (the `effort` tree mirrors `models` key for key: `effort.review`, `effort.plan`, `effort.patterns`, `effort.fix.implementer_standard`, `effort.fix.implementer_trivial`, `effort.fix.reviewer`, `effort.the_desert`). When one resolves, pass it as the Agent tool call's `effort` parameter (`low` | `medium` | `high` | `xhigh` | `max`); when none does, omit the parameter.

## Parallel dispatch

Launch parallel dispatches by issuing multiple Agent tool calls in a single assistant message — one call per agent.
