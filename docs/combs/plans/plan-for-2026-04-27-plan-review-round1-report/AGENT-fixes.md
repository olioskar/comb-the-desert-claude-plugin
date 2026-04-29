# AGENT-fixes — consolidated fix instructions

**Findings covered:** H1, L6, L12, L21 (agent-verification portion only)
**Target file:** `docs/superpowers/plans/2026-04-27-comb-the-desert-plugin.md`
**Affected tasks:** 15, 16, 17, 18, 19, 20

## What

- **H1** — Convert `disallowedTools` from YAML-list form to comma-separated string form in all 5 agent files (Tasks 15–19), matching the only form documented in the Claude Code plugins-reference.
- **L12** — Document an alternative read-only-by-allowlist approach (`tools: Read, Grep, Glob, Bash`) and let the executor pick H1 (denylist) or L12 (allowlist) when applying the fix.
- **L6** — Strengthen Task 20's frontmatter checks to validate field *values* (not just presence): each `name:` must equal the filename stem; `model:` must equal `opus`; `disallowedTools:` (or `tools:`) must contain the expected entries.
- **L21 (agent side)** — Fold the `name`-matches-filename-stem check for agents into Task 20 (the parallel skill-side check is handled in PROCESS-fixes).

## Why

H1 is a real safety risk: the plugins-reference page only documents `disallowedTools: Write, Edit` (comma-separated string). If the manifest parser rejects the YAML-list form silently, all 5 "read-only" reviewers ship with full Write/Edit/NotebookEdit permission and the read-only promise becomes body-text-only — unenforced by the manifest. L6 and L21 close verification gaps: the current Task 20 only proves frontmatter fields *exist*, so a typo (`name: code-revewer`), a wrong model (`model: sonnet`), or a malformed `disallowedTools` line could pass verification while breaking dispatch or safety. L12 is a recommended convention upgrade — an explicit allowlist is a stronger guarantee than a denylist (it can't be silently widened by a future tool addition), and the read-only reviewers genuinely only need `Read`, `Grep`, `Glob`, and `Bash` (for `gh pr diff` / `git diff` inspection).

## Where

- **H1**: Plan Task 15 Step 2 (frontmatter inside the embedded `agents/code-reviewer.md` markdown block); Task 16 Step 1 (`agents/simplifier.md`); Task 17 Step 1 (`agents/silent-failure-hunter.md`); Task 18 Step 1 (`agents/test-auditor.md`); Task 19 Step 1 (`agents/consistency-auditor.md`).
- **H1 (validation script)**: Plan Task 15 Step 3 — the embedded Python validation script asserts `'Write' in data['disallowedTools']`. Update assertion to match the chosen form.
- **L6 / L21 (agent side)**: Plan Task 20 — replace Step 2, replace Step 3, and add new Step 4 (renumbering current Step 4 "No commit needed" to Step 5).
- **L12 (recommended upgrade)**: Same locations as H1 — same five agent files, same validation script in Task 15 Step 3.

## How

### Reference: doc-supported frontmatter

Per `https://code.claude.com/docs/en/plugins-reference` ("Agents" section):

> Plugin agents support `name`, `description`, `model`, `effort`, `maxTurns`, `tools`, `disallowedTools`, `skills`, `memory`, `background`, and `isolation` frontmatter fields. […]
>
> ```markdown
> ---
> name: agent-name
> description: What this agent specializes in and when Claude should invoke it
> model: sonnet
> effort: medium
> maxTurns: 20
> disallowedTools: Write, Edit
> ---
> ```

The doc shows `disallowedTools` only in comma-separated-string form. `tools` is listed as a supported field (allowlist).

---

### H1 — Convert `disallowedTools` from YAML list to comma-separated string

**Affected:** All 5 agent files in plan Tasks 15, 16, 17, 18, 19. Each has the same frontmatter pattern.

**Before** (sample from Task 15 Step 2; the same three-line block appears in Tasks 16, 17, 18, 19):

```yaml
disallowedTools:
  - Write
  - Edit
  - NotebookEdit
```

**After:**

```yaml
disallowedTools: Write, Edit, NotebookEdit
```

Apply the identical change to all 5 agent files. The rest of each frontmatter block (`name`, `description`, `model`) is untouched.

**Also update the validation script in Task 15 Step 3.** It currently does:

```python
assert 'Write' in data['disallowedTools']
```

This works for both list and string forms (substring `in` works on strings) but is fragile. Replace with a tolerant check that handles both shapes and explicitly verifies the comma-separated form:

```python
import re, sys, yaml
with open('agents/code-reviewer.md') as f:
  content = f.read()
m = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
if not m:
  sys.exit('No frontmatter')
data = yaml.safe_load(m.group(1))
assert data['name'] == 'code-reviewer', f"name mismatch: {data.get('name')!r}"
assert data['model'] == 'opus', f"model mismatch: {data.get('model')!r}"
dt = data['disallowedTools']
assert isinstance(dt, str), f"disallowedTools must be a comma-separated string per plugins-reference, got {type(dt).__name__}"
tools = {t.strip() for t in dt.split(',')}
for required in ('Write', 'Edit', 'NotebookEdit'):
  assert required in tools, f"{required} missing from disallowedTools"
print('OK')
```

---

### L12 (recommended upgrade) — Use `tools:` allowlist instead of `disallowedTools:` denylist

**Tradeoff:**

- **Allowlist (`tools:`):** stronger guarantee. The agent can *only* use the listed tools — adding a new tool to Claude Code in the future cannot silently widen this agent's surface. Slightly more frontmatter to maintain; if the agent ever legitimately needs another tool (e.g., `WebFetch`), the allowlist must be updated.
- **Denylist (`disallowedTools:`):** smaller diff from current plan. Allows any tool *except* those listed. A future Claude Code release that adds, say, a `Patch` tool would silently grant it to these "read-only" agents until the denylist is updated.

For five reviewers whose entire purpose is read-only auditing, the allowlist is the safer convention.

**Recommended frontmatter for read-only reviewers** (replaces the `disallowedTools:` line entirely — do not keep both):

```yaml
tools: Read, Grep, Glob, Bash
```

`Bash` is included because reviewers may run read-only inspection commands such as `gh pr diff`, `gh pr view`, `git diff`, `git log`, `git show`, `npx tsc --noEmit`, and `npx vitest run`. If you want stronger isolation, drop `Bash` — but then the agent cannot run `gh pr diff` or test commands itself and must rely entirely on what the orchestrator preloads into its prompt.

**Decision required.** Pick one of the two approaches below and apply it to all 5 agents identically:

- **Option A — H1 only (denylist):** `disallowedTools: Write, Edit, NotebookEdit`
- **Option B — H1 + L12 (allowlist, recommended):** `tools: Read, Grep, Glob, Bash` (and remove the `disallowedTools` line)

Whichever option is chosen, apply it to *all five* agent frontmatter blocks (code-reviewer, simplifier, silent-failure-hunter, test-auditor, consistency-auditor) and update the Task 15 Step 3 validation script + the Task 20 verification (below) to match.

**If Option B is chosen, the Task 15 Step 3 validation script becomes:**

```python
import re, sys, yaml
with open('agents/code-reviewer.md') as f:
  content = f.read()
m = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
if not m:
  sys.exit('No frontmatter')
data = yaml.safe_load(m.group(1))
assert data['name'] == 'code-reviewer', f"name mismatch: {data.get('name')!r}"
assert data['model'] == 'opus', f"model mismatch: {data.get('model')!r}"
assert 'disallowedTools' not in data, "use tools: allowlist, not disallowedTools: denylist"
tools_field = data['tools']
assert isinstance(tools_field, str), f"tools must be a comma-separated string per plugins-reference, got {type(tools_field).__name__}"
tools = {t.strip() for t in tools_field.split(',')}
for required in ('Read', 'Grep', 'Glob', 'Bash'):
  assert required in tools, f"{required} missing from tools allowlist"
for forbidden in ('Write', 'Edit', 'NotebookEdit'):
  assert forbidden not in tools, f"{forbidden} must not appear in read-only reviewer's tools allowlist"
print('OK')
```

---

### L6 / L21 (agent side) — Strengthen Task 20 verification

The current Task 20 only checks that frontmatter fields are *present*; it does not validate values. Replace the body of Task 20 with the version below, which (a) verifies each `name:` equals its filename stem (closes L21 for agents), (b) verifies `model: opus`, (c) verifies the `disallowedTools` / `tools` field is in the documented comma-separated-string form and contains the expected entries, and (d) keeps the existing directory listing.

**Before — Task 20 Step 2 current text:**

```markdown
- [ ] **Step 2: Verify each has the required frontmatter fields**

```bash
for f in agents/*.md; do
  for field in name description model disallowedTools; do
    if ! grep -qE "^${field}:" "$f"; then
      echo "MISSING $field in $f"
    fi
  done
done
```

Expected: no output.
```

**Before — Task 20 Step 3 current text:**

```markdown
- [ ] **Step 3: Verify all 5 disallow Write/Edit/NotebookEdit**

```bash
for f in agents/*.md; do
  if ! grep -A 4 'disallowedTools:' "$f" | grep -q 'Write' || \
     ! grep -A 4 'disallowedTools:' "$f" | grep -q 'Edit' || \
     ! grep -A 4 'disallowedTools:' "$f" | grep -q 'NotebookEdit'; then
    echo "MISSING Write/Edit/NotebookEdit in disallowedTools: $f"
  fi
done
```

Expected: no output.
```

**After — replace Step 2 with this single value-checking step (covers H1, L6, L21, and L12 in one script). Then *delete* the old Step 3 entirely and renumber the old "Step 4: No commit needed" to "Step 4".**

```markdown
- [ ] **Step 2: Verify frontmatter values match the spec**

For each agent file, this single Python script checks:
- `name:` equals the filename stem (catches typos like `name: code-revewer`)
- `model:` equals `opus` (catches accidental `sonnet`)
- The read-only safety field (`disallowedTools:` denylist OR `tools:` allowlist — whichever was adopted) is present, parses as a comma-separated string per the plugins-reference, and contains the right entries.

```bash
python3 - <<'PY'
import os, re, sys, yaml, glob

# What "read-only" means for each option:
DENYLIST_REQUIRED = {"Write", "Edit", "NotebookEdit"}
ALLOWLIST_REQUIRED = {"Read", "Grep", "Glob", "Bash"}
ALLOWLIST_FORBIDDEN = {"Write", "Edit", "NotebookEdit"}

errors = []
files = sorted(glob.glob("agents/*.md"))
assert len(files) == 5, f"expected 5 agent files, got {len(files)}: {files}"

for path in files:
    stem = os.path.splitext(os.path.basename(path))[0]
    with open(path) as fh:
        content = fh.read()
    m = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not m:
        errors.append(f"{path}: no YAML frontmatter")
        continue
    try:
        data = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        errors.append(f"{path}: invalid YAML frontmatter: {e}")
        continue

    # name must match filename stem (closes L21 for agents)
    if data.get("name") != stem:
        errors.append(f"{path}: name {data.get('name')!r} != filename stem {stem!r}")

    # model must be opus
    if data.get("model") != "opus":
        errors.append(f"{path}: model {data.get('model')!r} != 'opus'")

    # description must be a non-empty string
    desc = data.get("description")
    if not isinstance(desc, str) or not desc.strip():
        errors.append(f"{path}: description missing or empty")

    # Read-only enforcement: accept EITHER tools allowlist OR disallowedTools denylist,
    # but the field must be a comma-separated string (the only form documented in
    # the plugins-reference). YAML-list form is rejected — it may parse as an empty
    # array and silently grant the agent full tool access.
    has_tools = "tools" in data
    has_disallowed = "disallowedTools" in data
    if has_tools and has_disallowed:
        errors.append(f"{path}: set tools OR disallowedTools, not both")
    elif not has_tools and not has_disallowed:
        errors.append(f"{path}: must set tools (allowlist) or disallowedTools (denylist)")
    elif has_tools:
        v = data["tools"]
        if not isinstance(v, str):
            errors.append(f"{path}: tools must be a comma-separated string per plugins-reference, got {type(v).__name__}")
        else:
            entries = {t.strip() for t in v.split(",") if t.strip()}
            for required in ALLOWLIST_REQUIRED:
                if required not in entries:
                    errors.append(f"{path}: tools allowlist missing {required!r}")
            for forbidden in ALLOWLIST_FORBIDDEN:
                if forbidden in entries:
                    errors.append(f"{path}: read-only agent must not allow {forbidden!r}")
    else:  # has_disallowed
        v = data["disallowedTools"]
        if not isinstance(v, str):
            errors.append(f"{path}: disallowedTools must be a comma-separated string per plugins-reference, got {type(v).__name__}")
        else:
            entries = {t.strip() for t in v.split(",") if t.strip()}
            for required in DENYLIST_REQUIRED:
                if required not in entries:
                    errors.append(f"{path}: disallowedTools missing {required!r}")

if errors:
    print("FAIL")
    for e in errors:
        print(" -", e)
    sys.exit(1)
print("OK")
PY
```

Expected output: `OK`

(If `pyyaml` is unavailable, install with `pip3 install pyyaml`.)
```

**After — old Step 3 is deleted. Renumber the old "Step 4: No commit needed" to "Step 3":**

```markdown
- [ ] **Step 3: No commit needed (verification only).**
```

Result: Task 20 has exactly two checkbox steps — Step 1 (`ls -1 agents/`, unchanged) and Step 2 (the value-checking script above) — plus the no-commit note as Step 3.

## Expected Outcome

After applying:

- All 5 agent files declare their read-only posture in the documented comma-separated-string form, so the Claude Code parser actually enforces it (H1 closed).
- Either approach (denylist or allowlist) is acceptable; the Task 15 Step 3 validation script and Task 20 Step 2 script accept whichever was adopted (L12 documented).
- Task 20 catches: typos in `name:` (e.g., `code-revewer`), wrong `model:` values (e.g., `sonnet`), missing or empty `description`, malformed `disallowedTools`/`tools` (YAML-list form rejected), missing required tool entries, and forbidden tools in an allowlist (L6 and the agent side of L21 closed).
- Read-only safety is enforced by the manifest schema, not just by the agent body's "you are read-only" sentence.

## Scope

**In scope:** edits to the 5 agent file frontmatter blocks embedded in plan Tasks 15 Step 2, 16 Step 1, 17 Step 1, 18 Step 1, 19 Step 1; the Python validation script in Task 15 Step 3; and the verification steps inside Task 20 (replace Step 2, delete Step 3, renumber).

**Out of scope:** any change to skill bodies (Tasks 21–24), directives (Tasks 6–13), the directives-verification task (Task 14), the manifest/marketplace JSON, the SKILL.md `name`-matches-directory check (handled in PROCESS-fixes), or any agent system-prompt body text below the frontmatter.
