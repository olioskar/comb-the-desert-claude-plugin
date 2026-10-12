# Shared block: manifest excerpts

Every consuming skill (`/comb:review`, `/comb:plan`, `/comb:fix`, and `/comb:the-desert` through them) delivers the PATTERNS manifest to agents as a **per-run excerpt**, not as the whole file. The excerpt is cut by the plugin's `scripts/manifest.py`; nobody reads the manifest to produce it. The command line lives in each skill body (the plugin-root variable is substituted there, not here); this block says what the `excerpt` subcommand does and what the skill does with its output. Every `manifest.py` command is run from the project root, because `.comb/` is keyed to the working directory.

## What `excerpt` does

Inputs: `--skill <name>`, `--manifest <path>`, and `--touched-from`, which takes files, a directory of `.md` files, or `-` for stdin.

Section classification, scope-line and anchor parsing, touched-path extraction, relevance, the banner, and staleness follow one grammar; it is the module docstring of `scripts/manifest.py` — the implementation's contract — and is not restated here. What it produces:

- The header and every **global** section (how-to-read, cross-reference map, drift register, maintenance, index) always travel; an **area** section travels when a touched path meets its scope — its `Scope:`/`Home:` globs, or its `file:line` anchors when it has no scope line — and a section with neither always travels.
- Touched paths are extracted by the script from the raw touched text (a piped diff name list, a review report, an instruction folder, a revise doc). No skill parses paths itself.
- The excerpt lands under `.comb/excerpts/` in the current working directory (`.comb/` is created with a `.gitignore` of `*`, so nothing under it ever appears in `git status`) and opens with a banner listing the omitted sections and their line ranges, so an agent can read one with `sed -n START,ENDp <manifest>`.
- Staleness compares the manifest's base commit (its `**Base commit:**` line, else the last hex token with a letter in the header) against the touched paths the manifest cites; a git failure or a missing base commit gives `unknown`.

It prints, and nothing more:

```
run: <stem>
excerpt: <absolute path under .comb/excerpts/>
PATTERNS excerpt: <n> of <m> area sections included (<headings>); <g> global; omitted: <headings or none>
stale: yes|no|unknown (<detail>)
base_commit: <sha or none>
```

## What the skill does

- **Run it once, after the touched text exists, never at load.** The touched text per skill:

  | Skill | `--touched-from` | After |
  |---|---|---|
  | review | the diff's name list piped on stdin (`git diff --name-only`, `gh pr diff --name-only`, or the user's file list) | Step 2 has gathered the diff |
  | plan | the review report | Step 3 has parsed it |
  | fix | the instruction folder (every `.md` in it: per-finding files or the revise doc) | Step 2.5 has listed the folder (and so after the pre-flight) |

- **Record `run`, `excerpt`, the log line, and `stale` once** and use the excerpt path in every dispatch of this run. `/comb:the-desert` records them afresh in each sub-step.
- **Deliver per `${CLAUDE_PLUGIN_ROOT}/shared/observed-baseline.md`**: the excerpt path and the full manifest path, with the excerpt sentences.
- **Echo the log line** in the presentation's manifest notes. When `stale` is `yes`, add the staleness note; when `unknown`, add `PATTERNS staleness unknown (<detail>)`.
- **Clean up last**: `manifest.py clean --run <stem>`. Best-effort; a leftover is ignored by git and harmless.
- **Never read the manifest.** Not with Read, `cat`, `head`, or a range-free `sed`. An agent that needs an omitted section reads it by the banner's line range.

## Fallback

When `excerpt` exits non-zero without printing an `excerpt:` line (including an empty touched set, which the script refuses so that an empty or failed diff never passes as a successful excerpt), print `PATTERNS excerpt unavailable (<reason>) — full manifest delivered`, deliver the full manifest path with the **fallback form** of the observed-baseline block (no excerpt sentences), skip staleness, and continue. Never silent, never a stop. A `stale: unknown` line is not a failure.
