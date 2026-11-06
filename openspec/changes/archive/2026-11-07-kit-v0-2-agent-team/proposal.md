# Proposal

## Why

Kit v0.1.0 has one agent (the verifier) and the human does all the coordinating. The owner wants a small agent team: one that tests the UI, one that implements tasks, one that proposes ideas inside the confirmed scope, and an orchestrator that dispatches them and picks a model per job so cheap work does not run on the biggest model.

Note: the requested change name `kit-v0.2-agent-team` is not valid for OpenSpec (dots are not allowed), so the change is named `kit-v0-2-agent-team`.

## What Changes

- Add subagents `implementer` (sonnet), `scout` (haiku), `qc-ui` (sonnet) and `brainstormer` (sonnet).
- Pin the verifier to `model: sonnet`.
- Add skill `/ai-sdlc-kit:orchestrate [change]`: one orchestration cycle with a model routing table, a parallelism cap, a run log, and stop rules. It can run under `/loop`.
- Add skill `/ai-sdlc-kit:brainstorm`: runs the brainstormer once; usable under `/loop 12h`.
- Add `templates/VISION.md` and make setup copy it to `docs/VISION.md`.
- Add `## UI` and `## Agent team` sections to `templates/CLAUDE.md`.
- README section on the team, routing and loops; CHANGELOG 0.2.0; version 0.2.0.

Out of scope: hooks, CI templates, an e2e framework (the product brings its own e2e command), pushing or merging by agents.

## Capabilities

### New Capabilities
- `agent-roles`: the implementer and scout subagents and the model pinned for every kit agent.
- `ui-qc-agent`: the qc-ui subagent that runs the e2e command and inspects screenshots.
- `orchestration`: the orchestrate skill: routing, parallelism, stop rules, run log, loop use.
- `idea-generation`: the brainstormer agent, the brainstorm skill and the VISION template.

### Modified Capabilities
- `project-instructions`: the template gains `UI` and `Agent team` sections.
- `kit-distribution`: setup also copies `VISION.md` to `docs/VISION.md`.

## Impact

New files under `agents/`, `skills/`, `templates/`. Changed: `agents/verifier.md`, `skills/setup/SKILL.md`, `templates/CLAUDE.md`, README, CHANGELOG, plugin manifests. Product repos that already ran setup keep their files; they merge the new CLAUDE.md sections by hand.
