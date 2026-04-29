# SPEC-DECISIONS — plan/spec alignment decisions

**Findings covered:** H2, H3, M1
**Target files:** depending on decision per finding —
- Plan: `docs/superpowers/plans/2026-04-27-comb-the-desert-plugin.md`
- Spec: `docs/superpowers/specs/2026-04-27-comb-the-desert-plugin-design.md` (and the working copy `DESIGN.md`)

---

## What

Three Round-1 review findings (H2, H3, M1) flag direct contradictions between the plan and the spec. Each contradiction can only be resolved one of two ways: change the plan to match the spec, or change the spec to authorize what the plan already does. This document presents the options, tradeoffs, and a recommendation per finding so the user can pick and apply the matching edits.

- **H2** — Plan Task 23 lets trivial items skip the reviewer (`(trivial — sonnet implementer, no reviewer)`). Spec §7.5 mandates implementer-then-reviewer for every item.
- **H3** — Plan Task 21 reinstates `CLAUDE.md` as the source for the base branch. Spec §10 explicitly drops `CLAUDE.md` base-branch lookup in favor of config + invocation-time override.
- **M1** — Plan Task 21 Step 2 reads the prior review report and tells agents which findings were already fixed. Spec §7.3 only specifies `N = count + 1`; spec §12 lists round-N-aware behavior as future work.

## Why

These can't be silently resolved. The plan and spec must agree before execution — without a decision, an executor is staring at contradictory instructions and will pick whichever interpretation feels right at the moment, baking the inconsistency into the implementation rather than surfacing it. Each of the three findings also touches a real tradeoff (cost, risk, or scope creep) that the user should weigh deliberately.

---

## Decisions required

### H2 — Trivial items: reviewer required or skippable?

**Plan currently says** (Task 23, Step 3b/3d, lines 2196 and 2226):
> "For trivial items: announce '(trivial — sonnet implementer, no reviewer)' and proceed accordingly."
>
> Step 3d header: "Send to reviewer (standard only)."
>
> Step 5 progress samples: `"PASS, trivial — skipped review"`, `"L1-L3: PASS (parallel batch, trivial — skipped review)"`.

**Spec currently says** (§7.5):
> "For each instruction: implementer (opus standard, sonnet trivial), then reviewer (opus)"

No exception for trivial. The spec specifies the model lane changes for trivial (`sonnet` instead of `opus`), but the reviewer step is non-conditional.

The contradiction is reinforced by §7.6 (Plan Task 24, the-desert): the plan's `the-desert` body explicitly says "Every item gets a reviewer — no 'trivial — skipped review'", which implies the plan author knows trivial-skip is the default elsewhere and wants the-desert to override it. The spec doesn't authorize either behavior.

**Option A — Update plan to match spec.** Run a reviewer on every item, including trivial. The trivial classification still affects implementer model (`sonnet` vs `opus`), but reviewer always runs (`opus`).

**Option B — Update spec to authorize trivial-skip.** Amend §7.5 to say trivial items skip the reviewer; remove the `the-desert` override from Task 24 since "every item gets a reviewer" would simply be the the-desert escalation of trivial back to standard.

**Tradeoffs:**

| Dimension | Option A (reviewer always) | Option B (skip on trivial) |
|---|---|---|
| Cost per trivial item | +1 opus reviewer call (~few cents, low single-digit seconds wall clock) | 0 reviewer cost |
| Risk of bad trivial fix shipping | Near-zero — opus reviewer catches lexical typos, scope creep, wrong-file edits | Non-zero — relies on triviality classifier being conservative; a mis-classified "trivial" could ship unverified |
| Workflow simplicity | Uniform: every item → implementer → reviewer | Two paths: trivial (no reviewer) vs standard (reviewer) |
| `the-desert` override needed? | No — uniform behavior already | Yes — the-desert must escalate trivial→reviewed (already in plan Task 24) |
| Bias toward conservatism | Strong — quality bar is the same regardless of size | Weaker — speed wins on items deemed trivial |
| Aligns with existing spec text | Yes (§7.5 as written) | No — requires spec amendment |

**Recommendation: Option A.**

Rationale: an opus reviewer on a single-line edit costs a fraction of a cent and a few seconds. The savings from Option B are negligible compared to the cost of one mis-classified "trivial" item slipping a real bug through. The triviality classifier is judgment-based by an orchestrator model — not airtight — and a uniform reviewer is the simplest and cheapest defense. Option A also collapses the `the-desert` override (Task 24) into the default case, which is a small simplification. The plan's "trivial — skipped review" lines read like an inherited optimization from `~/.claude/commands/comb/fix.md`; v1 of the plugin can drop it without losing anything material.

#### If Option A — Update plan to match spec

**Plan change** (no spec change):

In `docs/superpowers/plans/2026-04-27-comb-the-desert-plugin.md`, Task 23:

1. **Step 3b (line 2196).** Replace:
   > For trivial items: announce "(trivial — sonnet implementer, no reviewer)" and proceed accordingly.

   With:
   > For trivial items: announce "(trivial — sonnet implementer)" and proceed accordingly. Reviewer still runs (opus) per spec §7.5 — triviality only affects the implementer model lane, not the reviewer step.

2. **Step 3d header (line 2226).** Replace:
   > ### 3d. Send to reviewer (standard only)

   With:
   > ### 3d. Send to reviewer (always)

3. **Step 5 progress samples (lines 2308 and 2318).** Remove the "trivial — skipped review" framings:
   - Replace `{code} — PASS, trivial — skipped review ({N}/{total} complete)` with `{code} — PASS, trivial implementer ({N}/{total} complete)`
   - Replace `L1-L3: PASS (parallel batch, trivial — skipped review)` with `L1-L3: PASS (parallel batch, trivial implementer)`

4. **Task 24 (the-desert override, line ~2347 onward).** Remove or rephrase the "Every item gets a reviewer — no 'trivial — skipped review'" override since it's now the default. Replace with a reminder that the-desert preserves default behavior (no special trivial-skip) for clarity, or drop the line entirely.

**Spec change:** none. §7.5 stands as written.

#### If Option B — Update spec to authorize trivial-skip

**Plan change:** none (current behavior preserved).

**Spec change** in both `docs/superpowers/specs/2026-04-27-comb-the-desert-plugin-design.md` and the working copy `DESIGN.md`:

§7.5 currently reads:
> - For each instruction: implementer (opus standard, sonnet trivial), then reviewer (opus)

Replace with:
> - For each instruction: implementer (opus standard, sonnet trivial). Reviewer (opus) runs for standard items; **trivial items skip the reviewer** because the rubric for trivial (single-line edits, import reorders, comment fixes, lexical renames within one file) is narrow enough that a separate verification pass adds little. Users can override the classification per-item, and `/comb:the-desert` escalates every item to standard so trivial-skip never applies during the full sweep.

§7.6 already contains "the user-explicit `agents.<role>.model` override survives" language; add a sibling note:
> - Every item gets a reviewer during `the-desert` — the trivial-skip optimization from §7.5 is suppressed during the full sweep.

(The latter line already exists in plan Task 24 — promoting it into the spec keeps spec and plan in sync.)

---

### H3 — Base branch resolution

**Plan currently says** (Task 21, Step Inputs, line 1688):
> "**Base branch** — what to diff against. Default: read from the project's `CLAUDE.md` if it specifies one; else `main`. The user may override."

**Spec currently says** (§10, dropped behaviors):
> "Hardcoded base-branch lookup via `CLAUDE.md` — replaced by config + user override at invocation time"

This was an explicit cut in the spec. The plan reinstated it.

**Options:**

- **A — Update plan to match spec, with a config field.** Drop the `CLAUDE.md` lookup. Add a `paths.base_branch` (or `defaults.base_branch`) field to `defaults.json` with a default of `main`. The skill reads from merged config; the user overrides at invocation time. This faithfully implements §10's "config + user override at invocation time" without a hidden `CLAUDE.md` codepath.

- **B — Update spec to authorize the `CLAUDE.md` fallback.** Bring back the dropped behavior; treat `CLAUDE.md` as a useful project-aware default ahead of (or instead of) a config field.

- **C — Hybrid.** Keep the config approach (Option A) but also allow `CLAUDE.md` as a *last-resort* fallback before defaulting to `main`. Resolution order: invocation override → project `comb.config.json` → global `comb.config.json` → `CLAUDE.md` mention → `main`.

**Tradeoffs:**

| Dimension | A (config only) | B (CLAUDE.md only) | C (hybrid) |
|---|---|---|---|
| Predictability for users | High — single source of truth | Medium — depends on `CLAUDE.md` content shape | Low — four-step resolution chain |
| Aligns with spec §10 | Yes | No (requires un-dropping) | Partially (re-adds `CLAUDE.md`, weakened) |
| Works on projects without `CLAUDE.md` | Yes — falls back to config / `main` | Yes — falls back to `main` | Yes |
| Works on projects with `CLAUDE.md` saying "base: develop" | Only if user copies it into config | Yes, automatically | Yes, automatically |
| Encourages explicit config over implicit document parsing | Yes | No | Mixed |
| Scope/parser surface area | Smallest — JSON only | Adds `CLAUDE.md` markdown parsing | Largest — both |
| Risk of mis-parsing `CLAUDE.md` | None | Real (regex/heuristic) | Real |
| Comb's own `CLAUDE.md` parsing precedent | None added | Sets a precedent | Sets a precedent |

**Recommendation: Option A.**

Rationale: §10 dropped `CLAUDE.md` lookup deliberately. The replacement is "config + user override at invocation time" — and the plan implements only the latter half (user override) while reintroducing the half that was supposed to go away. Adding `paths.base_branch` to `defaults.json` is a 5-line change that closes the loop cleanly.

Option B is tempting because `CLAUDE.md` already declares conventions in many projects, but parsing markdown to extract a base branch is fragile (regex format? heading? "main branch is X"? ambiguous when both `main` and `master` are mentioned). Comb does not otherwise parse `CLAUDE.md` as authoritative input — the spec treats it as one of several context documents agents *read*, not as a config source. Adding a parser sets an awkward precedent.

Option C combines the worst of both: parser surface area plus four resolution steps the user has to memorize. Skip.

#### If Option A — Update plan to match spec, with a config field

**Spec changes** in both `docs/superpowers/specs/2026-04-27-comb-the-desert-plugin-design.md` and `DESIGN.md`:

1. **§4.2 (`defaults.json`).** Add a `paths.base_branch` key. Replace the existing `paths` block:
   ```json
   "paths": {
     "reviews": "docs/combs/reviews",
     "plans":   "docs/combs/plans"
   },
   ```
   With:
   ```json
   "paths": {
     "reviews":     "docs/combs/reviews",
     "plans":       "docs/combs/plans",
     "base_branch": "main"
   },
   ```

2. **§4.3 (Field reference table).** Add a row:
   | Field | Read by | Effect |
   |---|---|---|
   | `paths.base_branch` | every command | default base branch for diffs when the user does not pass an override at invocation time |

**Plan changes** in `docs/superpowers/plans/2026-04-27-comb-the-desert-plugin.md`:

1. **Task 5 (`config/defaults.json`, lines 253–356).** Add `"base_branch": "main"` to the `paths` block — mirror the spec edit byte-for-byte.

2. **Task 21, Step Inputs (line 1688).** Replace:
   > 2. **Base branch** — what to diff against. Default: read from the project's `CLAUDE.md` if it specifies one; else `main`. The user may override.

   With:
   > 2. **Base branch** — what to diff against. Default: `paths.base_branch` from merged config (ships as `main`). The user may override at invocation time; the override does not mutate config.

3. **Task 21, Step 2 (Gather context, line 1730).** Remove the bullet:
   > - Project's `CLAUDE.md` for conventions, gotchas, base-branch defaults

   And replace with:
   > - Project's `CLAUDE.md` for conventions and gotchas (do not read it for base-branch defaults — those come from `paths.base_branch` in merged config)

4. **Task 22 and Task 24** — verify neither one mentions `CLAUDE.md`-as-base-branch-source. (Task 22 is the planner; Task 24 is the-desert; both inherit the resolved base branch from the review step.) Audit both task bodies and remove any stray `CLAUDE.md`-base-branch references.

#### If Option B — Update spec to authorize the `CLAUDE.md` fallback

**Plan change:** none.

**Spec changes** in both `docs/superpowers/specs/2026-04-27-comb-the-desert-plugin-design.md` and `DESIGN.md`:

1. **§10 (Dropped behaviors).** Remove the bullet:
   > - Hardcoded base-branch lookup via `CLAUDE.md` — replaced by config + user override at invocation time

2. **§7.3 (`/comb:review`) or new §7.1.6 (Base branch resolution).** Add:
   > **Base branch resolution.** The orchestrator resolves the base branch in this order:
   > 1. User-supplied override at invocation (`/comb:review pr 123 base=develop`)
   > 2. The project's `CLAUDE.md`, if it declares one (heuristic match for "base branch:" / "main branch:" / similar)
   > 3. `main`
   >
   > The override does not mutate config or `CLAUDE.md`.

3. **§4.5 (or wherever pertinent).** Add a note that `CLAUDE.md` is parsed for the base-branch declaration and that this is the only field comb reads from `CLAUDE.md` as authoritative; everything else is treated as agent-read context only.

#### If Option C — Hybrid

**Plan changes:** as in Option A, plus an extra resolution-order step. Replace Task 21 Step Inputs line 1688 with:

> 2. **Base branch** — what to diff against. Resolution order: (a) user override at invocation, (b) `paths.base_branch` from merged config, (c) `CLAUDE.md` declaration if present, (d) `main`.

**Spec changes:** as in Option A (add `paths.base_branch`) plus Option B's additions to §7.3/§4.5 documenting the `CLAUDE.md` fallback step. Update §10 to clarify that `CLAUDE.md` lookup is now a last-resort fallback rather than the primary source.

---

### M1 — Round-N-aware "prior report read"

**Plan currently says** (Task 21, Step 2, line 1735):
> "The prior review report (for round N+1) — find via `paths.reviews`, read for context, tell agents which findings were already fixed"

And in Task 21 "Ground rules" (line 1906):
> "Round-aware. If round N+1, note prior findings status. Don't re-report fixed items as new."

**Spec currently says:**

§7.3:
> "**N is computed as `(count of existing files matching the prefix in paths.reviews) + 1`.**"

§12 (future work):
> "**Round-N-aware reviews** — current implementation derives `N` by counting existing reports (§7.3); a more sophisticated version could parse the most recent report to detect whether the diff has substantively changed and reset `N` if base/branch shifted."

Spec v1 has only the count-and-increment logic. Reading the prior report and informing agents about already-fixed findings is explicitly listed as v2 future work. The plan leaks v2 behavior into v1.

**Options:**

- **A — Update plan to match spec.** Drop the "read prior report and tell agents which findings were already fixed" step. Round detection stays purely count-based: filename prefix match + 1. The "Round-aware" ground rule loses its prior-findings-status piece.

- **B — Update spec to authorize.** Amend §7.3 to make round-N-aware behavior part of v1, and remove the corresponding bullet from §12 future work.

**Tradeoffs:**

| Dimension | A (drop from plan) | B (promote to v1 spec) |
|---|---|---|
| v1 scope discipline | Tight | Loose — promotes a future-work item |
| Risk of re-reporting fixed items in round 2 | Real but mitigated by the round number itself appearing in agent prompts | Lower — agents know exactly what was fixed |
| Implementation complexity in v1 | Minimal (counting logic only) | Higher (parse prior markdown report, extract finding codes, classify status) |
| Failure modes if round 2 report is malformed | None (we just count) | Real — parser has to be robust to manual edits, partial reports, etc. |
| Surface for future enhancement | Clean — v2 lands as an added feature | Already done; v2 work item collapses |
| Spec-vs-plan honesty | Restored | Restored (different direction) |

**Recommendation: Option A.**

Rationale: §12 explicitly carved out round-N-aware behavior as future work. v1's job is to ship the count-and-increment logic, not to start parsing prior reports. The risk of re-reporting fixed items in round 2 is mostly mitigated by the round number being in the prompt — agents reading the round-2 report header know they're in a follow-up and can be appropriately skeptical of "new" findings that look identical to old ones. Option B drags real parser work into v1 for marginal benefit and erases a clean v2 extension point.

There's a small benefit to Option A beyond scope discipline: it leaves §12 honest. The "future work" list earns trust by being a list of things that are genuinely deferred. Promoting items pre-execution muddies that.

#### If Option A — Update plan to match spec

**Plan changes** in `docs/superpowers/plans/2026-04-27-comb-the-desert-plugin.md`, Task 21:

1. **Step 2 (Gather context, line 1735).** Remove the bullet:
   > - The prior review report (for round N+1) — find via `paths.reviews`, read for context, tell agents which findings were already fixed

   Replace with nothing — round detection is exclusively `(count of files matching prefix in paths.reviews) + 1` per spec §7.3, and that logic already lives in Step 7 (line 1833).

2. **Step 3, sub-step 1 "Shared context block" (lines 1758–1772).** Remove the line:
   > <prior review note if round N+1>

   Agents see only the round number (in the report filename) and the diff. They don't get a fixed-findings list.

3. **"Ground rules" (line 1906).** Replace:
   > - **Round-aware.** If round N+1, note prior findings status. Don't re-report fixed items as new.

   With:
   > - **Round-aware.** The report filename includes round N, computed by counting existing reports + 1. v1 does not parse prior reports for fixed-findings status — agents may flag items that already shipped in a prior round; deduplication against prior rounds is future work (spec §12).

**Spec change:** none.

#### If Option B — Update spec to authorize

**Plan change:** none (current behavior preserved).

**Spec changes** in both `docs/superpowers/specs/2026-04-27-comb-the-desert-plugin-design.md` and `DESIGN.md`:

1. **§7.3.** After the line `**N is computed as ...**`, add:
   > **Round-N-aware context.** When N > 1, the orchestrator reads the most recent report at `<paths.reviews>/<prefix>-round{N-1}-report.md` and includes a "Previously fixed findings" section in each agent's dispatch prompt — a verbatim list of finding codes and titles that were marked as resolved in the prior round. Agents are instructed not to re-report items in this list unless they have reason to believe the fix is incomplete.

2. **§12 (Future work).** Remove the bullet:
   > **Round-N-aware reviews** — current implementation derives `N` by counting existing reports (§7.3); a more sophisticated version could parse the most recent report to detect whether the diff has substantively changed and reset `N` if base/branch shifted.

   Or, if the "reset N if base/branch shifted" half is still future work, replace with a narrower bullet that scopes only the reset-on-base-shift behavior to v2.

---

## Expected Outcome

After this decision document is reviewed and the chosen options are applied:

- Spec and plan agree on whether trivial items see a reviewer (H2).
- Spec and plan agree on how the base branch is resolved, with a single source of truth in either config or `CLAUDE.md` (H3).
- Spec and plan agree on what "round-N-aware" means in v1 — count-and-increment only, or richer behavior (M1).
- No silent contradictions remain in scope of these three findings.
- Future-work boundaries between v1 and v2 are clean and honest.

## Scope

**In scope:** decisions and concrete plan + spec edits for findings H2, H3, M1.

**Out of scope:**
- Other findings from the round-1 review report (C1, C2, C3, H1, H4, H5, H6, M2–M10, L1–L21, TG1) — handled by other decision groups.
- Execution of the chosen edits — left for the user to apply once they pick options per finding.
- Any v2 design work (round-N-aware diff comparison, base-shift detection, document-mode reviews).
