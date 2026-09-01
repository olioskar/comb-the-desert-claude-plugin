---
type: llm
criteria: Two same-file items run sequentially with per-item commits. M1 must be implemented, reviewed PASS, and committed; then M2 must be implemented, reviewed PASS, and committed. The M2 reviewer must scope its diff with `git diff HEAD` (plus `git status --porcelain` for new files) and must NOT flag M1's already-committed rename as a scope violation. Any reviewer use of `git diff HEAD~1` for an item's review, or a FAIL on M2 caused by M1's changes appearing in the reviewed diff, is the regression under test.
---

Read the transcript. Score 1 when both items end in PASS with one commit each and the M2 review never treats M1's committed change as part of M2's diff. Score 0 when a reviewer diffs against HEAD~1, when M2 FAILs on a scope violation that is actually M1's committed change, or when the run escalates to the user because of that false FAIL.
