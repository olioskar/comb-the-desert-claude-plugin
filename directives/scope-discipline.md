## Scope Discipline Directives

These directives govern what is in and out of any given change. Scope creep is the most common single cause of slow PRs, missed deadlines, and review churn.

Treat these rules as policy. Exceptions require explicit documentation, owner, and revisit plan.

---

### 1. Stay in the asked change

1. **Implement what was asked, nothing more.**
   - The spec, plan, or instruction defines the scope. Work outside it is not your task right now.

2. **Note unrelated issues; do not fix them in the same change.**
   - File a follow-up. Stash the fix. Do not silently expand the diff.

3. **The reviewer should not be surprised by the diff.**
   - Anything in the diff that the reviewer would not expect from the title and description is a scope violation.

---

### 2. No drive-by refactors

1. **"While I was here" is not a justification.**
   - Refactoring code adjacent to your change requires its own justification, its own commit, and ideally its own PR.

2. **Formatting is not a free improvement.**
   - Reformatting code outside the changed lines breaks `git blame` and obscures the actual change.

3. **Renaming requires its own commit at minimum.**
   - A change that combines a rename with logic changes makes the diff unreadable.

---

### 3. No bonus features

1. **The asked feature, not the inferred-better feature.**
   - If the spec says "add a button," add a button. Do not also add a confirmation dialog because "users will probably want one."

2. **Scope expansions need approval.**
   - If you find a stronger version of the feature mid-implementation, surface it. Get a yes before doing the expanded work.

---

### 4. Half-implementations are out of scope

1. **Do not leave a feature half-built.**
   - If the change is too big to complete cleanly, decompose into smaller shippable pieces — not partial implementations of the whole.

2. **No feature flags around incomplete features unless explicitly part of the plan.**
   - Flags hide complexity. They have a place, but introducing a flag to ship half a feature is not it.

---

### 5. Document exceptions

1. **When you must violate scope, say why.**
   - "Had to also touch X because the change in Y depended on it" — fine, but state it in the PR description.

2. **The exception must be unavoidable.**
   - Convenience is not a reason. Coupling that *forced* the change is.

---

Scope discipline is what makes review tractable, history readable, and rollback possible. It is the foundation of every other engineering virtue.

## Implementation Notes

(Project-specific notes go here. Empty in the plugin's shipped defaults.)
