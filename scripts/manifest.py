#!/usr/bin/env python3
"""comb manifest tool: excerpt, index, verify, gate, filter, apply, clean.

Deterministic text operations over a PATTERNS manifest so that no orchestrating
model has to read the manifest or reproduce a parsing rule. Stdlib only.

Contract: shared/manifest-slicing.md (excerpts) and shared/shave-rules.md (shave).
"""
import argparse
import fnmatch
import json
import os
import random
import re
import subprocess
import sys
import time

GLOBAL_PREFIXES = ("how to read", "cross-reference", "cross reference",
                   "drift register", "known drift", "maintenance")
GLOBAL_EXACT = ("patterns", "index")

TOKEN_SPLIT = re.compile(r"[`\s()\[\]|\"']+")
TRAILING_PUNCT = ",.;:)"
LINE_PART = re.compile(r":[0-9][0-9,\-]*$")
SEG = r"[A-Za-z0-9_.@~+\-]+"
FULL_PATH = re.compile(r"^(?:\.\./|\./)?(?:%s/)+%s\.[A-Za-z]{1,5}$" % (SEG, SEG))
BASENAME = re.compile(r"^%s\.[A-Za-z]{2,5}$" % SEG)
BASENAME_WITH_LINE = re.compile(r"^%s\.[A-Za-z]{1,5}$" % SEG)
URL = re.compile(r"^[a-z]+://")
HEX = re.compile(r"\b[0-9a-f]{7,40}\b")
HEADER_TRUNCATE_AT = 400
HEADER_KEEP = 160
GATE_FULL_TEXT_LIMIT = 200

FIXED_MARKERS = re.compile(r"\b(fixed|retired|resolved|done)\b", re.I)
OPEN_MARKERS = re.compile(
    r"\b(still|open|remaining|pending|todo|ongoing|in progress|partial|"
    r"mid-migration|backlog|migrating)\b", re.I)
ISSUE_REF = re.compile(r"#\d{3,}|PR #", re.I)
DRIFT_LINE = re.compile(r"⚠|\bdrift\b", re.I)
SEPARATORS = [", ", " + ", " / ", "; ", " and "]


# ---------------------------------------------------------------- utilities

def die(msg, code=2):
    sys.stderr.write("manifest.py: %s\n" % msg)
    sys.exit(code)


def repo_root():
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except Exception:
        return os.getcwd()


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


def read_lines(path):
    with open(path, encoding="utf-8") as f:
        return f.read().split("\n")


def strip_token(tok):
    tok = tok.strip()
    while tok and tok[-1] in TRAILING_PUNCT:
        tok = tok[:-1]
    return tok


def tokens_of(text):
    for raw in TOKEN_SPLIT.split(text):
        tok = strip_token(raw)
        if tok:
            yield tok


def classify_anchor(tok):
    """Return ("full", path, linepart) | ("base", name, linepart) | None."""
    if URL.match(tok) or "*" in tok or "{" in tok:
        return None
    m = LINE_PART.search(tok)
    line = m.group(0) if m else ""
    body = tok[: m.start()] if m else tok
    if "/" in body:
        if FULL_PATH.match(body):
            return ("full", body, line)
        return None
    if line and BASENAME_WITH_LINE.match(body):
        return ("base", body, line)
    if not line and BASENAME.match(body):
        return ("base", body, line)
    return None


def anchors_in(text):
    """Set of (kind, path) for every anchor token in text, line parts stripped."""
    found = []
    seen = set()
    for tok in tokens_of(text):
        c = classify_anchor(tok)
        if c and (c[0], c[1]) not in seen:
            seen.add((c[0], c[1]))
            found.append((c[0], c[1]))
    return found


def basename_key(path):
    return os.path.basename(path)


def norm_path(p):
    p = p.strip()
    if p.startswith("./"):
        p = p[2:]
    return p


# ------------------------------------------------------------ manifest model

def heading_text(line):
    return line[3:].strip()


def is_global(heading):
    h = re.sub(r"^[^A-Za-z0-9]+", "", heading).strip().lower()
    if h in GLOBAL_EXACT:
        return True
    return any(h.startswith(p) for p in GLOBAL_PREFIXES)


def scope_globs_of(lines):
    globs = []
    for line in lines:
        t = line.strip().lstrip("_*").strip()
        m = re.match(r"(?i)^(scope|home)\s*:(.*)$", t)
        if not m:
            continue
        rest = m.group(2)
        items = re.findall(r"`([^`]+)`", rest)
        if not items:
            rest = rest.split(" — ")[0]
            rest = rest.strip().strip("_*").strip()
            items = [x.strip() for x in rest.split(",") if x.strip()]
        for it in items:
            it = it.strip().strip("_*").strip()
            if not it or ("/" not in it and not any(c in it for c in "*?[")):
                continue  # prose, not a path: the line contributes nothing
            it = re.sub(r"\{[^}]*\}", "*", it)
            if it.endswith("/"):
                it += "**"
            elif not any(c in it for c in "*?["):
                it += "/**"
            globs.append(it)
    return globs


def glob_root(g):
    root = re.split(r"[*?\[]", g)[0]
    return root.rstrip("/")


def parse_manifest(lines):
    """Return (header_lines_count, sections) with 0-based [start, end) line indexes."""
    starts = [i for i, l in enumerate(lines) if l.startswith("## ")]
    header_end = starts[0] if starts else len(lines)
    sections = []
    for n, s in enumerate(starts):
        e = starts[n + 1] if n + 1 < len(starts) else len(lines)
        body = lines[s:e]
        heading = heading_text(lines[s])
        kind = "global" if is_global(heading) else "area"
        text = "\n".join(body)
        anchors = anchors_in(text)
        full = [p for k, p in anchors if k == "full"]
        base = [p for k, p in anchors if k == "base"]
        globs = scope_globs_of(body) if kind == "area" else []
        anchor_dirs = sorted({os.path.dirname(p) for p in full})
        unscoped = kind == "area" and not globs and not full
        sections.append({
            "n": n + 1, "kind": kind, "heading": heading,
            "start": s + 1, "end": e,  # 1-based inclusive
            "bytes": len(text.encode("utf-8")),
            "scope_globs": globs, "anchor_dirs": anchor_dirs,
            "anchors": full, "basenames": base, "unscoped": unscoped,
        })
    return header_end, sections


def base_commit_of(header_lines):
    for line in header_lines:
        t = line.strip().lstrip("_*").strip()
        if t.lower().startswith("base commit"):
            m = HEX.search(t)
            if m:
                return m.group(0)
    last = None
    for line in header_lines:
        for m in HEX.finditer(line):
            tok = m.group(0)
            if re.search(r"[a-f]", tok):
                last = tok
    return last


def relevant(section, touched):
    if section["kind"] != "area":
        return True
    if section["unscoped"]:
        return True
    for t in touched:
        for g in section["scope_globs"]:
            if fnmatch.fnmatchcase(t, g):
                return True
        if t in section["anchors"]:
            return True
        if not section["scope_globs"]:
            td = os.path.dirname(t)
            if td in section["anchor_dirs"]:
                return True
    return False


def touched_from_files(paths):
    touched = []
    seen = set()
    for p in paths:
        with open(p, encoding="utf-8", errors="replace") as f:
            text = f.read()
        for tok in tokens_of(text):
            if URL.match(tok) or "*" in tok or "{" in tok:
                continue
            body = LINE_PART.sub("", tok)
            body = norm_path(body)
            if "/" in body and not FULL_PATH.match(body) and not re.match(r"^(?:%s/)+%s$" % (SEG, SEG), body):
                continue
            if "/" not in body and not BASENAME.match(body):
                continue
            if "/" not in body:
                continue  # bare basenames are not touched paths
            if body not in seen:
                seen.add(body)
                touched.append(body)
    return touched


def cited_of(sections, root):
    cited = set()
    for s in sections:
        if s["kind"] != "area":
            continue
        for p in s["anchors"]:
            cited.add(norm_path(p))
        dirs = set(s["anchor_dirs"]) | {glob_root(g) for g in s["scope_globs"]}
        for b in s["basenames"]:
            for d in dirs:
                cand = os.path.join(d, b) if d else b
                if os.path.isfile(os.path.join(root, cand)):
                    cited.add(cand)
    return cited


def truncate_header_line(line):
    if len(line) > HEADER_TRUNCATE_AT:
        return line[:HEADER_KEEP] + " … [truncated in excerpt; full line in the manifest]"
    return line


def log_line(sections, included):
    areas = [s for s in sections if s["kind"] == "area"]
    inc = [s["heading"] for s in areas if s["n"] in included]
    omitted = [s["heading"] for s in areas if s["n"] not in included]
    g = sum(1 for s in sections if s["kind"] == "global")
    return "PATTERNS excerpt: %d of %d area sections included (%s); %d global; omitted: %s" % (
        len(inc), len(areas), "; ".join(inc) if inc else "none", g,
        "; ".join(omitted) if omitted else "none")


# ------------------------------------------------------------------ excerpt

def cmd_excerpt(a):
    lines = read_lines(a.manifest)
    header_end, sections = parse_manifest(lines)
    touched = touched_from_files(a.touched_from)
    included = {s["n"] for s in sections if relevant(s, touched)}
    ex_dir = comb_dir()
    stem = mint_stem(a.skill)
    out_path = os.path.join(ex_dir, stem + ".md")

    omitted = [s for s in sections if s["n"] not in included]
    banner = ["> comb excerpt of %s for this run. Omitted sections, readable by line range "
              "with `sed -n START,ENDp %s`:" % (a.manifest, a.manifest)]
    if omitted:
        for s in omitted:
            banner.append("> - %s — lines %d–%d" % (s["heading"], s["start"], s["end"]))
    else:
        banner.append("> - none")
    banner.append("")
    body = [truncate_header_line(l) for l in lines[:header_end]]
    for s in sections:
        if s["n"] in included:
            body.extend(lines[s["start"] - 1:s["end"]])
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(banner + body))
        if not body or body[-1] != "":
            f.write("\n")

    root = repo_root()
    cited = cited_of(sections, root)
    inter = sorted(cited & set(touched))
    base = base_commit_of(lines[:header_end])
    if not inter:
        stale = "no (no cited file in the touched set)"
    elif not base:
        stale = "unknown (no base commit in the manifest header)"
    else:
        try:
            r = subprocess.run(["git", "diff", "--name-only", base, "HEAD", "--"] + inter,
                               capture_output=True, text=True, cwd=root)
            if r.returncode != 0:
                stale = "unknown (%s)" % (r.stderr.strip().splitlines() or ["git error"])[0]
            else:
                changed = [l for l in r.stdout.splitlines() if l.strip()]
                stale = "yes (%d cited files changed since %s)" % (len(changed), base) if changed \
                    else "no (0 cited files changed since %s)" % base
        except FileNotFoundError:
            stale = "unknown (git not available)"
    print("run: %s" % stem)
    print("excerpt: %s" % os.path.relpath(out_path))
    print(log_line(sections, included))
    print("stale: %s" % stale)
    print("base_commit: %s" % (base or "none"))


# -------------------------------------------------------------------- index

def cmd_index(a):
    lines = read_lines(a.manifest)
    header_end, sections = parse_manifest(lines)
    ex_dir = comb_dir()
    stem = mint_stem(a.skill)
    idx_path = os.path.join(ex_dir, stem + ".index.json")
    for s in sections:
        if s["kind"] == "area":
            s["edits_path"] = os.path.relpath(os.path.join(ex_dir, "%s.edits-%d.json" % (stem, s["n"])))
    data = {"manifest": a.manifest, "run": stem, "header_end": header_end,
            "base_commit": base_commit_of(lines[:header_end]), "sections": sections}
    with open(idx_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
    print("run: %s" % stem)
    print("index: %s" % os.path.relpath(idx_path))
    print_size_table(lines, header_end, sections, with_edits=True)


def print_size_table(lines, header_end, sections, with_edits=False):
    hb = len("\n".join(lines[:header_end]).encode("utf-8"))
    print("header 1-%d %dB" % (header_end, hb))
    for s in sections:
        extra = ""
        if with_edits and s["kind"] == "area":
            extra = " edits=%s" % s["edits_path"]
        print("%s %d-%d %dB [%d] %s%s" % (s["kind"], s["start"], s["end"], s["bytes"], s["n"], s["heading"], extra))
    total = len("\n".join(lines).encode("utf-8"))
    areas = sum(1 for s in sections if s["kind"] == "area")
    globs = sum(1 for s in sections if s["kind"] == "global")
    print("total %dB ~%d tokens (bytes/4); %d area, %d global" % (total, total // 4, areas, globs))
    if total > 100 * 1024:
        print("Large manifest — consider /comb:patterns --shave")


# ------------------------------------------------------------------- verify

def load_edits(paths):
    edits = []
    for p in paths:
        with open(p, encoding="utf-8") as f:
            raw = f.read().strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```[a-zA-Z]*\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
        data = json.loads(raw)
        if isinstance(data, dict) and "edits" in data:
            data = data["edits"]
        if not isinstance(data, list):
            raise ValueError("%s: not a list" % p)
        for e in data:
            e["_file"] = p
            edits.append(e)
    return edits


def section_by_heading(index, heading):
    for s in index["sections"]:
        if s["heading"] == heading:
            return s
    return None


def section_text(lines, s):
    return "\n".join(lines[s["start"] - 1:s["end"]])


def find_whole_lines(text, old):
    """Return list of (char_start, char_end) where old occurs as whole lines."""
    hits = []
    start = 0
    while True:
        i = text.find(old, start)
        if i < 0:
            break
        j = i + len(old)
        at_line_start = i == 0 or text[i - 1] == "\n"
        at_line_end = j == len(text) or text[j] == "\n"
        if at_line_start and at_line_end:
            hits.append((i, j))
        start = i + 1
    return hits


def derive_anchor_new(old, dropped):
    tok = "`%s`" % dropped if ("`%s`" % dropped) in old else dropped
    if tok not in old:
        return None
    m = re.search(r"\s*\(canonical:\s*" + re.escape(tok) + r"\)", old)
    if m:
        return old[:m.start()] + old[m.end():]
    for sep in SEPARATORS:
        if sep + tok in old:
            return old.replace(sep + tok, "", 1)
    for sep in SEPARATORS:
        if tok + sep in old:
            return old.replace(tok + sep, "", 1)
    new = old.replace(tok, "", 1)
    return re.sub(r"[ \t]{2,}", " ", new)


def anchor_keys(text):
    keys = set()
    for k, p in anchors_in(text):
        keys.add(basename_key(p))
    return keys


def verify_edits(lines, index, edits):
    """Return (passing, rejected). passing edits gain start/end/new."""
    passing, rejected = [], []
    spans = []
    removed_keys = {}
    owners = {}

    def reject(e, why):
        rejected.append({"section": e.get("section"), "class": e.get("class"), "check": why, "file": e.get("_file")})

    for e in edits:
        sec = section_by_heading(index, e.get("section", ""))
        if not sec or sec["kind"] != "area":
            reject(e, "section is not an area section of the manifest")
            continue
        old = e.get("old", "")
        if not isinstance(old, str) or not old.strip():
            reject(e, "old is empty")
            continue
        old = old.rstrip("\n")
        if old.count("\n") >= 12:
            reject(e, "old exceeds 12 lines")
            continue
        text = section_text(lines, sec)
        hits = find_whole_lines(text, old)
        if len(hits) != 1:
            reject(e, "old occurs %d times as whole lines inside the section (need exactly 1)" % len(hits))
            continue
        if any(l.startswith("#") for l in old.split("\n")):
            reject(e, "old removes a heading")
            continue
        cls = e.get("class")
        old_anchors = anchors_in(old)
        if cls == "anchor":
            dropped = e.get("dropped_anchor", "")
            if not dropped:
                reject(e, "anchor edit without dropped_anchor")
                continue
            new = derive_anchor_new(old, dropped)
            if new is None:
                reject(e, "dropped_anchor not found in old")
                continue
            dk = basename_key(LINE_PART.sub("", dropped))
            if len({basename_key(p) for k, p in old_anchors}) < 2:
                reject(e, "old must contain at least one other anchor")
                continue
            if not anchors_in(new):
                reject(e, "derived new has no anchor left")
                continue
            e = dict(e, new=new)
            removed = {dk}
        elif cls == "duplicate":
            if not old_anchors:
                reject(e, "duplicate old contains no anchor")
                continue
            new = e.get("new", "") or ""
            if new and not re.match(r"^- See .+\.$", new.strip()):
                reject(e, "new must be empty or one pointer line '- See <owner heading>.'")
                continue
            if anchors_in(new):
                reject(e, "pointer line must contain no anchor")
                continue
            owner = e.get("owner", "")
            osec = section_by_heading(index, owner)
            if not osec or osec["kind"] != "area" or osec["heading"] == sec["heading"]:
                reject(e, "owner must be another area section")
                continue
            otext = section_text(lines, osec)
            okeys = anchor_keys(otext)
            if not any(basename_key(p) in okeys for k, p in old_anchors):
                reject(e, "owner section contains none of old's anchors")
                continue
            owners.setdefault(sec["heading"], set()).add(osec["heading"])
            e = dict(e, new=new)
            removed = {basename_key(p) for k, p in old_anchors} - anchor_keys(new)
        elif cls == "fixed-drift":
            if "\n" in old:
                reject(e, "fixed-drift old must be one line")
                continue
            if not DRIFT_LINE.search(old):
                reject(e, "not a drift line (no ⚠ or whole-word 'drift')")
                continue
            if not FIXED_MARKERS.search(old):
                reject(e, "no whole-word fixed marker")
                continue
            m = OPEN_MARKERS.search(old)
            if m:
                reject(e, "open marker present: %s" % m.group(0))
                continue
            m = ISSUE_REF.search(old)
            if m:
                reject(e, "issue reference present: %s" % m.group(0))
                continue
            e = dict(e, new="")
            removed = {basename_key(p) for k, p in old_anchors}
        else:
            reject(e, "unknown class %r" % cls)
            continue
        # span in manifest line numbers
        pre = text[:hits[0][0]]
        s_line = sec["start"] + pre.count("\n")
        e_line = s_line + old.count("\n")
        e = dict(e, start=s_line, end=e_line)
        for (a, b, other) in spans:
            if not (e_line < a or s_line > b):
                reject(e, "span overlaps another edit (%s)" % other)
                e = None
                break
        if e is None:
            continue
        clash = [k for k in removed if k in removed_keys]
        if clash:
            reject(e, "removes an anchor another edit removes: %s (%s)" % (clash[0], removed_keys[clash[0]]))
            continue
        for k in removed:
            removed_keys[k] = e["section"]
        spans.append((s_line, e_line, e["section"]))
        passing.append(e)

    # owner graph cycles
    def has_cycle():
        color = {}

        def dfs(u):
            color[u] = 1
            for v in owners.get(u, ()):
                c = color.get(v, 0)
                if c == 1:
                    return True
                if c == 0 and dfs(v):
                    return True
            color[u] = 2
            return False
        return any(color.get(u, 0) == 0 and dfs(u) for u in list(owners))

    if has_cycle():
        kept = []
        for e in passing:
            if e["class"] == "duplicate":
                reject(e, "duplicate owner graph has a cycle")
            else:
                kept.append(e)
        passing = kept
    for e in passing:
        e.pop("_file", None)
    return passing, rejected


def cmd_verify(a):
    lines = read_lines(a.manifest)
    with open(a.index, encoding="utf-8") as f:
        index = json.load(f)
    try:
        edits = load_edits(a.edits)
    except (ValueError, json.JSONDecodeError) as ex:
        die("unusable edit script: %s" % ex, 1)
    passing, rejected = verify_edits(lines, index, edits)
    for e in passing:
        print("ok %s [%s]" % (e["section"], e["class"]))
    for r in rejected:
        print("FAIL %s [%s]: %s" % (r["section"], r["class"], r["check"]))
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump({"manifest": a.manifest, "index": a.index, "edits": passing, "rejected": rejected}, f, indent=1)
    print("verify: %d passing, %d rejected; passing set: %s" % (len(passing), len(rejected), a.out))
    sys.exit(1 if rejected else 0)


# --------------------------------------------------------------------- gate

def cmd_gate(a):
    with open(a.edits, encoding="utf-8") as f:
        data = json.load(f)
    edits, rejected = data["edits"], data.get("rejected", [])
    by_sec = {}
    for e in edits:
        by_sec.setdefault(e["section"], []).append(e)
    full_lines = sum(e["old"].count("\n") + 1 + (e.get("new", "").count("\n") + 1 if e.get("new") else 0)
                     for e in edits if e["class"] == "duplicate")
    collapse = full_lines > GATE_FULL_TEXT_LIMIT and not a.show
    print("Shave gate — %d edits in %d sections, %d rejected. Reply: apply · skip <class> · skip <section> · show <section>" % (
        len(edits), len(by_sec), len(rejected)))
    if collapse:
        print("(duplicate edits collapsed: %d lines of full text; `show <section>` expands one)" % full_lines)
    for sec, es in by_sec.items():
        if a.show and sec != a.show:
            continue
        counts = {}
        removed = 0
        for e in es:
            counts[e["class"]] = counts.get(e["class"], 0) + 1
            removed += len(e["old"].encode("utf-8")) - len(e.get("new", "").encode("utf-8"))
        print("\n## %s — %s; −%dB" % (sec, ", ".join("%s×%d" % (k, v) for k, v in sorted(counts.items())), removed))
        for e in es:
            if e["class"] == "anchor":
                print("  anchor: drop `%s` from: %s" % (e["dropped_anchor"], e["old"].split("\n")[0]))
            elif e["class"] == "fixed-drift":
                print("  fixed-drift: %s" % e["old"])
            else:
                if collapse and not a.show:
                    print("  duplicate → %s: %s" % (e["owner"], e["old"][:80].replace("\n", " ")))
                else:
                    print("  duplicate → %s:" % e["owner"])
                    for l in e["old"].split("\n"):
                        print("    - %s" % l)
                    print("    + %s" % (e.get("new") or "(removed)"))
    if rejected and not a.show:
        print("\nRejected (not applied):")
        for r in rejected:
            print("  %s [%s]: %s" % (r["section"], r["class"], r["check"]))


# ------------------------------------------------------------------- filter

def cmd_filter(a):
    with open(a.edits, encoding="utf-8") as f:
        data = json.load(f)
    before = len(data["edits"])
    data["edits"] = [e for e in data["edits"]
                     if e["class"] not in (a.skip_class or [])
                     and e["section"] not in (a.skip_section or [])]
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
    print("filter: %d of %d edits kept → %s" % (len(data["edits"]), before, a.out))


# -------------------------------------------------------------------- apply

def cmd_apply(a):
    lines = read_lines(a.manifest)
    with open(a.index, encoding="utf-8") as f:
        index = json.load(f)
    with open(a.edits, encoding="utf-8") as f:
        data = json.load(f)
    edits = data["edits"]
    # re-verify against the current text (all-or-nothing)
    passing, rejected = verify_edits(lines, index, [dict(e) for e in edits])
    if rejected:
        for r in rejected:
            print("FAIL %s [%s]: %s" % (r["section"], r["class"], r["check"]))
        die("apply refused: %d edit(s) no longer verify; nothing written" % len(rejected), 1)
    before = len("\n".join(lines).encode("utf-8"))
    text = "\n".join(lines)
    # apply bottom-up by line
    for e in sorted(passing, key=lambda x: x["start"], reverse=True):
        sec = section_by_heading(index, e["section"])
        stext = section_text(lines, sec)
        hits = find_whole_lines(stext, e["old"])
        i, j = hits[0]
        new = e.get("new", "")
        if new:
            stext2 = stext[:i] + new + stext[j:]
        else:
            # remove the lines entirely, including one newline
            if j < len(stext) and stext[j] == "\n":
                stext2 = stext[:i] + stext[j + 1:]
            elif i > 0 and stext[i - 1] == "\n":
                stext2 = stext[:i - 1] + stext[j:]
            else:
                stext2 = stext[:i] + stext[j:]
        new_lines = stext2.split("\n")
        lines[sec["start"] - 1:sec["end"]] = new_lines
        # shift later sections
        delta = len(new_lines) - (sec["end"] - sec["start"] + 1)
        sec["end"] += delta
        for s in index["sections"]:
            if s["start"] > sec["start"]:
                s["start"] += delta
                s["end"] += delta
    if a.stamp:
        header_end = index["header_end"]
        after = len("\n".join(lines).encode("utf-8"))
        stamp = "**Shaved:** %s (%d → %d bytes)" % (time.strftime("%Y-%m-%d"), before, after)
        hdr = lines[:header_end]
        placed = False
        for k, l in enumerate(hdr):
            if l.strip().startswith("**Shaved:**"):
                hdr[k] = stamp
                placed = True
                break
        if not placed:
            for k, l in enumerate(hdr):
                if l.strip().startswith("**Generated:**"):
                    hdr.insert(k + 1, stamp)
                    placed = True
                    break
        if not placed:
            k = len(hdr)
            while k > 0 and not hdr[k - 1].strip():
                k -= 1
            hdr.insert(k, stamp)
        lines[:header_end] = hdr
    out = "\n".join(lines)
    with open(a.manifest, "w", encoding="utf-8") as f:
        f.write(out)
    after = len(out.encode("utf-8"))
    print("apply: %d edits applied; %d → %d bytes" % (len(passing), before, after))


# -------------------------------------------------------------------- clean

def cmd_clean(a):
    ex_dir = os.path.join(os.getcwd(), ".comb", "excerpts")
    n = 0
    if os.path.isdir(ex_dir):
        for name in os.listdir(ex_dir):
            if name.startswith(a.run):
                try:
                    os.remove(os.path.join(ex_dir, name))
                    n += 1
                except OSError:
                    pass
    print("clean: %d file(s) removed for run %s" % (n, a.run))


# --------------------------------------------------------------------- main

def main(argv=None):
    p = argparse.ArgumentParser(prog="manifest.py", description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("excerpt", help="write a per-run excerpt and print the log line and staleness")
    s.add_argument("--skill", required=True)
    s.add_argument("--manifest", required=True)
    s.add_argument("--touched-from", nargs="+", required=True)
    s.set_defaults(fn=cmd_excerpt)

    s = sub.add_parser("index", help="write the section index and print the size table")
    s.add_argument("--skill", default="patterns")
    s.add_argument("--manifest", required=True)
    s.set_defaults(fn=cmd_index)

    s = sub.add_parser("verify", help="check edit scripts mechanically; write the passing set")
    s.add_argument("--manifest", required=True)
    s.add_argument("--index", required=True)
    s.add_argument("--edits", nargs="+", required=True)
    s.add_argument("--out", required=True)
    s.set_defaults(fn=cmd_verify)

    s = sub.add_parser("gate", help="print the gate listing for a passing set")
    s.add_argument("--manifest", required=True)
    s.add_argument("--edits", required=True)
    s.add_argument("--show", default=None)
    s.set_defaults(fn=cmd_gate)

    s = sub.add_parser("filter", help="drop edits by class or section")
    s.add_argument("--edits", required=True)
    s.add_argument("--skip-class", nargs="*", default=[])
    s.add_argument("--skip-section", nargs="*", default=[])
    s.add_argument("--out", required=True)
    s.set_defaults(fn=cmd_filter)

    s = sub.add_parser("apply", help="apply a passing set, all-or-nothing")
    s.add_argument("--manifest", required=True)
    s.add_argument("--index", required=True)
    s.add_argument("--edits", required=True)
    s.add_argument("--stamp", action="store_true")
    s.set_defaults(fn=cmd_apply)

    s = sub.add_parser("clean", help="remove a run's working files")
    s.add_argument("--run", required=True)
    s.set_defaults(fn=cmd_clean)

    a = p.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
