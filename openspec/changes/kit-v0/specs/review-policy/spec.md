# Spec Delta

## Purpose

Defines one REVIEW.md that AI reviewers and the human owner apply to every pull request, so reviews are consistent, ranked by severity and free of noise.

## ADDED Requirements

### Requirement: Review passes
The kit SHALL provide a REVIEW.md template that defines four review passes run in this order: spec conformance (does the change do what its specs and tasks say), correctness, security, and tests.

#### Scenario: Passes listed
- **WHEN** a reviewer reads REVIEW.md
- **THEN** it finds the four passes, each with a short checklist of what to look for

### Requirement: Severity levels
REVIEW.md SHALL define exactly three severity levels - blocker (must fix before merge), major (fix in this PR unless the owner defers it in writing), minor (optional) - and every finding MUST carry one level, a file and line, and a failure scenario.

#### Scenario: Finding format
- **WHEN** a reviewer reports a finding
- **THEN** the finding has a severity, a location and a concrete failure scenario

### Requirement: Nit cap and exclusions
REVIEW.md SHALL cap minor findings at five per review and list exclusions that are never reported: formatting handled by the formatter, generated files, lock files, and style preferences not written in CLAUDE.md.

#### Scenario: Too many minors
- **WHEN** a reviewer finds eight minor issues
- **THEN** it reports the five most useful and states that three more were omitted

### Requirement: Humans approve, agents do not
REVIEW.md SHALL state that only the human owner approves and merges, that an agent never approves its own work, and that a PR merges only with no open blocker and a passing verifier report.

#### Scenario: Agent-authored PR
- **WHEN** an agent opened the PR
- **THEN** the merge still requires the human owner's approval
