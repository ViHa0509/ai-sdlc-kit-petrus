# CLAUDE.md

<!-- Keep this file at most 120 lines. Move long material to docs/ and link it. -->

## Project

<!-- One paragraph: what this product is, who uses it, and what matters most (for example correctness over speed). -->

## Commands

Agents and the verifier run exactly these commands to decide whether work is done.
Rows with `yes` in **Check?** are checks; the verifier runs every check and nothing else.

| Purpose | Command | Check? |
|---|---|---|
| <!-- Run backend --> | <!-- uvicorn app.main:app --reload --> | no |
| <!-- Backend tests --> | <!-- pytest --> | yes |
| <!-- Lint --> | <!-- ruff check . --> | yes |
| <!-- Type check --> | <!-- mypy . --> | yes |
| <!-- Format --> | <!-- ruff format . --> | no |

<!-- Write commands exactly as they are typed, with the folder to run them from if not the repo root. -->

## Layout

<!-- Top-level folders and what lives in each, one line per folder. -->

## Conventions

<!-- Rules an agent cannot infer from the code: naming, error handling, where config lives,
     what never to edit (generated files, migrations already applied), language of code and comments. -->

## Workflow

- Every change starts as an OpenSpec change: `/opsx:propose` -> review -> `/opsx:apply`.
- Work only on tasks in `openspec/changes/<change>/tasks.md`; mark a task `[x]` only when its check passes.
- A behavior the specs do not describe is new scope: update the change's artifacts first.
- Before a PR, run the verifier subagent on the change and paste its report into the PR.
- Never weaken or delete a test to make it pass.

## Definition of done

- [ ] Every command marked as a check in Commands passes.
- [ ] The tasks for this work are checked in the change's `tasks.md`.
- [ ] Every spec scenario touched by this work has a test.
- [ ] The verifier report is attached to the PR.

## Known mistakes

<!-- One line per mistake an agent really made here: date - mistake - rule that prevents it.
     Add a line when the same mistake happens a second time. Example:
     2026-01-15 - edited an applied migration - create a new migration instead. -->
