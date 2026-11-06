# Evidence

Date: 2026-11-07

| Check | Result |
|---|---|
| `openspec validate kit-v0-2-agent-team --strict` | exit 0, "valid" |
| `claude plugin validate .` | exit 0, marketplace manifest passed |
| `claude plugin validate .claude-plugin/plugin.json` | exit 0, passed |
| Frontmatter of all 5 agents has name, description, tools, model | pass; models: verifier sonnet, implementer sonnet, scout haiku, qc-ui sonnet, brainstormer sonnet |
| scout tools are exactly Read, Grep, Glob | pass |
| `templates/CLAUDE.md` line count | 74 (limit 80); sections in spec order |
| Setup logic on a scratch folder in %TEMP% (existing CLAUDE.md) | first run: CLAUDE.md skipped (content unchanged), REVIEW.md and docs/VISION.md created; second run: all three skipped; docs/VISION.md identical to template; folder deleted |
| Manifest version | plugin.json 0.2.0; marketplace.json carries no version; CHANGELOG has 0.2.0 |

Not verified: the agents and skills were not run end to end in a live Claude Code session (orchestrate, brainstorm, qc-ui need a product repo with e2e and VISION.md).

Note: the change is named `kit-v0-2-agent-team` because OpenSpec rejects dots in change names.

## Live use on LearningHub (2026-11-07)

The agents ran on a real product repo (LearningHub slices 2 and 3), dispatched by the main session as general-purpose subagents following `agents/<name>.md`. Plugin agents load only after a Claude Code restart, so the session could not use them by type.
- qc-ui (sonnet): two runs, both pass. Each inspected 9 to 10 screenshots in light and dark. It found 8 minor issues, and 4 were fixed: React Flow controls in dark mode, an unreadable start zoom, the list loading state, and contradictory empty-lesson copy. One claim was wrong: it said console errors were not recorded, but the suite records them.
- verifier (sonnet): one run covering two changes. Seven checks ran in sequence, both verdicts pass, and no scenarios were uncovered.
- brainstormer (sonnet): wrote 5 in-scope ideas to `ideas/BACKLOG.md` and parked none.
- orchestrate: run by hand by the main session, which acted as orchestrator. Entries are in LearningHub's `.sdlc/log.md`. `/loop` was not started because it needs the owner to type it.
