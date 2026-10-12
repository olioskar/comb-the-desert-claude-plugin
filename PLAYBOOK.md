# Playbook

How this plugin is developed. It describes the current process, not its history. When the process changes, edit this file.

## Where things live

- `skills/*/SKILL.md` and `shared/*.md` are the runtime contract. A behavior change is a change to one of these.
- `agents/*.md` holds the reviewers, the writer, and the two manifest agents.
- `directives/` holds the shipped policy.
- `config/defaults.json` holds the config keys and their defaults.
- `scripts/manifest.py` and `scripts/comb.py` are the helpers the skills call. `scripts/test-manifest.sh` and `scripts/test-comb.sh` pin their output, so change a script and its fixtures together.
- `evals/` holds the behavioral suite and `experiments/` the two-arm runs.
- `CHANGELOG.md` is the only version history users see.
- `docs/` is gitignored. It holds specs, plans, review reports, and the session-continuity files described below.

## The loop

1. **Design.** Non-trivial work starts with a dated spec in `docs/superpowers/specs/`. Agree on it before planning.
2. **Plan.** Turn the spec into a plan in `docs/superpowers/plans/` with one task per commit. Each task's test or check is written before the change and seen to fail.
3. **Branch.** Work on a feature branch. `main` changes only through pull requests.
4. **Execute.** Make one commit per task. An approved plan plus "go" authorizes those commits. Record any deviation from the plan, with its reason, in the execution ledger.
5. **Review.** Before execution, independent subagents on the strongest available model review the spec and the plan. Before release, they review the branch.
   - Brief each reviewer with the files, not with conclusions.
   - Give each lens its own reviewer. A code change gets two lenses: the contract, and the scripts and tests. A prose change gets one.
   - Reports go to `docs/combs/reviews/`.
   - Never review the plugin with its own `/comb:*` commands.
   - Fix the Critical and Important findings in one pass, each fix proven by a check that failed first. Fix Minor findings, or record them as deferred.
6. **Gate.** Run the release gate. Fix what it finds and skip nothing.
7. **Release.** Add the changelog entry. Bump `version` in `.claude-plugin/plugin.json` and the README Status line together; the gate checks they match. Push only on the maintainer's go. Then open the PR; the maintainer merges.

Small fixes skip steps 1 and 2, never 3 to 7.

## Release gate

1. `claude plugin validate .`
2. `scripts/check-contract.sh`
3. `claude plugin eval . --scaffold --ablation none --runs 1 --allow-tools Bash Write Edit`. On macOS it needs a standalone git, such as Homebrew's, first on the `PATH`. `evals/README.md` explains the flags.

`scripts/smoke.sh` is the offline structural check. CI runs gates 1 and 2 on every push and PR. Evals run on manual dispatch.

### Eval cadence

The suite costs money, so it runs only when behavior can have changed.

| Situation | What to run | Cost |
|---|---|---|
| Every commit | Gates 1 and 2, plus `scripts/smoke.sh` | Free |
| Every PR that can change behavior, before merge | The full suite (gate 3) | About 5 USD |
| A change confined to one area | That area's case, with `--case <name>` | About 1 USD |
| A prose-only edit | No eval | Free |
| Debugging something outside the plugin | No eval | Free |
| A grader that looks wrong | See below | Near free |
| Removing a guard passage from a prompt | A two-arm run in `experiments/`; see below | A few USD |

**A grader that looks wrong:** run that case once with `--keep-temp`. Then fix the grader offline with `python3 -I scripts/replay-graders.py evals/<case> <kept dir>`. Never re-run a paid case to test a grader edit.

**Removing a guard passage:** the control arm runs the plugin as shipped, and the treatment arm runs it with only that passage removed (`--eval-dir experiments`). The passage goes only if the treatment shows the failure does not recur. `experiments/README.md` records each result.

If the eval runner itself fails, report it and stop. Do not spend tokens debugging the runner.

## Design rules

Each rule came out of a past review. Check them when changing the contract.

- **Single source.** A block shared across skills lives in `shared/`. Never copy one back into a skill; the contract check catches it.
- **Every tier that produces an artifact a later tier trusts also verifies it.** Agent output, the consolidated report, plan instructions, and fix verdicts each have their own gate.
- **A gate states its bound.** If a gate doesn't say what it skips, it turns into a second review.
- **Correctness properties get no config knobs.** Config covers paths, models, agents, and commit behavior. A correctness gate that can be switched off fails silently.
- **Moving text moves its checks.** When a passage moves (prompt to brief, prose to script), update every grader, gate needle, and pointer that matched it.
- **Trust the model.** Prompts state concepts, not per-language catalogues. A fix that adds thirty lines of examples is the wrong fix.
- **Domain-neutral examples.** Shipped files name no specific product, team, or codebase.
- **No dead citations.** Shipped files never cite a document that does not ship.
- **Descriptions carry triggers.** A skill description says when to invoke the skill; the body says what to do.
- **Generation-only roles say so in `when_to_use`.** Review and plan pick roles by reading that field, so it is the one place a role opts out of the review, plan, and fix palette.

## Writing conventions

- **Changelog.** Keep a Changelog and SemVer, newest first. Each entry leads with what changed, then why.
- **Commits.** `type(scope): summary`. Release commits are `docs(release): vX.Y.Z — <theme>`.
- **Prose.** Plain and grounded, with no marketing language and no fields, knobs, or sections nobody asked for.
- **Scope.** Make the change asked for. Flag other opportunities without acting on them.

## Session continuity

Work spans many sessions. Three untracked stores under `docs/` let the next session pick up where the last one stopped:

- **`docs/handover/<session-name>.md`** is a snapshot of one line of work: what is in progress, done, next, and unresolved. Rewrite it at each milestone and before the session ends.
- **`docs/handover/ledger.md`** is append-only, with one dated line per event.
- **`docs/memory/`** holds one durable fact per file, indexed by `docs/memory/README.md`.

At session start, read the handover, the tail of the ledger, and the memory index. The handover file takes the session's name. If the session has no name, stop: suggest a name, or list the existing handovers. Never guess.
