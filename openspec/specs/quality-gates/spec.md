# quality-gates Specification

## Purpose
Runs a repo's declared checks automatically before commit, push and stop, reports only failures, and never reruns a suite that already passed on the same code.

## Requirements

### Requirement: Gate configuration
A product repo SHALL declare gates in `.sdlc/gates.json` as a list of objects with `name`, `cmd`, `kind` (one of unit, integration, e2e, lint, types, build) and `on` (a list of commit, push, stop), and an optional `timeout` in seconds. Commands run from the repository root in a POSIX shell. When the file does not exist or has no gates, no gate runs and nothing is printed.

#### Scenario: No config
- **GIVEN** the repo has no `.sdlc/gates.json`
- **WHEN** an agent runs `git commit -m x`
- **THEN** no gate runs and the hook prints nothing

### Requirement: Commit and push gates
Before a Bash call that runs `git commit`, the kit SHALL run every gate whose `on` contains `commit`; before `git push` (not `--dry-run`), every gate whose `on` contains `push`. When a gate fails, the call is denied with a short summary: the failing gate names with exit codes and at most the last 20 lines of each failing output. When all pass, the kit adds at most one line `gates passed: <names>` as context and never prints full logs.

#### Scenario: Failing unit gate blocks the commit
- **GIVEN** a commit gate `unit-tests` whose command exits 1
- **WHEN** an agent runs `git commit -m x`
- **THEN** the commit is denied and the reason names `unit-tests` and shows the tail of its output

#### Scenario: Passing gates
- **GIVEN** commit gates that exit 0
- **WHEN** an agent runs `git commit -m x`
- **THEN** the commit proceeds and the only gate text is one `gates passed:` line

### Requirement: Passed suites are not rerun
The kit SHALL record each gate pass against a content hash of the working tree (git-ignored files and `.sdlc/` excluded). An `e2e` gate is skipped when a pass for the same tree exists from any session; another gate is skipped when the same command passed on the same tree in the same session. Failures are never cached. The command `run.sh stamp <kind|name>` records a pass for the current tree; qc-e2e calls it after a passing suite.

#### Scenario: E2E stamp skips the push gate
- **GIVEN** qc-e2e recorded an e2e stamp and the tree has not changed
- **WHEN** an agent runs `git push`
- **THEN** the e2e gate is reported as cached and its command does not run

#### Scenario: Changed tree reruns
- **GIVEN** an e2e stamp exists
- **WHEN** a source file changes and an agent runs `git push`
- **THEN** the e2e gate runs again

### Requirement: Stop gate
When gates with `on: stop` exist and the working tree differs from both the tree at session start and the last tree that passed the stop gates, the kit SHALL run them when the agent stops and block the stop with the short summary when one fails. When the stop hook is already active, the kit blocks at most twice in a row per session and then lets the agent stop.

#### Scenario: Unchanged session
- **GIVEN** stop gates exist and no file changed in the session
- **WHEN** the agent stops
- **THEN** no gate runs

#### Scenario: Loop guard
- **GIVEN** the stop gate already blocked twice in a row and still fails
- **WHEN** the agent stops again with `stop_hook_active` true
- **THEN** the stop is allowed
