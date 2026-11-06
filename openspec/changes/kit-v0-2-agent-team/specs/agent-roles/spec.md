# Spec Delta

## Purpose
Defines the implementer and scout subagents and requires every kit agent to pin a model, so cost follows task complexity.

## ADDED Requirements

### Requirement: Every kit agent pins a model
Each subagent in the kit SHALL declare `name`, `description`, `tools` and `model` in its frontmatter. The models are: verifier sonnet, implementer sonnet, scout haiku, qc-ui sonnet, brainstormer sonnet.

#### Scenario: Frontmatter complete
- **WHEN** any file under `agents/` is inspected
- **THEN** its frontmatter has name, description, tools and model, and the model matches the list above

### Requirement: Implementer does one task
The implementer SHALL implement exactly one task from a change's tasks.md named by the caller. It reads the change's proposal, specs and design and the repo CLAUDE.md first, follows CLAUDE.md conventions, runs the relevant checks, and marks the task `[x]` only when its check passes. It MUST NOT edit specs, design or proposal, weaken a test, commit or push; when an artifact must change it reports that instead.

#### Scenario: Check passes
- **WHEN** the implementer finishes a task and its check exits 0
- **THEN** the task is marked `[x]` and the report says status done

#### Scenario: Check fails or spec is wrong
- **WHEN** the check cannot pass or the work needs a spec or design change
- **THEN** the task stays unchecked and the report says status blocked with the reason

### Requirement: Implementer report is fixed
The implementer SHALL end with a short report: task, files changed, checks run with exit codes, and status done or blocked with a reason.

#### Scenario: Report fields
- **WHEN** the implementer finishes
- **THEN** its final message contains those four items and nothing else

### Requirement: Scout is read-only fact finding
The scout SHALL have only Read, Grep and Glob, answer with `file:line` references, give no opinions and make no edits.

#### Scenario: Tool limits
- **WHEN** the scout definition is inspected
- **THEN** its tools are exactly Read, Grep and Glob
