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
  messages cannot be judged on its middle; `llm` graders here read `last_message` and
  confirm the final report, nothing more. Exact-text checks are `regex`, not a judge.
- **git on macOS.** Inside the eval sandbox `/usr/bin/git` is Apple's xcrun shim, which
  needs a cache file the sandbox denies, and `/Library/Developer/CommandLineTools` is
  unreadable from the sandbox. Cases that need git for diffs or commits
  (`fix-reviewer-diff-scope` above all) cannot pass on a Mac without a standalone git
  on the PATH; run them in CI on Linux.
- **Ablation.** `claude plugin eval .` defaults to a with-without arm that runs every
  case a second time without the plugin. Pass `--ablation none` for pass/fail.

## Run

```bash
claude plugin eval . --scaffold --ablation none --runs 1 --max-cost-usd 15 \
  --allow-tools Bash Write Edit --no-publish      # one run per case, bounded
claude plugin eval . --scaffold --allow-tools Bash Write Edit --case "help-*"
```

Measured 2026-10-11: six cases, one run each, about 10 minutes and 4 USD.
`scripts/smoke.sh` remains the offline structural gate. Run output lands under
`evals/results/` (gitignored).

## Cases

| Case | Guards against |
|---|---|
| `help-overview` | Help text drift; paraphrased instead of verbatim output |
| `config-null-delete` | `null`-as-delete merge semantics regressing (deleted role still dispatched) |
| `noncode-shortcircuit` | `/comb:the-desert` running plan/fix on a prose artifact |
| `fix-reviewer-diff-scope` | The fix reviewer reading the wrong diff (`HEAD~1` bug class, v0.9.0) |
| `dispatch-delivery` | Directive embedding returning for foreign agents (paths-only contract) |
| `manifest-slice` | Whole-manifest delivery returning: agents must get a per-run excerpt (entity-page section in, pdf and theme out) and the orchestrator must never print the manifest body |
