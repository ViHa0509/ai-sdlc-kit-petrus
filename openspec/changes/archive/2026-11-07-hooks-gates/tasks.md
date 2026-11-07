# Tasks

## 1. Hook runtime

- [x] 1.1 Add `hooks/run.sh` (off switch, Python probe, fail open) and `hooks/hooks.json` (PreToolUse Write|Edit|MultiEdit|NotebookEdit and Bash, PostToolUse, Stop, SessionStart). Verified by: shim test in `tests/` and `claude plugin validate .`.
- [x] 1.2 Add `hooks/sdlc_hooks.py` with secret guard, protected paths and command guard. Verified by: unittest cases for secrets, placeholders, allow-list, protected, force push, no-verify, cat .env, quoted text.
- [x] 1.3 Add gates: config, runner, tree hash, cache, stamp, commit/push gating, stop gate with loop guard. Verified by: unittest cases for failing gate, passing gate, no config, stamp skip, changed tree, stop_hook_active.
- [x] 1.4 Add SessionStart context and PostToolUse format. Verified by: unittest cases for empty and non-empty context and the line cap.
- [x] 1.5 Add `init-gates` generator. Verified by: unittest that builds gates from a sample Commands table and skips an existing file.

## 2. Skills, agents, templates

- [x] 2.1 Add `skills/gates/SKILL.md`; setup runs the gates step. Verified by: `claude plugin validate .`.
- [x] 2.2 qc-e2e writes the stamp after a passing run; orchestrate relies on gates. Verified by: grep for `stamp e2e` and `gates.json`.
- [x] 2.3 `templates/CLAUDE.md` mentions gates and `SDLC_HOOKS=off`. Verified by: grep; the file stays at most 120 lines.

## 3. Release

- [x] 3.1 README Hooks section, CHANGELOG 0.4.0, `plugin.json` 0.4.0. Verified by: grep for 0.4.0.
- [x] 3.2 `python -m unittest` passes, `openspec validate hooks-gates --strict` passes, `claude plugin validate .` passes. Verified by: exit codes.
- [x] 3.3 Write the Learning Hub `.sdlc/gates.json` (not committed there). Verified by: `init-gates` output plus the `protected` entry, valid JSON.
