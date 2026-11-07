# kit-distribution Specification

## Purpose
Lets a product repo install, set up and update the kit as one versioned Claude Code plugin instead of copying files by hand.

## Requirements

### Requirement: Installable Claude Code plugin
The kit repository SHALL be installable as a Claude Code plugin from its GitHub repository: it declares a plugin manifest with name, version and description, and a marketplace entry that points to that plugin.

#### Scenario: Install from GitHub
- **WHEN** the user adds the repository as a plugin marketplace in Claude Code and installs the kit plugin
- **THEN** the verifier subagent and the kit's setup command become available in that Claude Code session

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

### Requirement: Semantic versioning with a changelog
The kit SHALL use semantic versions in its plugin manifest, starting at `0.1.0` for Kit v0, and keep a CHANGELOG.md entry for every released version.

#### Scenario: First release
- **WHEN** Kit v0 is released
- **THEN** the manifest version is `0.1.0` and CHANGELOG.md has a `0.1.0` entry listing the templates, the verifier and the setup command

### Requirement: README explains install, setup and update
The kit SHALL include a README that explains in this order: what the kit is, how to install it, how to run setup in a product repo, how to update to a newer version, and what is planned but not yet included.

#### Scenario: New user follows README
- **WHEN** someone follows the README in a new product repo
- **THEN** they end with the plugin installed, CLAUDE.md and REVIEW.md present, and the verifier available

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
