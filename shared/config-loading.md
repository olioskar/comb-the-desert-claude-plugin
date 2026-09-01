# Shared block: layered config loading

Every comb skill loads its config this way. Read the layers in this order, deep-merging each layer onto the previous:

1. `${CLAUDE_PLUGIN_ROOT}/config/defaults.json` — shipped defaults
2. `~/.claude/comb.config.json` — global override (skip if not present)
3. `<project-root>/.claude/comb.config.json` — project override (skip if not present)

**Project root** is `git rev-parse --show-toplevel` (which correctly returns the worktree path for git worktrees; cwd fallback when not in git).

**Merge rules:**

- Objects: deep-merged
- Arrays: replaced wholesale
- `null` at any depth: removes that key from the merged result
- Invalid JSON in any layer: hard error (abort with a clear message naming the bad file)
- Schema violations (e.g., a role missing `subagent_type`): warn and skip the bad key, continue

Each skill states which keys it takes from the merged result.
