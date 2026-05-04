## Consistency Directives

These directives govern how new work fits with existing work. Consistency is what makes a codebase navigable — when one part of the system teaches you the conventions used by every other part.

Treat these rules as policy. Exceptions require explicit documentation, owner, and revisit plan.

---

### 1. Follow established patterns

1. **The existing codebase is the first source of truth for style.**
   - Before introducing a new pattern, check whether one already exists. If so, follow it.

2. **One way per concept.**
   - If state management uses X across the codebase, do not introduce Y for a single new feature unless deliberately migrating.

3. **Drift accumulates.**
   - "Just this once" inconsistencies become two-once, then three-once. The cost is cumulative; the benefit of any one inconsistency is local.

---

### 2. Reference implementations

1. **When a feature has a canonical example, follow it.**
   - "Build the new entity page like the existing Customers page" — when a reference is named, the reference is the spec.

2. **Identify and call out the reference in PR descriptions.**
   - The reviewer should know what the new code is modeled on; that's how they assess fidelity.

3. **Improvements to references are separate work.**
   - If the reference is wrong, that's a finding for the reference, not a license to deviate in the new feature.

---

### 3. Spec/plan alignment

1. **The spec is the contract for what we're building.**
   - The implementation must match. Findings about ambiguities or contradictions in the spec are bugs in the spec, not in the code.

2. **The plan is the contract for how we're building it.**
   - Deviations from the plan need explicit justification.

3. **Missing the spec is a critical finding.**
   - "Spec said X, code does Y" is a Critical-severity issue regardless of whether Y "seems fine."

---

### 4. Naming and vocabulary

1. **Use the codebase's domain vocabulary.**
   - If the codebase calls them "customers," do not introduce "clients" or "accounts" for the same concept.

2. **Consistent naming across layers.**
   - The API field, the model property, the form input, the UI label — should resolve to the same name where possible.

3. **Singular and plural conventions.**
   - Pick one (`customer` and `customers`, or `account` and `accounts`) and use it across.

---

### 5. Cross-domain ripple

1. **Schema changes ripple to every layer.**
   - Database, API, types, form fields, exports, tests, documentation — all reflect the change.

2. **Verify the ripple before approving.**
   - A schema change that updates the type but not the form, or the API but not the export, is half-done.

---

Consistency is not aesthetic preference. It's the property that lets a contributor read one part of the codebase and predict the rest.

## Implementation Notes

(Project-specific notes go here. Empty in the plugin's shipped defaults.)
