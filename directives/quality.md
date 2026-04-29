## Quality Directives

These directives govern correctness and robustness — making sure the code does what it claims and fails honestly when it cannot.

Treat these rules as policy. Exceptions require explicit documentation, owner, and revisit plan.

---

### 1. Correctness first

1. **Verify behavior, not assumptions.**
   - Run the code. Observe the output. "It should work" is not the same as "it works."

2. **Off-by-one, fence-post, and bounds errors are bugs, not nits.**
   - Test the edges: empty input, single item, very large input, exactly-at-boundary.

3. **Trust the type system, but verify the types.**
   - Strict typing catches a class of bugs. It does not catch logic errors. Both layers matter.

---

### 2. Honest error handling

1. **Surface errors, do not swallow them.**
   - A `catch` block that silently returns a default, logs nothing, or returns `null` to the caller hides bugs.

2. **Match the error to the recovery.**
   - If you can recover, recover. If you cannot, propagate. Do not pretend.

3. **Distinguish expected failures from bugs.**
   - "User submitted invalid input" is expected — return a clear validation error.
   - "Database returned undefined for a required field" is a bug — fail loudly so the bug is found.

---

### 3. Validate at boundaries

1. **External input is untrusted.**
   - User input, external API responses, file contents, environment variables — validate the shape and contents before acting on them.

2. **Internal contracts are trusted.**
   - Code you control communicates via types and interfaces. Re-validating at every internal call site is noise.

3. **One validation point per boundary.**
   - Validate at the edge, then trust the validated value through the rest of the flow. Multiple validations of the same value indicate unclear ownership.

---

### 4. No silent fallbacks for bugs

1. **A fallback that hides a bug is worse than a crash.**
   - Default values, optional chaining cascades, and `try/catch` returning `null` can mask a bug for months. The bug will resurface — usually in production, usually at a worse time.

2. **Fallbacks are only for known-acceptable defaults.**
   - "Use empty string if the user has no display name" — fine.
   - "Use empty array if the API returned a 500" — not fine. The 500 is the signal.

---

### 5. Clean state on failure

1. **Do not leave half-finished work behind.**
   - If a multi-step operation fails partway, undo what was started. Do not leave the system in an indeterminate state.

2. **Reset transient state on error.**
   - Loading flags, in-flight indicators, and modal openness should resolve to a definite state on every code path.

---

Quality is the absence of unpleasant surprises in production. Honest failure modes are the foundation.

## Implementation Notes

(Project-specific notes go here. Empty in the plugin's shipped defaults.)
