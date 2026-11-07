# project-instructions Specification

## Purpose
Gives every product repo one short, version-controlled CLAUDE.md that tells agents how to run, test and check the project and which mistakes not to repeat.

## Requirements

### Requirement: CLAUDE.md template sections
The kit SHALL provide a CLAUDE.md template with these sections in this order: Project (one paragraph), Commands (run, test, lint, type check, format), UI (app URL, e2e command, screenshot folder, viewport), Layout, Conventions, Workflow (how changes flow through OpenSpec), Agent team (one line per agent with model and job, and the two loop commands), Definition of done, Known mistakes.

#### Scenario: Template content
- **WHEN** a product repo installs the template
- **THEN** its CLAUDE.md contains every listed section with placeholder guidance in each

### Requirement: Template stays under one page
The filled-in template SHALL fit on one page: the kit's template itself MUST be at most 80 lines, and its guidance MUST tell the product to keep the file at most 120 lines and move long material to linked docs.

#### Scenario: Line budget
- **WHEN** the template file is measured
- **THEN** it has at most 80 lines

### Requirement: Commands are the single source of checks
The Commands section SHALL list exact, copy-pasteable commands per part of the product (for example backend and frontend), and the template MUST state that agents and the verifier run exactly these commands to decide whether work is done.

#### Scenario: Verifier reads commands
- **GIVEN** a product CLAUDE.md lists `pytest` and `npm test` under Commands
- **WHEN** the verifier runs
- **THEN** it runs those commands and no other test commands

### Requirement: Definition of done is explicit
The template SHALL define done as: all Commands pass, the change's tasks for the work are checked, specs scenarios touched by the work have tests, and the verifier report is attached to the PR.

#### Scenario: Done criteria present
- **WHEN** an agent reads the Definition of done section
- **THEN** it finds those four criteria as a checklist

### Requirement: Known mistakes grow from real failures
The Known mistakes section SHALL hold one line per mistake an agent actually made in this repo, each with the date and the rule that prevents it, and the template MUST say to add a line whenever the same mistake happens twice.

#### Scenario: Recording a repeated mistake
- **WHEN** an agent repeats a mistake already seen once
- **THEN** the guidance tells it to add a dated line under Known mistakes with the preventing rule

### Requirement: Template mentions gates
The CLAUDE.md template SHALL state that checks also run as hook gates from `.sdlc/gates.json`, that a denied commit means a failed check, and that `SDLC_HOOKS=off` is for humans only.

#### Scenario: Reading the template
- **WHEN** an agent reads a CLAUDE.md made from the template
- **THEN** it learns that commits run the gates and must not be bypassed
