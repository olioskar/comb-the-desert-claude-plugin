# Shared block: manifest excerpts

Every consuming skill (`/comb:review`, `/comb:plan`, `/comb:fix`, and `/comb:the-desert` through them) delivers the PATTERNS manifest to agents as a **per-run excerpt**, not as the whole file. The excerpt is cut by `${CLAUDE_PLUGIN_ROOT}/scripts/manifest.py`; nobody reads the manifest to produce it. The command line lives in each skill body (the plugin-root variable is substituted there, not here); this block says what the command does and what the skill does with its output.

## What `excerpt` does

`manifest.py excerpt --skill <name> --manifest <path> --touched-from <file>...`

1. Splits the manifest into a header (everything before the first `## ` heading) and `## ` sections.
2. Classifies each section. **Global**: a heading that, after leading non-alphanumerics, begins with `how to read`, `cross-reference`, `cross reference`, `drift register`, `known drift`, or `maintenance`, or equals `patterns` or `index`. **Area**: every other section.
3. Derives each area section's scope from two sources only. **Scope lines**: a line beginning `Scope:` or `Home:` (after leading `_`/`*`); its backticked path tokens become globs (`{x}` → `*`, trailing `/` → `/**`, no glob character → `/**`); a line with no path-like token is prose and counts as absent. **Anchors**: `path/with/ext:line` tokens in the text. A section with neither is **unscoped**.
4. Extracts touched paths from the raw text of every `--touched-from` file: diff name lists, a review report, instruction files, a revise doc. No skill parses paths itself.
5. Marks an area section relevant when a touched path matches one of its globs, equals one of its anchors, or (only for a section with no scope line) sits in the same directory as one of its anchors. Unscoped sections, the header, and every global section always travel.
6. Writes the excerpt under `.comb/excerpts/` in the current working directory, creating `.comb/` with a `.gitignore` of `*` on first use, so nothing under it ever appears in `git status` or gets staged. Header lines over 400 characters (provenance stamps) are truncated in the excerpt. The excerpt opens with a banner listing the omitted sections and their line ranges so an agent can read one with `sed -n START,ENDp <manifest>`.
7. Computes staleness: `cited` = the manifest's anchors (basenames resolved through their section's directories where the file exists); when `cited ∩ touched` is empty the manifest is not stale; otherwise `git diff --name-only <base_commit> HEAD -- <intersection>` decides; a git failure or a header with no base commit gives `unknown`. The base commit is the `**Base commit:**` line when present, else the last hex token in the header that contains a letter.

It prints, and nothing more:

```
run: <stem>
excerpt: .comb/excerpts/<stem>.md
PATTERNS excerpt: <n> of <m> area sections included (<headings>); <g> global; omitted: <headings or none>
stale: yes|no|unknown (<detail>)
base_commit: <sha or none>
```

## What the skill does

- **Run it once, after the touched text exists, never at load.** The touched text per skill:

  | Skill | `--touched-from` | After |
  |---|---|---|
  | review | the file holding the diff's name list (`git diff --name-only`, `gh pr diff --name-only`, or the user's file list) | Step 2 has gathered the diff |
  | plan | the review report | Step 3 has parsed it |
  | fix | every instruction file in the folder, or the revise doc | Step 2.5 has listed the folder (and so after the pre-flight) |

- **Record `run`, `excerpt`, the log line, and `stale` once** and use the excerpt path in every dispatch of this run. `/comb:the-desert` records them afresh in each sub-step.
- **Deliver per `${CLAUDE_PLUGIN_ROOT}/shared/observed-baseline.md`**: the excerpt path and the full manifest path, with the excerpt sentences.
- **Echo the log line** in the presentation's manifest notes. When `stale` is `yes`, add the staleness note; when `unknown`, add `PATTERNS staleness unknown (<detail>)`.
- **Clean up last**: `manifest.py clean --run <stem>`. Best-effort; a leftover is ignored by git and harmless.
- **Never read the manifest.** Not with Read, `cat`, `head`, or a range-free `sed`. An agent that needs an omitted section reads it by the banner's line range.

## Fallback

When `python3` is missing, or `excerpt` exits non-zero without printing an `excerpt:` line, print `PATTERNS excerpt unavailable (<reason>) — full manifest delivered`, deliver the full manifest path with the **fallback form** of the observed-baseline block (no excerpt sentences), skip staleness, and continue. Never silent, never a stop. A `stale: unknown` line is not a failure.
