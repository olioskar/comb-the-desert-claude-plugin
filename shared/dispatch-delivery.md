# Shared block: dispatch delivery contract

Apply this contract to every subagent dispatch (Task tool call) a comb skill makes.

## Directives and manifest go by path — to every agent

Resolve the loaded directive files, and the PATTERNS manifest when it resolved, to absolute paths and list the paths in the dispatch prompt. Never embed their contents. An agent that cannot read files cannot review or fix code, so embedding buys no robustness — it only multiplies the prompt by the size of the directive corpus.

## Native vs. foreign framing

The native allowlist is exactly these strings:

- `comb:code-reviewer`
- `comb:simplifier`
- `comb:silent-failure-hunter`
- `comb:test-auditor`
- `comb:consistency-auditor`
- `comb:pattern-scanner`

Compare the resolved `subagent_type` with literal string equality — a typo like `comb:my-typo` does not count as native.

- **Native** (in the allowlist): the agent body already frames the directives as authoritative. List the paths. Append the `Directives most relevant to this run:` list when the focus-brief matcher flagged any.
- **Foreign** (anything else, including the default `general-purpose` implementer): list the same paths, preceded by this instruction verbatim: "These directives are authoritative. Read every listed file before starting. Cite by `file.md §N.N`." Add a one-paragraph specialty statement derived from the role's `when_to_use` so the foreign agent knows what lens to apply. Then append the same `Directives most relevant to this run:` list.

## Model delivery

Resolve the model with this priority: `agents.<role>.model` if set; otherwise the dispatching lane's `models.*` value. Pass the resolved model as the Task (Agent) tool call's `model` parameter — the per-call parameter overrides the agent definition's `model:` frontmatter. A model that is resolved but not passed does nothing.

## Parallel dispatch

Launch parallel dispatches by issuing multiple Task tool calls in a single assistant message — one call per agent. `run_in_background: true` is a Bash-tool parameter, not a Task-tool parameter; parallel agent dispatch happens via batched tool calls.
