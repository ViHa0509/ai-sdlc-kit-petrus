# Design

## Context

The repository contains only OpenSpec setup. See proposal.md (Why) for motivation and the four specs for required behavior. The first consumer is LearningHub (FastAPI + React, Windows dev machine), which installs the kit in its task 1.5. Kit v0 must be usable the same day it lands and must leave room for hooks, evals and CI in later versions without moving files.

## Goals / Non-Goals

**Goals:**
- One plugin, installed from GitHub, that gives a product repo its CLAUDE.md, REVIEW.md and a verifier.
- Plain Markdown only: no scripts, no runtime, nothing that behaves differently on Windows.
- A layout where later pieces (hooks, eval harness, CI templates, more agents) are additions, not moves.

**Non-Goals:**
- Hooks, eval harness, CI workflow templates, monitoring, lessons automation (later versions).
- Supporting agents other than Claude Code.
- Automatic upgrades of files already copied into a product repo.

## Decisions

### Repository layout = plugin layout

```
ai-sdlc-kit/
  .claude-plugin/
    plugin.json          name "ai-sdlc-kit", version, description
    marketplace.json     one entry pointing at this repo root
  agents/verifier.md     the verifier subagent
  commands/setup.md      the setup command
  templates/CLAUDE.md
  templates/REVIEW.md
  README.md  CHANGELOG.md
  openspec/              this kit's own specs and changes
```

The repo root is the plugin root, so the marketplace entry points to `./`. Alternative: a `plugins/ai-sdlc-kit/` subfolder to host several plugins - unnecessary for one plugin; it can be introduced at 1.0 if the kit splits.

Later versions add `hooks/`, `evals/` and `templates/ci/` next to these folders.

### Templates are copied, not referenced

The setup command copies `templates/*.md` into the product repo, because CLAUDE.md and REVIEW.md must be committed in the product repo (the playbook's rule: the artifact chain lives beside the code) and then grow with product-specific content. The command never overwrites, so re-running it is safe. Cost: template improvements do not reach existing product files automatically; CHANGELOG entries call out template changes so the owner can merge them by hand.

Alternative: reference the templates from the plugin at runtime via imports - rejected, because product-specific content (commands, known mistakes) would then live outside the product repo.

### Setup is a slash command, not a script

`commands/setup.md` instructs Claude to read the templates from the plugin folder (`${CLAUDE_PLUGIN_ROOT}/templates/`), check which target files exist, write only missing ones, then report created and skipped. A Markdown command needs no interpreter and works the same on Windows and Unix. Alternative: a Python or shell script - adds a runtime dependency and Windows quoting issues for two file copies.

### Verifier: read-only tools, checks from CLAUDE.md

`agents/verifier.md` frontmatter declares a description that tells Claude to delegate to it after implementation work and before a PR, and an allowed tool list of read and run tools only (Read, Grep, Glob, Bash). It has no Edit, Write or NotebookEdit. Its prompt:

1. Read the product `CLAUDE.md`; collect check commands from the Commands section (lines marked as checks).
2. Run each, record exit code and the last 30 lines of output.
3. If a change name is given, read `openspec/changes/<name>/tasks.md` and `specs/**`; for each checked task look for evidence; list scenarios with no test that names them.
4. Emit the report in the fixed order from the verifier-agent spec.

Bash is allowed because checks must run; the prompt forbids commands that modify the working tree (no git commit, no file writes, no package installs). A guard hook that enforces this is a candidate for kit v0.2.

Alternative: let the main agent verify itself - rejected; the playbook's point is a fresh context that did not write the code.

### Marking checks in CLAUDE.md

The template's Commands section uses a simple convention the verifier can parse: a Markdown table with columns `Purpose | Command | Check?`. Rows with `yes` in `Check?` are run by the verifier. This keeps run/dev commands (not checks) in the same table without the verifier executing them.

### Versioning

`plugin.json` holds the version; Kit v0 is `0.1.0`. A git tag `v0.1.0` marks the release. CHANGELOG.md uses Keep a Changelog headings.

## Risks / Trade-offs

- [Claude Code plugin manifest format changes or differs from this design] -> Task 1.1 checks the current plugin documentation before writing manifests and adjusts file names to match; specs describe behavior, not file names.
- [Verifier runs Bash and could change files] -> Read-only tool list plus explicit prompt rules; a PreToolUse guard hook is planned for v0.2.
- [Copied templates drift from the kit] -> Accepted; CHANGELOG flags template changes for manual merge.
- [Check commands differ between Windows shells] -> CLAUDE.md commands are written for the shell the product documents; LearningHub documents its own.

## Migration Plan

New repository; nothing to migrate. Rollback is uninstalling the plugin; files already copied into a product repo stay and can be deleted by hand.
