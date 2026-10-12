#!/usr/bin/env python3
"""comb resolver: config, resolve, directives, brief, report-name, batches, findings.

Deterministic resolution of what every comb skill used to re-derive in prose per
run: the three-layer config merge, role and model resolution, directive matching,
the per-run dispatch brief, report naming, write-set batching, and finding
extraction. Stdlib only; run from the project root.

Prose contracts this script implements: shared/config-loading.md,
shared/directive-matching.md, shared/dispatch-delivery.md, shared/observed-baseline.md.

CLI (output is fixed-format; scripts/test-comb.sh diffs it):

  comb.py config [--plugin-root P] [--home H] [--project-root R]
    stdout: merged config as JSON, keys sorted, indent 1.
    stderr: `warning: agents.<role> dropped — missing <subagent_type|when_to_use>`
            plus a warning when `agents` is not an object, `directives.include_plugin_defaults` is not a
            boolean, or `directives.user_path` exists but is not a directory. A config file may start with a BOM.
    exit 2: `comb.py: invalid JSON in <path>: <msg>` (first bad layer) or `comb.py: <path>: <os error>`.
    Layers: P/config/defaults.json, H/.claude/comb.config.json, R/.claude/comb.config.json;
    missing override files are skipped. Dicts deep-merge, lists replace, null deletes
    at any depth; a role that is not a dict with string subagent_type and when_to_use
    is dropped with a warning.
    Defaults: P = parent of this script's directory; H = ~; R = git toplevel else cwd.

  comb.py resolve --role R --lane L [--coerce the_desert] [config flags]
    stdout: subagent_type: / model: / effort: <low|medium|high|xhigh|max|unset> / native: yes|no
    L is a dotted path under models. model: agents.R.model, else models.the_desert when
    coercing, else models.<L>. effort: agents.R.effort, else effort.the_desert when
    coercing and set, else effort.<L>, else unset. native: yes iff subagent_type equals
    "comb:" + the `name:` of some P/agents/*.md (literal equality).
    exit 2: role absent, lane absent, effort outside the five values.

  comb.py directives [--brief "<text>"] [config flags]
    stdout: plugin: <abs path> (sorted; none when include_plugin_defaults is false),
            user: <abs path> (sorted; none when R/<directives.user_path> is absent),
            primary: <abs path> … | primary: none
    A directive is primary when its basename (without .md) contains a lowercase word of
    the brief as a substring; a word shorter than 4 characters must equal a whole
    hyphen-separated segment of the basename instead (so "it" flags nothing, "api" flags api.md).

  comb.py brief --skill S --role R [--run <stem>] [--excerpt <path>] [--manifest <path>] [--brief "<text>"] [config flags]
    S in review|plan|fix|patterns. Writes .comb/excerpts/<run>.<S>.<R>.brief.md under the cwd
    (minting `<S>-<epoch>-<4 hex>` and printing `run: <stem>` first when --run is omitted;
    manifest.py clean --run removes it) and prints:
      brief: <abs path>
      form: native|foreign
      directives: <n> plugin, <m> user; primary: <basenames, comma-separated | none>
      baseline: <excerpt> (excerpt) + <manifest> (full manifest) | <manifest> (full manifest, no excerpt) | none
    The file holds, in order: `## Directives` (the foreign form adds the authority sentence and
    `Your lens: <when_to_use>`; the fix implementer reads the instruction's citations plus the
    primaries), `## Project conventions (observed baseline)` when --manifest is given (paths,
    the baseline paragraph, the excerpt sentences when --excerpt is given, the skill's role
    note), and `## User focus for this run` when --brief is given (framed for review, verbatim
    for the other skills).

  comb.py report-name --reviews <dir> (--pr N | --branch <name>)
    stdout: report: <dir>/<pr-N|branch-<slug>>-round<R>-report.md / round: <R>
    slug: `/`, whitespace, and `: ? * < > | "` and backslash become `-`; runs collapse; trailing `-` trimmed.
    R = 1 + the highest round parsed from files named <prefix>-round<digits>-report.md in
    <dir>; 1 when none match or the directory is missing. Files are never counted.

  comb.py batches --folder <plan folder>
    stdout: shape: per-finding | single-revise-doc | empty
            write-set <code>: <path> … | (none)       one per item, folder (filename) order
            not-reproduced: <codes> | none
            batch <n>: <codes>                         severity order C H M L T D X G, then number
    A write-set is the file paths named in `## Where` (backticked spans split on whitespace, or
    bare tokens, with a `/` or a 2-5 letter extension; `:12`/`:L12`/`#L12` dropped; `./a` and
    trailing `/` normalised), else those in `**File(s):**`; a revise
    doc's is its `**Target spec:**`. Items whose `**Finding status:**` starts with
    `not reproduced` are listed and left out of the batches. A batch holds at most three items
    with pairwise-disjoint write-sets (a directory covers everything under it); an item with no
    write-set runs alone. Batches are a ceiling: the skill may split one, never merge two.
    exit 2: missing or unreadable folder; a folder mixing per-finding files and revise-*.md; two files
    with the same code; more than one revise-*.md.

  comb.py findings --report <path>
    stdout: {"count": N, "shape": "code-shaped|non-code|unknown", "findings": [{code, title,
    source, files, verified}]} from the report template (`**{code} — {title}**`, `*Source: …*`,
    `File(s): …`, `**Verified:** …`). Code-less bullets under a Deferred heading become D<n> after the
    highest coded D item (a bare `None.` / `n/a` bullet is skipped).
    A report whose entries carry labels instead of codes is `non-code` with empty codes. A finding
    without a `**Verified:**` line (a report that predates the field) is returned with `verified: ""`.
    Anything else is count 0, shape unknown — never a traceback.
"""
import argparse
import glob
import json
import os
import random
import re
import subprocess
import sys
import time

EFFORTS = ("low", "medium", "high", "xhigh", "max")
SHORT_WORD = 4


# ---------------------------------------------------------------- utilities

def die(msg, code=2):
    sys.stdout.flush()
    sys.stderr.write("comb.py: %s\n" % msg)
    sys.exit(code)


def plugin_root_default():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def project_root_default():
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except Exception:
        return os.getcwd()


# ------------------------------------------------------------------- config

def deep_merge(base, over):
    if not isinstance(base, dict) or not isinstance(over, dict):
        return over
    out = dict(base)
    for k, v in over.items():
        if v is None:
            out.pop(k, None)
        elif isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_layer(path, required):
    if not os.path.exists(path):
        if required:
            die("%s: missing" % path)
        return None
    try:
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    except json.JSONDecodeError as ex:
        die("invalid JSON in %s: %s" % (path, ex.msg))
    except OSError as ex:
        die("%s: %s" % (path, ex.strerror))


def layer_paths(a):
    return [os.path.join(a.plugin_root, "config", "defaults.json"),
            os.path.join(a.home, ".claude", "comb.config.json"),
            os.path.join(a.project_root, ".claude", "comb.config.json")]


def merged_config(a):
    cfg = {}
    for i, p in enumerate(layer_paths(a)):
        layer = load_layer(p, required=(i == 0))
        if layer is not None:
            if not isinstance(layer, dict):
                die("invalid JSON in %s: top level is not an object" % p)
            cfg = deep_merge(cfg, layer)
    agents = cfg.get("agents")
    if not isinstance(agents, dict):
        if agents is not None:
            sys.stderr.write("warning: agents is not an object; no roles are defined\n")
        agents = {}
        cfg["agents"] = agents
    d = cfg.get("directives")
    if isinstance(d, dict) and "include_plugin_defaults" in d and not isinstance(d["include_plugin_defaults"], bool):
        sys.stderr.write("warning: directives.include_plugin_defaults is %s, not a boolean; treated as %s\n"
                         % (json.dumps(d["include_plugin_defaults"]), "true" if d["include_plugin_defaults"] else "false"))
        d["include_plugin_defaults"] = bool(d["include_plugin_defaults"])
    for role in sorted(agents):
        v = agents[role]
        missing = [k for k in ("subagent_type", "when_to_use")
                   if not (isinstance(v, dict) and isinstance(v.get(k), str))]
        if missing:
            sys.stderr.write("warning: agents.%s dropped — missing %s\n" % (role, ", ".join(missing)))
            del agents[role]
    sys.stderr.flush()
    return cfg


def cmd_config(a):
    cfg = merged_config(a)
    print(json.dumps(cfg, indent=1, sort_keys=True, ensure_ascii=False))


# ------------------------------------------------------------------ resolve

def walk(tree, dotted):
    cur = tree
    for k in dotted.split("."):
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur


def native_names(plugin_root):
    names = set()
    for f in sorted(glob.glob(os.path.join(plugin_root, "agents", "*.md"))):
        try:
            with open(f, encoding="utf-8") as fh:
                for line in fh:
                    m = re.match(r"^name:\s*(\S+)\s*$", line)
                    if m:
                        names.add(m.group(1))
                        break
        except OSError:
            continue
    return names


def role_spec(cfg, role):
    agents = cfg.get("agents", {})
    if role not in agents:
        die("role %s is not in agents (deleted or never defined)" % role)
    return agents[role]


def is_native(spec, plugin_root):
    return spec["subagent_type"] in {"comb:" + n for n in native_names(plugin_root)}


def resolve(cfg, role, lane, coerce, plugin_root):
    spec = role_spec(cfg, role)
    lane_model = walk(cfg.get("models", {}), lane)
    if lane_model is None:
        die("lane %s is not in models" % lane)
    if not isinstance(lane_model, str):
        die("lane %s is not a model string (got %s)" % (lane, type(lane_model).__name__))
    model = spec.get("model")
    if not isinstance(model, str):
        model = None
        if coerce == "the_desert":
            model = walk(cfg.get("models", {}), "the_desert")
        if not isinstance(model, str):
            model = lane_model
    effort = spec.get("effort")
    if not isinstance(effort, str):
        effort = None
        if coerce == "the_desert":
            effort = walk(cfg.get("effort", {}), "the_desert")
        if not isinstance(effort, str):
            effort = walk(cfg.get("effort", {}), lane)
        if not isinstance(effort, str):
            effort = "unset"
    if effort not in EFFORTS and effort != "unset":
        die("effort %r for %s is not one of %s" % (effort, role, "|".join(EFFORTS)))
    return {"subagent_type": spec["subagent_type"], "model": model, "effort": effort,
            "native": is_native(spec, plugin_root)}


def cmd_resolve(a):
    cfg = merged_config(a)
    r = resolve(cfg, a.role, a.lane, a.coerce, a.plugin_root)
    print("subagent_type: %s" % r["subagent_type"])
    print("model: %s" % r["model"])
    print("effort: %s" % r["effort"])
    print("native: %s" % ("yes" if r["native"] else "no"))


# --------------------------------------------------------------- directives

def directive_lists(cfg, a):
    d = cfg.get("directives", {}) if isinstance(cfg.get("directives"), dict) else {}
    plugin = []
    if d.get("include_plugin_defaults", True) is not False:
        plugin = sorted(os.path.abspath(p) for p in glob.glob(os.path.join(a.plugin_root, "directives", "*.md")))
    user = []
    up = d.get("user_path")
    if isinstance(up, str) and up:
        udir = os.path.join(a.project_root, up)
        if os.path.isdir(udir):
            user = sorted(os.path.abspath(p) for p in glob.glob(os.path.join(udir, "*.md")))
        elif os.path.exists(udir):
            sys.stderr.write("warning: directives.user_path %s is not a directory; no user directives\n" % up)
    sys.stderr.flush()
    return plugin, user


def brief_words(text):
    return [w for w in re.split(r"[^a-z0-9]+", (text or "").lower()) if w]


def is_primary(path, words):
    base = os.path.basename(path)
    if base.endswith(".md"):
        base = base[:-3]
    base = base.lower()
    segments = base.split("-")
    for w in words:
        if len(w) < SHORT_WORD:
            if w in segments:
                return True
        elif w in base:
            return True
    return False


def primaries(paths, brief):
    words = brief_words(brief)
    if not words:
        return []
    return sorted(p for p in paths if is_primary(p, words))


def cmd_directives(a):
    cfg = merged_config(a)
    plugin, user = directive_lists(cfg, a)
    for p in plugin:
        print("plugin: %s" % p)
    for p in user:
        print("user: %s" % p)
    prim = primaries(plugin + user, a.brief.strip())
    if prim:
        for p in prim:
            print("primary: %s" % p)
    else:
        print("primary: none")


# -------------------------------------------------------------------- brief
#
# Verbatim texts of the dispatch block, copied from the shared blocks and skill
# prompts they replace (shared/dispatch-delivery.md, shared/observed-baseline.md,
# skills/{review,plan,fix}/SKILL.md). Change them here and nowhere else.

AUTHORITY = ("These directives are authoritative. Read every listed file before starting. "
             "Cite by `file.md §N.N`.")
DIRECTIVES_INTRO = ("The project's authoritative directives apply. Read these directive files and "
                    "cite as `file.md §N.N`:")
DIRECTIVES_INTRO_IMPLEMENTER = (
    "The project's authoritative directives apply to this fix. Read the directives this "
    "instruction cites in its `## Directive citations`, plus those listed under \"most relevant\" "
    "below. Cite as `file.md §N.N` if you depart from any rule (you should not need to depart). "
    "The full list, for reference:")
PRIMARY_HEADING = "Directives most relevant to this run:"
BASELINE_HEADING = "## Project conventions (observed baseline)"
BASELINE_PARAGRAPH = (
    "This is the codebase's observed convention baseline as of its last generation — a prior, not "
    "the authority. Read the actual code around the diff; where it conflicts with the manifest, the "
    "live code wins. If the manifest has no entry for this area or theme, reconstruct the convention "
    "from the code — silence is neither a finding nor permission. Project directives outrank this "
    "manifest: a divergence that violates an up-to-date directive is drift no matter how widespread, "
    "and classifying it as a deliberate improvement or new canonical never excuses a directive "
    "violation. Before flagging a divergence, classify it: unjustified, inconsistent divergence is "
    "drift (a finding); a deliberate, consistently-applied improvement or migration, or the first "
    "canonical pattern for something genuinely new, is not a drift finding. When you judge a "
    "divergence to be an improvement/migration or a new canonical, say so explicitly so the "
    "orchestrator can emit the semantic refresh note. Cite manifest entries by area/section heading "
    "when raising conformance findings.")
EXCERPT_SENTENCES = (
    "The excerpt lists the sections it omits with their line ranges. Read an omitted section by "
    "that range when the excerpt or the code points you to it. Do not read the full manifest end "
    "to end.")
ROLE_NOTES = {
    "planner": ("(Planner note) When you author the instruction for a finding the review classified "
                "as a deliberate improvement or a new canonical, reference the manifest but do not "
                "bend the instruction back to the baseline — that divergence is sanctioned."),
    "implementer": ("(Implementer note) Conform to the baseline UNLESS this instruction is "
                    "implementing a sanctioned improvement or a new canonical pattern."),
    "reviewer": ("(Reviewer note) Conformance to the baseline is expected, but a deliberate "
                 "improvement/migration or a new canonical introduced by this fix is NOT a "
                 "compliance failure."),
}
FOCUS_HEADING = "## User focus for this run"
REVIEW_FOCUS_FRAMING = ("Findings matching this focus are highest priority. Surface other issues "
                        "too, but do not let the user's stated concerns slip.")
SKILLS = ("review", "plan", "fix", "patterns")


def comb_dir():
    d = os.path.join(os.getcwd(), ".comb")
    ex = os.path.join(d, "excerpts")
    os.makedirs(ex, exist_ok=True)
    gi = os.path.join(d, ".gitignore")
    if not os.path.exists(gi):
        with open(gi, "w") as f:
            f.write("*\n")
    return ex


def mint_stem(skill):
    return "%s-%d-%04x" % (skill, int(time.time()), random.randrange(0x10000))


def role_note_for(skill, role):
    if skill == "plan":
        return ROLE_NOTES["planner"]
    if skill == "fix":
        return ROLE_NOTES["implementer"] if role == "implementer" else ROLE_NOTES["reviewer"]
    return None


def existing(path, flag):
    if path is None:
        return None
    p = os.path.abspath(path)
    if not os.path.isfile(p):
        die("%s %s: no such file" % (flag, p))
    return p


def render_brief(skill, role, spec, native, plugin, user, prim, excerpt, manifest, brief):
    out = ["# comb brief — %s / %s (%s)" % (skill, role, spec["subagent_type"]), "", "## Directives", ""]
    if not native:
        out += [AUTHORITY, "Your lens: %s" % spec["when_to_use"], ""]
    out.append(DIRECTIVES_INTRO_IMPLEMENTER if (skill == "fix" and role == "implementer") else DIRECTIVES_INTRO)
    out += ["- %s" % p for p in plugin + user]
    if prim:
        out += ["", PRIMARY_HEADING] + ["- %s" % p for p in prim]
    if manifest:
        out += ["", BASELINE_HEADING, ""]
        if excerpt:
            out.append("- %s (excerpt)" % excerpt)
        out += ["- %s (full manifest)" % manifest, ""]
        out.append(BASELINE_PARAGRAPH + (" " + EXCERPT_SENTENCES if excerpt else ""))
        note = role_note_for(skill, role)
        if note:
            out += ["", note]
    if brief:
        out += ["", FOCUS_HEADING, ""]
        if skill == "review":
            out += [REVIEW_FOCUS_FRAMING, ""]
        out.append(brief)
    return "\n".join(out) + "\n"


def cmd_brief(a):
    cfg = merged_config(a)
    spec = role_spec(cfg, a.role)
    native = is_native(spec, a.plugin_root)
    plugin, user = directive_lists(cfg, a)
    brief = a.brief.strip()
    prim = primaries(plugin + user, brief)
    excerpt = existing(a.excerpt, "--excerpt")
    manifest = existing(a.manifest, "--manifest")
    if excerpt and not manifest:
        die("--excerpt given without --manifest")
    run = a.run
    minted = run is None
    if minted:
        run = mint_stem(a.skill)
    elif not re.match(r"^[a-z][a-z-]*-[0-9]+-[0-9a-f]{4}$", run):
        die("--run %r is not a run stem (<skill>-<digits>-<hex>)" % run)
    path = os.path.join(comb_dir(), "%s.%s.%s.brief.md" % (run, a.skill, a.role))
    with open(path, "w", encoding="utf-8") as f:
        f.write(render_brief(a.skill, a.role, spec, native, plugin, user, prim, excerpt, manifest, brief))
    if minted:
        print("run: %s" % run)
    print("brief: %s" % path)
    print("form: %s" % ("native" if native else "foreign"))
    print("directives: %d plugin, %d user; primary: %s"
          % (len(plugin), len(user), ", ".join(dict.fromkeys(os.path.basename(p) for p in prim)) if prim else "none"))
    if manifest and excerpt:
        print("baseline: %s (excerpt) + %s (full manifest)" % (excerpt, manifest))
    elif manifest:
        print("baseline: %s (full manifest, no excerpt)" % manifest)
    else:
        print("baseline: none")


# -------------------------------------------------------------- report-name

UNSAFE = re.compile(r'[/\\:?*<>|"\s]+')


def slugify(name):
    return re.sub(r"-{2,}", "-", UNSAFE.sub("-", name)).strip("-")


def cmd_report_name(a):
    if a.pr is None and not slugify(a.branch):
        die("--branch is empty")
    prefix = "pr-%d" % a.pr if a.pr is not None else "branch-%s" % slugify(a.branch)
    pat = re.compile(r"^%s-round(\d+)-report\.md$" % re.escape(prefix))
    rounds = [0]
    if os.path.isdir(a.reviews):
        try:
            names = os.listdir(a.reviews)
        except OSError as ex:
            die("%s: %s" % (a.reviews, ex.strerror))
        for name in names:
            m = pat.match(name)
            if m:
                rounds.append(int(m.group(1)))
    n = max(rounds) + 1
    print("report: %s" % os.path.join(a.reviews, "%s-round%d-report.md" % (prefix, n)))
    print("round: %d" % n)


# ------------------------------------------------------------------ batches

SEVERITY_ORDER = "CHMLTDXG"
ITEM_FILE = re.compile(r"^([CHMLTDXG])(\d+)-.*\.md$")
REVISE_FILE = re.compile(r"^revise-.*\.md$")
BATCH_MAX = 3
LINE_SUFFIX = re.compile(r"[:#]L?\d+(?:[-–,]\d+)*$")
EXT = re.compile(r"\.[A-Za-z]{2,5}$")
URL_LIKE = re.compile(r"^[a-z]+://")


def section(text, heading):
    """Body of `## <heading>` up to the next `## ` heading, or ''."""
    m = re.search(r"^## %s[ \t]*\n(.*?)(?=^## |\Z)" % re.escape(heading), text, re.M | re.S)
    return m.group(1) if m else ""


def header_value(text, label):
    m = re.search(r"^\*\*%s:\*\*[ \t]*(.*)$" % re.escape(label), text, re.M)
    return m.group(1).strip() if m else ""


def paths_in(text):
    """File paths named in a span: backticked spans (split on whitespace, so a span that
    holds a sentence still yields its paths) and bare tokens, kept when they carry a `/` or
    a 2-5 letter extension; `:12`, `:L12`, `#L12` line parts dropped; `./a/b` normalised to
    `a/b` and `src/x/` to `src/x`; order kept, duplicates removed."""
    out = []
    spans = re.findall(r"`([^`\n]+)`", text)
    bare = re.sub(r"`[^`\n]*`", " ", text)
    for tok in " ".join(spans).split() + bare.split():
        tok = tok.lstrip("(\"'").rstrip(",.;:)(\"'")
        tok = LINE_SUFFIX.sub("", tok)
        if not tok or "§" in tok or URL_LIKE.match(tok):
            continue
        if "/" in tok or EXT.search(tok):
            tok = os.path.normpath(tok)
            if tok not in out:
                out.append(tok)
    return out


def write_set_of(text):
    ws = paths_in(section(text, "Where"))
    if not ws:
        ws = paths_in(header_value(text, "File(s)"))
    return ws


def overlap(a, b):
    for x in a:
        for y in b:
            if x == y or x.startswith(y.rstrip("/") + "/") or y.startswith(x.rstrip("/") + "/"):
                return True
    return False


def severity_key(code):
    m = re.match(r"^([A-Z])(\d+)$", code)
    if not m:
        return (len(SEVERITY_ORDER), 0, code)
    return (SEVERITY_ORDER.find(m.group(1)), int(m.group(2)), code)


def make_batches(items):
    """items: [(code, write_set)] in severity order → [[code, …], …]; ≤ BATCH_MAX per batch,
    pairwise-disjoint write-sets, an item with no write-set alone."""
    pending = list(items)
    batches = []
    while pending:
        code, ws = pending.pop(0)
        if not ws:
            batches.append([code])
            continue
        batch, taken = [(code, ws)], []
        for i, (c2, ws2) in enumerate(pending):
            if len(batch) >= BATCH_MAX:
                break
            if ws2 and not any(overlap(ws2, w) for _, w in batch):
                batch.append((c2, ws2))
                taken.append(i)
        for i in reversed(taken):
            pending.pop(i)
        batches.append([c for c, _ in batch])
    return batches


def cmd_batches(a):
    folder = os.path.abspath(a.folder)
    if not os.path.isdir(folder):
        die("--folder %s: no such directory" % folder)
    try:
        names = sorted(os.listdir(folder))
    except OSError as ex:
        die("%s: %s" % (folder, ex.strerror))
    items = [n for n in names if ITEM_FILE.match(n)]
    revises = [n for n in names if REVISE_FILE.match(n)]
    if items and revises:
        die("%s mixes per-finding files and revise-*.md; one folder holds one shape" % folder)
    if not items and not revises:
        print("shape: empty")
        print("not-reproduced: none")
        return

    def read(n):
        path = os.path.join(folder, n)
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                return f.read()
        except OSError as ex:
            die("%s: %s" % (path, ex.strerror))

    if revises:
        if len(revises) > 1:
            die("%s holds %d revise-*.md files; a single-revise-doc folder holds one" % (folder, len(revises)))
        n = revises[0]
        code = n[:-3]
        ws = paths_in(header_value(read(n), "Target spec"))
        print("shape: single-revise-doc")
        print("write-set %s: %s" % (code, " ".join(ws) if ws else "(none)"))
        print("not-reproduced: none")
        print("batch 1: %s" % code)
        return

    by_code = {}
    for n in items:
        m = ITEM_FILE.match(n)
        by_code.setdefault(m.group(1) + m.group(2), []).append(n)
    for code, files in by_code.items():
        if len(files) > 1:
            die("%s: code %s appears in %s; one file per code" % (folder, code, " and ".join(files)))
    print("shape: per-finding")
    parsed, not_repro = [], []
    for n in items:
        m = ITEM_FILE.match(n)
        code = m.group(1) + m.group(2)
        text = read(n)
        ws = write_set_of(text)
        print("write-set %s: %s" % (code, " ".join(ws) if ws else "(none)"))
        if header_value(text, "Finding status").lower().startswith("not reproduced"):
            not_repro.append(code)
        else:
            parsed.append((code, ws))
    print("not-reproduced: %s" % (" ".join(not_repro) if not_repro else "none"))
    parsed.sort(key=lambda it: severity_key(it[0]))
    for i, b in enumerate(make_batches(parsed), 1):
        print("batch %d: %s" % (i, " ".join(b)))


# ----------------------------------------------------------------- findings

FINDING_HEAD = re.compile(r"^\*\*(.+?) — (.+?)\*\*\s*$")
CODE = re.compile(r"^[CHMLTDXG]\d+$")
SOURCE = re.compile(r"^\*Source:\s*(.*?)\*\s*$")
FILES = re.compile(r"^File\(s\):\s*(.*)$")
VERIFIED = re.compile(r"^\*\*Verified:\*\*\s*(.*)$")
BULLET = re.compile(r"^[-*]\s+(.*\S)\s*$")


def split_files(value):
    items = [x.strip() for x in re.split(r",\s*(?=`)", value) if x.strip()]
    if len(items) == 1 and "`" not in value:
        items = [x.strip() for x in value.split(",") if x.strip()]
    return [x.strip("`").replace("` § ", " § ").replace("`", "") for x in items]


def parse_findings(text):
    findings, deferred_bullets = [], []
    in_deferred = False
    cur = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("#"):
            in_deferred = line.lstrip("#").strip().lower() == "deferred"
            cur = None
            continue
        if not line.strip():
            cur = None  # a blank line ends the header fields; a later bullet is its own item
            continue
        m = FINDING_HEAD.match(line)
        if m:
            head, title = m.group(1).strip(), m.group(2).strip()
            cur = {"code": head if CODE.match(head) else "", "title": title, "source": "", "files": [], "verified": ""}
            findings.append(cur)
            continue
        if cur is not None:
            m = SOURCE.match(line)
            if m:
                cur["source"] = m.group(1).strip()
                continue
            m = FILES.match(line)
            if m:
                cur["files"] = split_files(m.group(1))
                continue
            m = VERIFIED.match(line)
            if m:
                cur["verified"] = m.group(1).strip()
                continue
        if in_deferred and cur is None:
            m = BULLET.match(line)
            if m and m.group(1).strip().rstrip(".").lower() not in ("none", "n/a", "nothing"):
                deferred_bullets.append(m.group(1))
    coded = [f for f in findings if f["code"]]
    labelled = [f for f in findings if not f["code"]]
    if coded:
        highest = max([int(f["code"][1:]) for f in coded if f["code"].startswith("D")] + [0])
        for i, t in enumerate(deferred_bullets, highest + 1):
            coded.append({"code": "D%d" % i, "title": t, "source": "", "files": [], "verified": ""})
        shape, out = "code-shaped", coded
    elif labelled:
        shape, out = "non-code", labelled
    else:
        shape, out = "unknown", []
    return {"count": len(out), "shape": shape, "findings": out}


def cmd_findings(a):
    path = os.path.abspath(a.report)
    if not os.path.isfile(path):
        die("--report %s: no such file" % path)
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError as ex:
        die("%s: %s" % (path, ex.strerror))
    try:
        result = parse_findings(text)
    except Exception:  # any parse surprise is "unknown", never a traceback
        result = {"count": 0, "shape": "unknown", "findings": []}
    print(json.dumps(result, indent=1, ensure_ascii=False))


# --------------------------------------------------------------------- main

def main(argv=None):
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--plugin-root", default=plugin_root_default())
    common.add_argument("--home", default=os.path.expanduser("~"))
    common.add_argument("--project-root", default=None)

    p = argparse.ArgumentParser(prog="comb.py", description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("config", parents=[common], help="print the merged three-layer config as JSON")
    s.set_defaults(fn=cmd_config)

    s = sub.add_parser("resolve", parents=[common], help="resolve a role's subagent_type, model, effort, and native form")
    s.add_argument("--role", required=True)
    s.add_argument("--lane", required=True)
    s.add_argument("--coerce", choices=["the_desert"], default=None)
    s.set_defaults(fn=cmd_resolve)

    s = sub.add_parser("directives", parents=[common], help="list directive files and the primaries a focus brief flags")
    s.add_argument("--brief", default="")
    s.set_defaults(fn=cmd_directives)

    s = sub.add_parser("brief", parents=[common], help="write the per-run dispatch brief and print its summary lines")
    s.add_argument("--skill", required=True, choices=SKILLS)
    s.add_argument("--role", required=True)
    s.add_argument("--run", default=None, help="run stem; minted (and printed as `run:`) when omitted")
    s.add_argument("--excerpt", default=None)
    s.add_argument("--manifest", default=None)
    s.add_argument("--brief", default="")
    s.set_defaults(fn=cmd_brief)

    s = sub.add_parser("report-name", help="derive the review report path; the round is parsed from existing filenames")
    s.add_argument("--reviews", required=True)
    g = s.add_mutually_exclusive_group(required=True)
    g.add_argument("--pr", type=int)
    g.add_argument("--branch")
    s.set_defaults(fn=cmd_report_name)

    s = sub.add_parser("batches", help="folder shape, per-item write-sets, not-reproduced items, and disjoint batches")
    s.add_argument("--folder", required=True)
    s.set_defaults(fn=cmd_batches)

    s = sub.add_parser("findings", help="findings of a review report as JSON (count 0 when the template is absent)")
    s.add_argument("--report", required=True)
    s.set_defaults(fn=cmd_findings)

    a = p.parse_args(argv)
    if getattr(a, "project_root", "") is None:
        a.project_root = project_root_default()
    a.fn(a)


if __name__ == "__main__":
    main()
