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
The plugin SHALL provide a setup command that copies the CLAUDE.md and REVIEW.md templates into the current repository root. It MUST NOT overwrite an existing file; it reports which files it created and which it skipped.

#### Scenario: Fresh repo
- **GIVEN** the repository has no CLAUDE.md and no REVIEW.md
- **WHEN** the user runs the setup command
- **THEN** both files are created from the templates and reported as created

#### Scenario: Existing file
- **GIVEN** the repository already has a CLAUDE.md
- **WHEN** the user runs the setup command
- **THEN** CLAUDE.md is left unchanged and reported as skipped, and REVIEW.md is created if missing

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
