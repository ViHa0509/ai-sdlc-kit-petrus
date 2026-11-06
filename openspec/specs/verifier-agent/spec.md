# verifier-agent Specification

## Purpose
Provides an independent verifier subagent that checks finished work with a fresh context, so "done" is decided by evidence rather than by the agent that wrote the code.

## Requirements

### Requirement: Fresh, read-only verifier
The kit SHALL provide a verifier subagent that runs in its own context and is limited to reading files and running commands; it MUST NOT have file editing or writing tools.

#### Scenario: Tool limits
- **WHEN** the verifier definition is inspected
- **THEN** its allowed tools exclude Edit, Write and NotebookEdit

### Requirement: Runs the product's declared checks
The verifier SHALL run every command in the product CLAUDE.md Commands section that is marked as a check (test, lint, type check), capture each command's exit code and the tail of its output, and never substitute other commands.

#### Scenario: All checks pass
- **WHEN** every declared check exits with code 0
- **THEN** the report lists each command with "pass" and its output tail

#### Scenario: A check fails
- **WHEN** one declared check exits non-zero
- **THEN** the report marks it "fail" with its output tail and the overall verdict is fail

#### Scenario: No commands declared
- **WHEN** the product CLAUDE.md has no check commands
- **THEN** the verifier reports "cannot verify: no checks declared" and the verdict is fail

### Requirement: Compares work with the OpenSpec change
Given a change name, the verifier SHALL read that change's tasks and specs and report, for each task marked done, whether evidence exists (a test, a file, an observable result), and list spec scenarios with no matching test.

#### Scenario: Task checked without evidence
- **GIVEN** task 2.3 is checked but no test covers its scenarios
- **WHEN** the verifier runs on the change
- **THEN** the report lists task 2.3 as "checked, no evidence" and the verdict is fail

### Requirement: Report format
The verifier SHALL end with one Markdown report: overall verdict (pass or fail) first, then a checks table, then task evidence, then uncovered scenarios, then at most five notes. It MUST NOT approve, merge or mark tasks itself.

#### Scenario: Report is pasteable
- **WHEN** the verifier finishes
- **THEN** its final message is a single Markdown report starting with the verdict, ready to paste into a PR
