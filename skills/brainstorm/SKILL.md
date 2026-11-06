---
name: brainstorm
description: Run the brainstormer agent once to add new, in-scope product ideas to ideas/BACKLOG.md and report their titles. Use when the user runs /ai-sdlc-kit:brainstorm or asks for new ideas for the product.
---

# Brainstorm new ideas

Run the `brainstormer` agent once.

## Steps

1. Check that `docs/VISION.md` exists. If it does not, tell the user to fill in `docs/VISION.md` (setup creates it) and stop.
2. Run the `brainstormer` agent. Tell it nothing beyond "run once".
3. Report the idea titles it added and the titles it parked, one per line. Say that `ideas/BACKLOG.md` holds the details and that the owner promotes an idea with `/opsx:propose`.
4. Do not start any idea.

## Running periodically

```
/loop 12h /ai-sdlc-kit:brainstorm
```
