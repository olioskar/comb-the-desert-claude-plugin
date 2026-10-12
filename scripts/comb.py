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
    S in review|plan|fix|patterns. Writes .comb/excerpts/<run>.<R>.brief.md under the cwd
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
        with open(path, encoding="utf-8") as f:
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
        agents = {}
        cfg["agents"] = agents
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


def resolve(cfg, role, lane, coerce, plugin_root):
    agents = cfg.get("agents", {})
    if role not in agents:
        die("role %s is not in agents (deleted or never defined)" % role)
    spec = agents[role]
    lane_model = walk(cfg.get("models", {}), lane)
    if not isinstance(lane_model, str):
        die("lane %s is not in models" % lane)
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
    subagent_type = spec["subagent_type"]
    native = subagent_type in {"comb:" + n for n in native_names(plugin_root)}
    return {"subagent_type": subagent_type, "model": model, "effort": effort,
            "native": native, "when_to_use": spec["when_to_use"]}


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
    prim = primaries(plugin + user, a.brief)
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
SKILL_LANE = {"review": "review", "plan": "plan", "patterns": "patterns"}


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
    agents = cfg.get("agents", {})
    if a.role not in agents:
        die("role %s is not in agents (deleted or never defined)" % a.role)
    spec = agents[a.role]
    native = spec["subagent_type"] in {"comb:" + n for n in native_names(a.plugin_root)}
    plugin, user = directive_lists(cfg, a)
    prim = primaries(plugin + user, a.brief)
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
    path = os.path.join(comb_dir(), "%s.%s.brief.md" % (run, a.role))
    with open(path, "w", encoding="utf-8") as f:
        f.write(render_brief(a.skill, a.role, spec, native, plugin, user, prim, excerpt, manifest, a.brief))
    if minted:
        print("run: %s" % run)
    print("brief: %s" % path)
    print("form: %s" % ("native" if native else "foreign"))
    print("directives: %d plugin, %d user; primary: %s"
          % (len(plugin), len(user), ", ".join(os.path.basename(p) for p in prim) if prim else "none"))
    if manifest and excerpt:
        print("baseline: %s (excerpt) + %s (full manifest)" % (excerpt, manifest))
    elif manifest:
        print("baseline: %s (full manifest, no excerpt)" % manifest)
    else:
        print("baseline: none")


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

    a = p.parse_args(argv)
    if a.project_root is None:
        a.project_root = project_root_default()
    a.fn(a)


if __name__ == "__main__":
    main()
