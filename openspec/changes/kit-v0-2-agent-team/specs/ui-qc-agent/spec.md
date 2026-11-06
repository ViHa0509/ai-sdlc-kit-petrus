# Spec Delta

## Purpose
Gives the team a UI quality check that runs the product's e2e suite and looks at the screenshots it produces, so UI defects are found before the owner sees them.

## ADDED Requirements

### Requirement: qc-ui reads the UI section
The qc-ui agent SHALL read the `## UI` section of the product CLAUDE.md for the app URL, the e2e command, the screenshot folder and the viewport. When there is no such section it MUST report "cannot check: no UI section" with verdict fail.

#### Scenario: No UI section
- **WHEN** CLAUDE.md has no `## UI` section
- **THEN** the report says "cannot check: no UI section" and the verdict is fail

### Requirement: qc-ui runs the suite and inspects screenshots
The agent SHALL run the e2e command exactly as written, record its exit code and output tail, open every screenshot in the screenshot folder, and inspect each against the UI scenarios of the change (when given) and general UI quality: readable text and contrast in light and dark, nothing overlapping or cut off, empty and error states, layout at the given viewport, and console or network errors when the suite records them.

#### Scenario: Suite fails
- **WHEN** the e2e command exits non-zero
- **THEN** the checks table marks it fail and the verdict is fail

#### Scenario: Visual defect
- **WHEN** a screenshot shows cut-off or low-contrast text
- **THEN** the findings list names the screenshot file, a severity, what is wrong and what the user would see

### Requirement: qc-ui does not change source
The agent SHALL NOT edit source files. It MAY write only inside the screenshot or results folder.

#### Scenario: Tool and path limits
- **WHEN** the agent definition is inspected
- **THEN** its tools are Read, Grep, Glob and Bash, and its rules limit writes to the results folder

### Requirement: qc-ui report format
The agent SHALL end with one report starting `## UI QC report: pass` or `fail`, then a checks table and a findings list. Severities are blocker, major and minor as in REVIEW.md. The verdict is fail if any check failed or any blocker or major finding exists.

#### Scenario: Clean run
- **WHEN** the suite passes and no blocker or major finding exists
- **THEN** the report starts `## UI QC report: pass`
