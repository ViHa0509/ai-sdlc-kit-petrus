# orchestration Specification

## Purpose
Defines one orchestration cycle that dispatches the team's agents on a change's pending tasks, chooses a model per task by complexity, and stops when a human is needed.

## Requirements

### Requirement: Cycle selects change and tasks
The orchestrate skill SHALL read the product CLAUDE.md and `openspec list --json`, then pick the change: the argument if given, else the only active change with pending tasks, else stop and ask. It then picks the next pending tasks of that change.

#### Scenario: Several candidate changes
- **WHEN** no argument is given and more than one active change has pending tasks
- **THEN** the cycle stops and asks which change to work on

#### Scenario: Nothing to do
- **WHEN** no active change has pending tasks
- **THEN** the cycle reports "idle"

### Requirement: Model routing table
The skill SHALL contain a routing table. Haiku: scout lookups, summaries and mechanical edits with no judgment. Sonnet: an implementer for a task whose spec and design are clear, qc-ui, verifier. Opus or the main session: writing or changing specs or design, tasks touching security, data migrations or cross-cutting design, resolving a blocked implementer, and the final review against REVIEW.md.

#### Scenario: Routing a task
- **WHEN** a task is a data migration
- **THEN** the cycle assigns it to opus or the main session, not to a sonnet implementer

### Requirement: Parallelism cap
The cycle SHALL run tasks that touch different files in parallel and tasks that touch the same files one after another. It MUST NOT run more than 3 subagents at once.

#### Scenario: Overlapping files
- **WHEN** two pending tasks edit the same file
- **THEN** they run one after the other

### Requirement: Verify, QC and one retry
After the implementers finish, the cycle SHALL run the verifier. If the change touches UI and CLAUDE.md has a UI section, it SHALL also run qc-ui. On a fail it sends the findings to an implementer once; if the result still fails it stops and reports.

#### Scenario: Second failure
- **WHEN** the verifier still fails after one retry
- **THEN** the cycle stops, commits nothing, and reports needs human

### Requirement: Commit only on green
The cycle SHALL commit only when every check passes, with a message naming the tasks. It MUST NOT push.

#### Scenario: All green
- **WHEN** the verifier verdict is pass (and qc-ui, when run)
- **THEN** one commit is made naming the task numbers

### Requirement: Needs-human stops
The cycle SHALL stop and report "needs human" for: a spec or design decision, missing credentials or API keys, a destructive or outward action not authorized in CLAUDE.md, and two failed attempts.

#### Scenario: Missing API key
- **WHEN** a task needs an API key that is not available
- **THEN** the cycle stops and reports needs human with the key name

### Requirement: Run log
Each cycle SHALL append an entry to `.sdlc/log.md` with the date, change, tasks attempted, agent and model per task, verdicts, and what needs the human.

#### Scenario: Log entry
- **WHEN** a cycle ends for any reason, including idle
- **THEN** `.sdlc/log.md` has a new entry with those fields

### Requirement: Loop use
The skill SHALL document `/loop /ai-sdlc-kit:orchestrate` and `/loop 30m /ai-sdlc-kit:orchestrate`. When run from /loop and the cycle is idle or needs a human, it MUST end the loop instead of scheduling another run.

#### Scenario: Idle in a loop
- **WHEN** a looped cycle finds no pending work
- **THEN** it reports idle and does not schedule another run

### Requirement: Cycle relies on hook gates
When the repo has `.sdlc/gates.json`, the orchestrate cycle SHALL treat a denied commit as a failed check (fix and retry under the retry rule) and MUST NOT rerun a suite the gates or a stamp report as passed on the same tree.

#### Scenario: Commit denied by a gate
- **WHEN** the cycle's commit is denied by a failing gate
- **THEN** the failing gate is handled like a failed check and the cycle does not bypass the hook
