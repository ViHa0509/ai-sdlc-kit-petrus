# AI SDLC Kit

A small Claude Code plugin that puts an AI-native development loop into any repository, following Anthropic's [AI-native SDLC playbook](https://claude.com/resources/articles/the-ai-native-sdlc-playbook) on top of [OpenSpec](https://github.com/Fission-AI/OpenSpec).

What you get in v0.1.0:

| Piece | What it does |
|---|---|
| `templates/CLAUDE.md` | One-page project instructions: commands (with a `Check?` column), layout, conventions, workflow, definition of done, known mistakes |
| `templates/REVIEW.md` | Review policy for every PR: four passes, three severities, a nit cap, human-only approval |
| `/ai-sdlc-kit:setup` | Copies both templates into the current repo, never overwriting existing files |
| `ai-sdlc-kit:verifier` | Read-only subagent with a fresh context: runs the `Check? = yes` commands from CLAUDE.md, checks an OpenSpec change's tasks and spec scenarios, and returns a pasteable pass/fail report |

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
2. Fill in `CLAUDE.md`: the Project paragraph, the Commands table (mark real checks with `yes`), Layout and Conventions.
3. Commit `CLAUDE.md` and `REVIEW.md`.
4. After implementing work, ask Claude to "run the verifier on change `<change-name>`" and paste the report into the PR.

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
