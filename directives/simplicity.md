## Simplicity Directives

These directives govern when *not* to do something. Every change should be the minimum that solves the stated problem. Speculative work, defensive patterns for impossible cases, and abstractions designed for hypothetical futures are recurring sources of bugs and review churn.

Treat these rules as policy. Exceptions require explicit documentation, owner, and revisit plan.

---

### 1. YAGNI

1. **Build for the asked problem, not the imagined one.**
   - If the spec or plan does not call for a feature, do not introduce it.
   - "We might need it later" is not a reason — when the need arrives, the code can be added with full context.

2. **One concrete use-case beats one abstraction.**
   - Do not create generic helpers, base classes, or configuration knobs to support a single caller.
   - Three similar lines is preferable to a premature abstraction. The third caller is the right time to extract.

3. **No design for hypothetical scale or extension.**
   - Avoid plugin systems, registries, or strategy patterns until at least two distinct concrete strategies exist.

---

### 2. No speculative defenses

1. **Trust internal code.**
   - Do not validate inputs at boundaries that internal callers control.
   - Validate at *external* boundaries only: user input, external APIs, file I/O, network responses.

2. **Do not catch what cannot fail.**
   - `try/catch` around code that has no failure mode is dead defensive paranoia. Remove it.
   - If a failure mode is theoretical but not real (e.g., a `JSON.parse` of literal-known-good content), do not wrap it.

3. **No defensive optional chaining for guaranteed values.**
   - If the type system or framework guarantees a value is present, do not add `?.` chains "just in case."

---

### 3. No hypothetical concerns in reviews

1. **Findings must reference real failure modes.**
   - "What if X happens?" — produce a path that triggers X. If you cannot, the concern is hypothetical.

2. **No "this could be improved" without a concrete what-and-why.**
   - Suggest the specific improvement and the specific cost it pays for. Vague gestures at quality are not findings.

3. **Don't invent issues.**
   - When a diff is small and clean, the right finding count is small. Padding a review with marginal observations dilutes the signal of real findings.

---

### 4. Minimal diffs

1. **Touch only what the change requires.**
   - Drive-by refactors, formatting fixes, and unrelated cleanups go in separate commits or separate PRs.

2. **No half-implementations.**
   - If a change is too large to ship cleanly, decompose into shippable slices. Do not leave a mid-state in the codebase.

3. **No backwards-compat shims for unreleased code.**
   - Until v1, change the code, do not maintain ghost APIs.

---

### 5. Comments are the last resort

1. **Prefer better names over explanatory comments.**
   - If a comment is needed because the code is unclear, fix the code.

2. **Comments document *why*, not *what*.**
   - Hidden constraints, surprising invariants, workarounds for specific bugs — yes. Restating what the next line does — no.

3. **No comments referencing the change itself.**
   - "Added for issue #123" / "used by X flow" — those rot. PR description and commit message carry that load.

---

A simpler change is a safer change. Aggressive simplicity is the foundation of every other directive in this set.

## Implementation Notes

(Project-specific notes go here. Empty in the plugin's shipped defaults.)
