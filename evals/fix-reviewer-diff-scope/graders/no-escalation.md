---
type: llm
focus: last_message
criteria: The final message is a completed /comb:fix summary in which both M1 and M2 ended in PASS with one commit each. It does not report a FAIL on M2 caused by M1's already-committed rename, and it does not stop to ask the user about a scope violation.
---

Score 1 when both items are reported PASS and committed. Score 0 when M2 is reported FAIL or the run escalated to the user over a scope violation that is actually M1's committed change.
