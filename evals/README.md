# comb eval suite

Behavioral regression tests for the comb plugin, in the `claude plugin eval` format
(`<case>/prompt.md` + `<case>/graders/*.md`, optional `scaffold.sh` per case).

## Status

First live run on 2026-10-11 (Claude Code 2.1.296). What it established:

- **Case layout.** Scaffolded cases carry a `case.yaml` beside `prompt.md` with
  `schema_version: "1.1"`, `name`, and `context.scaffold_script: scaffold.sh`;
  `scaffold_script` is not a `prompt.md` key. Every case lists its read-only tools in
  `allowed_tools` (`Read, Glob, Grep, Skill, Agent, TodoWrite`); without `Read` there,
  the session cannot open the plugin's own `shared/` and `skills/` files.
- **Gated tools come from the CLI.** Bash, Write, and Edit are removed from the session
  unless the run passes `--allow-tools Bash Write Edit`; a case cannot grant them.
- **Graders.** Facts about tool calls (what was dispatched, with what prompt, what was
  read) are checked by `tool_used`, `file_exists`, and `regex` graders. The LLM judge's
  `trace` view is the first and last 12 messages only, so a comb run of 40 to 100
  messages cannot be judged on its middle; every `llm` grader here reads `last_message`
  and confirms the final report, nothing more. Exact-text checks are `regex`, not a
  judge. Report contents are graded with `target: { source: file, path: … }`.
- **Scaffolds commit.** Every scaffold with a git repo commits its initial state so a reviewer's `git diff HEAD` has a HEAD to diff against.
- **git on macOS.** Inside the eval sandbox `/usr/bin/git` is Apple's xcrun shim, which
  needs `/Library/Developer/CommandLineTools`, and the sandbox cannot read it. A standalone
  git (`brew install git`) works, but the agent's shell still puts `/usr/bin` first
  (macOS `path_helper` reorders `PATH`), so plain `git` fails and the agent finds
  `/opt/homebrew/bin/git` itself. It did in every run on 2026-10-11, in varying forms: full
  path, `export PATH=…`, or `G=…; $G commit`. Graders that look for git commands therefore
  match the subcommand (`commit … -m`), not the word `git`. `fix-auto-on` turns per-item
  commits off so it needs no commits of its own.
- **Template wording varies.** The final message follows the skill's templates closely but
  not byte for byte, and the default judge is a small model that votes on wording. Graders
  on the final message match the template's fixed labels (`Plan: skipped … Fix: skipped`)
  with slack between them, and the outcome is graded from files and tool calls.
- **Pinning.** The CI job pins `--model` and `--judge-model` so a model rollout is not
  read as a plugin regression. The local command below floats on purpose.
- **Ablation.** `claude plugin eval .` defaults to a with-without arm that runs every
  case a second time without the plugin. Pass `--ablation none` for pass/fail.

## Run

```bash
claude plugin eval . --scaffold --ablation none --runs 1 --max-cost-usd 15 \
  --allow-tools Bash Write Edit --no-publish      # one run per case, bounded
claude plugin eval . --scaffold --allow-tools Bash Write Edit --case "help-*"
```

Measured 2026-10-11 at eight cases, one run each: about 9 minutes and 4.70 USD.
When and how often to run it: PLAYBOOK.md, "Eval cadence".

To debug a grader without paying for a re-run, keep one run and replay the case's
`regex`, `tool_used`, and `file_exists` graders against it (`llm` graders are skipped):

```bash
claude plugin eval . --scaffold --ablation none --runs 1 --allow-tools Bash Write Edit \
  --no-publish --keep-temp --case <name>          # prints "kept temp: /private/tmp/e-XXXX"
chmod 700 /private/tmp/e-XXXX /private/tmp/e-XXXX/sealed
python3 -I scripts/replay-graders.py evals/<name> /private/tmp/e-XXXX
```
`scripts/smoke.sh` remains the offline structural gate. Run output lands under
`evals/results/` (gitignored).

## Cases

| Case | Guards against |
|---|---|
| `help-overview` | Help text drift; paraphrased instead of verbatim output |
| `config-null-delete` | `null`-as-delete merge semantics regressing (deleted role still dispatched) |
| `noncode-shortcircuit` | `/comb:the-desert` running plan/fix on a prose artifact |
| `fix-reviewer-diff-scope` | The fix reviewer reading the wrong diff (`HEAD~1` bug class, v0.9.0); a commit landing without the project's test run (0.14.0); HEAD and tree checks skipped around the implementer |
| `dispatch-delivery` | Directive embedding returning for foreign agents (paths-only contract); the scaffold overrides the writer with `general-purpose` because the shipped default is native since 0.14.0 |
| `manifest-slice` | Whole-manifest delivery returning: agents must get a per-run excerpt (entity-page section in, pdf and theme out) and the orchestrator must never print the manifest body; also `Verified:` lines in the report, `.comb/excerpts` cleaned, `model` passed on dispatch |
| `fix-auto-off` | The model-only fix entry running without `fix.model_invocation: true` (must refuse, naming the observed value and `/comb:fix`, with no edits) |
| `fix-auto-on` | The model-only fix entry refusing or stalling when the flag is set (must run the fix workflow and apply the plan) |

`dispatch-delivery` also asserts the plan summary ends with `Next: /comb:fix …` and never
names `fix-auto`. Still uncovered, by cost: a code-shaped `/comb:the-desert` run past
review (the 0.10.0 hardcoded-reviewer class), `--shave` end to end, review round numbering
with a deleted earlier round, revert-on-FAIL and `## Attempts` (needs a FAILing reviewer on
demand), and the python3-missing fallback (PATH is inherited).
