# Design

## Context

Kit v0.1.0 is markdown only: agents, skills, templates. Subagents cannot spawn subagents, so the "orchestrator" must be a skill run by the main session, which then calls the other agents. `/loop` re-runs a prompt or slash command; a cycle must therefore be self-contained and safe to repeat. See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**
- Small team with clear, narrow roles and least-privilege tools.
- Model chosen per task by complexity, written down in one table.
- A cycle that is safe to loop: it stops itself when it needs a human.

**Non-Goals:**
- Hooks, CI, an e2e framework, pushing or merging.
- Agents deciding scope; scope comes from `docs/VISION.md`.

## Decisions

- **Orchestrator is a skill, not an agent.** Subagents cannot dispatch subagents, so the main session runs the skill. Alternative: an orchestrator agent; rejected for that reason.
- **Routing table in the skill.** One place to tune. Opus work stays in the main session instead of a subagent, so no extra context hand-off.
- **Agents coordinate through files.** The implementer reads tasks.md and writes `[x]`; the verifier and qc-ui read the result; `.sdlc/log.md` carries state between looped cycles. No agent needs to talk to another directly.
- **qc-ui uses the product's e2e command.** The kit does not pick a browser tool. Screenshots are read with Read, which renders images.
- **Brainstormer is bounded by VISION.md.** Ideas outside scope go to a parking lot. Write access is `ideas/BACKLOG.md` only (by rule; the tool list cannot limit paths).
- **Template budget.** The CLAUDE.md template stays at or under 80 lines with the two new sections.
- **Change name** uses hyphens (`kit-v0-2-agent-team`) because OpenSpec rejects dots.

## Risks / Trade-offs

- Tool lists cannot restrict paths, so brainstormer and qc-ui write limits are rules, not enforcement. A later hook can enforce them.
- A looped cycle that commits could commit wrong work; mitigated by committing only on green, never pushing, and the one-retry cap.
- Haiku mechanical edits may be wrong; the verifier runs after every cycle.
