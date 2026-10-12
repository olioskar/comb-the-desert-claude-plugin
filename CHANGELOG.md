# Changelog

All notable changes to this plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.15.1] — 2026-10-12

Prose trims from the family-lean review (P-4, P-5, P-9/R-2, B-1, D-10). Four second copies move to their single source; no behavior changes, so no eval run.

### Changed

- **`shared/manifest-slicing.md` states what the excerpt contains and points at the grammar.** The seven-step excerpt grammar (section classification, scope lines, anchors, touched paths, relevance, banner, staleness) now lives only in `scripts/manifest.py`'s module docstring, the implementation's own contract; the shared block keeps the inputs, four bullets on what travels and why, the printed lines, what the skill does, and the fallback. The fallback no longer mentions a missing `python3`, which has been required since 0.15.0.
- **`/comb:review` Step 3.5 keeps its two classification definitions and the output shape.** The three worked characterization examples and the three-case tie-break paragraph are gone; the tie-break's one rule — judge by content, not file extension; a mixed diff is code-shaped — joins the Classification intro.
- **`/comb:configure` derives keys and types from `config/defaults.json`.** The schema table was a copy of that file plus three absent-by-default keys; it is now a pointer, those three keys, a Notes list, and the accepted model values — `sonnet | opus | haiku | fable | <full id>`; `best`, `inherit`, and `opusplan` are `/model` session aliases the Agent call rejects, so configure refuses them. The translation rules keep the three that are not a direct key write (disable a role, add a custom agent, allow Claude to run fix).
- **README's manifest paragraph points at `shared/manifest-slicing.md`** instead of restating the scope rule, and says `python3` is required.

## [0.15.0] — 2026-10-12

Deterministic resolver and dispatch briefs, the third PR of the family-lean program. The steps every comb skill re-derived in prose per run — config merge, role and model resolution, directive matching, the common dispatch block, report naming, write-set batching, finding extraction — now run through one stdlib script, and the invariant parts of the planner, implementer, and fix-reviewer prompts move into shared brief files delivered by path. A dispatch prompt is a shared-context block plus two paths; the model stops re-deriving the same rules on every call and the output of each step has one fixed shape.

### Added

- **`scripts/comb.py`**, beside `manifest.py`, stdlib only, with seven subcommands. `config` merges the three config layers (objects deep-merge, arrays replace, `null` deletes at any depth, a role without `subagent_type`/`when_to_use` is dropped with a `warning:` line, bad JSON is an exit-2 error naming the file). `resolve --role R --lane L [--coerce the_desert]` prints `subagent_type`, `model`, `effort`, and `native: yes|no`; `agents.<role>.model` wins over the lane and survives coercion. `directives [--brief]` lists the plugin and user directive files and the primaries the focus brief flags. `brief` writes the per-run dispatch brief under `.comb/excerpts/<run>.<skill>.<role>.brief.md` and prints four summary lines (`brief:`, `form:`, `directives:`, `baseline:`). `report-name` derives the review report path with the round parsed from existing filenames. `batches --folder` prints the folder shape, each item's write-set, the not-reproduced items, and severity-ordered batches of at most three pairwise-disjoint items. `findings --report` turns a review report into JSON (a finding without a `Verified:` line comes back with an empty `verified` field, which `/comb:plan` already treats as unconfirmed) and returns `"count": 0` for anything not in the template shape instead of a traceback.
- **Shared briefs.** `shared/plan-brief.md`, `shared/fix-implementer-brief.md`, and `shared/fix-reviewer-brief.md` hold the job and output-format text that the plan and fix prompts carried verbatim; `shared/scan-rules.md` holds the scanner's lenses, classification, and output format, which the agent body and the `/comb:patterns` prompt both point at (as the shaver already did). The run brief holds what changes per run: directive paths in native or foreign form, primaries, the observed-baseline block with the skill's role note, the focus brief (framed for review, verbatim elsewhere).
- **python3 is required.** Every skill's first step runs `comb.py config` and stops on failure; the manifest excerpt's full-manifest fallback remains, but no comb command runs without `python3` on the `PATH`.
- **Gates.** `scripts/test-comb.sh` pins the script's output against 62 fixture expectations and runs inside `check-contract.sh`; rule 9 checks that every `(default: X)` in `/comb:help` equals `config/defaults.json`; rule 5 checks each skill invokes the subcommands it depends on; rule 8 checks each agent's frontmatter name equals its filename, which the native rule relies on.

### Changed

- **Skills call the script, one command line per step.** `/comb:review`, `/comb:plan`, `/comb:fix`, `/comb:patterns`, `/comb:the-desert`, `/comb:fix-auto`, and `/comb:configure` load config with `comb.py config`; review, plan, and fix match directives with `comb.py directives`, resolve each role with `comb.py resolve`, and write a run brief with `comb.py brief` before dispatching; review names its report with `comb.py report-name`; fix reads the folder shape, write-sets, and batch ceiling from `comb.py batches`; plan parses findings with `comb.py findings` and falls back to reading only when the parser finds nothing.
- **Dispatch prompts shrink to shared context plus two paths.** The planner, implementer, and fix-reviewer prompts carry their shared-context block and `Read these first, in order: <shared brief>, <run brief>`; review dispatches carry `Read first: <run brief>` and, for native agents, "output format per your agent definition" instead of the full spec; the four review agents that used to defer to the prompt's spec now carry the per-finding format (including the Confidence line) themselves. The directive list, authority sentence, observed-baseline block, and focus brief no longer appear in any prompt; they are in the brief. `skills/fix/SKILL.md` drops about 1,000 words and `skills/plan/SKILL.md` about 700.
- **Native is a rule, not a list.** An agent is native when its resolved `subagent_type` equals `comb:` plus the `name:` of a file in `agents/`, compared literally; the hand-maintained allowlist in `dispatch-delivery.md` is gone and `comb.py resolve` prints the answer.
- **The review orchestrator lists directive files and does not read them.** The matcher and the consolidation gate need names and paths; every agent reads the files itself from the run brief.
- **Discovered issues no longer make fix read the plan skill.** `/comb:fix` dispatches a plan-shaped prompt with the planner brief directly, so the plugin-root expansion paragraph leaves fix; the-desert and fix-auto keep theirs and now name `comb.py` command lines too.
- **The focus-brief matcher states its short-word rule.** A word shorter than four characters flags a directive only when it equals a whole hyphen-separated segment of the name, so `it` and `and` flag nothing while `api` still flags `api.md`. The matcher is still a literal substring check, never a stemmer: `tests` does not flag `testing.md`.
- **`/comb:the-desert` says once that every `comb.py resolve` in a sweep carries `--coerce the_desert`**, which is the models-and-effort override made mechanical; Step 1 runs `comb.py config` once and the sub-skills reuse its JSON.
- **Evals follow the brief.** The dispatch-delivery and manifest-slice graders that read the authority sentence, directive paths, and excerpt/manifest paths out of the Agent prompt now read the `form:`, `directives:`, and `baseline:` lines `comb.py brief` prints into the trace, and a `brief-delivered` grader per case checks the prompt carries the brief path; the brief's content is fixture-tested.
- **Shared briefs read standalone.** The brief headings are `## Your job` and `## Output format` (no skill numbering), and the briefs no longer cite skill step numbers an agent cannot see.
- **The matcher, the observed-baseline block, configure, and the implementer's `when_to_use` say "run brief"** where they said "dispatch prompt"; every skill says its `comb.py` command lines run from the project root and that the focus brief is quoted for the shell; the-desert's Step 2 runs `comb.py directives` once for the log.
- **Deferred minors from 0.14.0 closed.** The fix reviewer's two `## Divergences` references read `### Divergences`, the heading the implementer actually writes; the implementer's `when_to_use` says it is not part of the review palette; `agents/implementer.md` says the planner brief's output format replaces its own when `/comb:plan` dispatches it.

### Fixed

- **`comb.py batches` refuses two files with the same code** (`M1-a.md` and `M1-b.md`) with an exit-2 line naming both; `/comb:fix` addresses items by code, so an ambiguous batch line was unactionable.
- **`comb.py findings` keeps Deferred bullets that follow a coded Deferred entry**, numbers them after the highest coded `D<n>`, and skips a bare `None.` / `n/a` bullet instead of turning it into `D1`.
- **`comb.py config` warns instead of degrading silently** when `agents` is not an object, `directives.include_plugin_defaults` is not a boolean, or `directives.user_path` exists but is not a directory; a lane whose value is not a string says so (`lane review is not a model string (got list)`); a config file that starts with a BOM is read.
- **`comb.py brief` summary lines** de-duplicate primary basenames when a user directive shares a name with a shipped one, and a whitespace-only focus brief adds no focus section. `report-name --branch ""` is an exit-2 error, not a `branch--round1` file.
- **check-contract**: rule 8 trims trailing whitespace on an agent's `name:` so it agrees with the script's native rule; rule 9 fails loudly on a help line that states a default on a placeholder key (`agents.<role>.model`) instead of skipping it.

## [0.14.0] — 2026-10-11

Fix-tier hardening from the family-lean review's fan-out lens. Plan correctness becomes observable at the fix gate, and the fix tier's hygiene — fresh tree, reported files, clean commit — is checked with git instead of asserted. Every new gate states its bound; no config knob was added.

### Added

- **`comb:implementer`, the default writer** (`agents/implementer.md`, `disallowedTools: Agent, NotebookEdit`). The default implementer and planner were `general-purpose`: full tools, nested agents, git, and no statement of what a writer must not do. The shipped agent carries the boundaries once — write only inside the instruction's `## Where`; never commit, stage, stash, or dispatch; report every file — and the report format the fix reviewer reads. A project's own writer still overrides it and receives the same boundaries as its specialty statement. check-contract rule 8 asserts every `comb:*` default has an agent file and sits in the native allowlist.
- **Plan files say whether the finding was reproduced and how to check the fix.** The header gains `**Finding status:** confirmed — <observed> | not reproduced — <looked for>`; the planner reads the code before it writes and writes no `## How` for a non-defect. `## Expected Outcome` ends with a `Check:` line — a command or observable the fix reviewer can run, or `none — <why>`. Together they make the plan, the one artifact no tier verified, observable at the one gate that exists. Plan Step 7 also compares the folder listing with the parsed finding codes so a planner that wrote no file is reported instead of silently narrowing the fix queue.
- **`/comb:fix` verifies before it commits (4f.0).** The project's typecheck, tests, and lint — chosen by the same rule `/comb:review` Step 5 uses, and run once at Step 1.6 as a baseline — run again after the reviewer's PASS and before the commit, only when no implementer of the batch is still writing. Failing lines already in the baseline are not the item's; a new failure is attributed by path to the in-flight item whose write-set it names, or fails every waiting item when it names none (the bound says so, and recommends sequential items when a suite reports test files). No commit lands on red.
- **`/comb:fix` reverts before it retries and records every attempt.** On FAIL the reported files are checked out, created files deleted, and the tree confirmed clean for those paths before a new implementer is dispatched, so the second attempt starts where the first did. Each FAIL and any change the orchestrator makes to `## How` is appended under `## Attempts` in the instruction file; the next reviewer reads it, and the summary says `PASS after 1 retry (plan adjusted)` when the plan changed.
- **`/comb:fix` checks git around every implementer and commit, against a baseline.** Step 1.6 records the run's baseline once: the dirty paths the user accepted at pre-flight, HEAD, and the project's verification result. After each implementer returns, HEAD must equal the run's expected HEAD (advanced only by the run's own commits, so a batch-mate's commit is not read as the implementer's); the reported file list must equal the dirty paths inside the item's `## Where` (an unreported or phantom path stops the item, a reported path inside a batch-mate's write-set stops the batch); and nothing may be dirty outside the allowed set — the baseline, the instruction folder (where `## Attempts` and X-item files land), and the in-flight write-sets. An item whose `## Where` overlaps the baseline's dirty paths is not dispatched (commit or stash first), so a revert never touches a user's edit. After each commit the tree minus the allowed set must be empty. A commit-hook abort or a batch stop prints each in-flight item as committed, PASS-uncommitted with its files, in progress, or stopped. The write-set is now defined: the paths in `## Where`; "in flight" and "stop" are defined with it.
- **`/comb:review` reports its bookkeeping.** A `**Sources:**` line per agent (reported → kept, merged, dropped, or no report) makes a vanished finding visible; the shared context records the merge-base SHA so agents and orchestrator diff against the same commit; the consolidation gate resolves cited directive sections (`file.md §N`) because the planner copies them as policy; the gate's bound now says the verdict inherits agent severity unchecked.
- **`manifest.py anchors`.** Lists every line-carrying anchor in an area section whose file is missing or whose line is past the end, and every basename anchor that resolves to more than one file. `/comb:patterns` runs it on the draft before the pre-write summary and shows the lines; its bound is existence and line bounds, never the claim. Fixture `scripts/fixtures/anchors.md` covers each outcome (70 expectations).
- **Evals.** Three mechanical graders on `fix-reviewer-diff-scope` read the orchestrator's own Bash calls: a test run before commit, HEAD recorded, `git status --porcelain` run. The scaffold gains a `package.json` test runner, and its plan files carry `Finding status` and `Check:` lines; the replay fixtures carry the matching calls.

### Changed

- **The fix reviewer runs the `Check:` and knows its batch.** A failing `Check:` is a FAIL however faithful the diff; the reviewer's shared context lists the batch-mates' write-sets so a stray hunk can be attributed; it reads `## Attempts` before `## How`. A plan without a `Check:` predates the field and is treated as `none — not stated`.
- **The implementer reads the directives the instruction cites plus the primaries**, not the whole corpus for every item. The full list stays in the prompt for reference.
- **Discovered issues (`X{n}`) go through a planner dispatch.** The orchestrator no longer writes an instruction from a two-line DISCOVERED note; it dispatches `/comb:plan`'s planner prompt with the note as the finding and `Verified: none — discovered during fix`. `/comb:fix` Reads the plan skill for that prompt and carries the plugin-root expansion paragraph (contract rule 4).
- **Not-reproduced items are listed, not queued.** `/comb:fix` Step 2.5 lists items whose `Finding status` is `not reproduced` and runs one only when the user says so; `/comb:the-desert` skips them and lists them in its summary.
- **Shave checks the manifest's size across dispatch.** `wc -c` before and after the shavers return; a changed byte count stops the shave before `verify` would re-verify against altered text.
- help and the-desert describe the new contract; the-desert keeps every new check in a sweep and states that the three-FAIL stop is a halt, not a question.

### Removed

- **The trivial escape hatch.** After three FAILs on a trivial item the orchestrator could apply the fix inline, contradicting the ground rule that three failures mean something structural is wrong. Three FAILs now always stop and ask, trivial or standard (decision D3). With revert-before-retry the hatch was rarely reachable for a good reason anyway.

## [0.13.0] — 2026-10-11

Corrections and dedup from the family-lean review (four reports: a writing-skills pass and three adversarial lenses — token economy and deterministic tooling, fan-out risk, consistency and currency against the 5.5 model family). No new capability; the contract says the same things in fewer places.

### Changed

- **Dispatch prompts deliver the family's own artifacts by path, once.** The implementer prompt carried the instruction file by path and again in full; the fix-reviewer prompt carried it twice more and the implementer's reply twice; plan's non-code prompt embedded the report it also named. The delivery contract's paths-not-contents rule now applies to them, saving on the order of a thousand output tokens per fix item. Writers (planner, implementer, fix reviewer) get the focus brief verbatim, without the reviewer framing sentence that told them to "surface other issues" they have no slot for.
- **`/comb:the-desert` states each override once.** Models, deferral, confirmations, commits, config reuse, and the focus-brief flow live in one Overrides block; the comparison table, the per-step restatements, and the ground rules that paraphrased them are gone, as are two copies that had drifted ("only question" vs three allowed questions). The sub-skills reuse the config loaded in Step 1. Step announcements are emitted in the same message as the next step's first tool call, because a text-only turn ends the sweep.
- **The dispatch tool is `Agent`.** Every skill, shared block, and README said `Task`; Claude Code renamed it in 2.1.63 and the evals already used the new name. `WebFetch` is dropped from every `allowed-tools` list — no skill used it.
- **Restatements removed.** The merge-rule parentheticals beside the shared reference, configure's copy of the config layer list, the 6-subagent arithmetic, the unshipped skip-trivial-review paragraph, the scanner/shaver ineligibility sentence outside review, two of three Edge-case paragraphs, and the lists of build-manifest filenames (the project rule is "trust the model"). The review template's `TypeScript (tsc --noEmit)` row is now a generic typecheck/build row. Review also excludes the `implementer` role from the palette explicitly; it was eligible by the text.
- **User-facing text names config keys, not model aliases.** help, README, the-desert, and the fix announce line said opus/sonnet where the value is `models.*`; `opus` and `sonnet` now resolve to the 5.5 models, so the alias names were also misleading about which model runs.
- **Agent bodies no longer say "Same as code-reviewer"** for inputs and output format; the agent never sees that file. They name what the dispatch prompt provides.
- **`pattern-shaver`'s description carries triggers only**, per the rule applied to the skills in 0.10.0.
- **`/comb:plan` ends with a `Next:` line naming `/comb:fix <folder>`.** The summary had no next step, and in an eval run the model improvised one pointing at the model-only `fix-auto` skill, which cannot be typed.
- **The eval suite runs.** `claude plugin eval` became available for the maintainer's account on 2026-10-11 and the first live runs reshaped the suite: scaffold scripts are declared in a `case.yaml` beside each `prompt.md` (`context.scaffold_script`), every case lists its read-only tools in `allowed_tools`, and the run passes `--allow-tools Bash Write Edit` because gated tools cannot be granted by a case. Facts about tool calls (which agents were dispatched, with what prompt, what the orchestrator read) are now checked by `tool_used`, `file_exists`, and `regex` graders instead of an LLM judge, because the judge's trace view is the first and last 12 messages and a comb run is 40 to 100; the judge only confirms the final report. The verbatim help check is a regex. Five of six cases pass on macOS; `fix-reviewer-diff-scope` needs git, which the eval sandbox cannot run on a Mac (Apple's xcrun shim is blocked), so it passes only in CI on Linux. The CI eval job, README, PLAYBOOK, and `evals/README.md` carry the new flags and limits; `evals/results/` is gitignored.

### Fixed

- **Contradictions.** Review's ground rule said round N is "computed by counting existing reports + 1" while Step 8 said parse, never count (the 0.10.0 change missed the ground rule). The palette floor was 1 in three places and 2 in three others; it is 1 everywhere. The single-revise fix reviewer rule in Step 4 said "always consistency-auditor" with no fallback while 4e kept the fallback chain; Step 4 now defers to 4e. The-desert's "This is the only question you ask" contradicted its own three allowed questions.
- **Stale statements.** README's Status line was a release behind (now gated); `smoke.sh` still called itself an interim gate for a feature that shipped; `dispatch-delivery.md` asserted a `run_in_background` platform fact that is version-dependent (the instruction stands without it).
- **`check-contract.sh` needles.** Two of seven re-inline needles matched no current `shared/` text, so a copy of a live block passed the gate. Needles are now derived from each `shared/*.md` (its longest body line, which a body copy carries), plus the one historical needle. The gate also asserts README's version against plugin.json. Rules renumbered 1–7.
- **Evals.** The git-dependent case runs on macOS with a standalone git (Homebrew's) ahead of Apple's xcrun shim on the `PATH`; `evals/README.md` documents it and the earlier "Linux only" note is withdrawn. `fix-reviewer-diff-scope`'s only grader was an `llm` judge over the trace, which sees the first and last 12 messages and so could not observe the `HEAD~1` regression it names; `noncode-shortcircuit` had the same shape. Both now use `tool_used`/`file_exists`/`regex` graders for the middle of the run and a `last_message` judge for the summary. New graders: the plan summary ends with `Next: /comb:fix …` and never names `fix-auto`; the Agent call carries a `model`; the review report has `Verified:` lines; `.comb/excerpts` is empty at run end. Two new cases cover the `fix-auto` gate off and on (eight cases). CI pins `--model` and `--judge-model`.

### Added

- **Optional `effort` lanes.** Claude Code now takes an `effort` parameter on the Agent call, and the 5.5 models default to `medium`. comb passes nothing by default, so dispatched agents run at the session's effort; a project that wants more or less sets `effort.<lane>` (same keys as `models.*`) or `agents.<role>.effort`, and `effort.the_desert` coerces lanes in a sweep the way `models.the_desert` does. The accepted values are `low`, `medium`, `high`, `xhigh`, `max`; the parameter needs Claude Code 2.1.292 or later. No default was chosen because no measured run yet shows a higher setting finds more.
- **`scripts/replay-graders.py`.** Replays an eval case's `regex`, `tool_used`, and `file_exists` graders against a run kept with `--keep-temp`, so a grader can be fixed offline instead of by paid re-runs (the first eight-case run spent more on re-running cases to test grader edits than on the run itself). Stdlib only; bounds stated in its docstring. `scripts/test-replay.sh` runs it against fixture runs inside `check-contract.sh`. PLAYBOOK gains an "Eval cadence" section: gates every commit, the suite once per PR, one case for a confined change, replay for grader debugging, no eval for prose-only edits.
- `displayName: "Comb the Desert"` in plugin.json.

## [0.12.0] — 2026-10-10

### Added

- **`fix.model_invocation` and the `fix-auto` skill.** `/comb:fix` is user-only by frontmatter (`disable-model-invocation: true`), and Claude Code offers no way to override a plugin skill's frontmatter from settings or config, so a project that wants Claude to start the fix workflow from "apply the fixes" had to edit the installed file. A new model-only skill, `fix-auto` (`user-invocable: false`, so it cannot be typed as a slash command), reads `fix.model_invocation` (default `false`) and either stops with a message naming the observed value, `/comb:fix`, and the flag, or reads the fix skill from the plugin root and executes it unchanged, with every question, pre-flight check, and commit rule intact. Because the fix skill is loaded by Read, its plugin-root placeholder is not substituted; `fix-auto` carries the same expansion paragraph `/comb:the-desert` uses. The default refuses rather than doing nothing: the skill's trigger is in context in every project, so an un-opted-in "apply the fixes" gets the refusal message, not a code change. Claude Code treats a blocked `disable-model-invocation` skill as "do not reproduce it another way"; this skill is the sanctioned reproduction, which is why the default stays `false` and the gate lives in the skill body, not in a prompt.

### Fixed

- **`fix.commit_per_item` row** added to `/comb:configure`'s key table; it was missing.

## [0.11.0] — 2026-10-09

### Added

- **Per-run manifest excerpts.** `/comb:review`, `/comb:plan`, and `/comb:fix` no longer hand every agent the whole PATTERNS manifest. A consuming project reported a 188 KB / 18-section manifest costing every agent on the order of 50k tokens (reported as ~70k) before it opened the diff, multiplied across a 4–5 agent palette and again by `/comb:fix` and `/comb:the-desert`. Each run now cuts an excerpt with the new `scripts/manifest.py`: the header, the global sections (how-to-read, cross-reference map, drift register), and the area sections whose scope meets the change. Scope comes from a section's `Scope:`/`Home:` line (backticked path tokens; placeholders read as wildcards; prose lines count as absent) or from its `file:line` anchors (equality, or same directory when the section has no scope line); a section with neither always travels. The directory rule can over-include on sections that cite many directories and have no scope line; adding a `Home:` line to such a section is the documented way to tighten it. The excerpt opens with the omitted sections and their line ranges, so an agent that is pointed to one reads it with `sed -n` rather than reading the file. On that project's manifest a new entity-page diff yields a 19 KB excerpt; on the curated fixture a page diff yields 2.9 KB from 4.8 KB.
- **`/comb:patterns --shave`.** Trims an existing manifest without changing what it asserts, through a new `comb:pattern-shaver` agent (it writes one edit-script file and nothing else) (one per large section, at most five at a time) that writes an edit script in three classes only: a secondary anchor that pins the same claim as the canonical one, a bullet that restates a convention owned by another section (replaced by a pointer), and an in-section drift line whose every item is fixed. The script verifies every edit mechanically with a stated bound (exact once-in-section match, no heading removed, no citation vanishes from the manifest, the owner really cites it, no open marker or issue reference on a drift line, acyclic owners), tolerates an unparseable shaver file without losing the others, prints one gate with no default reply, applies all-or-nothing, and stamps the header. Prose rewriting and directive-echo removal were considered and rejected: both let a shaver change meaning while passing every mechanical check. Rules live once in `shared/shave-rules.md`.
- **A size line on every manifest write**, with a notice above 100 KB suggesting `--shave`. Fixed threshold; a correctness-adjacent notice does not get a knob.
- **`scripts/test-manifest.sh`**: 69 expectations over a template-shaped and a hand-curated manifest fixture (numbered headings, placeholder Home lines, basename anchors, an emoji-prefixed drift register, a ` / ` heading, a long provenance line), with one failing edit file per verify check. Runs inside `check-contract.sh` and CI. An eval case, `manifest-slice`, guards the excerpt delivery end to end.

### Changed

- **The orchestrator never reads the manifest.** The old load step read the file to compute `cited ∩ touched`; the script now computes staleness from the manifest's anchors (basenames resolved through their section's directories), reports `stale: unknown` instead of failing when the base commit is unreachable, and treats an empty intersection as not stale rather than running a pathspec-free `git diff`. The old wording is a contract-gate needle so a full read cannot return.
- **Observed-baseline delivery has two forms.** With an excerpt: the excerpt path and the full path, plus three sentences telling the agent to read an omitted section by range and never the whole file. Without one (no `python3`, or the script failed to write): the v0.10.0 block unchanged, with a printed notice. Never silent.
- **Working files live under `.comb/`** in the working directory, created by the script with a self-ignoring `.gitignore`, so they never appear in `git status`, never trip `/comb:fix`'s dirty-tree pre-flight, and need no change to a project's ignore rules. A temp directory outside the working directory was rejected because reading it would prompt every agent.
- **Command lines live in skill bodies, contracts in `shared/`.** `${CLAUDE_PLUGIN_ROOT}` is substituted in skill and agent bodies only, so a command line in a shared block would expand to nothing at the shell.
- **The manifest format is unchanged.** Every manifest written since v0.7.0, and hand-curated ones, work as before. Generating a cross-reference map and a drift register from `/comb:patterns` was deferred; the consumers recognise hand-written ones.

## [0.10.0] — 2026-09-01

### Added

- **`shared/` contract blocks.** Four blocks that were copy-pasted across the skills — config loading (×6), the focus-brief directive matcher (×4), the dispatch delivery contract (×5), and the observed-baseline paragraph (×6) — now live once under `shared/*.md`, read at runtime via `${CLAUDE_PLUGIN_ROOT}`. Copy drift had already produced a real contradiction (the stale reviewer rule fixed below); one source removes the failure class. The runtime contract is now the skill bodies plus `shared/*.md`.
- **An eval suite and release gates.** `evals/` carries five behavioral cases in the `claude plugin eval` format, one per known regression class: help verbatim output, `null`-as-delete config merge, the-desert's non-code short-circuit, the fix reviewer's diff scope (the v0.9.0 `HEAD~1` bug class), and path-based dispatch delivery. The eval feature is early access; until enabled, `scripts/smoke.sh` is the interim behavioral gate. `scripts/check-contract.sh` greps the shipped contract deterministically (no dead citations, shared references resolve, no re-inlined blocks, no `.DS_Store`). CI runs `claude plugin validate` + the contract greps on every push; evals run on manual dispatch. The README documents the gate order.

### Changed

- **Directives and the PATTERNS manifest reach every agent as file paths — the embed branch is gone.** The old contract embedded the full directive corpus (~600 lines) into every foreign-agent dispatch, and the *default* implementer (`general-purpose`) is foreign, so every `/comb:plan` and `/comb:fix` writer dispatch paid it. An agent that cannot read files cannot review or fix code, so embedding bought no robustness. Foreign agents now get the same paths plus an explicit authority instruction and a specialty statement.
- **Model delivery is stated, not implied.** The skills resolved a model from config but never said how to apply it; if the orchestrator did not pass it, the agent frontmatter's `model: opus` silently won and `models.*` config did nothing. Every dispatch site now says: pass the resolved model as the Task call's `model` parameter, which overrides agent frontmatter.
- **`/comb:the-desert` states its sub-workflow mechanism.** "Run the `/comb:review` workflow" left the mechanism to guesswork — invoking the Skill tool would load conflicting wait-and-present instructions. Each step now says: read the sub-skill's `SKILL.md` from the plugin root and execute it with the overrides, which win on conflict.
- **Skill descriptions carry triggers only.** A description that summarizes the workflow invites the model to follow the summary instead of loading the body; all seven descriptions now state when to invoke, not what the steps are.
- **Review round numbering parses instead of counts.** `N` is now the highest round parsed from existing report filenames + 1; counting files collided with a surviving later round after a deletion.
- **Version-history asides removed from user-facing text.** Help and README no longer explain v0.4.x behavior to readers who never saw it; the README also states plainly that reviewer read-only is enforced by instruction (Bash remains available), not by sandbox.

### Fixed

- **`/comb:the-desert` dispatched the wrong fix reviewer.** Its Step 5 still hardcoded `test-auditor` as the reviewer for every item — the v0.4.x rule — contradicting `/comb:fix` Step 4e's specialty matching (v0.5.0) and the-desert's own ground rule that it overrides only transitions, models, deferral, and confirmation. It now defers to the fix skill's specialty rule.
- **Dead spec citations removed.** 28 lines cited `spec §N` / `decision §N` from a design spec that is gitignored and does not ship, so the runtime model could never open them. Every cited rule was already stated inline; the citations are gone, and the contract grep keeps them out.

## [0.9.0] — 2026-09-01

### Added

- **A verification gate at `/comb:review`'s consolidation step.** Step 7 previously deduplicated agent findings and wrote the report; it carried no instruction to check anything. Verification was required at the agent tier and again at the plan tier, and absent at the tier between them — so every finding crossed one ungated step on its way into the only artifact in the chain that reads as settled. Agent output is a proposal, and instruction files run against real code; the report is neither proposed nor executed, just believed. The step now opens each cited line before it writes the anchor and takes the number from a numbered read rather than by counting rows, recomputes every count and every all/none/only claim, and refuses to state an untraced fix shape in the report's voice. The consolidator's own syntheses — a merged description, a cross-agent count — get the same treatment, because no agent wrote them. The gate is bounded on purpose: it reads the cited locations and recomputes the stated quantities, and it is explicitly **not** a second review — it does not re-derive findings, re-litigate severity, or hunt for what the agents missed.
- **A `Confidence` field on every reviewer finding.** The five reviewer agents had no channel for uncertainty. An agent that inferred a line range, estimated a count, or could not open a file had no way to say so, and the consolidator had no way to learn it. Each finding now carries `Verified`, or `Unverified — <the specific gap>`. The field is declared once in `comb:code-reviewer`'s output format, which the other four inherit, and once in the review dispatch prompt's output-format spec so a foreign agent gets the same contract.
- **An `Unverified:` line on every `/comb:fix` reviewer verdict.** The fix reviewer is the tier that turns a verdict into a merged commit, and it had no channel for doubt: its output format asked for a confirmation of what it verified, and the decision rule was strictly binary, so a reviewer that could not confirm a step had to pick a side without saying so. Every PASS and FAIL now carries `Unverified: <the step, outcome, or scope claim you could not confirm, and why>`, or `Unverified: nothing` when the whole `## How` was confirmed against the diff. The decision rule gains a matching clause — a step you could not verify is not a FAIL on its own — so a limit of the reviewer's does not become a spurious FAIL that counts toward the three-failure escalation. Step 4f consumes the line: a PASS that names a gap announces as `PASS (partial verification: …)` and carries the note into the end-of-run summary. It is a log line, not a gate; it does not block the commit, trigger a retry, or ask the user anything, so `/comb:the-desert`'s no-pause contract holds.
- **A `Verified:` line on every finding in the report.** Both templates — code-shaped and non-code — require it. It must name the check rather than the act: `Read foo.ts:118-126; recomputed the count (4 of 5)` counts, `verified against source` does not. It states both halves, what was confirmed and what was not.

### Changed

- **`/comb:plan` reads the `Verified:` line and acts on it.** The planner extracts the line with the rest of the finding, receives it verbatim in its dispatch prompt, and re-derives from the code anything the line names as unchecked. A fix shape the review marked unverified is a proposal to evaluate, not a spec to transcribe. Where the planner's instruction contradicts an unverified particular, it says so and supplies the corrected one. A report written before this field existed carries none; the planner then treats every particular as unconfirmed.
- **`/comb:the-desert` records that the gate survives the sweep.** The gate asks the user nothing, so the no-pause contract holds. The ground rule is written down so a future maintainer does not strip it for speed.

### Fixed

- **The `/comb:fix` reviewer read the wrong diff.** Step 4e told the reviewer to run `git diff HEAD~1` when `fix.commit_per_item` is on, on the stated grounds that "the previous commit is the implementer's per-item commit". It is not: Step 4f.1 commits only after a PASS, so at review time the item's changes are still uncommitted and `HEAD` is already the state before this item. `HEAD~1` therefore reached one commit too far back and pulled the previous item's committed changes into the reviewer's view — a false scope violation, and a FAIL that counts toward the three-failure escalation. It fired whenever two items touched the same file, which `/comb:plan` groups for by design, and it failed outright on the first item of a single-commit repository. The command is now `git diff HEAD`, with the rationale corrected and the path-scoping argument for parallel batches made explicit.
- **A file the implementer created was invisible to the reviewer.** `git diff` never lists an untracked path, so a new file — the normal outcome of a test-gap fix — produced an empty diff under both branches of the old instruction. The reviewer now runs `git status --porcelain` over the same paths and reads any path marked `??` in full instead of diffing it.
- **`/comb:plan`'s non-code branch had no verification instruction.** The code-shaped branch carries a failure-mode-trace instruction; the consolidated revise-doc branch carried nothing. A revise-doc quotes the spec's current text and cites a section anchor, and both are exactly the particulars that go stale. The planner now opens the spec at each cited anchor, confirms the quoted text, and records any correction in that revision's **Reason** line.

## [0.8.0] — 2026-06-02

### Added

- **Interactive steering in `/comb:patterns`.** Generation is no longer a single area gate followed by an automatic scan. The flow now batches everything the user can steer into one scan-plan gate — areas and path scopes, a directive→area mapping, a directive-currency check, and a list of non-authoritative regions to exclude — then opens two more user-driven steps *only when warranted*: a per-conflict reconciliation walk and a pre-write review. Every gate keeps a safe `go`/`write` default, so a clean repo still completes in one pass.
- **Non-authoritative region exclusion during recon.** Recon now detects and sets aside generated/build output, vendored code, and reference-only/legacy directories (read from `CLAUDE.md` statements and conventional names like `mockup/`, `legacy/`, `archive/`), proposing them as excluded at the gate. This prevents a scanner from laundering dead or pre-framework code into the manifest — the same failure class as the drift fix below, one level up. The user can re-include any region.
- **Per-area directive mapping and a currency check.** Directives are mapped to the areas they govern, and each scanner receives only its relevant subset — tighter lenses, less noise than sending every directive to every scanner. A one-line currency prompt lets the user down-weight a superseded or draft directive; a widespread practice that conflicts with a down-weighted directive is then recorded as the codebase's current norm rather than flagged as drift. Directive authority is decided **only at this gate** — a scanner never disregards a directive on its own judgment (e.g. from a draft-sounding title) — and recon pre-flags any directive that self-marks as draft/WIP as a *suggested* down-weight for the user to confirm.
- **Interactive conflict reconciliation (Step 7).** When a scanner reports a *dominant* practice that conflicts with an authoritative directive, `/comb:patterns` now walks the user through each conflict — (a) the directive is stale → record the practice as the new canonical norm, (b) it's drift → keep the directive's expectation and list the offending files, or (c) skip — and writes the chosen outcome into the manifest immediately. Replaces the previous passive end-of-run warning block, which changed nothing in the artifact and relied on the user circling back later.
- **Pre-write review and single-area re-scan (Step 8).** Before writing, a compact per-area summary flags thin or empty areas (a mis-scope signal) and offers to re-scan one area with a new scope, or to cherry-pick sections on a regenerate — all without a full re-run.

### Changed

- **`comb:pattern-scanner` conflicts channel tightened to dominant-only, with a pinned denominator.** The scanner now emits a `## Directive conflicts` section only when at least one *dominant* practice conflicts with an authoritative directive; a minority deviation is never placed under that heading in any form, annotated or otherwise. "Dominant" is measured against the area-wide population of that lens — never narrowed to a single component where the deviation happens to be universal, which would gerrymander a minority into a false dominant and trigger a spurious reconciliation prompt. The orchestrator adds two backstops: it drops any conflict that self-identifies as a minority, and any whose own text reveals the rest of the area follows the directive ("every other variant uses…", "the lone exception"). Closes both a placement slip and a denominator-gerrymandering misclassification found in testing.

### Fixed

- **PATTERNS manifest no longer launders drift into convention.** During generation, `comb:pattern-scanner` previously treated directives as topic *lenses* only, so a practice that deviated from an up-to-date directive could be recorded as a "new or improved pattern" even when the rest of the area followed the directive. Repeated regeneration would then bake that drift into the baseline. The scanner now treats directives as the authoritative baseline and classifies each candidate convention: conforming or net-new conventions are recorded; a *minority* deviation from a directive is drift and is dropped in favor of the directive-conforming norm; a *dominant* directive-conflicting practice is recorded as the directive-conforming expectation and the conflict is routed to a new out-of-band `## Directive conflicts` channel that `/comb:patterns` surfaces to the user (never written into the manifest) so a human reconciles it — a stale directive versus systemic drift look identical from inside one area.
- **Consumption stance now subordinates the manifest to directives.** The "Project conventions (observed baseline)" block injected by `/comb:review`, `/comb:plan`, and `/comb:fix` gains an explicit precedence rule: project directives outrank the manifest, a divergence that violates an up-to-date directive is drift no matter how widespread, and classifying a change as a deliberate improvement or new canonical never excuses a directive violation. The manifest banner reflects the same precedence.

## [0.7.0] — 2026-05-29

### Added

- `/comb:patterns` — a new interactive command that scans the codebase and writes a **PATTERNS manifest** (`paths.patterns`, default `docs/combs/PATTERNS.md`): a project-specific record of concrete conventions — structural patterns, naming & vocabulary, closed token/enum sets, abstraction calibration, reuse points, error/async patterns, and testing conventions — each with real `file:line` references. Generation does codebase recon, proposes scan areas, waits for the user to confirm, then dispatches one read-only `comb:pattern-scanner` agent per area in parallel and synthesizes an area-major manifest. Regeneration over an existing manifest is diff-then-confirm so hand-edits survive.
- `comb:pattern-scanner` — a new read-only agent (generation-only) that maps one codebase area and returns concrete conventions with code references.
- `paths.patterns` and `models.patterns` config keys, both editable via `/comb:configure`.

### Changed

- `/comb:review`, `/comb:plan`, and `/comb:fix` now load the PATTERNS manifest (when present) and inject it into agent dispatch as a **"Project conventions (observed baseline)"** block — a prior the reviewers reconcile against live code, never the sole authority. Where manifest and code conflict, live code wins; a manifest silent on an area sends agents back to reading the code (not "anything goes"); and deliberate improvements or new canonical patterns are recognized rather than flagged as drift. An absent manifest is a graceful no-op.
- Two non-blocking refresh signals: a commit-based staleness note (the manifest cites files that changed since its base commit) and a semantic refresh note (a reviewer judged the diff evolves a convention). `/comb:the-desert` prints both as log lines without pausing; it inherits the manifest but never regenerates it, and `models.the_desert` does not coerce `models.patterns`.

## [0.6.0] — 2026-05-12

### Added

- **Right-sized review apparatus.** `/comb:review` now reads the work before picking agents and emits a one-paragraph characterization, a stated lens, and a `code-shaped | non-code` classification. The classification conditionally turns off the verification table, severity scale, verdict block, and the full report template — non-code artifacts (spec docs, design docs, prose) get a condensed report with a flat labelled findings list. Code-shaped diffs behave as before.
- **Spec-as-artifact lens in `consistency-auditor`.** New step 2.6 explicitly frames the agent's work when the artifact under review *is* the spec, with working questions for pattern-breaking, reusability gaps, implicit quality issues, ambiguities, and blind spots.
- **Lens framing in dispatch prompts.** The 5-part dispatch order grows to 6: a new part 2 carries the orchestrator's characterization, the lens to apply, and an explicit bias guard ("you are reviewing work produced in another session"). Helps reviewer agents stay anchored to the artifact rather than the orchestrator's narration.
- **`/comb:plan` single revise-doc on non-code reports.** When the input report is non-code, plan emits a single `revise-{spec-stem}.md` instead of per-finding instruction files — the implementer applies all revisions to one spec file in one pass.
- **`/comb:fix` single-revise-doc execution branch.** Detects the revise-doc folder shape and dispatches one implementer + one consistency-auditor reviewer + one commit for the consolidated revisions.

### Changed

- **`/comb:the-desert` short-circuits on non-code artifacts.** Stops after review; does not auto-run plan or fix on prose. Surfaces findings for the user to integrate into the next round of their design conversation.
- **`code-reviewer.when_to_use`** narrowed from `"Always"` to `"When the diff contains executable code"`. Anchor agent for code-shaped diffs only.
- **`consistency-auditor.when_to_use`** broadened to include "OR is itself a spec/design/prose artifact whose conformity to codebase patterns and directives needs to be assessed". Anchor agent for prose-only diffs.
- **`code-reviewer` opening step.** New step 0 instructs the agent to confirm the artifact is in its lane before drafting findings; on a non-code artifact the agent returns LOOKS GOOD with a one-sentence "outside my specialty" note instead of padding findings.

### Removed

- **Markdown-only auto-detection in `/comb:review` Step 4.** Subsumed by the new "Read the work" step (Step 3.5), which makes a single classification judgment rather than a file-extension check. The header note about "Markdown-only diff — palette restricted" is no longer emitted.

## [0.5.3] — 2026-05-08

### Changed

- **Distribution moved to a dedicated marketplace.** The plugin is now distributed via [`olioskar/claude-plugins`](https://github.com/olioskar/claude-plugins) (marketplace name: `olioskar-marketplace`), not from this repo's `.claude-plugin/marketplace.json`. The in-repo `marketplace.json` has been removed; this repo is now solely the plugin source. The dedicated marketplace can host additional plugins as they're authored — adding a plugin is a single entry in the marketplace's `plugins[]` array.

### Migration

The plugin had no public users at the time of this change (no announcements, no installs in the wild beyond the author's own test sessions). If you're testing against this plugin and previously added the same-repo marketplace:

```
/plugin marketplace remove comb-marketplace
/plugin marketplace add olioskar/claude-plugins
/plugin install comb@olioskar-marketplace
```

The plugin's behavior, config schema, and skill bodies are unchanged in this release.

## [0.5.2] — 2026-05-08

### Changed

- **Reviewer calibration step.** Each of the five `comb:*` reviewer agents (`code-reviewer`, `simplifier`, `silent-failure-hunter`, `test-auditor`, `consistency-auditor`) now ends "How to work" with a final Step that requires self-calibration before publishing findings. The check is specialized per agent (real failure mode / real complexity cost / real silence / real coverage gap / real divergence with consequences) and reframes LOOKS GOOD as a positive deliverable rather than a missed opportunity. Addresses the diminishing-returns problem in multi-round `/comb:the-desert` sweeps where reviewers default to producing output even when the diff is clean.
- **`/comb:the-desert` recommends whether to run again.** The end-of-sweep "run again?" prompt now quotes the round's severity counts and gives an honest read: Critical/High → yes; only Medium/Low/Test gaps → judgment call; clean round → stop. The user still decides; the orchestrator just provides a recommendation so the loop can terminate confidently when noise is all that's left.

## [0.5.1] — 2026-05-08

### Changed

- **`consistency-auditor` sharpened on feature completeness.** Step 2 (spec/plan alignment) now requires a per-requirement checklist (DONE / PARTIAL / MISSING / N/A) with PARTIAL and MISSING items surfaced as findings. Flags TODO/FIXME placeholders that the spec required real implementation for.
- **No-spec intent reconstruction.** New Step 2.5 in `consistency-auditor` instructs the agent to reconstruct intent from evidence (PR description, commit messages, test names/assertions, TODO/FIXME comments, surrounding code patterns, UI behavior) when no formal spec is supplied. The reconstructed intent is treated as the de-facto spec, and the same completeness checklist runs against it. Replaces the prior "fall back to pattern consistency" behavior, which abandoned completeness review entirely.
- **`directives/consistency.md` §3** extended with sub-rule 4 (no-spec intent reconstruction) — the citation handle for the new agent behavior.
- **`/comb:review` shared-context block** now includes `PR description:` so all agents (not just consistency-auditor) can lean on the PR body as an intent signal.

## [0.5.0] — 2026-05-05

### Added

- **`agents.implementer` config field.** New writer-capable agent slot used by `/comb:fix` and `/comb:plan` for any task that writes files. Defaults to `general-purpose` (Claude's built-in writer-capable subagent). User-overridable per-project. Replaces the broken v0.4.x picker that resolved to read-only `comb:*` review agents and caused real-world fix runs to fail (G4 implementer refused to write, G6 escalated, G8 applied inline by orchestrator without authorization, 2/9 plan agents returned content inline).
- **`fix.commit_per_item` config flag** (default `true`). Orchestrator commits each item's changes on reviewer PASS, with `<finding-code>: <title>` message. Solves the cumulative-diff false-positive problem (reviewer scope-creep flags from prior items leaking into the current diff). Opt out with `false` to keep the v0.4.x no-commits behavior.
- **Pre-flight check on dirty tree.** New Step 1.5 in `/comb:fix`. If the working tree is dirty when the run starts, a one-shot question asks: commit / stash / proceed-without-commits / abort. In `/comb:the-desert`, the question is the third allowed question (alongside scope-at-start and run-again-at-end), and only fires when dirty.
- **Specialty-matched fix-reviewer.** Plan files gain a `**Specialty:**` header line carrying the source-agent info from the review report. `/comb:fix` Step 4e routes the reviewer to the matching specialty (e.g., `consistency-auditor` for scope/pattern findings, `silent-failure-hunter` for error-handling findings) rather than always dispatching `test-auditor`. Fallback chain: `agents.test-auditor` → `agents.code-reviewer`.
- **`## Considered alternatives` section in plan files** (optional). ADR-style appendix listing rejected approaches with one-line "rejected because…" rationale. Main body remains the single executable path; alternatives are documentation only.
- **Trivial-only escape hatch.** After 3 implementer failures on an item classified trivial, the orchestrator may apply the fix inline. The reviewer step still runs. Standard items that hit 3 failures escalate to the user as before. Documents the prior undocumented G8 inline-edit behavior with safer bounds.

### Changed

- **`/comb:fix` reviewer's role is now strict plan-compliance.** The reviewer reads the plan, the implementer's report (including any new `## Divergences` section), and the actual diff; decides PASS/FAIL on whether the plan was executed (or whether reported divergences are justified). Was previously a more general "did the fix work and stay in scope" lens biased toward `test-auditor`'s specialty.
- **Implementer report format adds `## Divergences` section** (optional). Implementers list deviations from the plan's `## How` with one-line rationale per deviation. The reviewer evaluates each rationale rather than re-litigating the fix's design.
- **Planner-quality nudge.** `/comb:plan` dispatch prompt now asks the planner to mentally trace through the proposed fix's failure modes before recommending — particularly when correctness depends on a runtime invariant (closure state, async timing, render scheduling). Directly addresses the G6 case where Option A passed plan but failed structurally.
- **Picker default in `/comb:fix` Step 4d** changed from `code-reviewer` to `agents.implementer`. The role-from-config picker still picks a specialty *lens* for prompt framing, but the writer that actually runs is `agents.implementer`.

### Migration

All changes are additive at the config layer. Existing user configs deep-merge against the new defaults — no migration required. Users who explicitly worked around the v0.4.x bug by mapping `agents.<role>.subagent_type: "general-purpose"` should remove the override after upgrade; the new default kicks in cleanly. Users who prefer the v0.4.x no-commits behavior set `fix.commit_per_item: false`.

## [0.4.3] — 2026-05-05

### Fixed

- **`D`-code collision between Deferred (review) and Discovered (fix).** Both severities used `D1, D2, …` — a fix run that discovered new issues would have overwritten the review's deferred-item plan files. Discovered items now use `X{n}` ("extras found during execution"). Deferred items keep `D{n}`.
- **Branch slug for review filename.** Branches with `/`, whitespace, or other path-unsafe characters (e.g., `feature/foo bar`) would have written to a malformed report path (`branch-feature/foo bar-round1-report.md`). The Step 8 naming rule now slugifies the branch name (`/` and unsafe chars → `-`, collapse runs, trim trailing).

### Changed

- **Group naming convention codified.** `/comb:plan` Step 4 now specifies `G{n}` for grouped findings, sequential in user-acceptance order. Step 6 file-naming rule references this. Earlier versions left the group code as the planner's invention (your tero run picked `G1, G2, G4`); future runs will be deterministic.
- **`docs/superpowers/specs/2026-04-27-comb-the-desert-plugin-design.md` marked historical.** The spec was authoritative for v0.1.0; the plugin has evolved past it. Added an "Update 2026-05-05" note pointing readers to README/CHANGELOG/skill bodies as the current source of truth. The spec is retained for design rationale.

## [0.4.2] — 2026-05-05

### Changed

- **Trim 0.4.1's over-correction.** Replaced the per-language operator/syntax enumerations in `silent-failure-hunter.md` and the 13-row manifest+commands table in `/comb:review` Step 5 with abstract patterns and a flat manifest list. The model already knows that `?.` is JS/TS, `unwrap_or` is Rust, and `composer test` belongs to PHP — listing them inline added tokens without adding judgment. Same paradigm-spanning behavior, less prompt weight.

## [0.4.1] — 2026-05-04

### Changed

- **`silent-failure-hunter` is now language-neutral.** The agent prompt previously listed JS/TS-specific operators (`??`, `||`, `?.`, `.catch()`, "unhandled promise rejection", `console.error`) as fallback and async-error patterns. Generalized to span Rust (`?`, `unwrap_or`, `let _ = result`), Go (`_, err := …`, ignored returns), Python (`or`, `except: pass`), Java/C#/PHP (empty `catch {}`), and JS/TS (still covered). The agent will now reason about silent failures equally well across paradigms.
- **Review verification step recognizes more ecosystems.** The manifest list in `/comb:review` Step 5 was Node/Python/Rust/Go only. Extended to a tabular form covering PHP (`composer.json`), Ruby (`Gemfile`), Java/Kotlin (`pom.xml`, `build.gradle`), .NET (`*.csproj`), Elixir (`mix.exs`), Swift (`Package.swift`), Dart/Flutter (`pubspec.yaml`), and C/C++ (`Makefile`, `CMakeLists.txt`). The graceful-degrade fallback ("skip with a note rather than run unrelated tooling") still applies for unrecognized manifests.

## [0.4.0] — 2026-05-04

### Added

- `/comb:help` skill — overview of the plugin and command list. Pass a command name (e.g., `/comb:help fix`) for a per-command deep dive (inputs, what it does, where output lands, examples). Covers all six commands.

## [0.3.1] — 2026-05-04

### Changed

- **Generalize examples in directives and agents.** Three files used domain-specific examples that leaked from the originating codebase: `consistency.md` referenced "Jobs page" and "worksites"; `reusability.md` named `formatRowDateForGrid`; `consistency-auditor.md` repeated the "Jobs page" example. Replaced with universal SaaS placeholders (Customers page, customers/clients/accounts, `formatDateForCustomerList`) so the examples remain concrete and teachable without pinning to one project.

## [0.3.0] — 2026-05-04

### Changed

- **Plan output template** — every `/comb:plan` instruction file now leads with a header block (`**Severity:**`, `**File(s):**`, optional `**Consolidates:**` for groups) and ends with a `## Directive citations` footer that lists every plugin directive, user directive, and project-level authoritative doc (CLAUDE.md, MEMORY.md) the fix relies on. The six body sections (What / Why / Where / How / Expected Outcome / Scope) are unchanged but now use H2 headings to match the H1 file title. Real-world output from a v0.2.0 run already converged on this shape — codifying so it ships consistently.
- **Deferred items get plans.** `/comb:plan` no longer skips Deferred findings. They were already documented as "every item gets a file" in Ground rules, but the planner was reading the prose framing as out-of-scope. Step 3 is now explicit: include Deferred, auto-number with `D1`, `D2`, … if the report uses bullets without codes.
- **Review reports give Deferred items D-codes.** `/comb:review` now numbers Deferred entries (D1, D2, …) using the same `**{code} — {title}**` shape as other severities, so `/comb:plan` can hand each one to an agent without retrofitting codes.

## [0.2.0] — 2026-05-04

### Added

- `/comb:configure` skill — conversational editor for `comb.config.json`. Resolves the right scope file (project or global), shows the merged effective config, translates natural-language asks ("disable test-auditor", "use sonnet for plan") into the JSON edit, shows a diff, writes, and verifies. Honors the same merge semantics as the rest of the plugin (deep-merge, null-as-delete, hard-fail on bad JSON).

### Fixed

- `marketplace.json` `source` field: `"."` → `"./"`. The bare-string form was rejected by Claude Code as an unsupported source type; relative paths require the leading `./` per the plugin-marketplaces docs.

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
