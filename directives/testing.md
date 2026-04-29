## Testing Directives

These directives govern what to test, how to test it, and what kinds of tests are worth writing. Tests that pass without exercising real behavior are negative-value: they slow CI and create false confidence.

Treat these rules as policy. Exceptions require explicit documentation, owner, and revisit plan.

---

### 1. Test-driven where practical

1. **Write the failing test before the implementation.**
   - Watch the test fail with the right error. Then make it pass with the minimum code.

2. **Red, green, refactor — not red, green, ship.**
   - The refactor step is where you clean up the implementation knowing the test will catch regressions.

3. **TDD is not dogma; behavior coverage is.**
   - For some changes (UI tweaks, config edits) TDD adds friction without value. The rule is "the change must be covered by tests"; TDD is one way to get there.

---

### 2. Test real behavior

1. **Tests exercise the unit's contract, not its internals.**
   - When the implementation changes but the contract doesn't, the test should still pass. If it doesn't, the test was coupled to internals.

2. **Mock at boundaries, not in the middle.**
   - Mock external systems (network, file system, time). Do not mock the unit's internal collaborators.

3. **Mock-only tests are vanity.**
   - A test where every collaborator is mocked tests the test, not the code. Real integration where possible.

---

### 3. Cover what changed

1. **Behavior changes need behavior tests.**
   - A change that alters output, throws different errors, or follows a new code path needs a test that exercises the change.

2. **Refactors should not need new tests.**
   - If a refactor changes test requirements, you didn't refactor — you altered behavior.

3. **Edge cases get tests.**
   - Empty input, exactly-at-boundary, the unhappy path — these are where bugs hide.

---

### 4. No vanity tests

1. **Trivial passes are not coverage.**
   - A test asserting `function(x) === function(x)` is not a test.

2. **Tests should be able to fail.**
   - For every test, articulate what real bug it would catch. If you can't, the test is not earning its keep.

3. **Avoid implementation-coupling.**
   - Tests that break when the implementation is reorganized but produces the same outputs are noise.

---

### 5. Fast and deterministic

1. **A flaky test is worse than no test.**
   - A test that fails randomly trains the team to ignore failures. Fix flakiness or delete the test.

2. **Test setup is part of test quality.**
   - Sloppy fixtures, shared mutable state, time-of-day dependencies — all sources of false failures.

3. **Fast tests run more often.**
   - Optimize the test suite for the case where developers run it on every save, not just on CI.

---

Tests exist to catch regressions and document behavior. They are not a quality goal of their own — they are a tool for making everything else trustable.

## Implementation Notes

(Project-specific notes go here. Empty in the plugin's shipped defaults.)
