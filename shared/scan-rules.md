# Scan rules (scanner and orchestrator)

The scanner follows these rules exactly; `/comb:patterns` synthesizes from output that follows them. Lenses, classification, and output format live here and nowhere else.

## Lenses

**For each thematic lens, extract the concrete convention this area actually follows.** A fact with a real reference, not a restated principle:
- **Structural conventions** — how recurring unit types are built; where things live; file/folder layout.
- **Naming & vocabulary** — the actual domain terms in use, casing conventions, file-naming conventions.
- **Closed sets** — finite token / enum / status-value / config-key sets that new code must draw from rather than invent. Enumerate the set, or name where it is defined.
- **Abstraction calibration** — the codebase's normal level of indirection; what warrants a service/wrapper/bridge layer here vs. what would be over-engineering, judged from what actually exists.
- **Reuse points** — the canonical utilities, components, hooks, or helpers a contributor should reach for instead of reinventing.
- **Error handling & async** — the established patterns for failures, loading, and async flow.
- **Testing conventions** — how tests are structured and named, and what is conventionally covered.

## Classification

**Classify every candidate convention against the directives before you record it:**
- **Conforms to a directive**, or **no directive covers it (net-new)** → record it. Conformance is the convention; net-new is how genuinely new or canonical patterns get captured.
- **Conflicts with a directive but is a *minority* in your area** (the surrounding code follows the directive) → this is **drift, not a convention.** Do not record the deviation. Record the directive-conforming norm the rest of the area follows.
- **Conflicts with a directive but is the *dominant, consistent* practice across your area** → do not silently canonize it and do not silently drop it. Record the directive-conforming expectation in the manifest body, and report the conflict separately under `## Directive conflicts` (see Output format) so a human reconciles it — a stale directive and systemic drift look identical from inside one area, and only the user knows which. (If that directive is marked `SUPERSEDED`, this is not a conflict at all — record the practice as the norm (a superseded directive was down-weighted by the user at the gate; a widespread practice that conflicts with it is the codebase's current norm).)
- **"Dominant" is measured against the whole area's instances of that lens — never a sub-scope.** The population is *every* instance of the lens across your assigned area (all modifier classes, all names of that kind, all error sites — whatever the lens is), not one component, file, or atom. A practice that is 100% consistent *within one component* but is the lone exception among the area's instances of that lens is a **MINORITY (drift)**, however internally tidy that component is. Never narrow the denominator to the subset where the deviation is universal — scoping "dominant" to "the `.btn` atom" when every other modifier in the area uses the directive's form gerrymanders a minority into a false dominant. **Self-check:** if you find yourself writing "every other X uses the directive's form, but this one component doesn't," you have the MINORITY case — record the conforming norm, do not emit a conflict.

## Output format

Return markdown only — no prose preamble. One `## {area label}` block containing only the thematic `### ` subsections that have content:

```
## {area label}

### Structural conventions
- {concrete convention} — `path:line` (canonical: `path:line`)

### Closed sets
- {set name}: `{value}`, `{value}`, … — defined at `path:line`

### Reuse points
- {canonical helper/component} — `path:line`
```

Use only the subsection headings from the lens list above, in that order, omitting any that are empty.

Emit a `## Directive conflicts` section **only if at least one DOMINANT practice in your area conflicts with an authoritative directive** (the fourth case under *Classification*). If you have no dominant conflict, emit **nothing** for this section — no heading, not even a parenthetical `(none — …)` that explains the absence. Do not narrate why there is no conflict; simply omit the section. A minority deviation is **never** placed under this heading in any form, annotated or otherwise; it belongs only in your conforming-norm entry, if anywhere. The section is **not** manifest content; the orchestrator extracts it for the user and never writes it into the manifest:

```
## Directive conflicts
- {practice} conflicts with `{directive}.md §{N}` — dominant in this area ({k} of {n} files), e.g. `path:line`. Reconcile: update the directive, or treat the practice as drift to fix.
```
