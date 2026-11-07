# AI SDLC Kit

A small Claude Code plugin that puts an AI-native development loop into any repository, following Anthropic's [AI-native SDLC playbook](https://claude.com/resources/articles/the-ai-native-sdlc-playbook) on top of [OpenSpec](https://github.com/Fission-AI/OpenSpec).

What you get in v0.4.0:

| Piece | What it does |
|---|---|
| `templates/CLAUDE.md` | One-page project instructions: commands (with a `Check?` column), layout, conventions, workflow, definition of done, known mistakes |
| `templates/REVIEW.md` | Review policy for every PR: four passes, three severities, a nit cap, human-only approval |
| `templates/VISION.md` | The scope the owner confirms: goals, in scope, out of scope, decisions, open questions |
| `/ai-sdlc-kit:setup` | Copies the templates into the current repo (`docs/VISION.md` for the vision), never overwriting existing files |
| `ai-sdlc-kit:verifier` | Read-only subagent with a fresh context: runs the `Check? = yes` commands from CLAUDE.md, checks an OpenSpec change's tasks and spec scenarios, and returns a pasteable pass/fail report |
| Agent team | `implementer`, `scout`, `qc-ui`, `qc-e2e`, `brainstormer`, plus `/ai-sdlc-kit:orchestrate` and `/ai-sdlc-kit:brainstorm` (see below) |
| Hooks | Secret and command guards, quality gates on commit/push/stop, protected paths, a compact session summary; `/ai-sdlc-kit:gates` writes the config (see [Hooks](#hooks)) |

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
3. Run `/ai-sdlc-kit:gates` once the Commands table has checks; it writes `.sdlc/gates.json` (see [Hooks](#hooks)).
4. Commit `CLAUDE.md`, `REVIEW.md`, `docs/VISION.md`, `.sdlc/gates.json` and `.gitignore`.
5. After implementing work, ask Claude to "run the verifier on change `<change-name>`" and paste the report into the PR.

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

Limits: at most 3 subagents at once, one retry per failed task, commits only when every check passes, never pushes. Each cycle appends to `.sdlc/log.md`. With `.sdlc/gates.json`, the commit gates run automatically before each commit.

## Hooks

The plugin ships Claude Code hooks (`hooks/hooks.json`). They run outside the model, so they cost no tokens when they pass, and they print nothing on success. They need `sh` and Python 3.8+ (standard library only); without Python they allow everything.

| Hook | Event | What it does | Needs config? |
|---|---|---|---|
| Secret guard | PreToolUse on Write, Edit, MultiEdit, NotebookEdit | Denies new content holding a likely secret: Anthropic, OpenAI, AWS, GitHub, Google or Slack keys, PEM private keys, long random values assigned to `*key*`, `*secret*`, `*token*`, `*password*` names. The reason names only the type and line. Placeholders (`sk-...`, `<your-key>`, `xxxx`, `changeme`, empty values) pass. | No |
| Protected paths | same | Denies changes to committed files matching `protected` globs; new and not-yet-committed files are allowed (for example a new migration next to applied ones). | `protected` |
| Command guard | PreToolUse on Bash | Denies force-push to main/master, `git commit --no-verify` (also `-n`, `core.hooksPath`), `git add` of `.env` or key files (also through `git add -A`), and printing secret files (`cat .env`, `Get-Content .env`, `head storage/secret.key`, ...). Quoted text and heredocs, such as commit messages, never trigger it. | No |
| Staged secrets | PreToolUse on Bash, `git commit` | Scans the added lines of the staged diff (plus unstaged and untracked files when the same command stages files) and denies with file, line and type. | No |
| Commit and push gates | PreToolUse on Bash, `git commit` / `git push` | Runs the gates for that stage. A failure denies the call with the failing names, exit codes and the last 20 lines of each failing output; success adds one `gates passed: ...` line. | `gates` |
| Stop gate | Stop | When files changed in the session, runs the `stop` gates before the agent may finish; blocks at most twice in a row (`stop_hook_active` guard). | a gate with `"on": ["stop"]` |
| Session summary | SessionStart (startup, resume, clear, compact) | At most 15 lines: active OpenSpec changes with task counts, the last `.sdlc/log.md` entry, the last gate results. Prints nothing when there is nothing. No kit hook runs on every prompt. | No |
| Formatter | PostToolUse on Write, Edit, MultiEdit | Runs the matching `format` command on the edited file, silently. | `format` |

**Passed suites are not rerun.** Every gate pass is recorded in `.sdlc/state/` against a content hash of the working tree (git-ignored files and `.sdlc/` left out). A gate that passed in the same session on the same code is reported as `(cached)` and not rerun. An `e2e` gate also reuses passes from other sessions: `qc-e2e` stamps a passing suite with `run.sh stamp e2e`, and the push gate skips the suite while the code is unchanged, also after the code is committed. Failures are never cached.

### Config: `.sdlc/gates.json`

Run `/ai-sdlc-kit:gates` to create it from the CLAUDE.md rows marked as checks (e2e on push, the rest on commit). Example:

```json
{
  "gates": [
    {"name": "backend-tests", "kind": "unit", "on": ["commit"], "cmd": "cd backend && pytest"},
    {"name": "lint", "kind": "lint", "on": ["commit"], "cmd": "ruff check ."},
    {"name": "e2e", "kind": "e2e", "on": ["push"], "cmd": "cd frontend && npm run e2e", "timeout": 1500}
  ],
  "protected": ["backend/alembic/versions/*"],
  "format": [{"glob": "backend/**/*.py", "cmd": "cd backend && ruff format {file}"}],
  "secrets": {"allow": ["FIXTURE_[A-Z_]+ ="], "ignore_paths": ["tests/fixtures/**"]},
  "hooks": {"secrets": true, "commands": true, "gates": true, "stop": true, "context": true, "protected": true, "format": true}
}
```

- `kind`: `unit`, `integration`, `e2e`, `lint`, `types`, `build`. `on`: `commit`, `push`, `stop`. Commands run from the repo root in `sh`; `timeout` defaults to 900 seconds (the hook itself allows 1800).
- Globs: `*` stays inside one folder, `**` crosses folders.
- `secrets.allow`: regular expressions matched against the flagged line. A line containing `sdlc:allow-secret` also passes; that marker is for humans, and agents are told to ask instead.
- `hooks`: set an entry to `false` to turn that hook off in the repo.
- Git-ignore `.sdlc/state/` (the gates skill adds the line; the folder also writes its own `.gitignore`).
- A formatter that rewrites a file can make the agent's next edit fail with "file modified since read"; `format` is opt-in for that reason.

Manual commands, from the repo root (`<plugin>` is in `.sdlc/state/plugin_root` after a session start): `sh <plugin>/hooks/run.sh check commit` runs the commit gates and prints only failures; `sh <plugin>/hooks/run.sh stamp e2e` records an e2e pass for the current code.

### Turning hooks off

- All kit hooks, for one shell or session: `SDLC_HOOKS=off claude`. This is for humans; the CLAUDE.md template tells agents never to use it.
- One hook in one repo: for example `"hooks": {"stop": false}` in `.sdlc/gates.json`.
- The whole plugin: `claude plugin disable ai-sdlc-kit@petrus-sdlc`.

Hooks load when a session starts: restart Claude Code after installing or updating the plugin.

## Update

```bash
claude plugin marketplace update petrus-sdlc
claude plugin update ai-sdlc-kit@petrus-sdlc
```

Updating never touches files already copied into a repo. When CHANGELOG.md says a template changed, compare your repo's file with the new template and merge by hand.

## Not yet included

Planned for later versions, driven by what goes wrong in real use:

- More hooks (for example a guard that keeps the verifier read-only, and one that blocks weakening tests during a fix).
- An eval harness and CI workflow templates.
- Monitoring and lessons-file automation.

## Development

The kit is planned and built with OpenSpec: see `openspec/changes/`. Validate before releasing:

```bash
claude plugin validate .
python -m unittest            # hook tests (stdlib only)
openspec validate --all --strict
```

## Dev and QC loop

The developers (`implementer`) build a change and keep its unit and API tests. `qc-e2e` then writes black-box e2e tests from the change's spec scenarios and runs the whole suite. Each product bug goes back to the implementer that owns the area, and `qc-e2e` runs again. The loop ends when the suite passes, or with `needs human` after 3 rounds that fail on the same scenario.

```
/loop run qc-e2e after the dev agents finish; send failures back to the dev agents; repeat until the tests pass
```
