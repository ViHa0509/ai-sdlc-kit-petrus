# AI SDLC Kit

A small Claude Code plugin that puts an AI-native development loop into any repository, following Anthropic's [AI-native SDLC playbook](https://claude.com/resources/articles/the-ai-native-sdlc-playbook) on top of [OpenSpec](https://github.com/Fission-AI/OpenSpec).

What you get in v0.2.0:

| Piece | What it does |
|---|---|
| `templates/CLAUDE.md` | One-page project instructions: commands (with a `Check?` column), layout, conventions, workflow, definition of done, known mistakes |
| `templates/REVIEW.md` | Review policy for every PR: four passes, three severities, a nit cap, human-only approval |
| `templates/VISION.md` | The scope the owner confirms: goals, in scope, out of scope, decisions, open questions |
| `/ai-sdlc-kit:setup` | Copies the templates into the current repo (`docs/VISION.md` for the vision), never overwriting existing files |
| `ai-sdlc-kit:verifier` | Read-only subagent with a fresh context: runs the `Check? = yes` commands from CLAUDE.md, checks an OpenSpec change's tasks and spec scenarios, and returns a pasteable pass/fail report |
| Agent team | `implementer`, `scout`, `qc-ui`, `brainstormer`, plus `/ai-sdlc-kit:orchestrate` and `/ai-sdlc-kit:brainstorm` (see below) |

## Install

In your shell:

```bash
claude plugin marketplace add ViHa0509/ai-sdlc-kit-petrus
claude plugin install ai-sdlc-kit@petrus-sdlc
```

Or inside a Claude Code session: `/plugin marketplace add ViHa0509/ai-sdlc-kit-petrus`, then `/plugin install ai-sdlc-kit@petrus-sdlc`.

Check it loaded: `claude plugin list` shows `ai-sdlc-kit@petrus-sdlc` as enabled.

## Set up a product repo

1. Open Claude Code in the product repository and run `/ai-sdlc-kit:setup`.
2. Fill in `CLAUDE.md`: the Project paragraph, the Commands table (mark real checks with `yes`), UI (if the product has one), Layout and Conventions. Fill in `docs/VISION.md`.
3. Commit `CLAUDE.md`, `REVIEW.md` and `docs/VISION.md`.
4. After implementing work, ask Claude to "run the verifier on change `<change-name>`" and paste the report into the PR.

## Agent team

| Agent or skill | Model | Job |
|---|---|---|
| `scout` | haiku | Read-only lookups, answers with `file:line` |
| `implementer` | sonnet | Does one task from `tasks.md`, runs the checks, marks the task done only when they pass |
| `verifier` | sonnet | Runs the checks, compares the change with its specs |
| `qc-ui` | sonnet | Runs the e2e command from the `## UI` section, inspects every screenshot, returns a UI QC report |
| `brainstormer` | sonnet | Adds 3 to 5 ideas inside `docs/VISION.md` scope to `ideas/BACKLOG.md`; never decides |
| `/ai-sdlc-kit:orchestrate` | main session | Runs one cycle: picks tasks, routes agents and models, verifies, commits on green, logs |
| `/ai-sdlc-kit:brainstorm` | main session | Runs the brainstormer once |

### Model routing

| Work | Model |
|---|---|
| Lookups, summaries, mechanical edits with no judgment | haiku |
| A task with a clear spec and design, the verifier, qc-ui | sonnet |
| Specs, design, security, data migrations, cross-cutting design, blocked tasks, final review | opus (main session) |

### Run it

- One cycle: `/ai-sdlc-kit:orchestrate [change]`.
- Looped: `/loop /ai-sdlc-kit:orchestrate` (self-paced) or `/loop 30m /ai-sdlc-kit:orchestrate`. The loop ends when the cycle is idle or needs a human.
- Ideas now and then: `/loop 12h /ai-sdlc-kit:brainstorm`. The owner promotes an idea with `/opsx:propose`.

Limits: at most 3 subagents at once, one retry per failed task, commits only when every check passes, never pushes. Each cycle appends to `.sdlc/log.md`.

## Update

```bash
claude plugin marketplace update petrus-sdlc
claude plugin update ai-sdlc-kit@petrus-sdlc
```

Updating never touches files already copied into a repo. When CHANGELOG.md says a template changed, compare your repo's file with the new template and merge by hand.

## Not yet included

Planned for later versions, driven by what goes wrong in real use:

- Hooks as guardrails (for example a guard that keeps the verifier read-only, and one that blocks editing tests during a fix).
- An eval harness and CI workflow templates.
- Monitoring and lessons-file automation.

## Development

The kit is planned and built with OpenSpec: see `openspec/changes/`. Validate before releasing:

```bash
claude plugin validate .
```
