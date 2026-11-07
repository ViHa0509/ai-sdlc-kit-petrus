# Evidence

Recorded 2026-11-07 on Windows 11, Git Bash, Python 3.12.10.

- `python -m unittest` (repo root): 40 tests, OK.
- `openspec validate hooks-gates --strict`: valid; after archive `openspec validate --all --strict`: 13 passed.
- `claude plugin validate .` and `claude plugin validate --strict .claude-plugin/plugin.json`: passed.
- Hook contract checked against https://code.claude.com/docs/en/hooks: PreToolUse `hookSpecificOutput.permissionDecision` deny with reason, Stop `decision: block` with `reason`, SessionStart `additionalContext`, exact-list matchers, timeouts in seconds.
- Learning Hub dry runs: secret scan over its 214 tracked files found 1 short fake key in a frontend test (covered by a narrow `secrets.allow` entry); protected path denies committed `0001_create_notes.py` and allows the uncommitted `0006_provider_key_kind.py`; session summary printed 8 lines with both active changes.
- Latency (Windows): Bash calls without git or secret-file names exit in the shell (~0.3 s, shell start-up); others ~0.8 s.
- Not verified here: live firing inside a running Claude Code session (needs a plugin update and a restart).
