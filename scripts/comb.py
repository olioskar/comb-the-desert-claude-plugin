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
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys

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

    a = p.parse_args(argv)
    if a.project_root is None:
        a.project_root = project_root_default()
    a.fn(a)


if __name__ == "__main__":
    main()
