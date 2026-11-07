# Spec Delta

## ADDED Requirements

### Requirement: Plugin ships hooks
The plugin SHALL declare its hooks in `hooks/hooks.json` with commands under `${CLAUDE_PLUGIN_ROOT}` that run on Windows (Git Bash), macOS and Linux with only a POSIX shell and the Python 3 standard library.

#### Scenario: Plugin validates
- **WHEN** `claude plugin validate .` runs in the kit repository
- **THEN** it passes with the hooks file present

### Requirement: Gates skill writes the gate config
The plugin SHALL provide `/ai-sdlc-kit:gates`, which writes `.sdlc/gates.json` from the CLAUDE.md Commands table rows marked `yes` in `Check?`, inferring each kind from the purpose (e2e on push, the rest on commit), and asks nothing. It MUST NOT overwrite an existing `.sdlc/gates.json`. It adds `.sdlc/state/` to `.gitignore` when missing. The setup command runs the same step after copying templates.

#### Scenario: Generate from CLAUDE.md
- **GIVEN** a CLAUDE.md with checks "Backend tests", "Backend lint" and "Frontend e2e"
- **WHEN** the user runs `/ai-sdlc-kit:gates`
- **THEN** `.sdlc/gates.json` holds a unit and a lint gate on commit and an e2e gate on push

#### Scenario: Existing config
- **GIVEN** `.sdlc/gates.json` exists
- **WHEN** the user runs `/ai-sdlc-kit:gates`
- **THEN** the file is unchanged and reported as skipped
