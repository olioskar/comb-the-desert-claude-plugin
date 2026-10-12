# Re-baseline experiments

Paid, two-arm runs that decide whether a prompt passage still earns its tokens. A passage is removed only when the treatment arm, with the passage removed, shows that the failure it guards against does not recur. Each case here has the same shape as `evals/` but stays out of the per-PR suite. Run one arm with:

```
PATH=/opt/homebrew/bin:$PATH claude plugin eval <plugin dir> --eval-dir experiments --case <name> \
  --scaffold --ablation none --runs 1 --allow-tools Bash Write Edit --no-publish --trust-plugin --keep-temp
```

The **control** arm is the plugin as shipped. The **treatment** arm is a worktree with only the passage under test removed. The decision is measured offline from the kept dirs. One run per arm is thin evidence, so a borderline result keeps the passage.

## Results (2026-10-12, Opus 5.5 orchestrator, reviewer lane `opus`)

### E1: reviewer calibration step (`calibration-clean-diff`)

A clean, tested `clamp()` addition. The treatment deleted the "Calibrate before publishing" step from all five reviewers.

| Arm | Agents picked | Non-deferred findings | Verdict | Cost |
|---|---|---|---|---|
| control | code-reviewer, test-auditor | 1 (T1: min/max type checks untested) | APPROVE | $0.75 |
| treatment | code-reviewer, test-auditor | 1 (the same T1) | APPROVE | $0.84 |

**Decision:** no padding without the step. The step is removed from `code-reviewer` and `test-auditor`, the two agents the run exercised. The review picked neither `simplifier`, `silent-failure-hunter`, nor `consistency-auditor` for this diff, so the run is no evidence about them, and they keep the step. To test those three, a case needs a clean diff that draws them (a refactor, a try/catch, a spec).

### E2: scanner dominance rule stated once (`scanner-gerrymander`)

This is the 0.8.0 scenario. A directive requires BEM `--` modifiers; five components follow it with 9 modifiers, and `btn.css` uses 4 single-dash modifiers consistently. Area-wide that is a minority (drift), not a dominant conflict. The treatment kept the Classification bullets in `shared/scan-rules.md`, which hold the rule, the area-wide denominator, and the self-check. It removed the restatements: the output-format paragraph's minority sentence, the agent's step-8 minority clause, and the agent's "launder drift" bullet.

| Arm | `## Directive conflicts` in the scanner reply | How btn was handled | Cost |
|---|---|---|---|
| control | none | left out of the BEM modifier sets | $0.52 |
| treatment | none | named in the BEM entry as "a minority across the area" | $0.48 |

**Decision:** the rule stated once is enough for this scenario, so the restatements are removed. The orchestrator's Step 6 backstops in `/comb:patterns`, which drop self-identified minorities and gerrymandered denominators, are a separate tier and stay. Each arm's dispatch prompt named its own `scan-rules.md`, which confirms the treatment text was the one under test.
