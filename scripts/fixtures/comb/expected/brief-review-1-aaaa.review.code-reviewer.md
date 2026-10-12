# comb brief — review / code-reviewer (comb:code-reviewer)

## Directives

The project's authoritative directives apply. Read these directive files and cite as `file.md §N.N`:
- FIX/plugin/directives/consistency.md
- FIX/plugin/directives/maintainability.md
- FIX/plugin/directives/modularity.md
- FIX/plugin/directives/quality.md
- FIX/plugin/directives/reusability.md
- FIX/plugin/directives/scope-discipline.md
- FIX/plugin/directives/simplicity.md
- FIX/plugin/directives/testing.md
- FIX/project/docs/directives/simplicity.md
- FIX/project/docs/directives/velocity-rules.md

Directives most relevant to this run:
- FIX/plugin/directives/scope-discipline.md
- FIX/plugin/directives/simplicity.md
- FIX/project/docs/directives/simplicity.md

## Project conventions (observed baseline)

- TMP/ex.md (excerpt)
- TMP/PATTERNS.md (full manifest)

This is the codebase's observed convention baseline as of its last generation — a prior, not the authority. Read the actual code around the diff; where it conflicts with the manifest, the live code wins. If the manifest has no entry for this area or theme, reconstruct the convention from the code — silence is neither a finding nor permission. Project directives outrank this manifest: a divergence that violates an up-to-date directive is drift no matter how widespread, and classifying it as a deliberate improvement or new canonical never excuses a directive violation. Before flagging a divergence, classify it: unjustified, inconsistent divergence is drift (a finding); a deliberate, consistently-applied improvement or migration, or the first canonical pattern for something genuinely new, is not a drift finding. When you judge a divergence to be an improvement/migration or a new canonical, say so explicitly so the orchestrator can emit the semantic refresh note. Cite manifest entries by area/section heading when raising conformance findings. The excerpt lists the sections it omits with their line ranges. Read an omitted section by that range when the excerpt or the code points you to it. Do not read the full manifest end to end.

## User focus for this run

Findings matching this focus are highest priority. Surface other issues too, but do not let the user's stated concerns slip.

scope and simplicity
