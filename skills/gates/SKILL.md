---
name: gates
description: Write the hook gate config .sdlc/gates.json from the CLAUDE.md Commands table rows marked as checks, without asking anything and without overwriting an existing file. Use when the user runs /ai-sdlc-kit:gates, asks to set up commit/push gates, or after setup.
---

# Write the gate config

The kit's hooks run quality gates before `git commit` and `git push` (and optionally when the agent stops). They read `.sdlc/gates.json` in the repository root. This skill creates that file from CLAUDE.md. Ask nothing.

## Steps

1. Run exactly this from the repository root and keep its output:

```bash
sh "${CLAUDE_PLUGIN_ROOT}/hooks/run.sh" init-gates
```

   It reads the `## Commands` table in CLAUDE.md, takes every row whose `Check?` cell is `yes`, infers a kind from the purpose (`e2e`, `integration`, `lint`, `types`, `build`, otherwise `unit`), puts e2e gates on `push` and all others on `commit`, writes `.sdlc/gates.json`, and appends `.sdlc/state/` to `.gitignore` when missing. It never overwrites an existing `.sdlc/gates.json`.

2. Report the output lines unchanged, then one line: `Edit .sdlc/gates.json to add "stop" to a gate's "on" list, "protected" globs (for example applied migrations) or "format" commands. Commit .sdlc/gates.json and .gitignore.`

Do not edit the generated file yourself unless the user asks. Do not commit.

## Config reference

```json
{
  "gates": [
    {"name": "backend-tests", "kind": "unit", "on": ["commit"], "cmd": "cd backend && pytest", "timeout": 900},
    {"name": "e2e", "kind": "e2e", "on": ["push"], "cmd": "cd frontend && npm run e2e"}
  ],
  "protected": ["backend/alembic/versions/*"],
  "format": [{"glob": "backend/**/*.py", "cmd": "cd backend && ruff format {file}"}],
  "secrets": {"allow": ["FIXTURE_[A-Z_]+ ="], "ignore_paths": ["tests/fixtures/**"]},
  "hooks": {"secrets": true, "commands": true, "gates": true, "stop": true, "context": true, "protected": true, "format": true}
}
```
