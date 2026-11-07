# Proposal

## Why

Agents in kit repos repeat the same expensive work: they rerun full test suites that already passed, rediscover the active change at every session start, and paste long test logs into the conversation. Nothing mechanical stops them from committing red code, writing an API key into a file, force-pushing `main` or printing `.env`. The rules live only in CLAUDE.md, which an agent can forget. Claude Code plugin hooks run outside the model, cost no tokens when they pass, and can block a tool call, so they are the right place for gates and guards.

## What Changes

- Ship plugin hooks (`hooks/hooks.json`) with one Python 3 stdlib script behind a small `sh` shim that finds a Python and fails open.
- **Secret guard** (PreToolUse on Write, Edit, MultiEdit, NotebookEdit): deny writes whose new content holds a likely secret; the reason names only the secret type and line.
- **Command guard** (PreToolUse on Bash): deny force-push to main/master, `git commit --no-verify`, `git add` of secret files, commands that print secret files, and commits whose staged diff holds a secret.
- **Quality gates**: a per-repo `.sdlc/gates.json` lists gate commands with a kind (unit, integration, e2e, lint, types, build) and when they run (commit, push, stop). Commit and push are denied with a short summary when a gate fails.
- **Freshness and cache**: a pass is recorded against a content hash of the working tree; an e2e gate that already passed on the same tree is skipped (qc-e2e records a stamp after a passing run); other gates reuse a pass from the same session.
- **Stop gate**: when source changed in the session, `stop` gates run before the agent may stop; a failure blocks the stop once or twice, never forever.
- **Session context**: a compact (at most 15 lines) SessionStart summary of the active OpenSpec change, the last log entry and the last gate results, printed only when there is something.
- **Repo standards**: `protected` path globs (committed files only) and an optional silent formatter after edits.
- Escape hatch `SDLC_HOOKS=off`; every hook silent on success.
- New skill `/ai-sdlc-kit:gates` writes `.sdlc/gates.json` from the CLAUDE.md Commands table; setup runs it.
- README Hooks section, template and orchestrate updates, version 0.4.0.

Out of scope: blocking test weakening, CI templates, hooks for other events (UserPromptSubmit is deliberately unused so no text repeats on every prompt).

## Capabilities

### New Capabilities
- `secret-guard`: secret detection on file writes and staged commits, placeholders and allow-lists.
- `command-guard`: Bash command rules (force push, no-verify, adding or printing secret files).
- `quality-gates`: gate config, commit/push/stop gates, short failure summaries, tree-hash cache and e2e stamps.
- `session-context`: the compact SessionStart summary.
- `repo-standards`: protected paths, optional formatter, the off switch and fail-open behavior.

### Modified Capabilities
- `kit-distribution`: the plugin ships hooks; a gates skill writes `.sdlc/gates.json`, and setup runs it.
- `orchestration`: the cycle relies on commit gates and does not rerun passed suites.
- `project-instructions`: the CLAUDE.md template mentions gates and `.sdlc/gates.json`.

## Impact

New: `hooks/hooks.json`, `hooks/run.sh`, `hooks/sdlc_hooks.py`, `skills/gates/SKILL.md`, `tests/`. Changed: `agents/qc-e2e.md`, `skills/setup/SKILL.md`, `skills/orchestrate/SKILL.md`, `templates/CLAUDE.md`, README, CHANGELOG, `plugin.json`. Product repos get the hooks on plugin update; the gates do nothing until `.sdlc/gates.json` exists, while the secret and command guards are on by default. Repos should git-ignore `.sdlc/state/`.
