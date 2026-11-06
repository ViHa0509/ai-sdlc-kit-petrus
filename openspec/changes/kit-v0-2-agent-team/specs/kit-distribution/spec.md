# Spec Delta

## MODIFIED Requirements

### Requirement: Setup command writes templates into the product repo
The plugin SHALL provide a setup command that copies the CLAUDE.md and REVIEW.md templates into the current repository root and the VISION.md template to `docs/VISION.md`. It MUST NOT overwrite an existing file; it reports which files it created and which it skipped.

#### Scenario: Fresh repo
- **GIVEN** the repository has no CLAUDE.md, no REVIEW.md and no docs/VISION.md
- **WHEN** the user runs the setup command
- **THEN** all three files are created from the templates and reported as created

#### Scenario: Existing file
- **GIVEN** the repository already has a CLAUDE.md
- **WHEN** the user runs the setup command
- **THEN** CLAUDE.md is left unchanged and reported as skipped, and REVIEW.md and docs/VISION.md are created if missing
