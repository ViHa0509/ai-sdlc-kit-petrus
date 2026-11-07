# Design

## Context

Hooks are the only kit piece that runs outside the model. Contract (Claude Code hooks docs, checked 2026-11-07): plugin hooks live in `hooks/hooks.json`, commands may use `${CLAUDE_PLUGIN_ROOT}`; input arrives as JSON on stdin (`session_id`, `cwd`, `hook_event_name`, `tool_name`, `tool_input`, `stop_hook_active`, `source`); PreToolUse denies with `hookSpecificOutput.permissionDecision: "deny"` and `permissionDecisionReason`; Stop blocks with top-level `decision: "block"` and `reason`; SessionStart adds `hookSpecificOutput.additionalContext`; matchers made of letters and `|` are exact tool-name lists; `timeout` is in seconds (default 600).

## Decisions

1. **One Python script, one shim.** `hooks/run.sh <subcommand>` honors `SDLC_HOOKS=off`, probes for a working Python 3 (`python`, `py -3`, `python3` on Windows, where `python3` is often the Store stub; `python3`, `python` elsewhere) with `-c ""`, then `exec`s `hooks/sdlc_hooks.py`. No Python: exit 0, plus a one-line stderr warning for the secret subcommands. The Python entry catches every exception and exits 0 (warning on stderr for secret checks). Stdlib only.
2. **JSON output only, never exit 2.** Denials use the PreToolUse JSON form so the reason is structured; exit code is always 0. Silence means allow and normal permission flow continues (we never emit `allow`, so hooks cannot bypass the user's permission prompts).
3. **Shell lexer for Bash rules.** Heredoc bodies are stripped first; then a small quote-aware lexer splits the command into simple commands on `&&`, `||`, `;`, `|`, `&` and newlines. Rules look only at command words, so a commit message that mentions `git push --force` is inert. Printing secret files is matched on the reader command plus a secret-file argument.
4. **Secret patterns.** Typed regexes for known providers, a PEM block rule, and a generic `name = value` rule that requires a name with key/secret/token/password, a value of at least 16 safe chars that ends the statement, letters and digits, and Shannon entropy >= 3.3. Placeholder heuristics run on the matched value. Findings report `type` and `line` only.
5. **Tree hash for freshness.** The key is `git write-tree` of a temporary index (copy of the real index, then `git add -A -- . ":(exclude).sdlc"`). It is content-addressed, so the hash after a commit equals the hash tested before it, and a push sees the same tree that qc-e2e tested. Not a git repo: no hash, no cache.
6. **Cache rules.** `.sdlc/state/cache.json` keeps the last 100 passes `{gate, kind, cmd_sha, tree, session}`. e2e passes count across sessions (stamps); others only within the session that ran them. Failures are not cached because they often depend on the environment (database down).
7. **Gate runner.** Gates run sequentially from the repo root through `sh -c` (falls back to the platform shell), with a per-gate timeout (default 900 s). All selected gates run so one denial reports every failure. Output is stripped of ANSI codes; the deny reason holds at most 20 tail lines per failing gate, 200 chars per line. Results go to `.sdlc/state/last-gates.json` for the session summary.
8. **Stop gate.** SessionStart records the baseline tree for the session (only when stop gates exist). Stop does nothing unless stop gates exist and the tree differs from the baseline and from the last passing stop tree. A per-session counter of consecutive blocks allows the stop after 2 blocks when `stop_hook_active` is true.
9. **Session context.** `openspec list --json` (10 s timeout) when `openspec/` exists, the last `## ` entry of `.sdlc/log.md` (heading + 5 lines), and the last gate results; capped at 15 lines; nothing when empty. SessionStart also writes `.sdlc/state/plugin_root` so agents can find `run.sh` for `stamp`. No UserPromptSubmit hook at all.
10. **Config.** `protected` applies to files committed in HEAD, so a migration still being written stays editable. `.sdlc/gates.json`: `gates`, `protected`, `format`, `secrets {allow, ignore_paths}`, `hooks {secrets, commands, gates, stop, context, protected, format}` (all true by default). Secret and command guards work with no config; gates, protected and format need it.
11. **Gates generator.** `run.sh init-gates` parses the CLAUDE.md Commands table deterministically (so the skill spends no tokens on judgment), infers kind from the purpose text (e2e > integration > lint > type > build > test), writes `.sdlc/gates.json` only when absent and appends `.sdlc/state/` to `.gitignore` when missing.
12. **Hook timeouts.** Bash PreToolUse and Stop: 1800 s (gates may run an e2e suite). Write guards: 30 s. SessionStart: 30 s. PostToolUse format: 60 s.

## Risks

- A formatter that rewrites a file can make the next Edit fail with "file modified since read"; the formatter is opt-in.
- Regex secret detection has false positives; allow-lists, inline markers and `ignore_paths` cover them.
- Running gates inside the Bash hook makes `git commit` slow when gates are slow; this is the point, and the cache keeps repeats cheap.
- Live firing inside Claude Code cannot be tested by unit tests; tests feed the documented JSON to the script.
