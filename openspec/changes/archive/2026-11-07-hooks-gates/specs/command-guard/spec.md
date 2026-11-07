# Spec Delta

## ADDED Requirements

### Requirement: Force push to main is denied
Before a Bash tool call, the kit SHALL deny a force push (`--force`, `-f`, `--force-with-lease`, a `+` refspec, `--mirror`) whose target is `main` or `master`, or that names no target while the current branch is `main` or `master`.

#### Scenario: Force push to main
- **WHEN** an agent runs `git push --force origin main`
- **THEN** the call is denied

#### Scenario: Normal push
- **WHEN** an agent runs `git push origin feature-x`
- **THEN** the guard allows it

### Requirement: Skipping commit hooks is denied
The kit SHALL deny `git commit` with `--no-verify` or `-n`.

#### Scenario: Skipping commit hooks
- **WHEN** an agent runs `git commit --no-verify -m x`
- **THEN** the call is denied

### Requirement: Secret files are recognized by name
A secret file SHALL be `.env`, `.env.*` other than `.env.example`, `.env.sample`, `.env.template` and `.env.dist`, or a file named `*.pem`, `*.key`, `*.p12`, `*.pfx`, `id_rsa`, `id_ed25519`, `id_ecdsa`.

#### Scenario: Example file is not secret
- **WHEN** an agent runs `git add .env.example`
- **THEN** the guard allows it

### Requirement: Adding secret files is denied
The kit SHALL deny `git add` of a secret file, and a bulk `git add -A`, `git add --all` or `git add .` when a secret file that is not git-ignored has changes.

#### Scenario: Adding .env
- **WHEN** an agent runs `git add backend/.env`
- **THEN** the call is denied

### Requirement: Printing secret files is denied
The kit SHALL deny Bash commands that print a secret file with a file reader: `cat`, `type`, `more`, `less`, `head`, `tail`, `Get-Content`, `gc`, `bat`, `nl`, `xxd`, `od`, `base64`, `strings`, `grep`, `rg`, `awk`, `sed`, `findstr` or `Select-String`, also when wrapped in `bash -c`, `sh -c`, `powershell -Command` or `pwsh -Command`.

#### Scenario: cat .env
- **WHEN** an agent runs `cat backend/.env`
- **THEN** the call is denied

#### Scenario: Example env file
- **WHEN** an agent runs `cat .env.example`
- **THEN** the call is allowed

### Requirement: Quoted text does not trigger rules
Rules SHALL look only at command words: quoted arguments and heredoc bodies (such as commit messages) MUST NOT trigger a rule.

#### Scenario: Commit message mentions a forbidden command
- **WHEN** an agent runs `git commit -m "docs: never use git push --force"`
- **THEN** no command rule denies it
