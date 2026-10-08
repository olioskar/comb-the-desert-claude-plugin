# Playbook

How this plugin is developed. It describes the current process, not its history. Edit it in place when the process changes.

## Where things live

- `skills/*/SKILL.md` and `shared/*.md` are the runtime contract. A behavior change is a change to one of these.
- `agents/*.md` are the reviewer and scanner subagents. `directives/` is the shipped policy corpus. `config/defaults.json` is the config schema and defaults.
- `CHANGELOG.md` records behavior changes per release. It is the only version history users see.
- `docs/` is gitignored. It holds working material: design specs, plans, comb reviews, and the session-continuity files described below.

## The loop

1. **Design.** Non-trivial work starts with a dated design spec in `docs/superpowers/specs/`. Agree on it before planning.
2. **Plan.** Turn the spec into a plan in `docs/superpowers/plans/`, one task per commit.
3. **Branch.** Work on a feature branch. `main` changes through pull requests.
4. **Execute.** One commit per task. An approved plan plus "go" authorizes those commits; confirm the commit policy once at the start, not per commit.
5. **Review.** Run `/comb:the-desert` (or `/comb:review` → `/comb:plan` → `/comb:fix`) over the branch. Reports land in `docs/combs/reviews/`.
6. **Gate.** Run the release gate. Fix what it finds; do not skip a step.
7. **Release.** Add the changelog entry, bump `version` in `.claude-plugin/plugin.json`, open a PR, merge.

Small fixes skip steps 1–2, never 3–7.

## Release gate

In order:

1. `claude plugin validate .`
2. `scripts/check-contract.sh`
3. `claude plugin eval . --scaffold`, or `scripts/smoke.sh` while evals are unavailable for the account.

CI runs 1–2 on every push and PR. Evals run on manual dispatch.

## Design rules

Each of these came out of a past review. Check them when changing the contract.

- **Single source.** A block shared across skills lives in `shared/`. Never re-inline one; the contract grep catches it.
- **Every tier that produces an artifact a downstream tier trusts verifies it.** Agent output, the consolidated report, plan instructions, fix verdicts: each has its own gate. Check this when adding a tier.
- **A gate states its bound.** Say what the gate does *not* do, or it becomes a second review.
- **Correctness properties do not get config knobs.** Config is capability wiring: paths, models, agents, commit behavior. A disableable correctness gate fails silently.
- **Trust the model.** Prompts state concepts, not per-language catalogues. If a fix adds thirty lines of examples, it is the wrong fix.
- **Domain-neutral examples.** Shipped files reference no specific product, team, or codebase.
- **No dead citations.** Shipped files cannot cite documents that do not ship.
- **Descriptions carry triggers, not summaries.** A skill description says when to invoke it. The body says what to do.

## Writing conventions

- **Changelog:** Keep a Changelog, SemVer, newest first. Lead with what changed, then why or what to expect.
- **Commits:** `type(scope): summary`, as in the git history. Release commits are `docs(release): vX.Y.Z — <theme>`.
- **Prose:** plain and grounded. No marketing language. Do not add fields, knobs, or sections nobody asked for.
- **Scope:** make the change asked for. Flag other opportunities; do not act on them unasked.

## Session continuity

Work spans many sessions. Three untracked stores under `docs/` let any session pick up where the last one left off.

- `docs/handover/<session-name>.md` — the current state of one line of work: in progress, done, next, unresolved. Rewritten on every update. A snapshot, not a log.
- `docs/handover/ledger.md` — append-only, dated, one line per event: session started or ended, decision made, release cut. The cross-session timeline.
- `docs/memory/` — one durable fact per file: a decision, a constraint, a preference that is not derivable from the repo. `docs/memory/README.md` indexes them.

At session start, read the handover for the current session name, the tail of the ledger, and the memory index.

Update the handover when a milestone lands and before the session ends. The handover file takes the session's name. If the session has no name, stop and say so: suggest a name, or list the existing handover names to continue one. Never write a handover under a guessed name.
