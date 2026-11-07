---
name: orchestrate
description: Run one orchestration cycle on an OpenSpec change. Picks the pending tasks, sends each to the right agent and model, runs the verifier and the UI check, commits when everything passes, and logs the cycle. Use when the user runs /ai-sdlc-kit:orchestrate [change] or loops it.
argument-hint: "[change-name]"
---

# Orchestrate one cycle

You are the main session. Subagents cannot start other subagents, so you dispatch them. Do one cycle, then stop.

## Steps

1. **Read context.** Read `CLAUDE.md` at the repository root. Run `openspec list --json`.
2. **Pick the change.** Use the argument if given. Otherwise use the only active change that has pending tasks. If several qualify, stop and ask which one. If none has pending tasks, go to step 10 with the result `idle`.
3. **Pick tasks.** Read `openspec/changes/<change>/tasks.md`. Take the next unchecked tasks, at most 3 at a time.
4. **Route each task** with the table below. Write down the agent and model for each.
5. **Dispatch.** Tasks that touch different files may run in parallel. Tasks that touch the same files run one after another. Never run more than 3 subagents at once. Give each implementer the change name and one task number.
6. **Test end to end.** This step is required. After the implementers finish, and before verifying or committing, run `qc-e2e` on the change whenever CLAUDE.md has an e2e command. If it has none, record `qc-e2e not run (no e2e command)` in the log. For each product bug it reports, send the bug to the implementer that owns the area, then run `qc-e2e` again. Repeat until it passes. Stop with `needs human` after 3 rounds that end with the same failing scenario.
7. **Verify.** When the implementers are done, run the `verifier` on the change. If the change touches UI and CLAUDE.md has a `## UI` section, also run `qc-ui`.
8. **Retry once.** If a verdict is fail, send the findings to an implementer once. Run the verdicts again. If it still fails, stop with `needs human` and commit nothing.
9. **Commit.** Only when every check and the e2e suite pass: review the diff against `REVIEW.md` yourself, then make one commit with a message naming the tasks, for example `Tasks 1.1, 1.2 of <change>: <short summary>`. Do not push.
10. **Log.** Append an entry to `.sdlc/log.md` (create the folder and file if missing):

```
## <YYYY-MM-DD HH:MM> <change or none>
- Result: done | idle | needs human
- Tasks: <numbers attempted>
- Agents: <task> -> <agent> (<model>), one per line
- Verdicts: qc-e2e <pass|fail|not run> (rounds: N), verifier <pass|fail>, qc-ui <pass|fail|not run>
- Needs human: <what, or none>
```

11. **Report** the same facts in a few lines.

## Routing table

| Work | Agent | Model |
|---|---|---|
| Lookups, file lists, summaries | `scout` | haiku |
| Mechanical edits with no judgment: renames, moving text, formatting | `implementer` told to do only that, or the main session | haiku |
| A task whose spec and design are clear | `implementer` | sonnet |
| Check the change | `verifier` | sonnet |
| Check the UI | `qc-ui` | sonnet |
| Write and run e2e tests from the specs | `qc-e2e` | sonnet |
| Write or change specs or design | main session | opus |
| Task touching security, a data migration, or cross-cutting design | main session | opus |
| Resolve a blocked implementer | main session | opus |
| Final review against REVIEW.md | main session | opus |

When unsure, use the more capable model. Pass the model to the Agent tool as an override when it differs from the agent's default.

## Needs human

Stop the cycle and report `needs human` when:

- a spec or design decision is needed;
- a credential or API key is missing (name it);
- an action is destructive or outward (push, deploy, delete data, send messages) and CLAUDE.md does not authorize it;
- the same task failed twice.

Never push. Never edit specs or design to get a task through; that is a human decision unless the change itself is to write them.

## Running in a loop

```
/loop /ai-sdlc-kit:orchestrate            # self-paced
/loop 30m /ai-sdlc-kit:orchestrate        # every 30 minutes
```

When this skill runs from `/loop` and the cycle ends `idle` or `needs human`, end the loop instead of scheduling another run, and say why.
