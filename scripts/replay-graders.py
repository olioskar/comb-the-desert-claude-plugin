#!/usr/bin/env python3
"""Replay an eval case's deterministic graders against a saved run, for free.

    python3 -I scripts/replay-graders.py <case-dir> <kept-run-dir>
    python3 -I scripts/replay-graders.py <case-dir> --trace <trace.jsonl> [--workspace <dir>]

<kept-run-dir> is the directory `claude plugin eval … --keep-temp` prints ("kept temp:
/private/tmp/e-XXXX"). Its trace is <dir>/out/trace.jsonl and the workspace is
<dir>/sealed/home/cwd; the eval seals that with mode 000, so run
`chmod 700 <dir> <dir>/sealed` first (the eval's own message says the same).

Replays `regex`, `tool_used`, and `file_exists` graders. `llm` and `baseline` graders are
listed as skipped: they need the judge model. Bounds, so a replay is read correctly:
regexes are JavaScript in the eval and Python `re` here (the subset the suite uses, such
as `\\s`, `\\b`, `[\\s\\S]`, `{m,n}`, behaves the same); `file_exists` sees every file in the
workspace, while the eval counts only files created during the run; tool inputs are
JSON-encoded the way JSON.stringify does it (no spaces, non-ASCII kept).

Exit 0 when every replayed grader passes, 1 when one fails, 2 on a usage or input error.
Stdlib only.
"""
import glob
import json
import os
import re
import sys


def die(msg):
    print(f"replay-graders: {msg}", file=sys.stderr)
    sys.exit(2)


# --- grader frontmatter (the YAML subset the suite uses) -------------------------------

def unquote(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] == "'":
        return v[1:-1].replace("''", "'")
    if len(v) >= 2 and v[0] == v[-1] == '"':
        out, i, body = [], 0, v[1:-1]
        esc = {"n": "\n", "t": "\t", '"': '"', "\\": "\\", "/": "/"}
        while i < len(body):
            c = body[i]
            if c == "\\" and i + 1 < len(body):
                out.append(esc.get(body[i + 1], "\\" + body[i + 1]))
                i += 2
            else:
                out.append(c)
                i += 1
        return "".join(out)
    return v


def parse_value(v):
    v = v.strip()
    if v.startswith("{") and v.endswith("}"):
        m = {}
        for part in v[1:-1].split(","):
            if ":" in part:
                k, _, val = part.partition(":")
                m[k.strip()] = unquote(val)
        return m
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    if v in ("true", "false"):
        return v == "true"
    return unquote(v)


def load_grader(path):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"---\n(.*?)\n---", text, re.S)
    if not m:
        die(f"{path}: no frontmatter")
    g = {}
    for line in m.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        k, _, v = line.partition(":")
        g[k.strip()] = parse_value(v)
    return g


# --- the saved run ---------------------------------------------------------------------

def load_trace(path):
    try:
        return open(path, encoding="utf-8").read()
    except OSError as e:
        die(f"cannot read trace {path}: {e.strerror} (sealed? chmod 700 the kept dir and its sealed/)")


def messages(raw):
    out = []
    for line in raw.splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def content_blocks(msg):
    m = msg.get("message")
    c = m.get("content") if isinstance(m, dict) else None
    return c if isinstance(c, list) else []


def last_message(msgs):
    for msg in reversed(msgs):
        if msg.get("type") != "assistant":
            continue
        texts = [b.get("text", "") for b in content_blocks(msg) if b.get("type") == "text"]
        if any(t.strip() for t in texts):
            return "\n".join(texts)
    return ""


def tool_calls(msgs, tool):
    for msg in msgs:
        for b in content_blocks(msg):
            if b.get("type") == "tool_use" and b.get("name") == tool:
                yield json.dumps(b.get("input", {}), separators=(",", ":"), ensure_ascii=False)


# --- graders ---------------------------------------------------------------------------

def run_regex(g, raw, msgs, ws):
    target = g.get("target", "last_message")
    if isinstance(target, dict) and target.get("source") == "file":
        if not ws:
            return None, "needs --workspace for a file target"
        p = os.path.join(ws, target.get("path", ""))
        try:
            text = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            return False, f"file not found: {target.get('path')}"
    elif target == "trace":
        text = raw
    elif target == "last_message":
        text = last_message(msgs)
    else:
        return None, f"target {target!r} not replayable"
    flags = re.I if "i" in str(g.get("flags", "")) else 0
    pat = re.compile(g["pattern"], flags)
    match = str(g.get("match", "contains"))
    n = len(pat.findall(text))
    if match == "contains":
        return n > 0, (f"matched {g['pattern']}" if n else "pattern not found")
    if match == "not_contains":
        return n == 0, ("pattern absent as expected" if n == 0 else f"pattern found {n}x")
    if match.startswith("count:"):
        want = int(match.split(":", 1)[1])
        return n == want, f"{n} matches (expected {want})"
    return None, f"match {match!r} not replayable"


def run_tool_used(g, raw, msgs, ws):
    lo, hi = g.get("min", 1), g.get("max")
    pat = re.compile(g["input_match"]) if g.get("input_match") else None
    n = sum(1 for enc in tool_calls(msgs, g["tool"]) if pat is None or pat.search(enc))
    ok = n >= lo and (hi is None or n <= hi)
    return ok, f"{g['tool']} called {n}x (expected {lo}..{'∞' if hi is None else hi})"


def run_file_exists(g, raw, msgs, ws):
    if not ws:
        return None, "needs --workspace"
    hits = glob.glob(os.path.join(ws, g["path"]), recursive=True)
    want = g.get("exists", True)
    if want:
        return bool(hits), (f"{g['path']} exists" if hits else f"{g['path']} not found")
    return not hits, (f"{g['path']} absent as expected" if not hits else f"{len(hits)} file(s) match {g['path']}")


RUNNERS = {"regex": run_regex, "tool_used": run_tool_used, "file_exists": run_file_exists}


def main(argv):
    if len(argv) < 2 or argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0 if argv and argv[0] in ("-h", "--help") else 2
    case = argv[0]
    rest = argv[1:]
    trace = ws = None
    if rest and not rest[0].startswith("--"):
        kept = rest.pop(0)
        trace = os.path.join(kept, "out", "trace.jsonl")
        for cand in (os.path.join(kept, "sealed", "home", "cwd"), os.path.join(kept, "home", "cwd")):
            if os.path.isdir(cand):
                ws = cand
                break
    while rest:
        flag = rest.pop(0)
        if flag in ("--trace", "--workspace") and rest:
            val = rest.pop(0)
            if flag == "--trace":
                trace = val
            else:
                ws = val
        else:
            die(f"unknown argument {flag!r}")
    if not trace:
        die("no trace: pass a kept run dir or --trace")
    gdir = os.path.join(case, "graders")
    if not os.path.isdir(gdir):
        die(f"{gdir} is not a directory")
    raw = load_trace(trace)
    msgs = messages(raw)
    failed = 0
    for path in sorted(glob.glob(os.path.join(gdir, "*.md"))):
        name = os.path.splitext(os.path.basename(path))[0]
        g = load_grader(path)
        runner = RUNNERS.get(g.get("type"))
        if runner is None:
            print(f"  - {name}: skipped ({g.get('type')} needs the judge)")
            continue
        try:
            ok, why = runner(g, raw, msgs, ws)
        except re.error as e:
            ok, why = False, f"bad regex: {e}"
        if ok is None:
            print(f"  - {name}: skipped ({why})")
        elif ok:
            print(f"  ✓ {name}: {why}")
        else:
            failed += 1
            print(f"  ✗ {name}: {why}")
    print(f"replay: {os.path.basename(os.path.normpath(case))} — {'FAIL' if failed else 'OK'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
