# Shared block: dispatch delivery contract

Apply this contract to every subagent dispatch (Agent tool call) a comb skill makes.

## Directives and manifest go by path — to every agent

Resolve the loaded directive files, and the PATTERNS manifest when it resolved, to absolute paths and list the paths in the dispatch prompt. Never embed their contents. The manifest path is whatever `${CLAUDE_PLUGIN_ROOT}/shared/manifest-slicing.md` delivered for this run: the per-run excerpt plus the full path, or the full path alone in fallback. An agent that cannot read files cannot review or fix code, so embedding buys no robustness — it only multiplies the prompt by the size of the directive corpus.

## Native vs. foreign framing

The native allowlist is exactly these strings:

- `comb:code-reviewer`
- `comb:simplifier`
- `comb:silent-failure-hunter`
- `comb:test-auditor`
- `comb:consistency-auditor`
- `comb:pattern-scanner`
- `comb:pattern-shaver`

Compare the resolved `subagent_type` with literal string equality — a typo like `comb:my-typo` does not count as native.

- **Native** (in the allowlist): the agent body already frames the directives as authoritative. List the paths. Append the `Directives most relevant to this run:` list when the focus-brief matcher flagged any.
- **Foreign** (anything else, including the default `general-purpose` implementer): list the same paths, preceded by this instruction verbatim: "These directives are authoritative. Read every listed file before starting. Cite by `file.md §N.N`." Add a one-paragraph specialty statement derived from the role's `when_to_use` so the foreign agent knows what lens to apply. Then append the same `Directives most relevant to this run:` list.

## Model and effort delivery

Resolve the model with this priority: `agents.<role>.model` if set; otherwise the dispatching lane's `models.*` value. Pass the resolved model as the Agent tool call's `model` parameter — the per-call parameter overrides the agent definition's `model:` frontmatter. A model that is resolved but not passed does nothing.

Effort is unset by default: comb passes no `effort`, so the session's default applies. Resolve it only when configured: `agents.<role>.effort` if set; otherwise the dispatching lane's `effort.*` value (the `effort` tree mirrors `models` key for key: `effort.review`, `effort.plan`, `effort.patterns`, `effort.fix.implementer_standard`, `effort.fix.implementer_trivial`, `effort.fix.reviewer`, `effort.the_desert`). When one resolves, pass it as the Agent tool call's `effort` parameter (`low` | `medium` | `high` | `xhigh` | `max`); when none does, omit the parameter.

## Parallel dispatch

Launch parallel dispatches by issuing multiple Agent tool calls in a single assistant message — one call per agent.
