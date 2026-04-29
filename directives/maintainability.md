## Maintainability Directives

These directives govern how the codebase ages. Maintainable code is code that the next contributor (human or AI) can read, understand, and change confidently — months or years after it was written.

Treat these rules as policy. Exceptions require explicit documentation, owner, and revisit plan.

---

### 1. Readable code

1. **Write for the reader, not the writer.**
   - Optimize for the time someone (likely you in three months) needs to understand and modify the code.

2. **Naming is the highest-leverage tool.**
   - A precise name eliminates the need for explanatory comments. Spend the time to choose well.
   - Names should reflect domain concepts when possible. `customer.invoice` beats `data.entry`.

3. **Avoid clever code.**
   - Compact tricks that save 3 lines but force the reader to pause are net-negative.

---

### 2. No dead code

1. **Delete what you do not use.**
   - Commented-out blocks, unused imports, abandoned helpers — version control already preserves history. The current file should reflect current truth.

2. **Unused parameters and exports are bugs.**
   - Keeping them "in case" creates false coupling and confuses readers about what the actual contract is.

---

### 3. Comment discipline

1. **Default to no comments.**
   - Most well-written code does not need them.

2. **Comment hidden constraints, not visible code.**
   - "This must come before X because Y" — yes.
   - "Increment the counter" above `counter++` — no.

3. **Don't reference the change in comments.**
   - "Added for issue #123" / "fix from PR #456" — that information lives in the commit message and PR. In the code, it rots.

---

### 4. No drive-by changes

1. **One change per commit, one purpose per PR.**
   - When you find an unrelated issue while working, file it or stash it. Address it in a focused change.

2. **Do not silently improve unrelated code.**
   - Reformatting, renaming, or "cleaning up" code outside the scope of the current task obscures the actual change and breaks `git blame`.

---

### 5. Consistent style

1. **Follow the codebase's conventions, even if you disagree with them.**
   - The cost of inconsistency exceeds the benefit of any individual style preference.

2. **One style per concept across the codebase.**
   - If half the codebase uses `async/await` and half uses `.then()`, pick one as part of a focused migration. Don't introduce a third.

---

Code is read more times than it is written. Maintainability is consideration for those future readers.

## Implementation Notes

(Project-specific notes go here. Empty in the plugin's shipped defaults.)
