# Changelog

All notable changes to this kit. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow semantic versioning.

## [0.1.0] - 2026-11-06

### Added
- `templates/CLAUDE.md`: one-page project instructions template with a `Purpose | Command | Check?` commands table, workflow, definition of done and known mistakes.
- `templates/REVIEW.md`: review policy template with four passes, three severity levels, a five-minor cap, exclusions and human-only approval.
- `ai-sdlc-kit:verifier`: read-only verifier subagent that runs declared checks, compares an OpenSpec change's tasks and scenarios with evidence, and returns a pass/fail report.
- `/ai-sdlc-kit:setup`: setup skill that copies the templates into the current repository without overwriting.
- Plugin and marketplace manifests (`petrus-sdlc` marketplace).
