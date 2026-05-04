## Reusability Directives

These directives govern duplication, extraction, and abstraction. The point is not "DRY at all costs" — over-abstraction is as costly as duplication. Aim for the right shape, not the most-shared shape.

Treat these rules as policy. Exceptions require explicit documentation, owner, and revisit plan.

---

### 1. Don't copy-paste

1. **Identical code in two places is a bug waiting to happen.**
   - One copy will be fixed, the other will not. The drift is invisible until it bites.

2. **Extract on the third occurrence, not the second.**
   - Two similar uses are often coincidence. Three are a pattern. Premature extraction at N=2 frequently produces an abstraction that breaks when N=3.

3. **When you copy, comment the copy.**
   - If you genuinely need a temporary copy (e.g., during a refactor), leave a TODO referencing the canonical version so the copy gets removed when the refactor lands.

---

### 2. Don't over-abstract

1. **The wrong abstraction is more expensive than duplication.**
   - A shared helper that almost-fits all callers forces every caller to bend, adds parameters to fit edge cases, and obscures the actual logic.

2. **No "configurable everything" base classes.**
   - When a parent class has more configuration knobs than concrete behavior, you have a meta-problem, not a base class.

3. **Inline before you abstract.**
   - When you find duplication, first try inlining one copy and seeing whether the resulting code reads more clearly. Sometimes "duplication" is just two clear pieces of code that happen to look similar.

---

### 3. Shared utilities are exceptions, not defaults

1. **Default to colocating helpers with their consumer.**
   - A helper used by one component lives in that component's file or a sibling file.

2. **Promote to shared only when needed.**
   - When a second consumer arrives, move the helper to a shared location. Until then, it's noise in the shared namespace.

3. **Shared utilities have tests.**
   - When a function becomes shared, it gains a contract that callers depend on. Treat it accordingly.

---

### 4. Naming conveys reusability

1. **Generic names imply generic usage.**
   - `formatDate(date)` implies broad reuse; `formatDateForCustomerList(date)` implies a specific caller.
   - Match the name's specificity to the actual scope.

2. **Don't lie with names.**
   - A function called `getUser` that fetches and creates and updates is not a getter. Either narrow it or rename it.

---

### 5. Extraction targets

1. **Extract complex logic, not boilerplate.**
   - Three identical 50-line functions with slight variations are a strong extraction target.
   - Three identical 2-line snippets often aren't worth abstracting.

2. **Extraction reduces cognitive load.**
   - The post-extraction call site should be easier to understand than the pre-extraction copies. If the extraction's signature has 7 parameters and a config object, you've moved complexity, not removed it.

---

Reusability is a means, not a goal. The goal is code that is easy to change. Sometimes that means sharing; sometimes it means deliberate, intentional duplication.

## Implementation Notes

(Project-specific notes go here. Empty in the plugin's shipped defaults.)
