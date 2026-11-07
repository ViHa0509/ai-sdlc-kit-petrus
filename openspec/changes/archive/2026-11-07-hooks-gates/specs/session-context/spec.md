# Spec Delta

## ADDED Requirements

### Requirement: Compact session start summary
On session start, resume, clear and compact, the kit SHALL add at most 15 lines of context: the active OpenSpec changes with task progress, the heading and up to 5 lines of the last `.sdlc/log.md` entry, and the last gate results. When none of these exists, it prints nothing. The kit MUST NOT add text on every user prompt.

#### Scenario: Repo with a run log
- **GIVEN** a `.sdlc/log.md` with entries
- **WHEN** a session starts
- **THEN** the context holds the last entry's heading, in at most 15 lines

#### Scenario: Empty repo
- **GIVEN** no OpenSpec changes, no log and no gate results
- **WHEN** a session starts
- **THEN** the hook prints nothing
