---
type: regex
pattern: "M1[^\\n]*PASS[\\s\\S]*M2[^\\n]*PASS"
target: last_message
match: contains
---
