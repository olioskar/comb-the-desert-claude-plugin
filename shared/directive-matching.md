# Shared block: surface relevant directives

Lowercase the focus brief and scan it for substring matches against the loaded directive filenames (both plugin defaults at `${CLAUDE_PLUGIN_ROOT}/directives/*.md` and the user's directives at `<project-root>/<directives.user_path>/*.md` if present). Strip the `.md` extension before matching, but match against the *full base name* — so `"scope"` matches `scope-discipline.md`, `"simplicity"` matches `simplicity.md`, and `"copy-paste"` would match a user directive named `copy-paste.md` if present (it doesn't match the shipped `reusability.md` — the matcher is a literal substring check, not a synonym mapper).

Record the matched directive paths. They are flagged as **primary** in the run brief under the heading "Directives most relevant to this run" so agents weight them first; the dispatch prompt itself carries no directive paths.

A brief word shorter than four characters (`it`, `a`, `and`) matches only when it equals a whole hyphen-separated segment of the base name, so `api` flags `api.md` and `it` flags nothing.

If the focus brief is empty, no directives are flagged primary; all directives still load normally.

`scripts/comb.py directives --brief "<text>"` performs the match and prints the `plugin:`, `user:`, and `primary:` lists; `comb.py brief` renders them into the run brief.
