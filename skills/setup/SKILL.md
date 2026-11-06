---
name: setup
description: Set up the AI SDLC kit in the current repository by copying the CLAUDE.md and REVIEW.md templates into the repository root and the VISION.md template into docs/ without overwriting existing files. Use when the user runs /ai-sdlc-kit:setup or asks to install the kit's templates into a repo.
---

# Set up the AI SDLC kit in this repository

Copy the kit's templates into the current repository: CLAUDE.md and REVIEW.md at the root, VISION.md in `docs/`. Never overwrite a file that already exists.

Templates (in this plugin):

- `${CLAUDE_PLUGIN_ROOT}/templates/CLAUDE.md`
- `${CLAUDE_PLUGIN_ROOT}/templates/REVIEW.md`
- `${CLAUDE_PLUGIN_ROOT}/templates/VISION.md` (goes to `docs/VISION.md`)

## Steps

1. Find the repository root: run `git rev-parse --show-toplevel`. If it fails, use the current working directory and say so.
2. For each template above, in this order (CLAUDE.md, REVIEW.md, VISION.md):
   - The target is the repository root for CLAUDE.md and REVIEW.md, and `docs/VISION.md` for VISION.md.
   - If a file already exists at the target, do not touch it. Record it as **skipped**.
   - Otherwise read the template and write its content unchanged to the target (create `docs/` if needed). Record it as **created**.
3. Do not create, change or delete any other file. Do not commit.
4. Report the result as a short list, exactly in this form:

```
AI SDLC kit setup
- CLAUDE.md: created | skipped (already exists)
- REVIEW.md: created | skipped (already exists)
- docs/VISION.md: created | skipped (already exists)
Next: fill in CLAUDE.md (Project, Commands with Check? column, UI, Layout, Conventions) and docs/VISION.md (Goals, In scope, Out of scope), then commit the files.
```

If you skipped a file, add one line suggesting the user compare it with the template at `${CLAUDE_PLUGIN_ROOT}/templates/` and merge by hand.
