# PROCESS-fixes — consolidated fix instructions

**Findings covered:** M4, M7, M8, M10, L3, L7, L8, L9, L10, L11, L13, L14, L15, L16, L17, L19, L20, TG1
**Target file:** `docs/superpowers/plans/2026-04-27-comb-the-desert-plugin.md`
**Affected tasks:** Phase 0, Task 20, Task 25, Task 28, Task 29, Task 30, Self-review section, plus one new task (Task 28.5)

---

## What

Grouped by affected task for readability:

**Phase 0**
- M10 — Reword the "previous attempt" wording so it doesn't flag legitimate brainstorm artifacts (`docs/`, `DESIGN.md`, `.gitignore`).
- L9 — Extend the prereq check to include `python3`, PyYAML (`python3 -c 'import yaml'`), `gh`, and `npx`.
- M7 — Once PyYAML is a Phase 0 prereq, the `import yaml` snippets in Tasks 15 and 21 stop failing with `ModuleNotFoundError`.

**Task 20**
- L7 — Replace the fragile `grep -A 4 ... | grep -q ...` window check with a PyYAML-based parser check (now safe, since PyYAML is a Phase 0 prereq).
- L8 — Guard the `for f in agents/*.md` loop against empty-glob expansion.

**Task 25**
- L3 — Verify `argument-hint`, `allowed-tools`, and `user-invocable` (currently only `disable-model-invocation` is checked).
- L15 — Replace fragile anchored greps with a PyYAML-based structural parse.
- L21 — Verify each skill's `name:` matches its directory name.
- L8 — Guard the `for d in skills/*/` loop against empty-glob expansion.

**Task 28**
- M4 — Make the cwd of the `claude --plugin-dir ...` invocation explicit.
- M8 — Drop the verdict-specific assertion ("Verdict is APPROVE"); assert structural shape instead.
- L19 / L20 — Pick one path: "create a fresh test repo." Drop the "navigate to a small test repo (any git repo with a recent commit)" wording.
- L16 — Add a `claude plugin validate` step before the runtime smoke test.

**Task 28.5 (NEW)**
- TG1 — Fixture-driven structural test of skill-body claims (config-merge `null`-as-delete + agent palette cap of 5).

**Task 29**
- L13 — Note that the `marketplace remove` slash-command syntax is undocumented; offer a safe fallback (skip cleanup or verify with `/plugin help`).
- L14 — Add an explicit "GitHub repo exists" precondition step before the install attempt.

**Task 30**
- L10 — Add a step documenting the version-bump rhythm for future releases.

**Self-review section**
- L17 — Soften "every task has actual content" to acknowledge runtime placeholders (`{...}`) inside skill-body templates.

**Documentation**
- L11 — Add a CHANGELOG (or README) note that `marketplace.json`'s schema was empirically verified via the Task 29 smoke test, since plugins-reference does not fully document it.

## Why

These are mostly verification, prereq, and smoke-test improvements. Individually small but together they make the plan more reliable to execute: the executor catches missing tools before mid-task failures, the verification commands check more (and aren't fooled by formatting variation), the smoke test is deterministic instead of dependent on agent judgment, plugin-validate catches manifest/frontmatter errors early, and a new structural test exercises the spec §4.1 merge semantics and §7.1.4 cap/floor at least once. Finally, the version-bump workflow is documented so future releases don't silently fail to update users.

## Where

- `docs/superpowers/plans/2026-04-27-comb-the-desert-plugin.md` — Phase 0 (lines ~17–35), Task 20 Step 2–3 (lines ~1603–1629), Task 25 Steps 2–4 (lines ~2513–2549), Task 28 Steps 1–3 (lines ~2774–2828), insertion point between Task 28 and Task 29 (line ~2838), Task 29 Steps 1 + 4 (lines ~2847–2880), Task 30 Step 7 / new Step 8 (lines ~2940–2941), self-review placeholder-scan paragraph (line ~2965).

---

## How

### Phase 0 — Strengthen prereq checks (L9, M7, M10)

**Affected:** Phase 0 Step 1 + Step 2 (lines ~21–35)

#### M10 — Reword Phase 0 Step 1 "previous attempt" wording

**Before:**

```
- [ ] **Confirm working directory is empty (or only contains the planning artifacts).**

```bash
ls -1 /Users/olafur/Development/comb-the-desert-claude-skill
```

Expected: only `docs/`, `DESIGN.md`, `.gitignore`. Anything else suggests a previous attempt — investigate before continuing.
```

**After:**

```
- [ ] **Confirm working directory contains only the brainstorm artifacts.**

```bash
ls -1 /Users/olafur/Development/comb-the-desert-claude-skill
```

Expected: `docs/`, `DESIGN.md`, `.gitignore` (these were produced during brainstorming and are committed/intended state). Anything other than these three entries may indicate a previous implementation attempt — investigate and clean before continuing.
```

#### L9 + M7 — Extend Phase 0 Step 2 prereq check

**Before:**

```
- [ ] **Verify `git`, `jq`, and `claude` CLI are installed.**

```bash
git --version && jq --version && which claude
```

Expected: versions printed, `claude` path reported.
```

**After:**

```
- [ ] **Verify all required CLIs and Python deps are installed.**

```bash
# Core CLIs used directly by the plan
git --version && \
jq --version && \
which claude && \
gh --version && \
npx --version && \
python3 --version

# PyYAML is required by validation snippets in Tasks 15, 20, 21, and 25.
# macOS system Python does NOT bundle it.
python3 -c 'import yaml; print("pyyaml", yaml.__version__)'
```

Expected: every command prints a version (or path, for `which claude`) and `python3 -c 'import yaml'` prints `pyyaml <version>`.

If `python3 -c 'import yaml'` fails with `ModuleNotFoundError`, install PyYAML first:

```bash
python3 -m pip install --user pyyaml
```

Then re-run the verification block before proceeding to Phase 1. **Do not start Phase 1 until every line of this block succeeds** — Tasks 15, 20, 21, 25, 28, 29, and 30 all assume these tools are present.
```

(This single update closes L9 — `python3`, `pyyaml`, `gh`, `npx` are all checked — and removes the M7 surprise, because PyYAML is now a documented prereq instead of an undocumented assumption inside the validation snippets.)

---

### Task 20 — Strengthen agent verification (L7, L8)

**Affected:** Task 20 Steps 2 and 3 (lines ~1603–1629)

**Before (Step 2):**

```bash
for f in agents/*.md; do
  for field in name description model disallowedTools; do
    if ! grep -qE "^${field}:" "$f"; then
      echo "MISSING $field in $f"
    fi
  done
done
```

**After (Step 2):**

```bash
shopt -s nullglob
agents=(agents/*.md)
shopt -u nullglob
if [ ${#agents[@]} -eq 0 ]; then
  echo "FAIL: no agent files found under agents/"
  exit 1
fi

for f in "${agents[@]}"; do
  for field in name description model disallowedTools; do
    if ! grep -qE "^${field}:" "$f"; then
      echo "MISSING $field in $f"
    fi
  done
done
```

**Before (Step 3):**

```bash
for f in agents/*.md; do
  if ! grep -A 4 'disallowedTools:' "$f" | grep -q 'Write' || \
     ! grep -A 4 'disallowedTools:' "$f" | grep -q 'Edit' || \
     ! grep -A 4 'disallowedTools:' "$f" | grep -q 'NotebookEdit'; then
    echo "MISSING Write/Edit/NotebookEdit in disallowedTools: $f"
  fi
done
```

**After (Step 3):**

Use a PyYAML-based parse so the check survives reordering and whitespace variation. PyYAML is now a Phase 0 prereq.

```bash
shopt -s nullglob
agents=(agents/*.md)
shopt -u nullglob
[ ${#agents[@]} -gt 0 ] || { echo "FAIL: no agent files found under agents/"; exit 1; }

for f in "${agents[@]}"; do
  python3 - "$f" <<'PY'
import re, sys, yaml
path = sys.argv[1]
with open(path) as fh:
    body = fh.read()
m = re.match(r'^---\n(.*?)\n---', body, re.DOTALL)
if not m:
    print(f"MISSING frontmatter: {path}")
    sys.exit(0)
data = yaml.safe_load(m.group(1)) or {}
disallowed = data.get('disallowedTools')

# Accept either YAML-list form or comma-separated string form
if isinstance(disallowed, str):
    items = {s.strip() for s in disallowed.split(',') if s.strip()}
elif isinstance(disallowed, list):
    items = set(disallowed)
else:
    print(f"MISSING disallowedTools (or wrong type): {path}")
    sys.exit(0)

required = {'Write', 'Edit', 'NotebookEdit'}
missing = required - items
if missing:
    print(f"MISSING {sorted(missing)} in disallowedTools: {path}")

# Also confirm name matches filename and model is opus
import os
expected_name = os.path.splitext(os.path.basename(path))[0]
if data.get('name') != expected_name:
    print(f"NAME MISMATCH: file={path} name={data.get('name')} expected={expected_name}")
if data.get('model') != 'opus':
    print(f"MODEL MISMATCH: file={path} model={data.get('model')} expected=opus")
PY
done
```

Expected: no output.

(This single replacement closes L7's window-grep fragility, L8's empty-glob fragility, and folds in L6's name/model checks for the agent-side verification — same parser-based approach Task 25 will use.)

---

### Task 25 — Strengthen skill verification (L3, L8, L15, L21)

**Affected:** Task 25 Steps 2, 3, 4 (lines ~2513–2549)

Replace Steps 2, 3, and 4 with a single PyYAML-driven structural check. The agent-side `disable-model-invocation` check has already been handled in Task 25's existing Steps 3 and 4 — we extend it to verify the rest of the §7.2 frontmatter contract (`argument-hint`, `allowed-tools`, `user-invocable`) and confirm `name:` matches the directory name.

**Before (Steps 2, 3, 4 combined):**

```bash
# Step 2 — verify each has SKILL.md
for d in skills/*/; do
  if [ ! -f "${d}SKILL.md" ]; then
    echo "MISSING SKILL.md: $d"
  fi
done

# Step 3 — destructive skills require disable-model-invocation: true
for skill in fix the-desert; do
  if ! grep -q '^disable-model-invocation: true$' "skills/$skill/SKILL.md"; then
    echo "MISSING disable-model-invocation: skills/$skill/SKILL.md"
  fi
done

# Step 4 — read-only skills require disable-model-invocation: false
for skill in review plan; do
  if ! grep -q '^disable-model-invocation: false$' "skills/$skill/SKILL.md"; then
    echo "MISSING disable-model-invocation: false: skills/$skill/SKILL.md"
  fi
done
```

**After (single combined step — replace Steps 2–4 with this one new "Step 2: Structurally verify all skill frontmatter"):**

```bash
shopt -s nullglob
skill_dirs=(skills/*/)
shopt -u nullglob
[ ${#skill_dirs[@]} -gt 0 ] || { echo "FAIL: no skill dirs under skills/"; exit 1; }

# Files must exist
for d in "${skill_dirs[@]}"; do
  [ -f "${d}SKILL.md" ] || { echo "MISSING SKILL.md: $d"; exit 1; }
done

# Structural verification via PyYAML
python3 - <<'PY'
import os, re, sys, yaml, pathlib

DESTRUCTIVE = {'fix', 'the-desert'}     # must have disable-model-invocation: true
READ_ONLY   = {'review', 'plan'}        # must have disable-model-invocation: false

REQUIRED_FIELDS = {'name', 'description', 'argument-hint', 'allowed-tools',
                   'user-invocable', 'disable-model-invocation'}

errors = []
for skill_dir in sorted(pathlib.Path('skills').iterdir()):
    if not skill_dir.is_dir():
        continue
    skill_name = skill_dir.name
    f = skill_dir / 'SKILL.md'
    body = f.read_text()
    m = re.match(r'^---\n(.*?)\n---', body, re.DOTALL)
    if not m:
        errors.append(f"{f}: missing YAML frontmatter")
        continue
    data = yaml.safe_load(m.group(1)) or {}

    # Required-field presence
    missing = REQUIRED_FIELDS - set(data.keys())
    if missing:
        errors.append(f"{f}: missing fields {sorted(missing)}")

    # name matches directory
    if data.get('name') != skill_name:
        errors.append(f"{f}: name={data.get('name')!r} != dir {skill_name!r}")

    # user-invocable must be a real boolean True
    if data.get('user-invocable') is not True:
        errors.append(f"{f}: user-invocable must be true (got {data.get('user-invocable')!r})")

    # disable-model-invocation must be a real boolean and match the destructive/read-only contract
    dmi = data.get('disable-model-invocation')
    if not isinstance(dmi, bool):
        errors.append(f"{f}: disable-model-invocation must be a boolean (got {dmi!r})")
    elif skill_name in DESTRUCTIVE and dmi is not True:
        errors.append(f"{f}: destructive skill must have disable-model-invocation: true (got {dmi!r})")
    elif skill_name in READ_ONLY and dmi is not False:
        errors.append(f"{f}: read-only skill must have disable-model-invocation: false (got {dmi!r})")

    # allowed-tools must be a non-empty list (or comma-separated string)
    tools = data.get('allowed-tools')
    if isinstance(tools, str):
        tool_set = {t.strip() for t in tools.split(',') if t.strip()}
    elif isinstance(tools, list):
        tool_set = set(tools)
    else:
        tool_set = set()
        errors.append(f"{f}: allowed-tools must be a list or comma-separated string (got {type(tools).__name__})")
    if tool_set and not tool_set:
        errors.append(f"{f}: allowed-tools is empty")

    # argument-hint must be a non-empty string
    hint = data.get('argument-hint')
    if not isinstance(hint, str) or not hint.strip():
        errors.append(f"{f}: argument-hint must be a non-empty string (got {hint!r})")

if errors:
    for e in errors:
        print(e)
    sys.exit(1)
print("OK — all 4 skills pass structural verification.")
PY
```

Expected output: `OK — all 4 skills pass structural verification.`

Steps 3 and 4 (the original `disable-model-invocation` greps) are now subsumed by Step 2 above and should be **deleted**. Renumber the existing "Step 5: No commit needed" to "Step 3: No commit needed."

(Closes L3, L8, L15, and L21 in one consolidated check.)

---

### Task 28 — Smoke test fixes (M4, M8, L16, L19, L20)

**Affected:** Task 28 Steps 1–3 (lines ~2774–2828).

#### L19 / L20 + M4 — Pick one path (create fresh test repo) and make cwd explicit

**Before (Step 1):**

```
- [ ] **Step 1: Verify plugin loads via `--plugin-dir`**

In a separate terminal, navigate to a small test repo (any git repo with a recent commit):

```bash
cd /tmp
mkdir -p comb-smoke-test && cd comb-smoke-test
git init -q
echo 'console.log("hello");' > app.js
git add app.js
git commit -q -m "initial"
echo 'console.log("hello world");' > app.js
git add app.js
git commit -q -m "say world"
```

Then launch Claude with the plugin:

```bash
claude --plugin-dir /Users/olafur/Development/comb-the-desert-claude-skill
```

Inside Claude:

```
/help
```

Expected: the slash menu lists `/comb:review`, `/comb:plan`, `/comb:fix`, `/comb:the-desert`. The agents appear in the agent list as `comb:code-reviewer`, etc.

If any are missing, check:
- `.claude-plugin/plugin.json` is valid JSON
- Skill directories all contain `SKILL.md`
- Agent `.md` files all have valid frontmatter
```

**After (Step 1 — replaced with a Step 1 + new Step 1.5 + Step 2 structure):**

```
- [ ] **Step 1: Create a fresh test repo**

Always create a new throwaway repo under `/tmp` — do not reuse an existing project. This keeps the smoke test deterministic.

In a separate terminal:

```bash
rm -rf /tmp/comb-smoke-test
mkdir -p /tmp/comb-smoke-test
cd /tmp/comb-smoke-test
git init -q
echo 'console.log("hello");' > app.js
git add app.js
git commit -q -m "initial"
echo 'console.log("hello world");' > app.js
git add app.js
git commit -q -m "say world"
```

- [ ] **Step 2: Validate the plugin manifest before launching Claude**

`claude plugin validate` catches manifest and frontmatter errors before runtime.

```bash
claude plugin validate /Users/olafur/Development/comb-the-desert-claude-skill
```

Expected: validation reports the plugin parses cleanly. If it errors, fix the reported issue before proceeding.

(If `claude plugin validate` is not available on the installed `claude` CLI version, note this in the smoke-test results and rely on `/plugin` slash-command output inside Claude as the validation step instead.)

- [ ] **Step 3: Launch Claude with the plugin**

Still in `/tmp/comb-smoke-test` (this matters — `/comb:review` operates on the cwd as the project root):

```bash
# pwd should print /tmp/comb-smoke-test
pwd
claude --plugin-dir /Users/olafur/Development/comb-the-desert-claude-skill
```

Inside Claude:

```
/help
```

Expected: the slash menu lists `/comb:review`, `/comb:plan`, `/comb:fix`, `/comb:the-desert`. The agents appear in the agent list as `comb:code-reviewer`, etc.

If any are missing, check:
- `.claude-plugin/plugin.json` is valid JSON
- Skill directories all contain `SKILL.md`
- Agent `.md` files all have valid frontmatter
```

#### M8 — Relax verdict expectation

**Before (existing Step 2 — will be renumbered to Step 4):**

```
- [ ] **Step 2: Run a review against the test repo**

```
/comb:review
```

Expected:
- The orchestrator picks 1–3 agents (small diff, so palette will be small)
- Verification checks run (some may fail in the toy repo — note in the report)
- A report is written to `<test-repo>/docs/combs/reviews/branch-main-round1-report.md` (or similar)
- Verdict is APPROVE (no real issues in the toy diff)
```

**After (renumbered to Step 4):**

```
- [ ] **Step 4: Run a review against the test repo**

```
/comb:review
```

Expected (structural — does not depend on agent verdict judgment):
- The orchestrator picks 1–3 agents (small diff, so the palette will be small).
- Verification checks run (some may fail in the toy repo — that's fine; expect them noted in the report).
- A report file is written under `<test-repo>/docs/combs/reviews/` matching the pattern `branch-*-round1-report.md` (the exact slug depends on the branch name).
- The report contains all standard sections: `Verification Summary`, `Verdict`, `Findings by Severity` (with at least the canonical sub-headings: `Critical`, `High`, `Medium`, `Low`, `Test Gaps`, `Deferred`).

**Do NOT** assert a specific verdict (`APPROVE` vs `NEEDS WORK`). Either is acceptable for a toy diff — the agent's judgment is not the property under test here. The property under test is "the plugin loaded and produced a structurally complete report."
```

#### Renumber the remaining Task 28 steps

After the changes above, the step list for Task 28 becomes:

- Step 1: Create a fresh test repo
- Step 2: Validate the plugin manifest before launching Claude (NEW — closes L16)
- Step 3: Launch Claude with the plugin (was Step 1)
- Step 4: Run a review against the test repo (was Step 2; M8 applied)
- Step 5: Verify the report file exists and has the expected structure (unchanged content)
- Step 6: Clean up the test repo (was Step 4)
- Step 7: No commit needed (was Step 5)

Update the `cat /tmp/comb-smoke-test/docs/combs/reviews/*.md` step's expected output to mirror M8's relaxed structural assertion (e.g., "shows the standard sections; verdict may be `APPROVE` or `NEEDS WORK` — either is fine.").

---

### Task 28.5 (NEW) — Structural test for skill-body claims (TG1)

Insert this brand-new task between Task 28 and Task 29 (line ~2838). Number it **Task 28.5** so it sits between the runtime smoke test (28) and the marketplace install test (29) without renumbering everything downstream.

```
### Task 28.5: Fixture-driven structural test for skill-body invariants

**Files:**
- (Test only — no source files modified)

**Goal:** Confirm two skill-body invariants from the spec are actually honored at runtime:
- §4.1 merge semantics: `null` at any depth deletes that key from the merged config (here: `agents.simplifier: null` removes `simplifier` from the dispatched palette).
- §7.1.4 agent-picking cap: a varied diff that would surface >5 candidate agents is capped at exactly 5, and `code-reviewer` is always included (soft floor 1, always-on).

These two assertions cannot be verified by manifest validation or runtime smoke alone — they exercise orchestrator logic in the skill body.

- [ ] **Step 1: Create fixture repo A — `null`-as-delete merge**

```bash
rm -rf /tmp/comb-fixture-a
mkdir -p /tmp/comb-fixture-a/.claude
cd /tmp/comb-fixture-a
git init -q
git commit -q --allow-empty -m "initial"

# Project-level config that disables the simplifier role via null
cat > .claude/comb.config.json <<'JSON'
{
  "agents": {
    "simplifier": null
  }
}
JSON

# Trivial diff so the picker would otherwise consider simplifier
echo 'function greet(name) { return "hi " + name; }' > greet.js
git add .claude greet.js
git commit -q -m "add greet"
echo 'function greet(name) { return `hi ${name}`; }' > greet.js  # template-string refactor — would normally trigger simplifier
git add greet.js
git commit -q -m "use template string"
```

Launch Claude (still inside `/tmp/comb-fixture-a`):

```bash
pwd  # /tmp/comb-fixture-a
claude --plugin-dir /Users/olafur/Development/comb-the-desert-claude-skill
```

Inside Claude:

```
/comb:review
```

When the skill announces its picks ("Picking code-reviewer (always), simplifier (...), ..."), confirm:
- `simplifier` is **not** in the announced palette
- The palette includes `code-reviewer` (always-on)

If `simplifier` appears, the merge logic is broken — file as a finding before proceeding.

- [ ] **Step 2: Create fixture repo B — agent-palette cap of 5**

```bash
rm -rf /tmp/comb-fixture-b
mkdir -p /tmp/comb-fixture-b
cd /tmp/comb-fixture-b
git init -q
git commit -q --allow-empty -m "initial"

# A varied diff designed to surface every shipped role:
#   - bugs/logic         -> code-reviewer
#   - refactor/dead code -> simplifier
#   - error handling     -> silent-failure-hunter
#   - tests              -> test-auditor
#   - existing patterns  -> consistency-auditor
# All five appear in the diff so a naive picker would return 5 anyway.
# Then add a sixth signal (a directive-coupled doc change) that, with default config,
# should still cap the palette at 5 and prefer the always-on roles.

mkdir -p src tests docs
cat > src/api.js <<'JS'
async function fetchUser(id) {
  try { return await api.get('/u/' + id); } catch (e) { console.error(e); return null; }
}
module.exports = { fetchUser };
JS
cat > tests/api.test.js <<'JS'
test('fetchUser returns null on error', () => {
  // mock-only test — should be flagged by test-auditor
  expect(true).toBe(true);
});
JS
cat > docs/style.md <<'MD'
# Style guide

Write functions like `getUser`, not `fetch_user`.
MD

git add src tests docs
git commit -q -m "initial impl"

# Make a varied edit across all five surfaces:
echo "function unused() {}" >> src/api.js                    # dead code (simplifier)
sed -i.bak 's/console.error(e); return null;/return null;/' src/api.js  # silent failure (silent-failure-hunter)
rm src/api.js.bak
echo "test('another mock test', () => expect(1).toBe(1));" >> tests/api.test.js  # vanity test (test-auditor)
echo "Use snake_case for new APIs." >> docs/style.md         # contradicts existing convention (consistency-auditor)
git add -A
git commit -q -m "varied changes across all reviewer surfaces"
```

Launch Claude (still inside `/tmp/comb-fixture-b`):

```bash
pwd  # /tmp/comb-fixture-b
claude --plugin-dir /Users/olafur/Development/comb-the-desert-claude-skill
```

Inside Claude:

```
/comb:review
```

When the skill announces its picks, confirm:
- The palette has **at most 5 agents**.
- `code-reviewer` is in the palette (always-on).
- The skill's announced rationale acknowledges that more than 5 candidates were considered (or that the cap was hit).

If more than 5 agents are picked, the cap logic is broken — file as a finding before proceeding.

- [ ] **Step 3: Clean up fixtures**

```bash
rm -rf /tmp/comb-fixture-a /tmp/comb-fixture-b
```

- [ ] **Step 4: No commit needed (test only).**
```

(Closes TG1.)

---

### Task 29 — Marketplace install smoke test (L13, L14)

**Affected:** Task 29 (lines ~2840–2882).

#### L14 — Add explicit "GitHub repo exists" precondition step

Insert a new **Step 0** before the existing Step 1, so Task 29 is no longer ambiguously dependent on Task 30 having pushed.

**New Step 0 (insert at line ~2847, before "Step 1: Add the marketplace from the GitHub URL"):**

```
- [ ] **Step 0: Confirm the GitHub repo exists and `main` is pushed**

This task installs from `olioskar/comb-the-desert-claude-plugin`. Confirm it is reachable before invoking the marketplace add. If the repo doesn't exist yet, complete Task 30 (push to GitHub) first, then return here.

```bash
gh repo view olioskar/comb-the-desert-claude-plugin --json url,defaultBranchRef,pushedAt
```

Expected: JSON output naming the repo URL, the default branch (`main`), and a recent `pushedAt` timestamp. Errors here (repo not found, 404) mean Task 30 hasn't run yet — go do Task 30 first.

If the repo doesn't exist at all, create it now (one-time):

```bash
gh repo create olioskar/comb-the-desert-claude-plugin --public --source=. --remote=origin --description "comb the desert: review/plan/fix Claude Code plugin"
```

Then run Task 30's push steps before returning to this task.
```

Update the existing parenthetical at the top of Task 29 ("This test verifies the marketplace install path works. Requires pushing the repo to GitHub first; if the repo isn't pushed yet, defer this task to after Task 30.") to:

> This test verifies the marketplace install path works. Requires the GitHub repo to exist and `main` to be pushed (Task 30). Step 0 below confirms this before proceeding.

#### L13 — Note the `marketplace remove` uncertainty

**Before (Step 4):**

```
- [ ] **Step 4: Uninstall (to clean up)**

```
/plugin uninstall comb
/plugin marketplace remove comb-marketplace
```
```

**After (Step 4):**

```
- [ ] **Step 4: Uninstall (to clean up — best effort)**

```
/plugin uninstall comb
```

The `comb` plugin is now uninstalled. To also remove the marketplace entry:

```
/plugin marketplace remove comb-marketplace
```

The exact `marketplace remove` slash-command syntax is not fully documented in the in-scope plugins reference. If the command above isn't recognized:

1. Run `/plugin help` and look for the documented removal syntax for marketplaces.
2. If still unclear, **skip this step**. Leaving the marketplace registered locally is harmless — it just means the marketplace entry persists in the local Claude Code installation, which is fine.

(Document the actual syntax in the README and CHANGELOG if you discover it during this smoke test.)
```

---

### Task 30 — Release process (L10)

**Affected:** Task 30 (lines ~2886–2941).

#### L10 — Document the version-bump workflow for future releases

Add a new **Step 8** at the end of Task 30 (after the existing Step 7 — line ~2940):

```
- [ ] **Step 8: Document the version-bump rhythm for future releases**

Per Claude Code's plugins-reference, users only see a plugin update when the `version` field in `.claude-plugin/plugin.json` changes. This plan ships `0.1.0`. For every subsequent release:

1. Bump `version` in `.claude-plugin/plugin.json` (semver: patch for fixes, minor for additive features, major for breaking config/skill-contract changes).
2. Add a `## [<new-version>] — YYYY-MM-DD` entry to `CHANGELOG.md` summarizing user-visible changes.
3. Commit the bump and changelog as one commit: `git commit -m "chore: release v<new-version>"`.
4. Tag and push: `git tag -a v<new-version> -m "v<new-version>"` then `git push origin main v<new-version>`.

Append this rhythm to `CHANGELOG.md` directly under the top header (above `## [Unreleased]`) so future maintainers see it:

```markdown
> **Releasing a new version:** bump `version` in `.claude-plugin/plugin.json`, add a changelog entry, commit as `chore: release vX.Y.Z`, then `git tag -a vX.Y.Z -m "vX.Y.Z"` and push both `main` and the tag. Users only see updates when `version` changes.
```

Commit the CHANGELOG note:

```bash
git add CHANGELOG.md
git commit -m "docs: document release/version-bump workflow"
```

(This commit is allowed *after* the v0.1.0 tag — it becomes part of the next release.)
```

---

### Self-review section — soften absolute claim (L17)

**Affected:** Self-review section, "Placeholder scan" paragraph (line ~2965).

**Before:**

```
Placeholder scan: no `TBD`, no `TODO`, no `add appropriate handling`, no `similar to Task N`. Every task has actual content.
```

**After:**

```
Placeholder scan: no `TBD`, no `TODO`, no `add appropriate handling`, no `similar to Task N`. Every task has actual content. (Note: skill bodies in Tasks 21–24 contain `{placeholder}` tokens — e.g., `{focus_brief if present}`, `{N}/{total}`, `{verdict}`. These are **runtime template slots** Claude fills in when the skill executes, not plan-stage gaps. They are intentional and required.)
```

---

### M7 — PyYAML prereq follow-up

Already addressed via L9 in Phase 0. No additional change in Tasks 15 or 21 — once PyYAML is verified at Phase 0, the existing `import yaml` snippets in those tasks work as written. The plan's existing parenthetical about `pip3 install pyyaml` inside Task 15/21 can be **removed** as redundant if desired (cleanup-optional, not required).

---

### L11 — `marketplace.json` schema empirical-verification note

**Affected:** Either README's Install section or CHANGELOG's `[0.1.0]` entry (Task 26 / Task 27).

Add a short note to the v0.1.0 CHANGELOG entry (Task 27) under a new "Notes" subheading, so the empirical-verification approach is recorded for future maintainers:

**Before (Task 27 v0.1.0 entry):**

```markdown
- Same-repo marketplace manifest (`.claude-plugin/marketplace.json`) for `/plugin marketplace add` install path
```

**After (Task 27 v0.1.0 entry — append a Notes subheading):**

```markdown
- Same-repo marketplace manifest (`.claude-plugin/marketplace.json`) for `/plugin marketplace add` install path

### Notes

- The `marketplace.json` schema used here matches the conventional shape from `anthropics/claude-code` and was empirically verified during release via the Task 29 smoke test (`/plugin marketplace add` + `/plugin install`). The plugins-reference docs do not fully enumerate the schema, so any schema changes in future releases must re-run the marketplace install smoke test.
```

---

## Expected Outcome

After applying all of the above:

- **Phase 0** catches missing `python3`, `pyyaml`, `gh`, and `npx` before Tasks 15, 20, 21, 25, 28, 29, or 30 fail mid-execution. The "previous attempt" wording no longer flags legitimate brainstorm artifacts as suspicious.
- **Task 20** verification uses a PyYAML structural parse instead of `grep -A 4 ... | grep -q ...`, so it survives reordering and whitespace variation, and also confirms `name` matches filename and `model: opus`.
- **Task 25** verification uses a single PyYAML structural parse to verify `name`, `description`, `argument-hint`, `allowed-tools`, `user-invocable`, and `disable-model-invocation` — including that `name` matches the directory and that the destructive/read-only `disable-model-invocation` contract holds. Empty-glob fragility is gone.
- **Task 28** smoke test is fully deterministic (always creates a fresh repo), the cwd of `claude --plugin-dir` is explicit, `claude plugin validate` runs first to catch manifest/frontmatter errors, and the report assertion is structural (sections present) rather than dependent on agent verdict judgment.
- **Task 28.5 (new)** exercises spec §4.1 merge semantics and §7.1.4 cap/floor at least once via two fixture repos — closing the most important test gap.
- **Task 29** has an explicit "GitHub repo exists" precondition step, removing the circular dependency on Task 30. The `marketplace remove` uncertainty is documented with a safe fallback ("skip cleanup; harmless to leave it registered locally").
- **Task 30** documents the version-bump workflow for every future release, so updates actually reach users.
- **Self-review** acknowledges that `{placeholder}` tokens inside skill bodies are runtime template slots, not plan-stage TODOs.
- **CHANGELOG** records that `marketplace.json`'s schema was empirically verified, so future schema-touching changes know to re-run the smoke test.

---

## Scope

**In scope:**
- Phase 0 prereq checks and "previous attempt" wording (M10, L9, M7).
- Task 20 verification commands (L7, L8 — agent side).
- Task 25 verification commands (L3, L8, L15, L21).
- Task 28 smoke test (M4, M8, L16, L19, L20).
- Task 28.5 — new structural test (TG1).
- Task 29 marketplace install (L13, L14).
- Task 30 release process (L10).
- Self-review wording (L17).
- CHANGELOG note about marketplace schema verification (L11).

**Out of scope (handled in other instruction docs):**
- Skill body content — focus brief → directive substring matching, dispatch prompt order, model resolution, allowlist enumeration, `disallowedTools` form (handled in SKILL-fixes / AGENT-fixes / DISPATCH-fixes).
- Agent file content — agent body, `disallowedTools` form, agent frontmatter (handled in AGENT-fixes).
- Directive content (handled in DIRECTIVE-fixes if any).
- Manifest content (`plugin.json`, `marketplace.json`) — beyond the empirical-verification note (L11) above.
- `defaults.json` (config) content (handled in CONFIG-fixes if any).
