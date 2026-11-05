# Tasks

## 1. Plugin skeleton

- [x] 1.1 Check the current Claude Code plugin and marketplace documentation and record the confirmed manifest file names and fields in design.md if they differ, and verify the note is committed
- [x] 1.2 Add `.claude-plugin/plugin.json` (name `ai-sdlc-kit`, version `0.1.0`, description) and `.claude-plugin/marketplace.json` pointing at the repo root, and verify `/plugin marketplace add` on the local folder lists the plugin

## 2. Project instructions template (spec: project-instructions)

- [x] 2.1 Write `templates/CLAUDE.md` with the sections in spec order, a `Purpose | Command | Check?` Commands table, the four-item Definition of done and the Known mistakes rule, and verify it has at most 80 lines and every section from the spec is present

## 3. Review policy template (spec: review-policy)

- [x] 3.1 Write `templates/REVIEW.md` with the four passes and their checklists, the three severity levels, the finding format, the five-minor cap, the exclusions and the human-approval rule, and verify each review-policy scenario against the text

## 4. Verifier subagent (spec: verifier-agent)

- [x] 4.1 Write `agents/verifier.md` with a delegation description, a tool list of Read, Grep, Glob and Bash only, and the four-step prompt with the fixed report format, and verify the frontmatter has no Edit, Write or NotebookEdit
- [x] 4.2 Try the verifier on a scratch repo whose CLAUDE.md has one passing and one failing check, and verify the report starts with verdict fail, lists both commands with exit codes, and that no file in the scratch repo changed (`git status` clean)
- [x] 4.3 Try the verifier on a scratch repo with no check commands, and verify it reports "cannot verify: no checks declared"

## 5. Setup command and distribution (spec: kit-distribution)

- [x] 5.1 Write `skills/setup/SKILL.md` that copies missing templates from `${CLAUDE_PLUGIN_ROOT}/templates/` and reports created and skipped files, and verify on a scratch repo: first run creates both, second run skips both, a pre-existing CLAUDE.md is untouched
- [x] 5.2 Write `README.md` (what, install, setup, update, not yet included) and `CHANGELOG.md` with a `0.1.0` entry, and verify by following the README from scratch in a new empty repo

## 6. Release and first use

- [x] 6.1 Install the plugin from `https://github.com/ViHa0509/ai-sdlc-kit-petrus` in a fresh Claude Code session and verify the setup command and verifier are available
- [x] 6.2 Tag `v0.1.0` and push the tag, and verify `git ls-remote --tags origin` shows it

## Workflow follow-up

- Use Kit v0 in LearningHub task 1.5 of `slice-1-import-and-map`; record what the verifier missed or got wrong as candidate items for kit v0.2.
- Archive this change with `/opsx:archive` after release.
