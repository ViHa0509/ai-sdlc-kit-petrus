# Spec Delta

## MODIFIED Requirements

### Requirement: CLAUDE.md template sections
The kit SHALL provide a CLAUDE.md template with these sections in this order: Project (one paragraph), Commands (run, test, lint, type check, format), UI (app URL, e2e command, screenshot folder, viewport), Layout, Conventions, Workflow (how changes flow through OpenSpec), Agent team (one line per agent with model and job, and the two loop commands), Definition of done, Known mistakes.

#### Scenario: Template content
- **WHEN** a product repo installs the template
- **THEN** its CLAUDE.md contains every listed section with placeholder guidance in each
