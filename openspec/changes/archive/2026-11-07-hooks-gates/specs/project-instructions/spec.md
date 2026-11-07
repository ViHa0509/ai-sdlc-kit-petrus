# Spec Delta

## ADDED Requirements

### Requirement: Template mentions gates
The CLAUDE.md template SHALL state that checks also run as hook gates from `.sdlc/gates.json`, that a denied commit means a failed check, and that `SDLC_HOOKS=off` is for humans only.

#### Scenario: Reading the template
- **WHEN** an agent reads a CLAUDE.md made from the template
- **THEN** it learns that commits run the gates and must not be bypassed
