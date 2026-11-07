# Changelog

All notable changes to this kit. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow semantic versioning.

## 0.4.0 - 2026-11-07

### Added
- Hooks (`hooks/hooks.json`, `hooks/run.sh`, `hooks/sdlc_hooks.py`; Python 3 stdlib, fail open, `SDLC_HOOKS=off`):
  - Secret guard on Write, Edit, MultiEdit and NotebookEdit, and on the staged diff before `git commit`; reasons name only the type and line.
  - Command guard on Bash: force-push to main/master, `--no-verify`, staging or printing `.env` and key files.
  - Quality gates from `.sdlc/gates.json` before `git commit` and `git push`, and an optional stop gate with a loop guard; only failures are printed (last 20 lines each).
  - Tree-hash cache: passed gates are not rerun on unchanged code in the session; e2e stamps (`run.sh stamp e2e`, written by `qc-e2e`) let the push gate skip an already-passed suite.
  - Compact SessionStart summary (at most 15 lines): active changes with task counts, last log entry, last gate results.
  - `protected` path globs and optional `format` commands.
- `/ai-sdlc-kit:gates`: writes `.sdlc/gates.json` from the CLAUDE.md Commands checks and git-ignores `.sdlc/state/`.
- `tests/`: stdlib `unittest` suite for the hooks (`python -m unittest`).

### Changed
- `setup` also writes `.sdlc/gates.json`; `qc-e2e` stamps a passing run; `orchestrate` treats a denied commit as a failed check and does not rerun passed suites.
- `templates/CLAUDE.md` Workflow: gates and `SDLC_HOOKS=off`. Existing repos: add the two lines by hand, run `/ai-sdlc-kit:gates`, git-ignore `.sdlc/state/`, and restart Claude Code.

## 0.3.1 - 2026-11-07

- E2E is now a required step: `orchestrate` always runs `qc-e2e` after the implementers finish and loops dev fixes until the suite passes; the CLAUDE.md template adds the rule to Workflow and Definition of done, and lists `qc-e2e` in the agent team.

## 0.3.0 - 2026-11-07

### Added
- `qc-e2e` agent (sonnet): writes black-box e2e tests from a change's spec scenarios, runs the suite, and reports product bugs with the scenario they break. It writes only in the e2e folder and never fixes product code.
- Orchestration: a dev -> QC -> fix loop. See the README section "Dev and QC loop".

## [0.2.0] - 2026-11-07

### Added
- `ai-sdlc-kit:implementer` (sonnet): implements one task from a change's `tasks.md`, runs the checks, never commits.
- `ai-sdlc-kit:scout` (haiku): read-only fact finder with `file:line` answers.
- `ai-sdlc-kit:qc-ui` (sonnet): runs the e2e command from CLAUDE.md `## UI`, inspects screenshots, returns a UI QC report.
- `ai-sdlc-kit:brainstormer` (sonnet): appends 3 to 5 in-scope ideas to `ideas/BACKLOG.md`.
- `/ai-sdlc-kit:orchestrate [change]`: one orchestration cycle with a model routing table, a 3-subagent cap, stop rules and a run log in `.sdlc/log.md`; works under `/loop`.
- `/ai-sdlc-kit:brainstorm`: runs the brainstormer once; `/loop 12h` for periodic runs.
- `templates/VISION.md`, copied by setup to `docs/VISION.md`.
- `templates/CLAUDE.md`: new `## UI` and `## Agent team` sections.

### Changed
- `ai-sdlc-kit:verifier` now pins `model: sonnet`.
- `/ai-sdlc-kit:setup` also copies `docs/VISION.md` (never overwrites).
- Existing repos: add the `UI` and `Agent team` sections to your CLAUDE.md by hand.

## [0.1.0] - 2026-11-06

### Added
- `templates/CLAUDE.md`: one-page project instructions template with a `Purpose | Command | Check?` commands table, workflow, definition of done and known mistakes.
- `templates/REVIEW.md`: review policy template with four passes, three severity levels, a five-minor cap, exclusions and human-only approval.
- `ai-sdlc-kit:verifier`: read-only verifier subagent that runs declared checks, compares an OpenSpec change's tasks and scenarios with evidence, and returns a pass/fail report.
- `/ai-sdlc-kit:setup`: setup skill that copies the templates into the current repository without overwriting.
- Plugin and marketplace manifests (`petrus-sdlc` marketplace).
