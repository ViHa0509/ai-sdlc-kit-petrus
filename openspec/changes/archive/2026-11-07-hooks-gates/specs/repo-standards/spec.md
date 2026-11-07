# Spec Delta

## ADDED Requirements

### Requirement: Protected paths
When `.sdlc/gates.json` lists `protected` globs (relative to the repo root, `*` within one folder, `**` across folders), the kit SHALL deny Write, Edit, MultiEdit and NotebookEdit calls on an existing file that matches and is committed in HEAD (outside git: any existing file). Creating a new file, or changing one that is not committed yet, is allowed.

#### Scenario: Applied migration
- **GIVEN** `protected` holds `backend/alembic/versions/*` and `0001_init.py` is committed there
- **WHEN** an agent edits `backend/alembic/versions/0001_init.py`
- **THEN** the edit is denied

#### Scenario: New migration
- **WHEN** an agent writes a new file `backend/alembic/versions/0002_add.py`
- **THEN** the write is allowed

#### Scenario: Migration not committed yet
- **GIVEN** `0003_wip.py` exists in `backend/alembic/versions/` but is not committed
- **WHEN** an agent edits it
- **THEN** the edit is allowed

### Requirement: Optional silent formatter
When `.sdlc/gates.json` lists `format` entries (`glob`, `cmd` with `{file}`), the kit SHALL run the matching command on the edited file after a successful Write, Edit or MultiEdit, and print nothing whatever the result.

#### Scenario: Formatter configured
- **GIVEN** a `format` entry whose glob matches the edited file
- **WHEN** an agent edits that file
- **THEN** the command runs with the file path and the hook prints nothing

### Requirement: Off switch and fail open
Every hook SHALL do nothing when the environment variable `SDLC_HOOKS` is `off`. When no Python 3 is found or the script fails, the hook allows the call; a secret check that cannot run writes a one-line warning to stderr. Hooks print nothing on success except the one-line gate summary and the session context.

#### Scenario: Escape hatch
- **GIVEN** `SDLC_HOOKS=off`
- **WHEN** an agent runs `git push --force origin main`
- **THEN** the hook allows it

#### Scenario: Bad input fails open
- **WHEN** the hook receives input that is not JSON
- **THEN** it exits 0 and allows the call
