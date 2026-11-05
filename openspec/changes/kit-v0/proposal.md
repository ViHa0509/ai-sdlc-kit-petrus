# Proposal

## Why

Building Learning Hub with AI agents only becomes real Agentic Engineer experience if the agents work inside a repeatable, reviewable process instead of ad-hoc prompts. Anthropic's AI-native SDLC playbook names the minimum pieces (shared project instructions, a review policy, an independent verifier), and they should live in one reusable kit rather than being copied by hand into each product repo. Kit v0 is the thinnest version that the first product change (`slice-1-import-and-map` in LearningHub) can already use.

## What Changes

- Add a `CLAUDE.md` template for product repos: sections for run, test and lint commands, conventions, architecture notes and a "known mistakes" list that grows when an agent repeats an error; kept under one page.
- Add a `REVIEW.md` template: review passes (correctness, security, spec conformance, tests), severity levels, a cap on nits, and exclusions.
- Add a verifier subagent definition that starts with a fresh context, runs the checks listed in the product's `CLAUDE.md`, compares the result with the change's specs and tasks, and reports pass/fail with the actual command output. It never edits code and never approves its own work.
- Package the kit as a Claude Code plugin so a product repo installs it instead of copying files, with a README explaining install and update.
- Out of scope for v0: hooks (guardrails), eval harness and CI workflows, monitoring and lessons automation. They come in later kit versions, driven by what goes wrong in Learning Hub.

## Capabilities

### New Capabilities

- `project-instructions`: the CLAUDE.md template and how a product repo fills it in.
- `review-policy`: the REVIEW.md template that AI and human reviewers follow on every PR.
- `verifier-agent`: the independent verification subagent and its report format.
- `kit-distribution`: packaging and installing the kit into a product repo as a Claude Code plugin, and versioning it.

### Modified Capabilities

None. The kit has no existing specs.

## Impact

- New files in this repo: `templates/CLAUDE.md`, `templates/REVIEW.md`, `agents/verifier.md`, plugin manifest, `README.md`.
- First consumer: LearningHub (`https://github.com/ViHa0509/LearningHub`), task 1.5 of `slice-1-import-and-map`.
- No runtime dependencies; requires Claude Code with plugin support.
