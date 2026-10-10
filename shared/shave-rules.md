# Shared block: shave rules

`/comb:patterns --shave` reduces a PATTERNS manifest's token cost by removing what is redundant or finished, without changing what the manifest asserts. These rules bind the shaver agent (`comb:pattern-shaver`, or any foreign agent dispatched in its role) and the orchestrator alike. Shave never rescans the codebase. It reads code only to confirm that two anchors pin the same convention.

## What you receive

All by path, nothing embedded:

- the manifest;
- the index file (JSON; per section: `heading`, `kind`, `start`, `end`, `bytes`, `scope_globs`, `anchor_dirs`, `anchors`, `basenames`);
- your own section's heading and line range;
- the path of the edit-script file you must write.

Open your section with `sed -n START,ENDp <manifest>`. Open an owner section the same way, by the range the index gives. Never read the manifest end to end.

## The three operations (the whole set)

| Class | Operation | You supply | The script checks | Your truth guard |
|---|---|---|---|---|
| `anchor` | Drop one secondary anchor that pins the same claim as the canonical one. | `old` (whole lines), `dropped_anchor`; no `new` | Derives `new` by removing the backticked token and one adjacent separator (`, `, ` + `, ` / `, `; `, ` and `), or an emptied `(canonical: …)` wrapper. `old` must keep at least one other anchor. | Read both locations. A basename anchor that resolves to more than one existing file is never dropped. An anchor that pins a different variant stays. |
| `duplicate` | Remove a bullet that restates a convention owned by another section; leave a pointer. | `old` (whole lines), `new` (empty, or exactly `- See <owner heading>.`), `owner` | `old` contains an anchor; `new` has none; `owner` is another area section whose text contains one of `old`'s anchors (by basename); the owner graph over all duplicate edits is acyclic. | Open the owner by range and confirm it states the convention with an anchor. A convention whose anchors sit inside your own section's scope is never a duplicate here. |
| `fixed-drift` | Drop an in-section drift line whose every item is fixed or retired. | `old` (one line); no `new` | The line carries `⚠` or the word `drift`; a whole-word fixed marker (`fixed`, `retired`, `resolved`, `done`); no whole-word open marker (`still`, `open`, `remaining`, `pending`, `todo`, `ongoing`, `in progress`, `partial`, `mid-migration`, `backlog`, `migrating`); no issue reference (`#` + three or more digits, `PR #`). The drift register is a global section and is never edited. | The line says it. The gate shows it. |

`old` is always whole lines, at most 12, occurring exactly once in your section. Conservative by design: when in doubt, leave the line.

**Never:** drop a convention, change a citation, change a closed-set value, renumber, remove a heading, edit the header or any global section, rewrite prose, or touch any file other than your edit-script file.

Resolve a basename anchor (`Foo.tsx:12`) by joining it to your section's `scope_globs` roots and `anchor_dirs` and checking which exist; if more than one exists, treat the anchor as ambiguous and leave it.

## What you return

Write the edit script as JSON to the path you were given, with a Bash heredoc (`cat > <path> <<'EOF' … EOF`). This is the one file you write. Then reply with that path and the edit count, nothing else. A section with nothing to shave gets `[]`.

```json
[
  {"section": "1. Entity Page", "class": "anchor",
   "old": "- Page is the single state owner; Body is presentation-only — `ContactsPage.tsx:200-208`, `ContactsBody.tsx:3,38-44`.",
   "dropped_anchor": "ContactsBody.tsx:3,38-44",
   "evidence": "read src/pages/entity/contact/ContactsPage.tsx:200-208 and ContactsBody.tsx:3,38-44; both show the same props-only Body"},
  {"section": "14. Testing conventions", "class": "duplicate",
   "old": "- Tokens are CSS custom properties — `src/theme/tokens.css:1-40` (restated; home is #9).",
   "new": "- See 9. Design system / primitives.",
   "owner": "9. Design system / primitives",
   "evidence": "owner states it at src/theme/tokens.css:1-40"},
  {"section": "3. SidePanel / PanelHost", "class": "fixed-drift",
   "old": "⚠ Drift: the hand-rolled focus trap was retired on 2026-07-04 and the `createPortal` half is fixed too.",
   "evidence": "line says so"}
]
```

## What the orchestrator does with it

`manifest.py verify` applies the checks above plus: `old` occurs exactly once inside its section, removes no heading, overlaps no other edit, and (for `anchor` and `duplicate` edits) leaves every anchor it removes still present somewhere in the manifest after all edits, so no citation vanishes (an anchor with a directory must survive with the same directory; a bare basename anchor is matched by basename). A file it cannot parse is reported as `UNUSABLE` and skipped; the other files still verify. **Bound:** verify checks these properties only. It does not judge whether a surviving anchor still supports its claim, does not open the codebase, and does not evaluate your comparison. Those are your job and the gate's. Rejected edits are listed with the failing check and excluded; the passing set goes to the gate, where the user accepts or skips by class or section, and `manifest.py apply` writes all-or-nothing.
