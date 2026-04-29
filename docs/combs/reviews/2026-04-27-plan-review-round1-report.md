# comb-the-desert plugin plan — Round 1 Review Report

**Scope:** `docs/superpowers/plans/2026-04-27-comb-the-desert-plugin.md` (the implementation plan)
**Spec under review:** `docs/superpowers/specs/2026-04-27-comb-the-desert-plugin-design.md`
**Reviewers:** 2 agents (plan-vs-spec alignment, convention/correctness) + orchestrator self-pass
**Date:** 2026-04-27
**Focus brief:** Ambiguities + inconsistencies vs spec + correctness/conventions

---

## Verification Summary

| Check | Result |
|-------|--------|
| Plan exists at canonical path | ✓ |
| Spec exists and was read by both agents | ✓ |
| Embedded JSON content (`plugin.json`, `marketplace.json`, `defaults.json`) | byte-equivalent to spec — no drift |
| Claude Code plugins-reference + plugins + skills docs fetched | ✓ |
| Singular/plural directory naming | consistent |
| Plugin-name vs marketplace-name distinction | maintained correctly |
| `${CLAUDE_PLUGIN_ROOT}` usage in skill bodies | confirmed correct per docs |

---

## Verdict: **NEEDS WORK**

3 Critical findings break core spec contracts. 6 High findings include a likely-silent permission grant (the YAML-list form of `disallowedTools` may not parse) and several behavioral contradictions with the spec. The plan is structurally sound — embedded artifacts match the spec byte-for-byte, namespacing is consistent, manifests validate — but the four skill bodies have important gaps and direct contradictions that need to be fixed before execution.

---

## Findings by Severity

### Critical

**C1 — Plan/fix dispatches force `general-purpose` and skip directives in dispatch prompts**
*Source: plan-vs-spec-alignment*
File: `plan §Task 22, §Task 23`

Plan Task 22 (`/comb:plan`) hardcodes `subagent_type: general-purpose` for every planner. Task 23 (`/comb:fix`) does the same for every implementer and reviewer. This bypasses the entire `agents.<role>.subagent_type` config (spec §4.3) and contradicts §5.3 where `test-auditor` is explicitly named the plan/fix verifier. Worse, neither task includes directives in the dispatch prompt — but per spec §7.1.5, every skill builds prompts that include directives, and per §5.4 foreign agents (which `general-purpose` is) must receive **full directive contents**. The result: planners and implementers/reviewers run without the project's authoritative policy docs.

Fix: replace `subagent_type: general-purpose` in Tasks 22/23 with `subagent_type: <resolved from agents config>`. Add the standard directive-embed step (full contents for non-`comb:*`) to all three dispatch prompts (planner, implementer, reviewer). Use `comb:test-auditor` as the canonical fix-reviewer per spec §5.3.

**C2 — Per-agent model override silently lost in `/comb:plan` and `/comb:fix`**
*Source: plan-vs-spec-alignment*
File: `plan §Task 22, §Task 23`

Spec §4.3 states `agents.<role>.model` "applies to every command" and survives the-desert coercion (§7.6). Plan Task 21 (review) and Task 24 (the-desert) honor this. Tasks 22 and 23 don't mention it — they only resolve from `models.plan` or `models.fix.*` lanes. A user who sets `agents.simplifier.model: sonnet` would see it ignored when their agent runs as a planner or fix-reviewer.

Fix: add the same "Resolve model: `agents.<role>.model` if set, else `models.<lane>`" line in Tasks 22 and 23, mirroring Task 21.

**C3 — Substring-matching of focus brief against directive filenames is missing entirely**
*Source: plan-vs-spec-alignment*
File: `plan §Tasks 21–24` (all skill bodies)

Spec §8 specifies that the orchestrator scans the focus brief and surface relevant directives (e.g., `"simplicity"` → `simplicity.md`, `"scope"` → `scope-discipline.md`) by lowercased substring matching, then flags matches as primary in agent prompts. None of the 4 skill bodies in the plan describe this behavior. The brief is captured, biased into agent picking, injected verbatim, and carried through — but the directive cross-reference is absent.

Fix: add a step to each skill body that lowercases the focus brief, scans for substring hits against the loaded directive filenames, and flags matched directives in the dispatch prompt as "directives most relevant to this run."

---

### High

**H1 — `disallowedTools` uses YAML-list form; docs only show comma-separated string form (potential silent permission grant)**
*Source: convention/correctness*
File: `plan §Tasks 15–19` (all 5 agent files)

Plugins-reference shows `disallowedTools: Write, Edit` — comma-separated string. The plan uses YAML list form:
```yaml
disallowedTools:
  - Write
  - Edit
  - NotebookEdit
```
The doc lists `disallowedTools` as a supported field but only demonstrates the string form. If the plugin manifest parser accepts only the documented form, the YAML-list parses as an empty array — and our 5 "read-only reviewers" silently get Write/Edit permission. The agent body says read-only; the manifest enforcement would lapse.

Fix: convert to documented form: `disallowedTools: Write, Edit, NotebookEdit`. Or test both forms with `claude plugin validate` before relying on the list form.

**H2 — Trivial items skip the reviewer; contradicts spec §7.5**
*Source: plan-vs-spec-alignment*
File: `plan §Task 23, Step 3b/3d`

Spec §7.5: "For each instruction: implementer (opus standard, sonnet trivial), then reviewer (opus)" — no exception for trivial. Plan Task 23 announces `(trivial — sonnet implementer, no reviewer)` and explicitly skips the reviewer. The-desert override in Task 24 says "Every item gets a reviewer — no 'trivial — skipped review'" — implying trivial-skip is the default, which the plan author knows isn't authorized by the spec.

Fix: either run a reviewer on trivial items per spec, or update the spec to authorize trivial-skip behavior. The author's intent is ambiguous.

**H3 — `CLAUDE.md` base-branch lookup reinstated; contradicts spec §10**
*Source: plan-vs-spec-alignment*
File: `plan §Task 21, Inputs`

Spec §10 lists "Hardcoded base-branch lookup via `CLAUDE.md` — replaced by config + user override at invocation time" as one of the dropped behaviors. Plan Task 21 reinstates it: "Default: read from the project's `CLAUDE.md` if it specifies one; else `main`. The user may override."

Fix: remove the `CLAUDE.md` lookup. Either add a `paths.base_branch` (or similar) config field to the spec, or fall back to `main` and rely on user override at invocation time.

**H4 — Markdown-only palette restriction wording is looser than spec §7.3**
*Source: plan-vs-spec-alignment*
File: `plan §Task 21, Step 3`

Spec §7.3: "if `git diff --name-only` returns only `.md` files, the orchestrator restricts the palette to `code-reviewer` + `consistency-auditor`." Plan: "If scope is markdown-only (`.md` files), restrict palette..." Without the explicit `git diff --name-only` detection, an implementer might apply this only when the user says "review my markdown" rather than as automatic detection on the diff.

Fix: add the explicit `git diff --name-only` check in the skill body.

**H5 — Allowlist-match (not prefix-check) rule not propagated to plan/fix skills**
*Source: plan-vs-spec-alignment*
File: `plan §Tasks 22, 23`

Spec §5.4: "The check is an **allowlist match**, not a prefix check, so a typo like `subagent_type: 'comb:my-typo'` gets foreign-agent treatment rather than being assumed native." Task 21 enumerates the allowlist; Tasks 22 and 23 don't. Once C1 is fixed (these tasks dispatch via configured `subagent_type`), the allowlist semantics become load-bearing for them too.

Fix: when fixing C1, mirror Task 21's allowlist enumeration in Tasks 22 and 23.

**H6 — Planner / implementer / reviewer dispatch prompts are missing required sections**
*Source: plan-vs-spec-alignment*
File: `plan §Task 22 Step 5, §Task 23 Steps 3c/3d`

Spec §7.1.5 prescribes a 5-part dispatch prompt order: shared context, directives, focus brief heading, agent-specific instructions, output format spec. Plan §Task 22's planner prompt has only Finding/What-to-do/Save/Sections/focus brief — missing shared context, directives, output format. §Task 23's implementer and reviewer prompts are missing directives and shared context too.

Fix: restructure all three dispatch prompts (planner, implementer, reviewer) to follow the §7.1.5 order. See C1 for the directive-embed component.

---

### Medium

**M1 — Round-N-aware "prior report read and inform agents" goes beyond spec v1**
*Source: plan-vs-spec-alignment*
File: `plan §Task 21, Step 2`

Spec §7.3 specifies only `N = count + 1`. §12 lists "Round-N-aware reviews — parse most recent report ... reset N if base/branch shifted" as future work. Plan Task 21 reads the prior report and tells agents which findings were already fixed — that's the v2 behavior leaking into v1.

Fix: either remove the prior-report-read step from Task 21, or update the spec to authorize it as v1 behavior.

**M2 — `allowed-tools` array contains `Agent` — not a Claude Code tool name**
*Source: convention/correctness*
File: `plan §Tasks 21–24` (all 4 skill files)

The Claude Code subagent dispatch tool is named `Task`, not `Agent`. Including `Agent` in `allowed-tools` doesn't match any actual tool, so it neither pre-approves anything nor blocks anything. Functionality probably still works (permissions apply per-tool), but the entry is misleading documentation.

Fix: replace `Agent` with `Task` in the `allowed-tools` array of all 4 skills.

**M3 — Skill bodies say "use `run_in_background: true`" — not a Task-tool parameter**
*Source: convention/correctness*
File: `plan §Tasks 21–24` (skill bodies)

`run_in_background: true` is a Bash-tool parameter. Task tool does not accept it. Parallel subagent dispatches happen by issuing multiple Task tool calls in a single assistant message, not via this parameter. Claude executing the skill will probably figure out the right primitive, but the instruction as written points to a non-existent parameter.

Fix: replace "Launch all dispatches in parallel using `run_in_background: true`" with "Launch all dispatches in parallel by issuing multiple Task tool calls in a single assistant message."

**M4 — Smoke test cwd ambiguity in Task 28**
*Source: convention/correctness*
File: `plan §Task 28, Step 1`

Test setup `cd /tmp/comb-smoke-test` is presented in the same code block as the test repo creation. The next instruction `claude --plugin-dir /Users/olafur/.../comb-the-desert-claude-skill` is in isolation. Whether the executor runs `claude` from `/tmp/comb-smoke-test` is ambiguous. If they're not in the test repo's cwd, `/comb:review` will pick up the wrong repo or fail to find one.

Fix: explicit step: "Still in `/tmp/comb-smoke-test`, run: `claude --plugin-dir ...`"

**M5 — `npx tsc --noEmit` and `npx vitest run` hardcoded in review skill body**
*Source: convention/correctness, orchestrator self-pass*
File: `plan §Task 21, Step 4`

The skill body specifies TypeScript-flavored verification commands. The plugin is supposed to be domain-neutral. For Python, Rust, or any non-TS project, these commands fail or produce misleading output.

Fix: reframe as "Run project-appropriate verification (typecheck, tests, lint). Examples: `npx tsc --noEmit`, `npx vitest run`, `pytest`, `cargo check`. Read `CLAUDE.md` or the project's manifest (`package.json`, `pyproject.toml`, `Cargo.toml`) to choose."

**M6 — Verification step doesn't actually verify "judgment-based picking with hard cap 5"**
*Source: plan-vs-spec-alignment*
File: `plan §Task 25, §Task 28`

Spec §7.1.4 specifies "judgment-based selection ... Hard cap: 5 ... Soft floor: 1." The plan's verification (Task 25) only checks file existence and `disable-model-invocation` boolean values. The smoke test in Task 28 runs a single review on a tiny diff but doesn't exercise cap/floor.

Fix: add a smoke step exercising a varied-enough diff to force >5 candidate agents, confirm orchestrator caps at 5 and includes `code-reviewer`.

**M7 — Python `import yaml` snippet in Tasks 15 and 21 doesn't pre-check PyYAML**
*Source: convention/correctness*
File: `plan §Task 15 Step 3, §Task 21 Step 3`

Validation snippet does `import yaml` (PyYAML — third-party). macOS system Python doesn't bundle it. Plan has a parenthetical noting this, but the executor sees a `ModuleNotFoundError` first.

Fix: either replace with stdlib regex-based parsing, or add `python3 -c 'import yaml'` to Phase 0 prereq checks (with `pip3 install pyyaml` fallback).

**M8 — Smoke test verdict expectation is too specific**
*Source: orchestrator self-pass*
File: `plan §Task 28, Step 2`

Plan asserts "Verdict is APPROVE (no real issues in the toy diff)." This depends on agent judgment about a 1-line change — could go either way. Smoke test is more useful as "did the plugin load and produce a structured report" than "did the review reach a specific verdict."

Fix: relax expectation to "report file is created at the expected path and matches the structural template" — drop the verdict requirement.

**M9 — "3 pairs concurrent" terminology ambiguous**
*Source: plan-vs-spec-alignment*
File: `plan §Task 23, Step 4`

Spec §7.5 phrase "max 3 pairs concurrent" is ambiguous (a "pair" implies implementer+reviewer running together; 3 pairs = 6 concurrent agents? or 3 items?). Plan inherits the ambiguity.

Fix: pin to one interpretation. Recommend: "max 3 implementer/reviewer pairs running concurrently — i.e., up to 3 items being implemented and verified at any given moment."

**M10 — Phase 0 misleading wording about "previous attempt"**
*Source: orchestrator self-pass*
File: `plan §Phase 0, Step 1`

Phase 0 says "Anything else suggests a previous attempt — investigate before continuing." But the working dir already legitimately contains `docs/`, `DESIGN.md`, `.gitignore` from the brainstorm. The wording sounds like these would be unexpected.

Fix: reword to "Anything other than `docs/`, `DESIGN.md`, `.gitignore` may be a previous attempt — investigate before continuing."

---

### Low

**L1 — Spec §4 worktree note dropped from skill bodies**
*Source: plan-vs-spec-alignment*

Spec parenthetical notes that `git rev-parse --show-toplevel` correctly handles git worktrees. The plan's skill bodies don't carry this. Behavior is still correct (`--show-toplevel` does the right thing), just a documentation gap.

**L2 — Triviality "judgment-based" framing missing from `/comb:fix` body**
*Source: plan-vs-spec-alignment*
File: `plan §Task 23, Step 3b`

Spec §7.5 says triviality is "judgment-based by the orchestrator using this rubric." Plan lists the rubric items but doesn't include the "judgment-based" framing.

**L3 — Task 25 doesn't verify `argument-hint`, `allowed-tools`, `user-invocable`**
*Source: plan-vs-spec-alignment*

Plan verifies only `disable-model-invocation`. Other spec §7.2 frontmatter fields not checked.

Fix: extend Task 25 with greps for the other fields.

**L4 — `WebFetch` missing from `allowed-tools` in plan/fix skills**
*Source: plan-vs-spec-alignment*

Spec §7.2 frontmatter example includes WebFetch. Tasks 22 and 23 omit it (defensible — plan/fix don't fetch from the web), but no justification appears in the plan.

**L5 — `/comb:fix` step ordering puts "Parallel execution" after "Execution loop"**
*Source: plan-vs-spec-alignment*
File: `plan §Task 23, Steps 3 and 4`

Reading literally, parallel batching happens after the loop is done — but it's meant to govern the loop. Organizational issue.

Fix: restructure — put the parallel-batching policy inside or before Step 3.

**L6 — Task 20 verification doesn't check `name` matches filename or `model` value**
*Source: plan-vs-spec-alignment, convention/correctness*

Verifies presence of fields, not values. Could miss typos (e.g., `name: code-revewer`).

Fix: add `grep -q '^model: opus'` and `grep -q "^name: $(basename "$f" .md)"`.

**L7 — `grep -A 4 ... | grep -q ...` window-based check is fragile**
*Source: convention/correctness*
File: `plan §Task 20, Step 3`

A 4-line window assumes specific YAML layout; minor edits push items out.

Fix: use a YAML parser if PyYAML is already a dependency.

**L8 — Glob expansion fragility: `for f in directives/*.md`**
*Source: convention/correctness*

If the directory is empty, bash expands the glob to literal text and the loop body errors. Earlier tasks guarantee files exist, so this is latent fragility, not a bug.

**L9 — Phase 0 prereq missing `python3`, `pyyaml`, `gh`, and `npx`**
*Source: convention/correctness*

Phase 0 verifies `git`, `jq`, `claude`. Tasks downstream use python3+yaml (15, 21), `gh` (28, 29 if smoke-testing PRs), `npx` (review skill verification step).

Fix: extend Phase 0 prereq list.

**L10 — Plan doesn't describe version-bump workflow**
*Source: convention/correctness*

Per plugins-reference, setting `version` in `plugin.json` requires bumping it on each release for users to receive updates. Plan sets `0.1.0` (Task 3) and tags `v0.1.0` (Task 30) but doesn't establish the bump rhythm.

Fix: note in CONTRIBUTING or CHANGELOG that future releases must bump `plugin.json` `version`.

**L11 — `marketplace.json` schema not fully documented in the in-scope Claude Code docs**
*Source: convention/correctness*

The conventional shape used (matching `anthropics/claude-code`) is reasonable but not strictly verifiable from `plugins-reference` alone. Smoke test (Task 29) is the practical verification.

**L12 — Tighter `tools:` allowlist would beat `disallowedTools:` denylist**
*Source: convention/correctness*

For read-only reviewers, an explicit allowlist (`tools: Read, Grep, Glob, Bash`) provides stronger guarantees than a denylist. Convention slip, not a bug.

**L13 — `marketplace remove` slash-command syntax undocumented**
*Source: convention/correctness*
File: `plan §Task 29, Step 4`

Plan uses `/plugin marketplace remove comb-marketplace` — undocumented in the in-scope plugins doc.

Fix: verify with `/plugin help` during smoke test, or skip the cleanup step (cheap to leave the marketplace installed locally).

**L14 — Task 30 assumes the GitHub repo exists; Task 29 depends on Task 30 having pushed**
*Source: convention/correctness, orchestrator self-pass*

Plan flags this in a parenthetical but creates a circular dependency (Task 29 → Task 30 → manual GitHub setup).

Fix: add explicit "Confirm GitHub repo exists at olioskar/comb-the-desert-claude-plugin (use `gh repo create` if not)" before push.

**L15 — Task 25 grep checks anchored to specific YAML formatting**
*Source: convention/correctness*

`grep -q '^disable-model-invocation: true$'` would miss `True`, quoted values, or trailing whitespace. Works for as-written, fragile against edits.

**L16 — Plan's smoke test doesn't run `claude plugin validate`**
*Source: convention/correctness*

Plugins-reference suggests `claude plugin validate` for catching manifest/frontmatter errors. Plan only does `claude --plugin-dir ...` then `/help`.

Fix: add `claude plugin validate <path>` to Task 28 Step 1.

**L17 — Self-review claim "every task has actual content" slightly overstated**
*Source: convention/correctness*

Skill bodies (Tasks 21–24) contain `{placeholder}`s in the report templates. Strictly these are runtime placeholders Claude fills in, not plan-stage placeholders, but the self-review's claim is absolute.

**L18 — Skill bodies missing the `model` frontmatter field (informational)**
*Source: convention/correctness*

Skills don't set `model:` in frontmatter — they let the user's session model run, then the body's logic dispatches subagents at the configured `models.<lane>` model. This is the correct intent, just worth noting (the skill body's runtime model is independent of the model used for dispatched agents).

**L19 — Smoke test instruction wording mixes "use existing repo" and "create new repo"**
*Source: convention/correctness*
File: `plan §Task 28, Step 1`

"Navigate to a small test repo (any git repo with a recent commit)" followed by `mkdir -p comb-smoke-test && git init`. Confusing.

Fix: pick one — recommend "create a fresh test repo" since it's deterministic.

**L20 — `subagent_type: general-purpose` assumed available without verification**
*Source: convention/correctness*

The skills doc confirms `general-purpose` is a built-in. Whether it's directly addressable as a Task-tool `subagent_type` is conventional; not enumerated in the docs in scope.

**L21 — Skill `name` field inheritance check missing from Task 25**
*Source: convention/correctness*

Plan doesn't verify each `SKILL.md`'s `name:` matches its directory name (which would produce the `/comb:<name>` invocation correctly).

---

### Test Gaps

**TG1 — No structural test for skill-body claims**
The skill bodies prescribe complex orchestrator behavior (config merge, agent picking, dispatch prompt assembly). The plan's smoke test runs one review against a tiny diff. There's no test that confirms config-merge null-as-delete works, or that the agent palette caps at 5, or that directives surface correctly. Spec §4.1 merge semantics are unverified.

Fix: add at least one fixture-driven test in Phase 5: a fake project with a known `comb.config.json` setting `agents.simplifier: null`, run `/comb:review`, confirm simplifier doesn't appear in the dispatched palette.

### Deferred

None.

---

## Notes

- **Embedded artifacts are clean.** `plugin.json`, `marketplace.json`, `defaults.json`, all 8 directives, and all 5 agent specialty descriptions match the spec byte-equivalent or in spirit. No drift in the static content.
- **The four skill bodies are where most issues concentrate.** They encode the orchestrator logic, and that's where spec contracts are most easily lost in translation. The fixes for C1, C2, C3, H4, H5, H6, M2, M3, M5, M6 all touch skill bodies.
- **`disallowedTools` form (H1) is the single most likely cause of a real production issue.** If the plugin manifest parser doesn't accept the YAML-list form, the read-only-agents safety promise lapses silently. Worth converting to the documented comma-string form OR running `claude plugin validate` to confirm both forms parse.
- **Top 5 to fix before execution:**
  1. C1 — restore `subagent_type` resolution and directive embedding in plan/fix dispatches
  2. C2 — honor `agents.<role>.model` in plan/fix
  3. C3 — implement focus-brief→directive substring matching in all 4 skill bodies
  4. H1 — convert `disallowedTools` to documented comma-string form
  5. H4 — drop the `CLAUDE.md` base-branch lookup
