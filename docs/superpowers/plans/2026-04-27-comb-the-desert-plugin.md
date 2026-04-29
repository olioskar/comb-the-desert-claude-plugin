# comb-the-desert plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship v0.1.0 of the `comb` Claude Code plugin — a `/comb:review` → `/comb:plan` → `/comb:fix` pipeline with `/comb:the-desert` for the full sweep, configurable agents, and authoritative directives.

**Architecture:** Plugin manifest + same-repo marketplace + 5 read-only reviewer subagents (`comb:*`) + 8 domain-neutral directives + 4 user-invocable skills containing the orchestrator logic + layered config (`project > global > shipped defaults`).

**Tech Stack:** Markdown (skills, agents, directives), JSON (manifests, config), bash (smoke tests, validation), Claude Code plugin runtime.

**Source spec:** `docs/superpowers/specs/2026-04-27-comb-the-desert-plugin-design.md`

**Working directory:** `/Users/olafur/Development/comb-the-desert-claude-skill`

---

## Phase 0: Pre-flight

Before starting, verify:

- [ ] **Confirm working directory contains only the brainstorm artifacts.**

```bash
ls -1 /Users/olafur/Development/comb-the-desert-claude-skill
```

Expected: `docs/`, `DESIGN.md`, `.gitignore` (these were produced during brainstorming and are committed/intended state). Anything other than these three entries may indicate a previous implementation attempt — investigate and clean before continuing.

- [ ] **Verify all required CLIs and Python deps are installed.**

```bash
# Core CLIs used directly by the plan
git --version && \
jq --version && \
which claude && \
gh --version && \
npx --version && \
python3 --version

# PyYAML is required by validation snippets in Tasks 15, 20, 21, and 25.
# macOS system Python does NOT bundle it.
python3 -c 'import yaml; print("pyyaml", yaml.__version__)'
```

Expected: every command prints a version (or path, for `which claude`) and `python3 -c 'import yaml'` prints `pyyaml <version>`.

If `python3 -c 'import yaml'` fails with `ModuleNotFoundError`, install PyYAML first:

```bash
python3 -m pip install --user pyyaml
```

Then re-run the verification block before proceeding to Phase 1. **Do not start Phase 1 until every line of this block succeeds** — Tasks 15, 20, 21, 25, 28, 29, and 30 all assume these tools are present.

---

## Phase 1: Repo foundation

### Task 1: Initialize git repo and write project metadata files

**Files:**
- Create: `.gitignore`
- Create: `LICENSE` (MIT)
- Create: `CHANGELOG.md`

- [ ] **Step 1: Initialize git**

```bash
cd /Users/olafur/Development/comb-the-desert-claude-skill
git init
git branch -M main
```

- [ ] **Step 2: Write `.gitignore`**

The existing `.gitignore` only excludes `DESIGN.md` (working copy of the spec). Append nothing — keep it minimal. Verify content:

```bash
cat .gitignore
```

Expected output:
```
# Local working copy of the spec — committed version lives at docs/superpowers/specs/
DESIGN.md
```

- [ ] **Step 3: Write `LICENSE` (MIT)**

Create `LICENSE` with this exact content:

```
MIT License

Copyright (c) 2026 Olafur Oskarsson

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 4: Write `CHANGELOG.md` placeholder**

```markdown
# Changelog

All notable changes to this plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

(Initial v0.1.0 entry filled in at the end of this plan — see Phase 5.)
```

- [ ] **Step 5: First commit**

```bash
git add .gitignore LICENSE CHANGELOG.md
git commit -m "chore: initialize repo with MIT license and changelog"
```

---

### Task 2: Write README.md scaffold

**Files:**
- Create: `README.md`

The full README content is finalized in Task 23 once skills and config are implemented. For now, scaffold the structure so links from `plugin.json` (`homepage`, `repository`) point at a non-empty document.

- [ ] **Step 1: Write README scaffold**

```markdown
# comb-the-desert

A Claude Code plugin for code review: a `/comb:review` → `/comb:plan` → `/comb:fix` pipeline with `/comb:the-desert` for the full sweep. Configurable reviewer agents and authoritative project directives.

> Status: in development. v0.1.0 is the first published release.

## Install

(Filled in at the end of Phase 5.)

## Usage

(Filled in at the end of Phase 5.)

## Configuration

(Filled in at the end of Phase 5.)

## License

MIT
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README scaffold"
```

---

### Task 3: Write `.claude-plugin/plugin.json` manifest

**Files:**
- Create: `.claude-plugin/plugin.json`

- [ ] **Step 1: Create directory**

```bash
mkdir -p .claude-plugin
```

- [ ] **Step 2: Write plugin.json**

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

- [ ] **Step 3: Validate JSON**

```bash
jq . .claude-plugin/plugin.json
```

Expected: prints the JSON pretty-formatted with no error.

- [ ] **Step 4: Commit**

```bash
git add .claude-plugin/plugin.json
git commit -m "feat: add plugin manifest (v0.1.0)"
```

---

### Task 4: Write `.claude-plugin/marketplace.json`

**Files:**
- Create: `.claude-plugin/marketplace.json`

This makes the same repo serve as both the marketplace and the single-plugin source — same pattern as `anthropics/claude-code`.

- [ ] **Step 1: Write marketplace.json**

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

- [ ] **Step 2: Validate JSON**

```bash
jq . .claude-plugin/marketplace.json
```

Expected: prints the JSON pretty-formatted with no error.

- [ ] **Step 3: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "feat: add marketplace manifest"
```

---

### Task 5: Write `config/defaults.json`

**Files:**
- Create: `config/defaults.json`

This is the shipped default config layer. User layers (`.claude/comb.config.json` project-local, `~/.claude/comb.config.json` global) deep-merge on top of it at runtime.

- [ ] **Step 1: Create directory**

```bash
mkdir -p config
```

- [ ] **Step 2: Write defaults.json**

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

- [ ] **Step 3: Validate JSON**

```bash
jq . config/defaults.json
```

Expected: prints the JSON pretty-formatted with no error.

- [ ] **Step 4: Verify the agents map has all 5 shipped roles**

```bash
jq '.agents | keys' config/defaults.json
```

Expected output:
```json
[
  "code-reviewer",
  "consistency-auditor",
  "silent-failure-hunter",
  "simplifier",
  "test-auditor"
]
```

- [ ] **Step 5: Commit**

```bash
git add config/defaults.json
git commit -m "feat: add shipped config defaults"
```

---

## Phase 2: Directives (8 authoritative policy docs)

Each directive follows the format pinned in spec §6.1:
- Numbered hierarchical sections (`§N`, `§N.M`)
- Prescriptive voice
- Each section explains the *why*, not just the *what*
- Optional `## Implementation Notes` appendix at the end (empty for plugin defaults; users add their own)

Cited in findings as `<file>.md §N.N`.

### Task 6: Write `directives/simplicity.md`

**Files:**
- Create: `directives/simplicity.md`

- [ ] **Step 1: Create directives directory**

```bash
mkdir -p directives
```

- [ ] **Step 2: Write the directive**

```markdown
## Simplicity Directives

These directives govern when *not* to do something. Every change should be the minimum that solves the stated problem. Speculative work, defensive patterns for impossible cases, and abstractions designed for hypothetical futures are recurring sources of bugs and review churn.

Treat these rules as policy. Exceptions require explicit documentation, owner, and revisit plan.

---

### 1. YAGNI

1. **Build for the asked problem, not the imagined one.**
   - If the spec or plan does not call for a feature, do not introduce it.
   - "We might need it later" is not a reason — when the need arrives, the code can be added with full context.

2. **One concrete use-case beats one abstraction.**
   - Do not create generic helpers, base classes, or configuration knobs to support a single caller.
   - Three similar lines is preferable to a premature abstraction. The third caller is the right time to extract.

3. **No design for hypothetical scale or extension.**
   - Avoid plugin systems, registries, or strategy patterns until at least two distinct concrete strategies exist.

---

### 2. No speculative defenses

1. **Trust internal code.**
   - Do not validate inputs at boundaries that internal callers control.
   - Validate at *external* boundaries only: user input, external APIs, file I/O, network responses.

2. **Do not catch what cannot fail.**
   - `try/catch` around code that has no failure mode is dead defensive paranoia. Remove it.
   - If a failure mode is theoretical but not real (e.g., a `JSON.parse` of literal-known-good content), do not wrap it.

3. **No defensive optional chaining for guaranteed values.**
   - If the type system or framework guarantees a value is present, do not add `?.` chains "just in case."

---

### 3. No hypothetical concerns in reviews

1. **Findings must reference real failure modes.**
   - "What if X happens?" — produce a path that triggers X. If you cannot, the concern is hypothetical.

2. **No "this could be improved" without a concrete what-and-why.**
   - Suggest the specific improvement and the specific cost it pays for. Vague gestures at quality are not findings.

3. **Don't invent issues.**
   - When a diff is small and clean, the right finding count is small. Padding a review with marginal observations dilutes the signal of real findings.

---

### 4. Minimal diffs

1. **Touch only what the change requires.**
   - Drive-by refactors, formatting fixes, and unrelated cleanups go in separate commits or separate PRs.

2. **No half-implementations.**
   - If a change is too large to ship cleanly, decompose into shippable slices. Do not leave a mid-state in the codebase.

3. **No backwards-compat shims for unreleased code.**
   - Until v1, change the code, do not maintain ghost APIs.

---

### 5. Comments are the last resort

1. **Prefer better names over explanatory comments.**
   - If a comment is needed because the code is unclear, fix the code.

2. **Comments document *why*, not *what*.**
   - Hidden constraints, surprising invariants, workarounds for specific bugs — yes. Restating what the next line does — no.

3. **No comments referencing the change itself.**
   - "Added for issue #123" / "used by X flow" — those rot. PR description and commit message carry that load.

---

A simpler change is a safer change. Aggressive simplicity is the foundation of every other directive in this set.

## Implementation Notes

(Project-specific notes go here. Empty in the plugin's shipped defaults.)
```

- [ ] **Step 3: Verify file exists and has expected section count**

```bash
grep -c '^### ' directives/simplicity.md
```

Expected: `5` (sections 1-5).

- [ ] **Step 4: Commit**

```bash
git add directives/simplicity.md
git commit -m "feat(directives): add simplicity policy"
```

---

### Task 7: Write `directives/modularity.md`

**Files:**
- Create: `directives/modularity.md`

- [ ] **Step 1: Write the directive**

```markdown
## Modularity Directives

These directives govern how code is decomposed: where boundaries fall, how units communicate, and what each unit is responsible for. Good modularity is the strongest single predictor of how easy a codebase is to work in over time.

Treat these rules as policy. Exceptions require explicit documentation, owner, and revisit plan.

---

### 1. One responsibility per unit

1. **Each file, function, or component has one clear job.**
   - The reader should be able to state the unit's responsibility in one sentence without "and."
   - If a unit's name needs "and" or "manager" or "helper" to describe it, decompose.

2. **No god files.**
   - When a file grows past comfortable working context (~300–500 lines, codebase-dependent), split by responsibility, not by technical layer.

3. **Files that change together stay together.**
   - The natural unit of cohesion is "what changes for the same reason." A model file and its validators belong near the consumers; not necessarily in a `models/` flat directory.

---

### 2. Clear interfaces

1. **Each unit exposes a deliberate API.**
   - Public functions, types, and exports represent contracts. Internal helpers stay internal.

2. **Hide implementation, not behavior.**
   - Consumers should not need to know how a unit accomplishes its job, only what it accomplishes.

3. **No leaky abstractions.**
   - If consumers need to know about cache states, internal queues, or transactional details to use a unit, the boundary is wrong.

---

### 3. Composition over inheritance

1. **Prefer small composable pieces to deep hierarchies.**
   - Extending classes to share behavior creates rigid coupling. Composing focused functions/components keeps each piece independent.

2. **Cross-cutting concerns belong in cross-cutting tools.**
   - Logging, metrics, auth — use middleware, decorators, or context, not inheritance.

---

### 4. Boundaries are testable

1. **A well-bounded unit can be tested in isolation.**
   - If a unit can only be tested through its consumers, its boundary is too implicit.

2. **Inputs and outputs are observable.**
   - Effects (network, file system, time) sit at the edges. Pure logic sits inside.

---

### 5. Coupling is intentional

1. **Imports are a coupling signal.**
   - Many imports across module boundaries means the modules are not as independent as they look.

2. **Circular dependencies are bugs.**
   - Even if the runtime allows them, they indicate that the boundary between the two units does not exist.

3. **Deep dependency chains are a smell.**
   - A → B → C → D for a simple operation suggests that the chain represents accidental rather than essential structure.

---

Smaller, well-bounded units are easier for humans and AI alike to reason about, modify safely, and test confidently.

## Implementation Notes

(Project-specific notes go here. Empty in the plugin's shipped defaults.)
```

- [ ] **Step 2: Commit**

```bash
git add directives/modularity.md
git commit -m "feat(directives): add modularity policy"
```

---

### Task 8: Write `directives/reusability.md`

**Files:**
- Create: `directives/reusability.md`

- [ ] **Step 1: Write the directive**

```markdown
## Reusability Directives

These directives govern duplication, extraction, and abstraction. The point is not "DRY at all costs" — over-abstraction is as costly as duplication. Aim for the right shape, not the most-shared shape.

Treat these rules as policy. Exceptions require explicit documentation, owner, and revisit plan.

---

### 1. Don't copy-paste

1. **Identical code in two places is a bug waiting to happen.**
   - One copy will be fixed, the other will not. The drift is invisible until it bites.

2. **Extract on the third occurrence, not the second.**
   - Two similar uses are often coincidence. Three are a pattern. Premature extraction at N=2 frequently produces an abstraction that breaks when N=3.

3. **When you copy, comment the copy.**
   - If you genuinely need a temporary copy (e.g., during a refactor), leave a TODO referencing the canonical version so the copy gets removed when the refactor lands.

---

### 2. Don't over-abstract

1. **The wrong abstraction is more expensive than duplication.**
   - A shared helper that almost-fits all callers forces every caller to bend, adds parameters to fit edge cases, and obscures the actual logic.

2. **No "configurable everything" base classes.**
   - When a parent class has more configuration knobs than concrete behavior, you have a meta-problem, not a base class.

3. **Inline before you abstract.**
   - When you find duplication, first try inlining one copy and seeing whether the resulting code reads more clearly. Sometimes "duplication" is just two clear pieces of code that happen to look similar.

---

### 3. Shared utilities are exceptions, not defaults

1. **Default to colocating helpers with their consumer.**
   - A helper used by one component lives in that component's file or a sibling file.

2. **Promote to shared only when needed.**
   - When a second consumer arrives, move the helper to a shared location. Until then, it's noise in the shared namespace.

3. **Shared utilities have tests.**
   - When a function becomes shared, it gains a contract that callers depend on. Treat it accordingly.

---

### 4. Naming conveys reusability

1. **Generic names imply generic usage.**
   - `formatDate(date)` implies broad reuse; `formatRowDateForGrid(date)` implies a specific caller.
   - Match the name's specificity to the actual scope.

2. **Don't lie with names.**
   - A function called `getUser` that fetches and creates and updates is not a getter. Either narrow it or rename it.

---

### 5. Extraction targets

1. **Extract complex logic, not boilerplate.**
   - Three identical 50-line functions with slight variations are a strong extraction target.
   - Three identical 2-line snippets often aren't worth abstracting.

2. **Extraction reduces cognitive load.**
   - The post-extraction call site should be easier to understand than the pre-extraction copies. If the extraction's signature has 7 parameters and a config object, you've moved complexity, not removed it.

---

Reusability is a means, not a goal. The goal is code that is easy to change. Sometimes that means sharing; sometimes it means deliberate, intentional duplication.

## Implementation Notes

(Project-specific notes go here. Empty in the plugin's shipped defaults.)
```

- [ ] **Step 2: Commit**

```bash
git add directives/reusability.md
git commit -m "feat(directives): add reusability policy"
```

---

### Task 9: Write `directives/maintainability.md`

**Files:**
- Create: `directives/maintainability.md`

- [ ] **Step 1: Write the directive**

```markdown
## Maintainability Directives

These directives govern how the codebase ages. Maintainable code is code that the next contributor (human or AI) can read, understand, and change confidently — months or years after it was written.

Treat these rules as policy. Exceptions require explicit documentation, owner, and revisit plan.

---

### 1. Readable code

1. **Write for the reader, not the writer.**
   - Optimize for the time someone (likely you in three months) needs to understand and modify the code.

2. **Naming is the highest-leverage tool.**
   - A precise name eliminates the need for explanatory comments. Spend the time to choose well.
   - Names should reflect domain concepts when possible. `customer.invoice` beats `data.entry`.

3. **Avoid clever code.**
   - Compact tricks that save 3 lines but force the reader to pause are net-negative.

---

### 2. No dead code

1. **Delete what you do not use.**
   - Commented-out blocks, unused imports, abandoned helpers — version control already preserves history. The current file should reflect current truth.

2. **Unused parameters and exports are bugs.**
   - Keeping them "in case" creates false coupling and confuses readers about what the actual contract is.

---

### 3. Comment discipline

1. **Default to no comments.**
   - Most well-written code does not need them.

2. **Comment hidden constraints, not visible code.**
   - "This must come before X because Y" — yes.
   - "Increment the counter" above `counter++` — no.

3. **Don't reference the change in comments.**
   - "Added for issue #123" / "fix from PR #456" — that information lives in the commit message and PR. In the code, it rots.

---

### 4. No drive-by changes

1. **One change per commit, one purpose per PR.**
   - When you find an unrelated issue while working, file it or stash it. Address it in a focused change.

2. **Do not silently improve unrelated code.**
   - Reformatting, renaming, or "cleaning up" code outside the scope of the current task obscures the actual change and breaks `git blame`.

---

### 5. Consistent style

1. **Follow the codebase's conventions, even if you disagree with them.**
   - The cost of inconsistency exceeds the benefit of any individual style preference.

2. **One style per concept across the codebase.**
   - If half the codebase uses `async/await` and half uses `.then()`, pick one as part of a focused migration. Don't introduce a third.

---

Code is read more times than it is written. Maintainability is consideration for those future readers.

## Implementation Notes

(Project-specific notes go here. Empty in the plugin's shipped defaults.)
```

- [ ] **Step 2: Commit**

```bash
git add directives/maintainability.md
git commit -m "feat(directives): add maintainability policy"
```

---

### Task 10: Write `directives/quality.md`

**Files:**
- Create: `directives/quality.md`

- [ ] **Step 1: Write the directive**

```markdown
## Quality Directives

These directives govern correctness and robustness — making sure the code does what it claims and fails honestly when it cannot.

Treat these rules as policy. Exceptions require explicit documentation, owner, and revisit plan.

---

### 1. Correctness first

1. **Verify behavior, not assumptions.**
   - Run the code. Observe the output. "It should work" is not the same as "it works."

2. **Off-by-one, fence-post, and bounds errors are bugs, not nits.**
   - Test the edges: empty input, single item, very large input, exactly-at-boundary.

3. **Trust the type system, but verify the types.**
   - Strict typing catches a class of bugs. It does not catch logic errors. Both layers matter.

---

### 2. Honest error handling

1. **Surface errors, do not swallow them.**
   - A `catch` block that silently returns a default, logs nothing, or returns `null` to the caller hides bugs.

2. **Match the error to the recovery.**
   - If you can recover, recover. If you cannot, propagate. Do not pretend.

3. **Distinguish expected failures from bugs.**
   - "User submitted invalid input" is expected — return a clear validation error.
   - "Database returned undefined for a required field" is a bug — fail loudly so the bug is found.

---

### 3. Validate at boundaries

1. **External input is untrusted.**
   - User input, external API responses, file contents, environment variables — validate the shape and contents before acting on them.

2. **Internal contracts are trusted.**
   - Code you control communicates via types and interfaces. Re-validating at every internal call site is noise.

3. **One validation point per boundary.**
   - Validate at the edge, then trust the validated value through the rest of the flow. Multiple validations of the same value indicate unclear ownership.

---

### 4. No silent fallbacks for bugs

1. **A fallback that hides a bug is worse than a crash.**
   - Default values, optional chaining cascades, and `try/catch` returning `null` can mask a bug for months. The bug will resurface — usually in production, usually at a worse time.

2. **Fallbacks are only for known-acceptable defaults.**
   - "Use empty string if the user has no display name" — fine.
   - "Use empty array if the API returned a 500" — not fine. The 500 is the signal.

---

### 5. Clean state on failure

1. **Do not leave half-finished work behind.**
   - If a multi-step operation fails partway, undo what was started. Do not leave the system in an indeterminate state.

2. **Reset transient state on error.**
   - Loading flags, in-flight indicators, and modal openness should resolve to a definite state on every code path.

---

Quality is the absence of unpleasant surprises in production. Honest failure modes are the foundation.

## Implementation Notes

(Project-specific notes go here. Empty in the plugin's shipped defaults.)
```

- [ ] **Step 2: Commit**

```bash
git add directives/quality.md
git commit -m "feat(directives): add quality policy"
```

---

### Task 11: Write `directives/consistency.md`

**Files:**
- Create: `directives/consistency.md`

- [ ] **Step 1: Write the directive**

```markdown
## Consistency Directives

These directives govern how new work fits with existing work. Consistency is what makes a codebase navigable — when one part of the system teaches you the conventions used by every other part.

Treat these rules as policy. Exceptions require explicit documentation, owner, and revisit plan.

---

### 1. Follow established patterns

1. **The existing codebase is the first source of truth for style.**
   - Before introducing a new pattern, check whether one already exists. If so, follow it.

2. **One way per concept.**
   - If state management uses X across the codebase, do not introduce Y for a single new feature unless deliberately migrating.

3. **Drift accumulates.**
   - "Just this once" inconsistencies become two-once, then three-once. The cost is cumulative; the benefit of any one inconsistency is local.

---

### 2. Reference implementations

1. **When a feature has a canonical example, follow it.**
   - "Build the new entity page like the Jobs page" — the reference is the spec.

2. **Identify and call out the reference in PR descriptions.**
   - The reviewer should know what the new code is modeled on; that's how they assess fidelity.

3. **Improvements to references are separate work.**
   - If the reference is wrong, that's a finding for the reference, not a license to deviate in the new feature.

---

### 3. Spec/plan alignment

1. **The spec is the contract for what we're building.**
   - The implementation must match. Findings about ambiguities or contradictions in the spec are bugs in the spec, not in the code.

2. **The plan is the contract for how we're building it.**
   - Deviations from the plan need explicit justification.

3. **Missing the spec is a critical finding.**
   - "Spec said X, code does Y" is a Critical-severity issue regardless of whether Y "seems fine."

---

### 4. Naming and vocabulary

1. **Use the codebase's domain vocabulary.**
   - If the codebase calls them "worksites," do not introduce "sites" or "locations" for the same concept.

2. **Consistent naming across layers.**
   - The API field, the model property, the form input, the UI label — should resolve to the same name where possible.

3. **Singular and plural conventions.**
   - Pick one (`workSite` and `workSites`, or `site` and `sites`) and use it across.

---

### 5. Cross-domain ripple

1. **Schema changes ripple to every layer.**
   - Database, API, types, form fields, exports, tests, documentation — all reflect the change.

2. **Verify the ripple before approving.**
   - A schema change that updates the type but not the form, or the API but not the export, is half-done.

---

Consistency is not aesthetic preference. It's the property that lets a contributor read one part of the codebase and predict the rest.

## Implementation Notes

(Project-specific notes go here. Empty in the plugin's shipped defaults.)
```

- [ ] **Step 2: Commit**

```bash
git add directives/consistency.md
git commit -m "feat(directives): add consistency policy"
```

---

### Task 12: Write `directives/scope-discipline.md`

**Files:**
- Create: `directives/scope-discipline.md`

- [ ] **Step 1: Write the directive**

```markdown
## Scope Discipline Directives

These directives govern what is in and out of any given change. Scope creep is the most common single cause of slow PRs, missed deadlines, and review churn.

Treat these rules as policy. Exceptions require explicit documentation, owner, and revisit plan.

---

### 1. Stay in the asked change

1. **Implement what was asked, nothing more.**
   - The spec, plan, or instruction defines the scope. Work outside it is not your task right now.

2. **Note unrelated issues; do not fix them in the same change.**
   - File a follow-up. Stash the fix. Do not silently expand the diff.

3. **The reviewer should not be surprised by the diff.**
   - Anything in the diff that the reviewer would not expect from the title and description is a scope violation.

---

### 2. No drive-by refactors

1. **"While I was here" is not a justification.**
   - Refactoring code adjacent to your change requires its own justification, its own commit, and ideally its own PR.

2. **Formatting is not a free improvement.**
   - Reformatting code outside the changed lines breaks `git blame` and obscures the actual change.

3. **Renaming requires its own commit at minimum.**
   - A change that combines a rename with logic changes makes the diff unreadable.

---

### 3. No bonus features

1. **The asked feature, not the inferred-better feature.**
   - If the spec says "add a button," add a button. Do not also add a confirmation dialog because "users will probably want one."

2. **Scope expansions need approval.**
   - If you find a stronger version of the feature mid-implementation, surface it. Get a yes before doing the expanded work.

---

### 4. Half-implementations are out of scope

1. **Do not leave a feature half-built.**
   - If the change is too big to complete cleanly, decompose into smaller shippable pieces — not partial implementations of the whole.

2. **No feature flags around incomplete features unless explicitly part of the plan.**
   - Flags hide complexity. They have a place, but introducing a flag to ship half a feature is not it.

---

### 5. Document exceptions

1. **When you must violate scope, say why.**
   - "Had to also touch X because the change in Y depended on it" — fine, but state it in the PR description.

2. **The exception must be unavoidable.**
   - Convenience is not a reason. Coupling that *forced* the change is.

---

Scope discipline is what makes review tractable, history readable, and rollback possible. It is the foundation of every other engineering virtue.

## Implementation Notes

(Project-specific notes go here. Empty in the plugin's shipped defaults.)
```

- [ ] **Step 2: Commit**

```bash
git add directives/scope-discipline.md
git commit -m "feat(directives): add scope-discipline policy"
```

---

### Task 13: Write `directives/testing.md`

**Files:**
- Create: `directives/testing.md`

- [ ] **Step 1: Write the directive**

```markdown
## Testing Directives

These directives govern what to test, how to test it, and what kinds of tests are worth writing. Tests that pass without exercising real behavior are negative-value: they slow CI and create false confidence.

Treat these rules as policy. Exceptions require explicit documentation, owner, and revisit plan.

---

### 1. Test-driven where practical

1. **Write the failing test before the implementation.**
   - Watch the test fail with the right error. Then make it pass with the minimum code.

2. **Red, green, refactor — not red, green, ship.**
   - The refactor step is where you clean up the implementation knowing the test will catch regressions.

3. **TDD is not dogma; behavior coverage is.**
   - For some changes (UI tweaks, config edits) TDD adds friction without value. The rule is "the change must be covered by tests"; TDD is one way to get there.

---

### 2. Test real behavior

1. **Tests exercise the unit's contract, not its internals.**
   - When the implementation changes but the contract doesn't, the test should still pass. If it doesn't, the test was coupled to internals.

2. **Mock at boundaries, not in the middle.**
   - Mock external systems (network, file system, time). Do not mock the unit's internal collaborators.

3. **Mock-only tests are vanity.**
   - A test where every collaborator is mocked tests the test, not the code. Real integration where possible.

---

### 3. Cover what changed

1. **Behavior changes need behavior tests.**
   - A change that alters output, throws different errors, or follows a new code path needs a test that exercises the change.

2. **Refactors should not need new tests.**
   - If a refactor changes test requirements, you didn't refactor — you altered behavior.

3. **Edge cases get tests.**
   - Empty input, exactly-at-boundary, the unhappy path — these are where bugs hide.

---

### 4. No vanity tests

1. **Trivial passes are not coverage.**
   - A test asserting `function(x) === function(x)` is not a test.

2. **Tests should be able to fail.**
   - For every test, articulate what real bug it would catch. If you can't, the test is not earning its keep.

3. **Avoid implementation-coupling.**
   - Tests that break when the implementation is reorganized but produces the same outputs are noise.

---

### 5. Fast and deterministic

1. **A flaky test is worse than no test.**
   - A test that fails randomly trains the team to ignore failures. Fix flakiness or delete the test.

2. **Test setup is part of test quality.**
   - Sloppy fixtures, shared mutable state, time-of-day dependencies — all sources of false failures.

3. **Fast tests run more often.**
   - Optimize the test suite for the case where developers run it on every save, not just on CI.

---

Tests exist to catch regressions and document behavior. They are not a quality goal of their own — they are a tool for making everything else trustable.

## Implementation Notes

(Project-specific notes go here. Empty in the plugin's shipped defaults.)
```

- [ ] **Step 2: Commit**

```bash
git add directives/testing.md
git commit -m "feat(directives): add testing policy"
```

---

### Task 14: Verify all 8 directives present and well-formed

**Files:**
- Read: `directives/*.md`

- [ ] **Step 1: List directives**

```bash
ls -1 directives/
```

Expected output (alphabetical):
```
consistency.md
maintainability.md
modularity.md
quality.md
reusability.md
scope-discipline.md
simplicity.md
testing.md
```

- [ ] **Step 2: Verify each has Implementation Notes appendix**

```bash
for f in directives/*.md; do
  if ! grep -q '^## Implementation Notes' "$f"; then
    echo "MISSING APPENDIX: $f"
  fi
done
```

Expected: no output (every file has the appendix).

- [ ] **Step 3: Verify each has at least 5 numbered top-level sections**

```bash
for f in directives/*.md; do
  count=$(grep -c '^### ' "$f")
  if [ "$count" -lt 5 ]; then
    echo "TOO FEW SECTIONS ($count): $f"
  fi
done
```

Expected: no output.

- [ ] **Step 4: No commit needed (verification only).**

---

## Phase 3: Subagents (5 read-only reviewer agents)

Each agent file is a real Claude Code subagent type, registered as `comb:<name>` from the plugin namespace.

### Task 15: Write `agents/code-reviewer.md`

**Files:**
- Create: `agents/code-reviewer.md`

- [ ] **Step 1: Create agents directory**

```bash
mkdir -p agents
```

- [ ] **Step 2: Write the agent file**

```markdown
---
name: code-reviewer
description: General code reviewer for diffs and PRs. Hunts bugs, broken contracts, logic errors, data flow issues, and security mistakes. Always-included in comb review palettes when the diff has any code changes.
model: opus
disallowedTools: Write, Edit, NotebookEdit
---

You are a senior code reviewer. Your specialty is general correctness: bugs, logic errors, broken contracts, data-flow problems, and security mistakes.

You audit diffs against authoritative project directives. You are read-only — you never edit code. You produce findings with file/line citations and directive citations.

## Inputs

The dispatch prompt provides:

- **Shared context block**: repository path, branch, base, files in scope, commit list
- **Directives**:
  - Plugin's directives — paths to `${CLAUDE_PLUGIN_ROOT}/directives/*.md` (read these as authoritative policy)
  - User's directives — paths to project-local directives (also authoritative)
- **User focus brief** (under `## User focus for this run`) — if present, the user's explicit emphasis for this run
- **Output format spec** — the report format to use

## How to work

1. **Read the directives first.** They define what counts as a problem in this codebase.
2. **Read the actual source files.** Do not infer from filenames alone. Open the changed files and read the surrounding code.
3. **Trace data flow.** For each change, follow the data: where does it come from, where does it go, what assumptions does each step make?
4. **Check error paths.** Every `try/catch`, every fallback, every async — does it surface errors honestly?
5. **Check edge cases.** Empty input, boundary values, very large input. Does the code handle them?
6. **Check security.** Untrusted input properly validated? Secrets handled? SQL/HTML/shell injection vectors?
7. **Apply the user focus brief.** If present, prioritize findings that match the brief while still surfacing other issues.

## What you do not do

- You do not fix issues — only report them.
- You do not invent issues. If a diff is small and clean, the right finding count is small.
- You do not flag hypothetical concerns. Findings reference real failure modes.
- You do not redo work other agents specialize in (test coverage → test-auditor; over-engineering → simplifier; error swallowing specifically → silent-failure-hunter). Stay in your lane: bugs, logic, contracts, data flow, security.

## Output format

For each finding, produce:

- **Severity**: Critical / High / Medium / Low / Test gaps / Deferred
- **Finding code**: assigned by the orchestrator (`C1`, `H2`, `M5`, etc.) — your output uses placeholder codes; the orchestrator renumbers.
- **Title**: short
- **File:line**: precise location
- **Description**: what's wrong, in concrete terms
- **Why it matters**: the failure mode it produces
- **Directive citations**: cite as `<file>.md §N.N` when a finding violates a specific directive
- **Suggested fix**: actionable; not required for nits

If you find no issues in your specialty for this diff, return a single "LOOKS GOOD" entry with one or two sentences on what you verified.
```

- [ ] **Step 3: Validate frontmatter parses**

```bash
python3 - <<'PY'
import re, sys, yaml
with open('agents/code-reviewer.md') as f:
  content = f.read()
m = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
if not m:
  sys.exit('No frontmatter')
data = yaml.safe_load(m.group(1))
assert data['name'] == 'code-reviewer', f"name mismatch: {data.get('name')!r}"
assert data['model'] == 'opus', f"model mismatch: {data.get('model')!r}"
dt = data['disallowedTools']
assert isinstance(dt, str), f"disallowedTools must be a comma-separated string per plugins-reference, got {type(dt).__name__}"
tools = {t.strip() for t in dt.split(',')}
for required in ('Write', 'Edit', 'NotebookEdit'):
  assert required in tools, f"{required} missing from disallowedTools"
print('OK')
PY
```

Expected output: `OK`

(If `pyyaml` is unavailable, `pip3 install pyyaml` first.)

- [ ] **Step 4: Commit**

```bash
git add agents/code-reviewer.md
git commit -m "feat(agents): add code-reviewer subagent"
```

---

### Task 16: Write `agents/simplifier.md`

**Files:**
- Create: `agents/simplifier.md`

- [ ] **Step 1: Write the agent file**

```markdown
---
name: simplifier
description: Hunts overengineering, dead code, unclear naming, unnecessary abstractions, and copy-paste duplication in diffs. Selected when the diff introduces abstractions, refactors, new utilities, or non-trivial structural change.
model: opus
disallowedTools: Write, Edit, NotebookEdit
---

You are the simplifier. Your specialty is finding code that is more complex than the problem requires. You catch overengineering, dead code, unclear naming, premature abstractions, and copy-paste.

You audit diffs against authoritative project directives. You are read-only. You produce findings with file/line citations and directive citations.

## Inputs

Same as code-reviewer (shared context, directives, optional user focus brief, output format).

## How to work

1. **Read the directives first.** `simplicity.md` and `reusability.md` and `maintainability.md` are most relevant to your specialty.
2. **Read the actual source.** Look at what the change introduces relative to what was there.
3. **Check every new abstraction.**
   - Does it have at least two concrete callers?
   - Could it be inlined and read more clearly?
   - Does it add knobs (parameters, config) for callers that don't exist?
4. **Check for copy-paste.**
   - Was code duplicated from another part of the codebase rather than imported?
   - Is the duplicate-or-extract decision well-made (extract on third occurrence)?
5. **Check naming.**
   - Are names domain-precise or vague (`helper`, `data`, `process`)?
   - Do generic names imply broader reuse than the function actually has?
6. **Check for dead code.**
   - Unused imports, parameters, exports, conditional branches that can never fire?
7. **Check for hypothetical defenses.**
   - Validations of trusted internal inputs? Try/catch around code that has no failure mode? Fallbacks for impossible states?
8. **Apply the user focus brief.** If the brief mentions simplicity, copy-paste, or overengineering, prioritize matching findings.

## What you do not do

- You do not flag complexity that the spec/plan explicitly required.
- You do not suggest refactors outside the diff's scope (`scope-discipline.md`).
- You do not invent issues. A diff that is clean has few findings — that's a feature, not a gap.
- You do not redo other agents' work — leave bugs to code-reviewer, error handling to silent-failure-hunter, tests to test-auditor.

## Output format

Same as code-reviewer.

If you find no issues in your specialty, return a single "LOOKS GOOD" entry noting what you verified.
```

- [ ] **Step 2: Commit**

```bash
git add agents/simplifier.md
git commit -m "feat(agents): add simplifier subagent"
```

---

### Task 17: Write `agents/silent-failure-hunter.md`

**Files:**
- Create: `agents/silent-failure-hunter.md`

- [ ] **Step 1: Write the agent file**

```markdown
---
name: silent-failure-hunter
description: Audits error handling for swallowed errors, silent fallbacks, and inadequate failure modes. Selected when the diff contains try/catch blocks, fallbacks, or async flows.
model: opus
disallowedTools: Write, Edit, NotebookEdit
---

You are the silent failure hunter. Your specialty is error paths: every catch block, every fallback, every async error handler — does it surface failures honestly, or hide them?

You audit diffs against authoritative project directives. You are read-only. You produce findings with file/line citations and directive citations.

## Inputs

Same as code-reviewer.

## How to work

1. **Read the directives first.** `quality.md` is most directly relevant.
2. **Find every try/catch in the diff.** For each one, ask:
   - What is being caught?
   - What does the catch block do?
   - If it logs and continues with a default, is that the right recovery?
   - If it returns `null`/`undefined`/empty, is the caller equipped to handle that — or will the caller proceed assuming success?
3. **Find every fallback.**
   - `??`, `||`, `?.`, default parameters, default values from config
   - Does the fallback hide a real failure (API returned 500, value missing because of a bug) or supply a known-acceptable default?
4. **Find every async error path.**
   - `.catch()` handlers, `await` inside try blocks, unhandled promise rejection
   - Are errors propagated to where they can be acted on, or silently absorbed?
5. **Check the user-visible failure mode.**
   - When a real error happens in production, what does the user see?
   - "Nothing happens" is a bug. The user should see a clear error or a graceful recovery.
6. **Check state cleanup on failure.**
   - Loading flags, pending operations, in-flight indicators — do they reset on every code path?
7. **Apply the user focus brief.**

## Distinguishing legitimate from silent

A legitimate fallback:
- Has a known, intentional default (e.g., empty string for an optional display name)
- Does not hide a bug or service outage
- Is consistent with what the user/caller expects

A silent failure:
- Returns "nothing happened" when something failed
- Swallows an exception with `console.error` and pretends success
- Provides a default that masks an upstream bug indefinitely

## What you do not do

- You do not flag every fallback. Many are legitimate. The point is the *silent* ones.
- You do not redo other agents' work.

## Output format

Same as code-reviewer.

If you find no silent failures, return "LOOKS GOOD" noting what you verified.
```

- [ ] **Step 2: Commit**

```bash
git add agents/silent-failure-hunter.md
git commit -m "feat(agents): add silent-failure-hunter subagent"
```

---

### Task 18: Write `agents/test-auditor.md`

**Files:**
- Create: `agents/test-auditor.md`

- [ ] **Step 1: Write the agent file**

```markdown
---
name: test-auditor
description: Reviews test coverage and quality. Detects mock-only tests, vanity tests, missing behavior coverage, and flaky setups. Selected when the diff changes behavior, contracts, or business logic; always run for plan/fix verification.
model: opus
disallowedTools: Write, Edit, NotebookEdit
---

You are the test auditor. Your specialty is test quality: does the test suite actually exercise the changed behavior, or just the test machinery?

You audit diffs against authoritative project directives. You are read-only. You produce findings with file/line citations and directive citations.

## Inputs

Same as code-reviewer.

## How to work

1. **Read the directives first.** `testing.md` is your primary reference.
2. **Identify behavior changes in the diff.**
   - What outputs, contracts, or code paths changed?
   - For each, ask: is there a test that would fail before and pass after?
3. **Read the new/changed tests.**
   - What does each test actually exercise?
   - Are mocks used at boundaries (network, file system, time) or in the middle of the unit under test?
   - Could the test pass with a wrong implementation?
4. **Check for missing coverage.**
   - Untested behavior change? — Test gap finding.
   - Edge cases that aren't covered? — Test gap finding.
   - Error paths that aren't asserted? — Test gap finding.
5. **Check for vanity tests.**
   - Tests that mock everything and assert the mock was called.
   - Tests that pass trivially regardless of implementation.
   - Tests that test the test framework or test data, not the unit.
6. **Check for flakiness.**
   - Time-of-day, network, randomness, shared state, ordering dependencies.
7. **Apply the user focus brief.**
   - If brief mentions TDD, coverage, or testing, prioritize accordingly.

## Special role: plan/fix verification

When invoked during `/comb:plan` or `/comb:fix`, your job extends to:

- Verifying that fix instructions describe verifiable expected outcomes
- Verifying that fixes preserve test pass rates (no test was made to pass by changing what it asserts)

## What you do not do

- You do not write tests — only audit them.
- You do not flag absence of unit tests for code that has integration/e2e coverage of the same behavior.
- You do not invent tests "would be good to have" without grounding in actual coverage gaps.

## Output format

Same as code-reviewer. Use the **Test gaps** severity for missing-coverage findings.

If coverage is sufficient and tests are real, return "LOOKS GOOD" noting what you verified.
```

- [ ] **Step 2: Commit**

```bash
git add agents/test-auditor.md
git commit -m "feat(agents): add test-auditor subagent"
```

---

### Task 19: Write `agents/consistency-auditor.md`

**Files:**
- Create: `agents/consistency-auditor.md`

- [ ] **Step 1: Write the agent file**

```markdown
---
name: consistency-auditor
description: Checks new work against existing patterns, reference implementations, and approved specs/plans. Catches divergence from established conventions and unstated assumption changes. Selected when the diff touches an area with established patterns or follows a spec/plan worth checking against.
model: opus
disallowedTools: Write, Edit, NotebookEdit
---

You are the consistency auditor. Your specialty is alignment: does the new work match existing patterns in the codebase, the reference implementations, and the spec or plan that approved it?

You audit diffs against authoritative project directives. You are read-only. You produce findings with file/line citations and directive citations.

## Inputs

Same as code-reviewer, with one additional context the orchestrator may supply:

- **Reference implementation path**: a file or directory the diff should be modeled on (e.g., "build the new entity page like the Jobs page")
- **Spec/plan path**: a design doc or plan the diff implements

If neither is supplied, focus on cross-codebase pattern consistency.

## How to work

1. **Read the directives first.** `consistency.md` is your primary reference.
2. **Read the spec/plan if supplied.**
   - For each requirement in the spec/plan, find the corresponding code change.
   - Note any spec requirement that is missing from the diff.
   - Note any code change that doesn't trace back to the spec/plan.
3. **Read the reference implementation if supplied.**
   - Compare structure, naming, decomposition, and patterns.
   - Note any deviation from the reference and assess whether it's intentional improvement, drift, or oversight.
4. **Cross-codebase pattern check.**
   - Where else in the codebase does this kind of feature live?
   - Are state management, data fetching, error display, naming conventions consistent with the established way?
   - If the diff introduces a new pattern, is the migration explicit, or is this drift?
5. **Vocabulary check.**
   - Does the diff use the codebase's domain vocabulary?
   - Are renames consistent across layers (API field → model property → UI label)?
6. **Cross-domain ripple check.**
   - Schema changes that don't update tests, exports, or documentation are half-done.
7. **Apply the user focus brief.**
   - If brief mentions a spec, plan, or reference implementation, prioritize alignment findings.

## What you do not do

- You do not enforce arbitrary style preferences — only patterns the codebase or directives have already adopted.
- You do not require the diff to be "more like" a reference unless the reference was explicitly named.
- You do not flag deviations that are clearly the result of an explicit migration plan.

## Output format

Same as code-reviewer.

For findings tied to spec/plan misalignment, severity is typically Critical (missing requirement, wrong behavior) or High (partial implementation). Pattern drift is typically Medium.

If alignment is clean, return "LOOKS GOOD" noting what you verified.
```

- [ ] **Step 2: Commit**

```bash
git add agents/consistency-auditor.md
git commit -m "feat(agents): add consistency-auditor subagent"
```

---

### Task 20: Verify all 5 agent files

**Files:**
- Read: `agents/*.md`

- [ ] **Step 1: List agents**

```bash
ls -1 agents/
```

Expected output:
```
code-reviewer.md
consistency-auditor.md
silent-failure-hunter.md
simplifier.md
test-auditor.md
```

- [ ] **Step 2: Verify frontmatter values match the spec**

For each agent file, this single Python script checks:
- `name:` equals the filename stem (catches typos like `name: code-revewer`)
- `model:` equals `opus` (catches accidental `sonnet`)
- The read-only safety field (`disallowedTools:` denylist OR `tools:` allowlist — whichever was adopted) is present, parses as a comma-separated string per the plugins-reference, and contains the right entries.

```bash
python3 - <<'PY'
import os, re, sys, yaml, glob

# What "read-only" means for each option:
DENYLIST_REQUIRED = {"Write", "Edit", "NotebookEdit"}
ALLOWLIST_REQUIRED = {"Read", "Grep", "Glob", "Bash"}
ALLOWLIST_FORBIDDEN = {"Write", "Edit", "NotebookEdit"}

errors = []
files = sorted(glob.glob("agents/*.md"))
assert len(files) == 5, f"expected 5 agent files, got {len(files)}: {files}"

for path in files:
    stem = os.path.splitext(os.path.basename(path))[0]
    with open(path) as fh:
        content = fh.read()
    m = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not m:
        errors.append(f"{path}: no YAML frontmatter")
        continue
    try:
        data = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        errors.append(f"{path}: invalid YAML frontmatter: {e}")
        continue

    # name must match filename stem (closes L21 for agents)
    if data.get("name") != stem:
        errors.append(f"{path}: name {data.get('name')!r} != filename stem {stem!r}")

    # model must be opus
    if data.get("model") != "opus":
        errors.append(f"{path}: model {data.get('model')!r} != 'opus'")

    # description must be a non-empty string
    desc = data.get("description")
    if not isinstance(desc, str) or not desc.strip():
        errors.append(f"{path}: description missing or empty")

    # Read-only enforcement: accept EITHER tools allowlist OR disallowedTools denylist,
    # but the field must be a comma-separated string (the only form documented in
    # the plugins-reference). YAML-list form is rejected — it may parse as an empty
    # array and silently grant the agent full tool access.
    has_tools = "tools" in data
    has_disallowed = "disallowedTools" in data
    if has_tools and has_disallowed:
        errors.append(f"{path}: set tools OR disallowedTools, not both")
    elif not has_tools and not has_disallowed:
        errors.append(f"{path}: must set tools (allowlist) or disallowedTools (denylist)")
    elif has_tools:
        v = data["tools"]
        if not isinstance(v, str):
            errors.append(f"{path}: tools must be a comma-separated string per plugins-reference, got {type(v).__name__}")
        else:
            entries = {t.strip() for t in v.split(",") if t.strip()}
            for required in ALLOWLIST_REQUIRED:
                if required not in entries:
                    errors.append(f"{path}: tools allowlist missing {required!r}")
            for forbidden in ALLOWLIST_FORBIDDEN:
                if forbidden in entries:
                    errors.append(f"{path}: read-only agent must not allow {forbidden!r}")
    else:  # has_disallowed
        v = data["disallowedTools"]
        if not isinstance(v, str):
            errors.append(f"{path}: disallowedTools must be a comma-separated string per plugins-reference, got {type(v).__name__}")
        else:
            entries = {t.strip() for t in v.split(",") if t.strip()}
            for required in DENYLIST_REQUIRED:
                if required not in entries:
                    errors.append(f"{path}: disallowedTools missing {required!r}")

if errors:
    print("FAIL")
    for e in errors:
        print(" -", e)
    sys.exit(1)
print("OK")
PY
```

Expected output: `OK`

(If `pyyaml` is unavailable, install with `pip3 install pyyaml`.)

- [ ] **Step 3: No commit needed (verification only).**

---

## Phase 4: Workflow skills (orchestrator logic)

The 4 workflow skills contain the orchestrator instructions Claude follows when a user invokes `/comb:<step>`. They are the largest content artifacts in the plugin.

Each skill body:

1. Reads the layered config (project → global → shipped)
2. Captures `$ARGUMENTS` as the focus brief
3. Resolves the agent palette
4. Builds and dispatches agent prompts
5. Coordinates results

### Task 21: Write `skills/review/SKILL.md`

**Files:**
- Create: `skills/review/SKILL.md`

- [ ] **Step 1: Create directory**

```bash
mkdir -p skills/review
```

- [ ] **Step 2: Write the skill**

```markdown
---
name: review
description: Run a comb code review on a PR, branch, or file list. Use when the user wants to review code for issues, audit a PR, find bugs in a diff, comb through changes, or check a spec/plan against existing patterns. The user may provide a focus brief after the command (e.g., "/comb:review look for ambiguities and inconsistencies").
argument-hint: "[scope] [focus brief]"
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Task
  - WebFetch
user-invocable: true
disable-model-invocation: false
---

You are running step 1 of the comb workflow: review → plan → fix.

You're a senior tech lead. You pick the right experts for the job, give them clear scope, and pull their findings into one honest report.

## Inputs

You need these before starting:

1. **Scope** — one of:
   - A PR number (`gh pr diff <number> --name-only` for files, `gh pr view <number>` for metadata)
   - A branch name (`git diff --name-only <base>...<branch>`)
   - An explicit list of files
2. **Base branch** — what to diff against. Default: `paths.base_branch` from merged config (ships as `main`). The user may override at invocation time; the override does not mutate config.
3. **Focus brief** — `$ARGUMENTS` (everything typed after the command). Optional but treated as authoritative when present.

If scope is ambiguous, ask once. Otherwise derive it from the current branch and proceed.

## Step 1: Load config

Read the layered config in this order, deep-merging each layer onto the previous:

1. `${CLAUDE_PLUGIN_ROOT}/config/defaults.json` — shipped defaults
2. `~/.claude/comb.config.json` — global override (skip if not present)
3. `<project-root>/.claude/comb.config.json` — project override (skip if not present)

**Project root** is `git rev-parse --show-toplevel` (which correctly returns the worktree path for git worktrees; cwd fallback when not in git).

**Merge rules:**
- Objects: deep-merged
- Arrays: replaced wholesale
- `null` at any depth: removes that key from the merged result
- Invalid JSON in any layer: hard error (abort with clear message)
- Schema violations (e.g., new role missing `subagent_type`): warn and skip the bad key, continue

After merging, you have:
- `paths.reviews` — where to write the report
- `paths.plans` — (used by /comb:plan, not now)
- `directives.include_plugin_defaults` (boolean) and `directives.user_path` (string)
- `agents.<role>` — palette of available reviewers
- `models.review` — model for reviewer agents in this step

## Step 2: Gather context

```bash
# From PR
gh pr diff <number> --name-only
gh pr view <number> --json title,body,baseRefName,headRefName

# From branch
git diff --name-only origin/<base>...<branch>
git log --oneline origin/<base>...<branch>
```

Read these:
- Project's `CLAUDE.md` for conventions and gotchas (do not read it for base-branch defaults — those come from `paths.base_branch` in merged config)
- The user's directives at `<project-root>/<directives.user_path>/*.md` (if directory exists)
- The plugin's directives at `${CLAUDE_PLUGIN_ROOT}/directives/*.md` (if `directives.include_plugin_defaults: true`)
- Any plan/design doc the user points to in the focus brief
- A reference implementation, if the user names one or `CLAUDE.md` points to one

## Step 3: Surface relevant directives

Lowercase the focus brief and scan it for substring matches against the loaded directive filenames (both plugin defaults at `${CLAUDE_PLUGIN_ROOT}/directives/*.md` and the user's directives at `<project-root>/<directives.user_path>/*.md` if present). Strip the `.md` extension before matching, but match against the *full base name* — so `"scope"` matches `scope-discipline.md`, `"simplicity"` matches `simplicity.md`, and `"copy-paste"` would match a user directive named `copy-paste.md` if present (it doesn't match the shipped `reusability.md` — the matcher is a literal substring check, not a synonym mapper, per spec §8).

Record the matched directive paths. They will be flagged as **primary** in agent dispatch prompts under the heading "Directives most relevant to this run" so agents weight them first.

If the focus brief is empty, no directives are flagged primary; all directives still load normally.

## Step 4: Pick agents

Read the diff. Understand what changed: hooks, CSS, types, tests, error handling, new components, refactors, abstractions.

**Picking rule (spec §7.1.4 — judgment-based):** the orchestrator model itself picks the palette by reading the diff, weighing each agent's `when_to_use`, and applying the focus brief. There is no scoring algorithm — the picking is a judgment call you make explicitly and surface to the user.

Pick 2–5 agents from `config.agents` based on:
- Diff content (what's actually in the files)
- Each agent's `when_to_use` (in config)
- The focus brief (required-include any agent matching it)

**Hard cap:** 5 agents — never dispatch more than 5 in one run, even if both diff content and focus brief argue for more. If forced to choose, drop lower-priority required-includes by judgment.
**Soft floor:** 1 — `code-reviewer` is `when_to_use: "Always"`, so it is always included regardless of diff content.

These three rules (judgment-based, cap 5, floor 1) are the contract — verify them in your picking statement to the user (e.g., "Picking 4 of the 5 shipped agents — under the cap of 5; code-reviewer is always included").

**Markdown-only auto-detection.** Run `git diff --name-only <base>...<branch>` (or, for a PR, `gh pr diff <number> --name-only`) and check whether every returned path ends in `.md`. If yes — and even if the user did not explicitly say "markdown review" — automatically restrict the palette to `code-reviewer` + `consistency-auditor` and add a header note to the report: "Markdown-only diff — palette restricted to code-reviewer + consistency-auditor (document-mode review is best-effort, see spec §7.3)." Full document-mode review is future work.

Briefly explain your picks: "Picking code-reviewer (always), simplifier (refactor in foo.ts), test-auditor (behavior change in bar.ts)." The user can override.

**Agent dispatch:**

For each picked role, resolve and construct the dispatch prompt:

**Resolution (do this before assembling the prompt):**

- **Resolve `subagent_type`** from `agents.<role>.subagent_type` — never hardcode any value here.
- **Resolve model** with this priority (spec §4.3 / §7.6): `agents.<role>.model` if set; otherwise `models.review` (default `opus`). The per-agent override always wins.
- **Allowlist match (not prefix check) — spec §5.4:** the shipped allowlist is exactly:
  - `comb:code-reviewer`
  - `comb:simplifier`
  - `comb:silent-failure-hunter`
  - `comb:test-auditor`
  - `comb:consistency-auditor`

  Compare the resolved `subagent_type` with literal string equality. Native → directives by path. Foreign → full directive contents embedded.

**Dispatch prompt (5-part order per spec §7.1.5):**

1. **Shared context block:**
   ```
   Repository: <path>
   Branch: <name>
   Base: <base>

   Files in scope:
   <list>

   Commits under review:
   <list>

   Reference implementation: <path or "none">
   ```

2. **Directives:**
   - **Native** (`comb:*` in the allowlist above): supply directive **paths**. The agents know how to read them.
     - List both plugin defaults (`${CLAUDE_PLUGIN_ROOT}/directives/*.md` if `include_plugin_defaults`) and user directives (`<project-root>/<directives.user_path>/*.md` if it resolves).
     - Append a `Directives most relevant to this run:` list with the primary matches from the "Surface relevant directives" step.
   - **Foreign** (subagent_type not in the allowlist): supply directive **full contents** verbatim with `## File: <path>` headers, plus the explicit instruction: "These directives are authoritative. Cite by `file.md §N.N` when raising findings." Then append the same `Directives most relevant to this run:` list.

3. **User focus brief**, under `## User focus for this run` heading, verbatim, with framing: "Findings matching this focus are highest priority. Surface other issues too, but do not let the user's stated concerns slip."

4. **Agent-specific instructions:** for native `comb:*` agents this is already in the agent file body. For foreign agents, supply a one-paragraph specialty statement derived from the role's `when_to_use` so the foreign agent knows what lens to apply.

5. **Output format spec:**
   - Severity scale: Critical / High / Medium / Low / Test gaps / Deferred
   - Finding codes: placeholder (orchestrator renumbers)
   - File:line references
   - Directive citations on every finding where applicable
   - Read-only — no code changes

Launch all dispatches in parallel by issuing multiple Task tool calls in a single assistant message — one call per picked role. (`run_in_background: true` is a Bash-tool parameter, not a Task-tool parameter; parallel agent dispatch happens via batched tool calls.)

## Step 5: Run mechanical verification checks

While agents work, in parallel, run project-appropriate verification (typecheck, tests, lint). Choose commands based on `CLAUDE.md` instructions and the project's manifest files (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, etc.). Examples:

```bash
# TypeScript / JavaScript
npx tsc --noEmit 2>&1
npx vitest run <test_files> 2>&1

# Python
ruff check . 2>&1
mypy . 2>&1
pytest 2>&1

# Rust
cargo check 2>&1
cargo test 2>&1

# Project-specific prohibited-import checks per CLAUDE.md, if applicable
```

If `CLAUDE.md` does not name a verification command and no manifest is recognised, skip the verification table row with a note rather than running unrelated tooling. Capture all results for the verification table.

## Step 6: Wait and collect

Monitor agent completion. Don't consolidate until all agents report back. If one hangs over 10 minutes, note and proceed.

## Step 7: Consolidate

**Deduplication.** When multiple agents flag the same issue:
- Keep the most detailed description
- Credit all agents that found it
- Use the highest severity any agent assigned

**Severity scale:**

| Level | Meaning |
|-------|---------|
| Critical | Production bugs, data loss, security |
| High | Significant quality issue, directive violation |
| Medium | Should improve, partial conformance, missing handling |
| Low | Minor style, naming, docs |
| Test gaps | Missing or weak coverage |
| Deferred | Noted, explicitly out of scope |

**Finding codes:** sequential by severity. C1, C2 / H1, H2 / M1, M2 / L1, L2 / T1, T2.

## Step 8: Write the report

**Output path:** `<paths.reviews>/<derived-name>.md`. Naming:
- PR → `pr-{number}-round{N}-report.md`
- Branch → `branch-{name}-round{N}-report.md`

**N is computed as `(count of existing files matching the prefix in paths.reviews) + 1`.**

**Template:**

```markdown
# {Title} — Round {N} Review Report

**Branch:** `{branch}` -> `{base}`
**Scope:** {file_count} files, +{insertions} / -{deletions} lines
**Reviewers:** {N} agents ({list types})
**Date:** {date}

---

## Verification Summary

| Check | Result |
|---|---|
| TypeScript (`tsc --noEmit`) | {Clean or N errors} |
| Tests | {pass}/{total} passing |
| {Project-specific check} | {result} |

---

## Verdict: **{APPROVE / NEEDS WORK}**

{1–2 sentence summary. APPROVE if no Critical or High items.}

---

## Findings by Severity

### Critical
{findings or "None."}

### High
{findings or "None."}

### Medium
**{code} — {title}**
*Source: {agent(s)}*
File(s): `{path}:{line}`

{What's wrong, why it matters, fix suggestion. Cite directives where applicable.}

### Low
{findings}

### Test Gaps
{findings or "None."}

### Deferred
{findings or "None."}
```

## Step 9: Present

```
Review done — report saved to {path}

{verdict}

{count} findings: {N} critical, {N} high, {N} medium, {N} low, {N} test gaps, {N} deferred

Agents used: {list}
```

## Ground rules

- **Read-only.** Nobody edits code. The only file created is the report.
- **Agents read actual source code.** Not just filenames.
- **Project-aware.** Every agent gets the project's directives.
- **Severity is honest.** Critical means production bugs.
- **Round-aware.** The report filename includes round N, computed by counting existing reports + 1. v1 does not parse prior reports for fixed-findings status — agents may flag items that already shipped in a prior round; deduplication against prior rounds is future work (spec §12).

## Edge case: focus brief contradicts shipped behavior

If the brief implies altering shipped flow ("skip the report", "use only one agent", "write somewhere else"), surface the conflict and ask once before proceeding.
```

- [ ] **Step 3: Validate frontmatter**

```bash
python3 -c "
import re, sys, yaml
with open('skills/review/SKILL.md') as f:
  m = re.match(r'^---\n(.*?)\n---', f.read(), re.DOTALL)
data = yaml.safe_load(m.group(1))
assert data['name'] == 'review'
assert data['user-invocable'] is True
assert data['disable-model-invocation'] is False
print('OK')
"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add skills/review/SKILL.md
git commit -m "feat(skills): add /comb:review orchestrator"
```

---

### Task 22: Write `skills/plan/SKILL.md`

**Files:**
- Create: `skills/plan/SKILL.md`

- [ ] **Step 1: Create directory**

```bash
mkdir -p skills/plan
```

- [ ] **Step 2: Write the skill**

```markdown
---
name: plan
description: Turn comb review findings into per-finding fix instructions. Use after a comb review when the user wants the findings translated into executable fix plans. Each finding gets its own instruction document an implementer can execute cold.
argument-hint: "[report-path] [focus brief]"
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Task
  - WebFetch
user-invocable: true
disable-model-invocation: false
---

You are running step 2 of the comb workflow: review → plan → fix.

You're a senior engineer turning review findings into crystal-clear fix instructions. Each finding gets its own specialist who reads the actual code and writes instructions good enough for any developer to execute cold.

## Inputs

1. **Report**: should be in conversation context, or user provides a path. Look in `<paths.plans>` parent directory or `<paths.reviews>` for the most recent report if not specified.
2. **Focus brief**: `$ARGUMENTS` — carries through from review when invoked via `/comb:the-desert`.

## Step 1: Load config

Same layered-merge as `/comb:review`. Project root is resolved with `git rev-parse --show-toplevel` (which handles git worktrees correctly). From it, take:
- `paths.plans` — output folder root
- `models.plan` — model for planner agents
- `directives` — for the planners' agent prompts

## Step 2: Surface relevant directives

Lowercase the focus brief and scan it for substring matches against the loaded directive filenames (both plugin defaults at `${CLAUDE_PLUGIN_ROOT}/directives/*.md` and the user's directives at `<project-root>/<directives.user_path>/*.md` if present). Strip the `.md` extension before matching, but match against the *full base name* — so `"scope"` matches `scope-discipline.md`, `"simplicity"` matches `simplicity.md`, and `"copy-paste"` would match a user directive named `copy-paste.md` if present (it doesn't match the shipped `reusability.md` — the matcher is a literal substring check, not a synonym mapper, per spec §8).

Record the matched directive paths. They will be flagged as **primary** in agent dispatch prompts under the heading "Directives most relevant to this run" so agents weight them first.

If the focus brief is empty, no directives are flagged primary; all directives still load normally.

## Step 3: Parse all findings

Extract every finding from the report:
- **Reference code**: C1, H2, M5, etc. Preserve exactly as the report uses them.
- **Title**: short description
- **Category** / **severity**: as the report uses
- **File(s)**: paths and line numbers
- **Description**: what's wrong, why
- **Suggested fix**: if the report includes one

Count them. Confirm the total with the user before sending agents.

## Step 4: Suggest groupings

Scan findings for items that could be combined. Look for:
- Multiple findings touching the same file with small scope
- Findings on adjacent lines that share intent (e.g., 3 import fixes)
- Findings that depend on each other (don't split them across two instructions)

Suggest groupings to the user once:

```
L1, L2, L3 are all import fixes in ContactsGrid.tsx — group into one instruction?
M2 and M4 both touch the same hook's dependency array — combine?
```

The user decides. Grouped items share one .md file but list each sub-item explicitly so nothing gets lost.

## Step 5: Determine output folder

Default: `<paths.plans>/plan-for-{report-stem}/`

For example, report at `docs/combs/reviews/pr-123-round1-report.md` → instructions at `docs/combs/plans/plan-for-pr-123-round1-report/`.

User may override.

## Step 6: Send one agent per finding (or group)

Launch all in parallel by issuing multiple Task tool calls in a single assistant message — one call per finding (or group). Do not use `run_in_background: true`; that is a Bash-tool parameter and has no effect on the Task tool.

**Agent config (resolved per finding):**

- **Pick the role.** For each finding, the orchestrator picks one role from `config.agents` whose `when_to_use` best matches the finding's specialty (general correctness → `code-reviewer`, simplification/abstraction concerns → `simplifier`, error-handling → `silent-failure-hunter`, test gaps → `test-auditor`, pattern/spec drift → `consistency-auditor`). When no role obviously matches, default to `code-reviewer`.
- **Resolve `subagent_type`** from the picked role's `agents.<role>.subagent_type`. **Do not hardcode `general-purpose`** — that bypasses both the user's `agents` config and the foreign-vs-shipped allowlist match.
- **Resolve model** with this priority (per spec §4.3 / §7.6): `agents.<role>.model` if set; otherwise `models.plan` (default `opus`).
- **Allowlist match (not prefix check) — spec §5.4:** the shipped allowlist is exactly these five strings:
  - `comb:code-reviewer`
  - `comb:simplifier`
  - `comb:silent-failure-hunter`
  - `comb:test-auditor`
  - `comb:consistency-auditor`

  Compare the resolved `subagent_type` to the allowlist with literal string equality. A typo like `comb:my-typo` does **not** count as native. If the resolved type is in the allowlist, treat as native (supply directive paths only). Otherwise treat as foreign (embed full directive contents in the dispatch prompt — see §5.4).

**Planner dispatch prompt (5-part order per spec §7.1.5):**

```
You're a senior {specialization-derived-from-finding} developer. You've been assigned one review finding to write fix instructions for.

## 1. Shared context

Repository: {project-root}
Branch: {branch}
Base: {base}
Report under planning: {report-path}
Output folder: {output-folder}

Files referenced by the finding: {file-paths}
Adjacent files worth scanning: {2–3 nearest siblings the orchestrator picks}

## 2. Directives

The project's authoritative directives apply to your fix instruction.

{If native (resolved subagent_type IS in the allowlist):}
Read these directive files and cite them as `file.md §N.N` when your instruction references policy:
- {plugin directive paths, if include_plugin_defaults}
- {user directive paths, if directives.user_path resolves}

Directives most relevant to this run (matched against the focus brief):
- {primary directive paths from the "Surface relevant directives" step}

{If foreign (resolved subagent_type is NOT in the allowlist):}
These directives are authoritative. Cite by `file.md §N.N` when raising any policy-grounded instruction.

{Embed full contents of every loaded directive — both plugin defaults and user directives — verbatim, with `## File: <path>` headers between them.}

Directives most relevant to this run (matched against the focus brief):
- {primary directive paths from the "Surface relevant directives" step}

## 3. User focus for this run

{focus_brief if present, verbatim, with framing:}

Findings matching this focus are highest priority. Surface other issues too, but do not let the user's stated concerns slip.

## 4. Your job

You are writing fix instructions for **one** review finding. Treat the finding as the spec for your work.

### Finding

### {reference_code}. {title} ({severity})

{full_finding_description}

### What to do

1. Read the affected file(s): {file_paths}
2. Read 2–3 nearby files to understand the surrounding patterns
3. Write a fix instruction document at `{output_folder}/{reference_code}-{title-slug}.md`

## 5. Output format

Your output is a single markdown file at `{output_folder}/{reference_code}-{title-slug}.md` with these sections in order:

### What
Exactly what needs to change. Name the exact code, lines, patterns.

### Why
Why this matters. What breaks or degrades if left unfixed.

### Where
Exact file path(s) and line number(s). Only include related files if they're part of the fix.

### How
The exact changes, with before/after code blocks. Precise enough to apply mechanically.

### Expected Outcome
What's different after the fix. How to verify it worked.

### Scope
What IS in scope. What is explicitly OUT of scope — no drive-by refactors, no bonus cleanup.

Be concise and precise. No fluff. These instructions are the single source of truth for this fix.

File naming: `{reference-code}-{title-slug}.md`. Title kebab-case, 5–8 words max.
```

## Step 7: Collect results

Once all agents finish, present the full list grouped by severity:

```
All {N} instruction files ready:

Critical ({count}):
  - docs/combs/plans/plan-for-.../C1-stale-closure-in-hook.md
  - ...

High ({count}):
  - ...

Medium ({count}):
  - ...
```

## Ground rules

- **Every item** in the report gets its own instruction file. Don't skip deferred items or test gaps — they all get documented.
- **Agents read source code.** They don't just parrot the review.
- **Instructions are self-contained.** Anyone picking up one file has everything they need to execute without reading the original report.
- **Scope boundaries are explicit.** Every instruction states what's in and out of scope.

## Edge case: focus brief contradicts shipped behavior

Same as `/comb:review`: surface and ask once.
```

- [ ] **Step 3: Commit**

```bash
git add skills/plan/SKILL.md
git commit -m "feat(skills): add /comb:plan orchestrator"
```

---

### Task 23: Write `skills/fix/SKILL.md`

**Files:**
- Create: `skills/fix/SKILL.md`

- [ ] **Step 1: Create directory**

```bash
mkdir -p skills/fix
```

- [ ] **Step 2: Write the skill**

```markdown
---
name: fix
description: Execute comb fix instructions sequentially or in parallel batches. Use after /comb:plan has produced instruction files. Each instruction goes to an implementer; standard items also go to a verifier. The user must invoke this explicitly — Claude does not auto-trigger it because it edits code.
argument-hint: "[instruction-folder] [focus brief]"
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Task
  - WebFetch
user-invocable: true
disable-model-invocation: true
---

You are running step 3 of the comb workflow: review → plan → fix.

You're a team lead working through a stack of fix instructions. For each: hand it to an implementer, then hand the result to a reviewer. If it fails, adjust and retry. Track progress; don't let anything slip.

## Inputs

1. **Folder of instruction documents** — from `/comb:plan` or any structured fix instructions. User specifies, or default to most recent under `<paths.plans>`.
2. **Execution order** — user specifies (e.g., "C1 → H1-H3 → M1-M10"), or derive from filenames/categories (Critical → High → Medium → Low → Test gaps). Confirm with user. Exclude items the user marks deferred or out-of-scope.
3. **Focus brief** — `$ARGUMENTS` — carries through from review when invoked via `/comb:the-desert`.

## Step 1: Load config

Same layered-merge as `/comb:review`. Project root is resolved with `git rev-parse --show-toplevel` (which handles git worktrees correctly). From it:
- `models.fix.implementer_standard`
- `models.fix.implementer_trivial`
- `models.fix.reviewer`
- `directives` and `agents` (for verifier dispatch)

## Step 2: Surface relevant directives

Lowercase the focus brief and scan it for substring matches against the loaded directive filenames (both plugin defaults at `${CLAUDE_PLUGIN_ROOT}/directives/*.md` and the user's directives at `<project-root>/<directives.user_path>/*.md` if present). Strip the `.md` extension before matching, but match against the *full base name* — so `"scope"` matches `scope-discipline.md`, `"simplicity"` matches `simplicity.md`, and `"copy-paste"` would match a user directive named `copy-paste.md` if present (it doesn't match the shipped `reusability.md` — the matcher is a literal substring check, not a synonym mapper, per spec §8).

Record the matched directive paths. They will be flagged as **primary** in agent dispatch prompts under the heading "Directives most relevant to this run" so agents weight them first.

If the focus brief is empty, no directives are flagged primary; all directives still load normally.

## Step 3: Suggest groupings

Scan instruction files for items that touch the same file with trivial scope. Suggest combining:

```
L1, L2, L3 all touch imports in ContactsGrid.tsx — combine?
M2 and M4 both fix the same hook — combine?
```

The user decides. Grouped items share one implementation pass but each sub-item gets verified.

## Step 4: Execution loop

For each item (or group):

### 4a. Parallel execution policy (governs Step 4b–4f)

Two instructions overlap if their **write-sets** intersect — reads are free. Apply this policy to the execution loop below:

- Same-file writes → sequential.
- Different-file writes → parallel batch.
- **Concurrency limit:** max 3 implementer/reviewer pairs running concurrently — i.e., up to 3 items being implemented and verified at any given moment (so up to 6 in-flight subagents at peak: 3 implementers running while 3 reviewers verify previous batches, or 3 implementer+reviewer pairs interleaved).

To launch a parallel batch, issue multiple Task tool calls in a single assistant message — one call per item in the batch. Do not use `run_in_background: true` (that is a Bash-tool parameter and has no effect on the Task tool).

Announce batches before launching:

```
Running batch: L1, L2, L3 in parallel (no file overlap, 3-pair concurrency)
```

### 4b. Read the instruction

Read the full fix instruction file. Understand What, Why, Where, How, Expected Outcome, Scope.

### 4c. Classify: trivial or standard?

Triviality is **judgment-based by the orchestrator** using this rubric (spec §7.5):

**Trivial:**
- Single-line edits
- Import reorders
- Comment fixes
- Lexical renames within a single file

**Standard:**
- Anything multi-file
- Anything that changes behavior
- Anything that introduces a new control-flow branch

This is a judgment call — borderline cases lean **standard**, because the cost of a needless reviewer is small but the cost of a missed regression is high. The user can override the classification for any item.

For trivial items: announce "(trivial — sonnet implementer per `models.fix.implementer_trivial`, reviewer per `models.fix.reviewer`)" and proceed. Note that the reviewer is **not** skipped for trivial items in the standard `/comb:fix` flow — that skip-trivial-review behavior only happens if the user explicitly authorises it for a given run, and is overridden in `/comb:the-desert` where every item gets a reviewer regardless.

### 4d. Send to implementer

**Agent config (resolved per item):**

- **Pick the role.** Implementer roles aren't restricted — pick whichever shipped role best matches the instruction's domain. When no domain match is clear, default to `code-reviewer`.
- **Resolve `subagent_type`** from the picked role's `agents.<role>.subagent_type`. **Do not hardcode `general-purpose`** — honor the user's `agents` config.
- **Resolve model** with this priority (spec §4.3 / §7.6): `agents.<role>.model` if set; otherwise `models.fix.implementer_standard` for standard items, `models.fix.implementer_trivial` for trivial items.
- **Allowlist match (not prefix check) — spec §5.4:** the shipped allowlist is exactly:
  - `comb:code-reviewer`
  - `comb:simplifier`
  - `comb:silent-failure-hunter`
  - `comb:test-auditor`
  - `comb:consistency-auditor`

  Compare the resolved `subagent_type` to this list with literal string equality. Native → supply directive paths only. Foreign → embed full directive contents.
- **Fresh agent per item** — no accumulated state.

**Implementer dispatch prompt (5-part order per spec §7.1.5):**

```
You're an implementer. Execute this fix instruction precisely and completely.

## 1. Shared context

Repository: {project-root}
Branch: {branch}
Item: {reference_code} — {title}
Instruction file: {instruction-path}

## 2. Directives

The project's authoritative directives apply to this fix.

{If native:}
Read these directive files and cite as `file.md §N.N` if you depart from any rule (you should not need to depart):
- {plugin directive paths, if include_plugin_defaults}
- {user directive paths, if directives.user_path resolves}

Directives most relevant to this run:
- {primary directive paths from the "Surface relevant directives" step}

{If foreign:}
These directives are authoritative. Cite by `file.md §N.N` if you depart from any rule.

{Embed full contents of every loaded directive verbatim with `## File: <path>` headers between them.}

Directives most relevant to this run:
- {primary directive paths from the "Surface relevant directives" step}

## 3. User focus for this run

{focus_brief if present, verbatim, with framing:}

Findings matching this focus are highest priority. Surface other issues too, but do not let the user's stated concerns slip.

## 4. Your job

Execute the fix instruction below. The instruction is the spec — do exactly what it says.

### Fix Instruction

{full instruction document content}

### Steps

1. Read the affected file(s) named in the instruction's "Where" section
2. Apply the exact changes from the "How" section
3. Stay strictly within the documented "Scope" — no drive-by refactors, no bonus cleanup
4. Confirm the "Expected Outcome" is met

## 5. Output format

Report back in plain text:

- Files you changed (paths)
- What changed in each (1-line summary)
- Confirmation that the "Expected Outcome" is met (yes/no with rationale)

Do not include code in your reply — your edits are the artifact.
```

### 4e. Send to reviewer (always)

**Agent config (resolved per item):**

- **Pick the role.** The fix-reviewer is **always `test-auditor`** — that is the canonical fix-verifier role per spec §5.3 ("`test-auditor` … Always for plan/fix verification."). Do not pick another role here unless the user has remapped `agents.test-auditor` in their config.
- **Resolve `subagent_type`** from `agents.test-auditor.subagent_type`. **Do not hardcode `general-purpose`** — honor the user's `agents.test-auditor` config (which defaults to `comb:test-auditor`).
- **Resolve model** with this priority (spec §4.3 / §7.6): `agents.test-auditor.model` if set; otherwise `models.fix.reviewer` (default `opus`).
- **Allowlist match (not prefix check) — spec §5.4:** the shipped allowlist is exactly:
  - `comb:code-reviewer`
  - `comb:simplifier`
  - `comb:silent-failure-hunter`
  - `comb:test-auditor`
  - `comb:consistency-auditor`

  Compare with literal string equality. Native (the default) → supply directive paths. Foreign (user remapped `agents.test-auditor.subagent_type` to something else) → embed full directive contents.
- **Fresh agent.**

**Reviewer dispatch prompt (5-part order per spec §7.1.5):**

```
You're a code reviewer verifying a fix against its original instruction.

## 1. Shared context

Repository: {project-root}
Branch: {branch}
Item: {reference_code} — {title}
Instruction file: {instruction-path}
Implementer summary: {implementer's reply}

## 2. Directives

The project's authoritative directives apply to your verification.

{If native:}
Read these directive files and cite as `file.md §N.N` when raising findings:
- {plugin directive paths, if include_plugin_defaults}
- {user directive paths, if directives.user_path resolves}

Directives most relevant to this run:
- {primary directive paths from the "Surface relevant directives" step}

{If foreign:}
These directives are authoritative. Cite by `file.md §N.N` when raising findings.

{Embed full contents of every loaded directive verbatim with `## File: <path>` headers between them.}

Directives most relevant to this run:
- {primary directive paths from the "Surface relevant directives" step}

## 3. User focus for this run

{focus_brief if present, verbatim, with framing:}

Findings matching this focus are highest priority. Surface other issues too, but do not let the user's stated concerns slip.

## 4. Your job

Verify the fix below was done correctly.

### Original Instruction

{instruction document content}

### What the implementer changed

{implementer's summary}

### Check these things

1. The change from "How" was applied correctly
2. The "Expected Outcome" is satisfied
3. No unrelated changes were introduced
4. The fix stays within documented "Scope"

## 5. Output format

Report `PASS` or `FAIL` on the first line with specifics:

- **PASS** — single line plus a 1–2-sentence confirmation of what you verified.
- **FAIL** — explain exactly what's wrong, with file:line citations.

### Discovered issues (optional)

If you spot a real problem in the same file(s) that's NOT part of this fix — a bug, type error, missing guard — report it under a `DISCOVERED` heading with:
- Short title
- File path and line(s)
- Brief description and suggested fix

Only flag genuine issues, not style preferences. One or two max. If nothing stands out, omit this heading.
```

### 4f. Handle the result

- **PASS** — log it, announce complete, move on.
- **FAIL** — read feedback. Adjust instructions if needed. Send a new implementer. Review again. **If 3 failures on one item, stop and ask the user.**
- **DISCOVERED** — write a new instruction document in the same folder using the next available code (`D1`, `D2`...). Same format as all other items. Add to the end of the queue. Announce:
  ```
  M3 — PASS (5/15 complete)
  Discovered issue added: D1 — {title} (queue is now 16 items)
  Next: M4 — {title}
  ```

## Step 5: Progress tracking

After each item:

```
{code} — PASS ({N}/{total} complete)
Next: {next_code} — {title}
```

With extras:
```
{code} — PASS after 1 retry ({N}/{total} complete)
{code} — PASS, trivial implementer ({N}/{total} complete)
```

At the end:

```
All {N} items complete:
  - C1: PASS
  - H1: PASS
  - H2: PASS (1 retry)
  - L1-L3: PASS (parallel batch, trivial implementer)
  - D1: PASS (discovered during H2 review)
  - ...

{M} items deferred:
  - X1-X6: {reason}

{K} discovered during execution:
  - D1: {title} (found reviewing H2) — PASS
```

## Ground rules

- **Fresh agents.** Each implementer and reviewer is a new subagent. No accumulated state.
- **The instruction is the spec.** Implementer follows it. Reviewer verifies against it. If the doc is wrong, fix the doc first, then re-implement.
- **Scope is sacred.** Implementers don't make changes outside scope. Reviewers flag scope violations as FAIL.
- **Don't loop forever.** Three failures means something's structurally wrong. Stop and ask.
- **Parallelize when safe.** Different writes = safe. Same file = sequential.
```

- [ ] **Step 3: Commit**

```bash
git add skills/fix/SKILL.md
git commit -m "feat(skills): add /comb:fix orchestrator"
```

---

### Task 24: Write `skills/the-desert/SKILL.md`

**Files:**
- Create: `skills/the-desert/SKILL.md`

- [ ] **Step 1: Create directory**

```bash
mkdir -p skills/the-desert
```

- [ ] **Step 2: Write the skill**

```markdown
---
name: the-desert
description: Run the full comb pipeline — review → plan → fix — as one continuous sweep. No pauses, no items skipped, no confirmations. Opus everywhere. The user must invoke this explicitly — it executes code changes.
argument-hint: "[scope] [focus brief]"
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Task
  - WebFetch
user-invocable: true
disable-model-invocation: true
---

You're running the full comb pipeline as one continuous sweep. No pauses between steps, no items skipped, no confirmations requested. You comb the desert until it's clean.

## How this differs from running each step individually

| Aspect | Individual steps | The Desert |
|---|---|---|
| Transitions | User decides when to move on | Automatic — no pause between steps |
| Deferred items | Excluded from fix by default | **Included** — nothing is deferred |
| Agent models | Mixed (lane defaults) | **`models.the_desert` everywhere** (default opus) |
| User confirmation | Asked between steps and for groupings | **None** — you make all decisions |

## Inputs

Same as `/comb:review`:
1. **Scope** — PR number, branch, or file list
2. **Base branch** — config or `main`
3. **Focus brief** — `$ARGUMENTS`

If scope is ambiguous, ask once. This is the only question you ask.

## Step 1: Load config

Same layered-merge as `/comb:review`. Project root is resolved with `git rev-parse --show-toplevel` (which handles git worktrees correctly). The relevant override:

- `models.the_desert` (default `opus`) overrides every lane default in this run
- **Exception:** explicit `agents.<role>.model` user overrides survive `the-desert` coercion (per spec §7.6). Only lane defaults are coerced.

## Step 2: Surface relevant directives

Lowercase the focus brief and scan it for substring matches against the loaded directive filenames (both plugin defaults at `${CLAUDE_PLUGIN_ROOT}/directives/*.md` and the user's directives at `<project-root>/<directives.user_path>/*.md` if present). Strip the `.md` extension before matching, but match against the *full base name* — so `"scope"` matches `scope-discipline.md`, `"simplicity"` matches `simplicity.md`, and `"copy-paste"` would match a user directive named `copy-paste.md` if present (it doesn't match the shipped `reusability.md` — the matcher is a literal substring check, not a synonym mapper, per spec §8).

Record the matched directive paths. They will be flagged as **primary** in agent dispatch prompts under the heading "Directives most relevant to this run" so agents weight them first. The matched-directive flagging carries through review → plan → fix without re-computing.

If the focus brief is empty, no directives are flagged primary; all directives still load normally.

## Step 3: Run review

Run the `/comb:review` workflow with these overrides:

- All agents use `models.the_desert`
- Save the report to `paths.reviews` per the standard naming
- **Do NOT present the report and wait** — log the verdict and finding count, then immediately continue

When review finishes, announce:

```
[review] Done — {verdict}, {N} findings ({breakdown by severity})
Moving to plan →
```

## Step 4: Run plan

Run the `/comb:plan` workflow with these overrides:

- All agents use `models.the_desert`
- **Include every finding** — Critical, High, Medium, Low, Test gaps, AND Deferred. Nothing is skipped.
- **Make grouping decisions yourself** — if items touch the same file with small scope, group them. Don't ask.
- Save instruction files to `paths.plans` per the standard structure

When plan finishes, announce:

```
[plan] Done — {N} instruction files created
Moving to fix →
```

## Step 5: Run fix

Run the `/comb:fix` workflow with these overrides:

- All implementers use `models.the_desert` — including trivial items (no sonnet downgrade)
- All reviewers use `models.the_desert`
- **Execute every item** — nothing is deferred or excluded
- **Every item gets a reviewer** — no "trivial — skipped review". The reviewer is `agents.test-auditor.subagent_type` (default `comb:test-auditor`), per spec §5.3, with model coerced to `models.the_desert` unless an explicit `agents.test-auditor.model` user override is set.
- **Make grouping decisions yourself** — combine same-file trivial items without asking
- Execution order: Critical → High → Medium → Low → Test gaps → Deferred (now treated as regular items) → Discovered
- Run parallel batches where safe (different writes), sequential otherwise — launch parallel batches by issuing multiple Task tool calls in a single assistant message (do not use `run_in_background: true`; that is a Bash-tool parameter and has no effect on the Task tool).

Track progress as normal. When all items complete, present the full summary.

## Focus brief flow

The focus brief from `$ARGUMENTS` flows through review → plan → fix without re-asking. Every dispatch in every step gets it under `## User focus for this run`.

## After completion

```
[the-desert] Complete

Review: {verdict}, {N} findings
Plan: {N} instruction files
Fix: {N}/{N} items complete, {K} discovered during execution

All items:
  - C1: PASS
  - H1: PASS
  - ...

Want to run the sequence again? A fresh review will check if the fixes introduced new issues.
```

Wait for the user's response. If yes, start again from review with the same scope. The new review naturally detects whether prior fixes introduced regressions or new issues.

## Ground rules

- **No confirmation prompts.** Don't ask "should I continue?" between steps. Don't ask about groupings or ordering. Decide and move.
- **Nothing is deferred.** Every finding from review gets planned and fixed. "Deferred" is not a valid category in this mode.
- **`models.the_desert` for lane defaults.** Explicit per-agent overrides survive (spec §7.6).
- **Only questions:** scope at the start (if ambiguous), and "run again?" at the end.
- **All `/comb:review`, `/comb:plan`, `/comb:fix` rules still apply** — read source, fresh agents per item, scope boundaries, 3-failure escalation, parallel when safe. This skill overrides only transitions, model coercion, deferral policy, and confirmation policy.

## Edge case: focus brief contradicts shipped behavior

Same handling as `/comb:review`: surface and ask once before proceeding.
```

- [ ] **Step 3: Commit**

```bash
git add skills/the-desert/SKILL.md
git commit -m "feat(skills): add /comb:the-desert full-sweep orchestrator"
```

---

### Task 25: Verify all 4 skills

**Files:**
- Read: `skills/*/SKILL.md`

- [ ] **Step 1: List skills**

```bash
ls -1 skills/
```

Expected output:
```
fix
plan
review
the-desert
```

- [ ] **Step 2: Structurally verify all skill frontmatter**

```bash
shopt -s nullglob
skill_dirs=(skills/*/)
shopt -u nullglob
[ ${#skill_dirs[@]} -gt 0 ] || { echo "FAIL: no skill dirs under skills/"; exit 1; }

# Files must exist
for d in "${skill_dirs[@]}"; do
  [ -f "${d}SKILL.md" ] || { echo "MISSING SKILL.md: $d"; exit 1; }
done

# Structural verification via PyYAML
python3 - <<'PY'
import os, re, sys, yaml, pathlib

DESTRUCTIVE = {'fix', 'the-desert'}     # must have disable-model-invocation: true
READ_ONLY   = {'review', 'plan'}        # must have disable-model-invocation: false

REQUIRED_FIELDS = {'name', 'description', 'argument-hint', 'allowed-tools',
                   'user-invocable', 'disable-model-invocation'}

errors = []
for skill_dir in sorted(pathlib.Path('skills').iterdir()):
    if not skill_dir.is_dir():
        continue
    skill_name = skill_dir.name
    f = skill_dir / 'SKILL.md'
    body = f.read_text()
    m = re.match(r'^---\n(.*?)\n---', body, re.DOTALL)
    if not m:
        errors.append(f"{f}: missing YAML frontmatter")
        continue
    data = yaml.safe_load(m.group(1)) or {}

    # Required-field presence
    missing = REQUIRED_FIELDS - set(data.keys())
    if missing:
        errors.append(f"{f}: missing fields {sorted(missing)}")

    # name matches directory
    if data.get('name') != skill_name:
        errors.append(f"{f}: name={data.get('name')!r} != dir {skill_name!r}")

    # user-invocable must be a real boolean True
    if data.get('user-invocable') is not True:
        errors.append(f"{f}: user-invocable must be true (got {data.get('user-invocable')!r})")

    # disable-model-invocation must be a real boolean and match the destructive/read-only contract
    dmi = data.get('disable-model-invocation')
    if not isinstance(dmi, bool):
        errors.append(f"{f}: disable-model-invocation must be a boolean (got {dmi!r})")
    elif skill_name in DESTRUCTIVE and dmi is not True:
        errors.append(f"{f}: destructive skill must have disable-model-invocation: true (got {dmi!r})")
    elif skill_name in READ_ONLY and dmi is not False:
        errors.append(f"{f}: read-only skill must have disable-model-invocation: false (got {dmi!r})")

    # allowed-tools must be a non-empty list (or comma-separated string)
    tools = data.get('allowed-tools')
    if isinstance(tools, str):
        tool_set = {t.strip() for t in tools.split(',') if t.strip()}
    elif isinstance(tools, list):
        tool_set = set(tools)
    else:
        tool_set = set()
        errors.append(f"{f}: allowed-tools must be a list or comma-separated string (got {type(tools).__name__})")
    if not tool_set:
        errors.append(f"{f}: allowed-tools is empty")

    # argument-hint must be a non-empty string
    hint = data.get('argument-hint')
    if not isinstance(hint, str) or not hint.strip():
        errors.append(f"{f}: argument-hint must be a non-empty string (got {hint!r})")

if errors:
    for e in errors:
        print(e)
    sys.exit(1)
print("OK — all 4 skills pass structural verification.")
PY
```

Expected output: `OK — all 4 skills pass structural verification.`

- [ ] **Step 3: No commit needed (verification only).**

---

## Phase 5: Polish, smoke test, and release

### Task 26: Write the final README.md

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Replace the README scaffold with the full content**

```markdown
# comb-the-desert

A Claude Code plugin for code review: a `/comb:review` → `/comb:plan` → `/comb:fix` pipeline with `/comb:the-desert` for the full sweep.

The plugin ships configurable reviewer agents, eight domain-neutral directives, and a layered config system that lets your project policy take precedence.

## What it does

- **`/comb:review`** — dispatches 2–5 reviewer agents over a PR / branch / file list, consolidates findings into a severity-ranked report
- **`/comb:plan`** — turns each finding into a self-contained fix instruction
- **`/comb:fix`** — executes the instructions, with implementer + reviewer per item, parallel batching where safe
- **`/comb:the-desert`** — runs all three steps as one continuous sweep, opus everywhere, no pauses

Each command accepts a free-form focus brief that biases agent picking and finding priorities:

```
/comb:review look for spec/plan misalignment
/comb:the-desert ensure simplicity, scope discipline, and TDD coverage
```

## Install

The plugin is shipped via a same-repo marketplace.

1. Add the marketplace:

```
/plugin marketplace add olioskar/comb-the-desert-claude-plugin
```

2. Install the plugin:

```
/plugin install comb@comb-marketplace
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

### Common overrides

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

See `config/defaults.json` for every supported field. The full reference is in the design spec at `docs/superpowers/specs/2026-04-27-comb-the-desert-plugin-design.md`.

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
- `comb:consistency-auditor` — patterns, reference impl, spec/plan alignment

You can invoke them directly via the Task tool or let the comb skills pick them automatically.

### A note on skill `model` frontmatter

The four `/comb:*` skills intentionally omit the `model:` frontmatter field. The orchestrator runs in the user's session model (whatever they invoked Claude Code with), and the skill body's logic dispatches subagents at the configured `models.<lane>` model (or `agents.<role>.model` when set). Adding a `model:` field to a skill would only fix the orchestrator's model — it would have no effect on the dispatched agents, which is what actually matters for cost and quality.

## Status

v0.1.0 — first published release.

## License

MIT
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: write full README"
```

---

### Task 27: Finalize CHANGELOG.md for v0.1.0

**Files:**
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Replace the placeholder with v0.1.0 entry**

```markdown
# Changelog

All notable changes to this plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-04-27

### Added

- `/comb:review` skill — orchestrates 2–5 reviewer agents over a PR/branch/file list and produces a severity-ranked report
- `/comb:plan` skill — turns review findings into per-finding fix instructions
- `/comb:fix` skill — executes fix instructions with implementer + reviewer per item; parallel batching where safe
- `/comb:the-desert` skill — runs the full review→plan→fix sweep, opus everywhere, no pauses
- Five `comb:*` reviewer subagents: `code-reviewer`, `simplifier`, `silent-failure-hunter`, `test-auditor`, `consistency-auditor` — all read-only
- Eight domain-neutral directives: `simplicity.md`, `modularity.md`, `reusability.md`, `maintainability.md`, `quality.md`, `consistency.md`, `scope-discipline.md`, `testing.md`
- Layered config system (`project > global > shipped defaults`) supporting agent substitution, extensions, model lanes, and path overrides
- Same-repo marketplace manifest (`.claude-plugin/marketplace.json`) for `/plugin marketplace add` install path

### Notes

- The `marketplace.json` schema used here matches the conventional shape from `anthropics/claude-code` and was empirically verified during release via the Task 29 smoke test (`/plugin marketplace add` + `/plugin install`). The plugins-reference docs do not fully enumerate the schema, so any schema changes in future releases must re-run the marketplace install smoke test.
```

- [ ] **Step 2: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs: write v0.1.0 changelog entry"
```

---

### Task 28: Local smoke test via `--plugin-dir`

**Files:**
- (Test only — no source files modified)

- [ ] **Step 1: Create a fresh test repo**

Always create a new throwaway repo under `/tmp` — do not reuse an existing project. This keeps the smoke test deterministic.

In a separate terminal:

```bash
rm -rf /tmp/comb-smoke-test
mkdir -p /tmp/comb-smoke-test
cd /tmp/comb-smoke-test
git init -q
echo 'console.log("hello");' > app.js
git add app.js
git commit -q -m "initial"
echo 'console.log("hello world");' > app.js
git add app.js
git commit -q -m "say world"
```

- [ ] **Step 2: Validate the plugin manifest before launching Claude**

`claude plugin validate` catches manifest and frontmatter errors before runtime.

```bash
claude plugin validate /Users/olafur/Development/comb-the-desert-claude-skill
```

Expected: validation reports the plugin parses cleanly. If it errors, fix the reported issue before proceeding.

(If `claude plugin validate` is not available on the installed `claude` CLI version, note this in the smoke-test results and rely on `/plugin` slash-command output inside Claude as the validation step instead.)

- [ ] **Step 3: Launch Claude with the plugin**

Still in `/tmp/comb-smoke-test` (this matters — `/comb:review` operates on the cwd as the project root):

```bash
# pwd should print /tmp/comb-smoke-test
pwd
claude --plugin-dir /Users/olafur/Development/comb-the-desert-claude-skill
```

Inside Claude:

```
/help
```

Expected: the slash menu lists `/comb:review`, `/comb:plan`, `/comb:fix`, `/comb:the-desert`. The agents appear in the agent list as `comb:code-reviewer`, etc.

If any are missing, check:
- `.claude-plugin/plugin.json` is valid JSON
- Skill directories all contain `SKILL.md`
- Agent `.md` files all have valid frontmatter

- [ ] **Step 4: Run a review against the test repo**

```
/comb:review
```

Expected (structural — does not depend on agent verdict judgment):
- The orchestrator picks 1–3 agents (small diff, so the palette will be small).
- Verification checks run (some may fail in the toy repo — that's fine; expect them noted in the report).
- A report file is written under `<test-repo>/docs/combs/reviews/` matching the pattern `branch-*-round1-report.md` (the exact slug depends on the branch name).
- The report contains all standard sections: `Verification Summary`, `Verdict`, `Findings by Severity` (with at least the canonical sub-headings: `Critical`, `High`, `Medium`, `Low`, `Test Gaps`, `Deferred`).

**Do NOT** assert a specific verdict (`APPROVE` vs `NEEDS WORK`). Either is acceptable for a toy diff — the agent's judgment is not the property under test here. The property under test is "the plugin loaded and produced a structurally complete report."

- [ ] **Step 5: Verify the report file exists and has the expected structure**

```bash
ls /tmp/comb-smoke-test/docs/combs/reviews/
cat /tmp/comb-smoke-test/docs/combs/reviews/*.md | head -40
```

Expected output: a report file is present and shows the standard sections (Verification Summary, Verdict, Findings by Severity). Verdict may be `APPROVE` or `NEEDS WORK` — either is fine.

- [ ] **Step 6: Clean up the test repo**

```bash
rm -rf /tmp/comb-smoke-test
```

- [ ] **Step 7: No commit needed (smoke test, not source).**

---

### Task 28.5: Fixture-driven structural test for skill-body invariants

**Files:**
- (Test only — no source files modified)

**Goal:** Confirm two skill-body invariants from the spec are actually honored at runtime:
- §4.1 merge semantics: `null` at any depth deletes that key from the merged config (here: `agents.simplifier: null` removes `simplifier` from the dispatched palette).
- §7.1.4 agent-picking cap: a varied diff that would surface >5 candidate agents is capped at exactly 5, and `code-reviewer` is always included (soft floor 1, always-on).

These two assertions cannot be verified by manifest validation or runtime smoke alone — they exercise orchestrator logic in the skill body.

- [ ] **Step 1: Create fixture repo A — `null`-as-delete merge**

```bash
rm -rf /tmp/comb-fixture-a
mkdir -p /tmp/comb-fixture-a/.claude
cd /tmp/comb-fixture-a
git init -q
git commit -q --allow-empty -m "initial"

# Project-level config that disables the simplifier role via null
cat > .claude/comb.config.json <<'JSON'
{
  "agents": {
    "simplifier": null
  }
}
JSON

# Trivial diff so the picker would otherwise consider simplifier
echo 'function greet(name) { return "hi " + name; }' > greet.js
git add .claude greet.js
git commit -q -m "add greet"
echo 'function greet(name) { return `hi ${name}`; }' > greet.js  # template-string refactor — would normally trigger simplifier
git add greet.js
git commit -q -m "use template string"
```

Launch Claude (still inside `/tmp/comb-fixture-a`):

```bash
pwd  # /tmp/comb-fixture-a
claude --plugin-dir /Users/olafur/Development/comb-the-desert-claude-skill
```

Inside Claude:

```
/comb:review
```

When the skill announces its picks ("Picking code-reviewer (always), simplifier (...), ..."), confirm:
- `simplifier` is **not** in the announced palette
- The palette includes `code-reviewer` (always-on)

If `simplifier` appears, the merge logic is broken — file as a finding before proceeding.

- [ ] **Step 2: Create fixture repo B — agent-palette cap of 5**

```bash
rm -rf /tmp/comb-fixture-b
mkdir -p /tmp/comb-fixture-b
cd /tmp/comb-fixture-b
git init -q
git commit -q --allow-empty -m "initial"

# A varied diff designed to surface every shipped role:
#   - bugs/logic         -> code-reviewer
#   - refactor/dead code -> simplifier
#   - error handling     -> silent-failure-hunter
#   - tests              -> test-auditor
#   - existing patterns  -> consistency-auditor
# All five appear in the diff so a naive picker would return 5 anyway.
# Then add a sixth signal (a directive-coupled doc change) that, with default config,
# should still cap the palette at 5 and prefer the always-on roles.

mkdir -p src tests docs
cat > src/api.js <<'JS'
async function fetchUser(id) {
  try { return await api.get('/u/' + id); } catch (e) { console.error(e); return null; }
}
module.exports = { fetchUser };
JS
cat > tests/api.test.js <<'JS'
test('fetchUser returns null on error', () => {
  // mock-only test — should be flagged by test-auditor
  expect(true).toBe(true);
});
JS
cat > docs/style.md <<'MD'
# Style guide

Write functions like `getUser`, not `fetch_user`.
MD

git add src tests docs
git commit -q -m "initial impl"

# Make a varied edit across all five surfaces:
echo "function unused() {}" >> src/api.js                    # dead code (simplifier)
sed -i.bak 's/console.error(e); return null;/return null;/' src/api.js  # silent failure (silent-failure-hunter)
rm src/api.js.bak
echo "test('another mock test', () => expect(1).toBe(1));" >> tests/api.test.js  # vanity test (test-auditor)
echo "Use snake_case for new APIs." >> docs/style.md         # contradicts existing convention (consistency-auditor)
git add -A
git commit -q -m "varied changes across all reviewer surfaces"
```

Launch Claude (still inside `/tmp/comb-fixture-b`):

```bash
pwd  # /tmp/comb-fixture-b
claude --plugin-dir /Users/olafur/Development/comb-the-desert-claude-skill
```

Inside Claude:

```
/comb:review
```

When the skill announces its picks, confirm:
- The palette has **at most 5 agents**.
- `code-reviewer` is in the palette (always-on).
- The skill's announced rationale acknowledges that more than 5 candidates were considered (or that the cap was hit).

If more than 5 agents are picked, the cap logic is broken — file as a finding before proceeding.

- [ ] **Step 3: Clean up fixtures**

```bash
rm -rf /tmp/comb-fixture-a /tmp/comb-fixture-b
```

- [ ] **Step 4: No commit needed (test only).**

---

### Task 29: Marketplace install smoke test

**Files:**
- (Test only)

This test verifies the marketplace install path works. Requires the GitHub repo to exist and `main` to be pushed (Task 30). Step 0 below confirms this before proceeding.

- [ ] **Step 0: Confirm the GitHub repo exists and `main` is pushed**

This task installs from `olioskar/comb-the-desert-claude-plugin`. Confirm it is reachable before invoking the marketplace add. If the repo doesn't exist yet, complete Task 30 (push to GitHub) first, then return here.

```bash
gh repo view olioskar/comb-the-desert-claude-plugin --json url,defaultBranchRef,pushedAt
```

Expected: JSON output naming the repo URL, the default branch (`main`), and a recent `pushedAt` timestamp. Errors here (repo not found, 404) mean Task 30 hasn't run yet — go do Task 30 first.

If the repo doesn't exist at all, create it now (one-time):

```bash
gh repo create olioskar/comb-the-desert-claude-plugin --public --source=. --remote=origin --description "comb the desert: review/plan/fix Claude Code plugin"
```

Then run Task 30's push steps before returning to this task.

- [ ] **Step 1: Add the marketplace from the GitHub URL**

In Claude:

```
/plugin marketplace add olioskar/comb-the-desert-claude-plugin
```

Expected: Claude reports the marketplace was added, listing one plugin (`comb`).

- [ ] **Step 2: Install the plugin**

```
/plugin install comb@comb-marketplace
```

Expected: install succeeds; `/help` shows the four `/comb:*` skills.

- [ ] **Step 3: Run a review**

In any small git repo:

```
/comb:review
```

Expected: works the same as the `--plugin-dir` test — report written to `docs/combs/reviews/`.

- [ ] **Step 4: Uninstall (to clean up — best effort)**

```
/plugin uninstall comb
```

The `comb` plugin is now uninstalled. To also remove the marketplace entry:

```
/plugin marketplace remove comb-marketplace
```

The exact `marketplace remove` slash-command syntax is not fully documented in the in-scope plugins reference. If the command above isn't recognized:

1. Run `/plugin help` and look for the documented removal syntax for marketplaces.
2. If still unclear, **skip this step**. Leaving the marketplace registered locally is harmless — it just means the marketplace entry persists in the local Claude Code installation, which is fine.

(Document the actual syntax in the README and CHANGELOG if you discover it during this smoke test.)

- [ ] **Step 5: No commit needed.**

---

### Task 30: Tag v0.1.0 and push to GitHub

**Files:**
- (Git operations only)

- [ ] **Step 1: Verify working tree is clean**

```bash
git status
```

Expected: `nothing to commit, working tree clean`. If anything is dirty, investigate and clean before tagging.

- [ ] **Step 2: Verify the spec exists in the committed history**

```bash
git ls-files docs/superpowers/specs/
```

Expected: `docs/superpowers/specs/2026-04-27-comb-the-desert-plugin-design.md`

(If the spec is not committed yet — it was written during brainstorming before this plan executed — commit it now: `git add docs/ && git commit -m "docs: add design spec and round-1 review report"`.)

- [ ] **Step 3: Create the v0.1.0 tag**

```bash
git tag -a v0.1.0 -m "v0.1.0 — initial release"
```

- [ ] **Step 4: Add the GitHub remote**

(Skip if already added.)

```bash
git remote add origin git@github.com:olioskar/comb-the-desert-claude-plugin.git
```

- [ ] **Step 5: Push main and the tag**

```bash
git push -u origin main
git push origin v0.1.0
```

(Confirm with the user before running this — pushing to a public remote is a one-way action. The user must have already created the empty repo on GitHub.)

- [ ] **Step 6: Verify the GitHub repo is live**

```bash
gh repo view olioskar/comb-the-desert-claude-plugin
```

Expected: the repo exists and shows v0.1.0 as the latest tag.

- [ ] **Step 7: Run Task 29 (marketplace install smoke test) now that the repo is pushed.**

- [ ] **Step 8: Document the version-bump rhythm for future releases**

Per Claude Code's plugins-reference, users only see a plugin update when the `version` field in `.claude-plugin/plugin.json` changes. This plan ships `0.1.0`. For every subsequent release:

1. Bump `version` in `.claude-plugin/plugin.json` (semver: patch for fixes, minor for additive features, major for breaking config/skill-contract changes).
2. Add a `## [<new-version>] — YYYY-MM-DD` entry to `CHANGELOG.md` summarizing user-visible changes.
3. Commit the bump and changelog as one commit: `git commit -m "chore: release v<new-version>"`.
4. Tag and push: `git tag -a v<new-version> -m "v<new-version>"` then `git push origin main v<new-version>`.

Append this rhythm to `CHANGELOG.md` directly under the top header (above `## [Unreleased]`) so future maintainers see it:

```markdown
> **Releasing a new version:** bump `version` in `.claude-plugin/plugin.json`, add a changelog entry, commit as `chore: release vX.Y.Z`, then `git tag -a vX.Y.Z -m "vX.Y.Z"` and push both `main` and the tag. Users only see updates when `version` changes.
```

Commit the CHANGELOG note:

```bash
git add CHANGELOG.md
git commit -m "docs: document release/version-bump workflow"
```

(This commit is allowed *after* the v0.1.0 tag — it becomes part of the next release.)

---

## Self-review

After writing the plan, look at the spec with fresh eyes. Spec coverage check:

| Spec section | Covered by |
|---|---|
| §1 Goal | Whole plan |
| §2 Non-goals | (No tasks needed — they describe what we don't build) |
| §3 Plugin layout | Tasks 1, 3, 4, 5, 6–13, 15–19, 21–24 |
| §3.1 `${CLAUDE_PLUGIN_ROOT}` | Embedded in skill bodies (Tasks 21–24) |
| §3.2 `plugin.json` | Task 3 |
| §4 Config + merge semantics | Task 5 (defaults), Tasks 21–24 (loader logic in skill bodies) |
| §5 Agents | Tasks 15–20 |
| §6 Directives | Tasks 6–14 |
| §7 Skills (workflow) | Tasks 21–25 |
| §8 Inline argument handling | Embedded in each skill body (Tasks 21–24) |
| §9 Discoverability | Skill descriptions in Tasks 21–24 |
| §10 What's dropped | (No new tasks — porting captures dropped items by omission) |
| §11 Distribution | Task 4 (marketplace.json), Task 26 (README), Tasks 28–30 (smoke + push) |
| §12 Open items | (Future work — not in this plan) |

Placeholder scan: no `TBD`, no `TODO`, no `add appropriate handling`, no `similar to Task N`. Every task has actual content. (Note: skill bodies in Tasks 21–24 contain `{placeholder}` tokens — e.g., `{focus_brief if present}`, `{N}/{total}`, `{verdict}`. These are **runtime template slots** Claude fills in when the skill executes, not plan-stage gaps. They are intentional and required.)

Type consistency: agent names match across `defaults.json`, agent files, and skill bodies. Field names (`subagent_type`, `when_to_use`, `paths.reviews`, etc.) match across all artifacts.

---

## Execution

Plan complete and saved to `docs/superpowers/plans/2026-04-27-comb-the-desert-plugin.md`. Two execution options:

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks, fast iteration
2. **Inline Execution** — execute tasks in this session with checkpoints

Pick one to proceed.
