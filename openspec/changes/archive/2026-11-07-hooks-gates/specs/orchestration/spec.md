# Spec Delta

## ADDED Requirements

### Requirement: Cycle relies on hook gates
When the repo has `.sdlc/gates.json`, the orchestrate cycle SHALL treat a denied commit as a failed check (fix and retry under the retry rule) and MUST NOT rerun a suite the gates or a stamp report as passed on the same tree.

#### Scenario: Commit denied by a gate
- **WHEN** the cycle's commit is denied by a failing gate
- **THEN** the failing gate is handled like a failed check and the cycle does not bypass the hook
