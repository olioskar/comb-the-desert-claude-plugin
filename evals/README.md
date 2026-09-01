# comb eval suite

Behavioral regression tests for the comb plugin, in the `claude plugin eval` format
(`<case>/prompt.md` + `<case>/graders/*.md`, optional `scaffold.sh` per case).

## Status

Authored 2026-09-01 against the documented eval format. `claude plugin eval` was
**early-access-gated** for this account at authoring time, so the suite has not yet
had a live run. On the first enabled run, confirm two format details before trusting
red results:

- the `scaffold_script` frontmatter key name (each scaffolded case declares
  `scaffold_script: scaffold.sh` and needs `--scaffold` on the CLI);
- the `focus` values accepted by `llm` graders (cases that must judge the whole
  transcript omit `focus`).

## Run

```bash
claude plugin eval . --scaffold                # full suite
claude plugin eval . --case "help-*"           # one case
claude plugin eval . --runs 1 --max-cost-usd 5 # budget-bounded
```

Until the feature is enabled, `scripts/smoke.sh` is the interim gate.

## Cases

| Case | Guards against |
|---|---|
| `help-overview` | Help text drift; paraphrased instead of verbatim output |
| `config-null-delete` | `null`-as-delete merge semantics regressing (deleted role still dispatched) |
| `noncode-shortcircuit` | `/comb:the-desert` running plan/fix on a prose artifact |
| `fix-reviewer-diff-scope` | The fix reviewer reading the wrong diff (`HEAD~1` bug class, v0.9.0) |
| `dispatch-delivery` | Directive embedding returning for foreign agents (paths-only contract) |
