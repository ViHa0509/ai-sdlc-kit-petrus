# Tasks

## 1. Agents

- [x] 1.1 Add `agents/implementer.md`. Verified by: frontmatter check lists name, description, tools, model sonnet.
- [x] 1.2 Add `agents/scout.md`. Verified by: frontmatter check shows tools Read, Grep, Glob and model haiku.
- [x] 1.3 Add `agents/qc-ui.md`. Verified by: frontmatter check; file contains the `UI QC report` format and the no-UI-section rule.
- [x] 1.4 Add `agents/brainstormer.md`. Verified by: frontmatter check; file names `ideas/BACKLOG.md` and Parking lot.
- [x] 1.5 Add `model: sonnet` to `agents/verifier.md`. Verified by: frontmatter check.

## 2. Skills

- [x] 2.1 Add `skills/orchestrate/SKILL.md` with routing table, parallelism cap, stop rules, log and loop section. Verified by: `claude plugin validate .` and grep for each rule.
- [x] 2.2 Add `skills/brainstorm/SKILL.md`. Verified by: `claude plugin validate .` and grep for the `/loop 12h` line.
- [x] 2.3 Update `skills/setup/SKILL.md` to also copy `templates/VISION.md` to `docs/VISION.md`. Verified by: manual run of the steps on a scratch folder, twice (created, then skipped).

## 3. Templates

- [x] 3.1 Add `## UI` and `## Agent team` to `templates/CLAUDE.md`. Verified by: `wc -l` is at most 80 and sections are in spec order.
- [x] 3.2 Add `templates/VISION.md`. Verified by: grep shows the five sections in order.

## 4. Release

- [x] 4.1 Update README, CHANGELOG (0.2.0) and manifests to 0.2.0. Verified by: grep for the version in both manifests and CHANGELOG.
- [x] 4.2 Run `claude plugin validate .` and `openspec validate kit-v0-2-agent-team --strict`, and write `evidence.md`. Verified by: exit codes 0 recorded in evidence.md.
