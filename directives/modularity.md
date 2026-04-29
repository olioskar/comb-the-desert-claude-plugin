## Modularity Directives

These directives govern how code is decomposed: where boundaries fall, how units communicate, and what each unit is responsible for. Good modularity is the strongest single predictor of how easy a codebase is to work in over time.

Treat these rules as policy. Exceptions require explicit documentation, owner, and revisit plan.

---

### 1. One responsibility per unit

1. **Each file, function, or component has one clear job.**
   - The reader should be able to state the unit's responsibility in one sentence without "and."
   - If a unit's name needs "and" or "manager" or "helper" to describe it, decompose.

2. **No god files.**
   - When a file grows past comfortable working context (~300–500 lines, codebase-dependent), split by responsibility, not by technical layer.

3. **Files that change together stay together.**
   - The natural unit of cohesion is "what changes for the same reason." A model file and its validators belong near the consumers; not necessarily in a `models/` flat directory.

---

### 2. Clear interfaces

1. **Each unit exposes a deliberate API.**
   - Public functions, types, and exports represent contracts. Internal helpers stay internal.

2. **Hide implementation, not behavior.**
   - Consumers should not need to know how a unit accomplishes its job, only what it accomplishes.

3. **No leaky abstractions.**
   - If consumers need to know about cache states, internal queues, or transactional details to use a unit, the boundary is wrong.

---

### 3. Composition over inheritance

1. **Prefer small composable pieces to deep hierarchies.**
   - Extending classes to share behavior creates rigid coupling. Composing focused functions/components keeps each piece independent.

2. **Cross-cutting concerns belong in cross-cutting tools.**
   - Logging, metrics, auth — use middleware, decorators, or context, not inheritance.

---

### 4. Boundaries are testable

1. **A well-bounded unit can be tested in isolation.**
   - If a unit can only be tested through its consumers, its boundary is too implicit.

2. **Inputs and outputs are observable.**
   - Effects (network, file system, time) sit at the edges. Pure logic sits inside.

---

### 5. Coupling is intentional

1. **Imports are a coupling signal.**
   - Many imports across module boundaries means the modules are not as independent as they look.

2. **Circular dependencies are bugs.**
   - Even if the runtime allows them, they indicate that the boundary between the two units does not exist.

3. **Deep dependency chains are a smell.**
   - A → B → C → D for a simple operation suggests that the chain represents accidental rather than essential structure.

---

Smaller, well-bounded units are easier for humans and AI alike to reason about, modify safely, and test confidently.

## Implementation Notes

(Project-specific notes go here. Empty in the plugin's shipped defaults.)
