# idea-generation Specification

## Purpose
Lets the team propose product ideas now and then, kept inside the scope the owner confirmed, without the agent deciding or building anything.

## Requirements

### Requirement: VISION template
The kit SHALL provide `templates/VISION.md` with sections Goals, In scope, Out of scope, Confirmed decisions and Open questions, each with placeholder guidance.

#### Scenario: Template sections
- **WHEN** the template is read
- **THEN** it has those five sections in that order

### Requirement: Brainstormer adds scoped ideas
The brainstormer SHALL read CLAUDE.md Project, `docs/VISION.md`, `openspec/specs`, active changes and `ideas/BACKLOG.md`, and append 3 to 5 ideas under a dated heading in `ideas/BACKLOG.md`, creating it if missing. Each idea has a title, the problem it solves, a proposal in 2 to 3 sentences, the VISION goal it serves, size S, M or L, and risks.

#### Scenario: New batch
- **WHEN** the brainstormer runs
- **THEN** `ideas/BACKLOG.md` gains a dated heading with 3 to 5 ideas, each with all listed fields

### Requirement: Out-of-scope ideas are parked
An idea outside VISION's scope SHALL go under `## Parking lot` with the reason. The brainstormer MUST NOT repeat an idea already in the backlog or specs.

#### Scenario: Out-of-scope idea
- **WHEN** an idea matches an item in VISION's Out of scope list
- **THEN** it is listed under Parking lot with the reason and not under the dated heading

### Requirement: Brainstormer only proposes
The brainstormer MUST NOT write code or change any file except `ideas/BACKLOG.md`, and MUST NOT decide: the owner promotes an idea with `/opsx:propose`.

#### Scenario: Other files untouched
- **WHEN** the brainstormer finishes
- **THEN** only `ideas/BACKLOG.md` has changed

### Requirement: Brainstorm skill
The `/ai-sdlc-kit:brainstorm` skill SHALL run the brainstormer once, report the titles it added, and document `/loop 12h /ai-sdlc-kit:brainstorm` for periodic runs.

#### Scenario: One run
- **WHEN** the user runs the skill
- **THEN** it reports the new idea titles
