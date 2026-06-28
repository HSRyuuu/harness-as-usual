# Skill Improvement Rules

## Candidate criteria (3-of-5)

A reusable, non-trivial procedure is a skill candidate if 3+ hold:
1. reusable for the same kind of task again
2. has 3+ steps
3. tool ordering matters
4. failure path differs from success path
5. has a verification method

## memory vs skill

Short facts / judgment criteria → memory. Multi-step reusable procedures → skill.

## Overlap analysis (Pass 1)

Compare each candidate to existing registered skills:
- overlaps an existing skill's purpose → patch that skill (add exception/verification)
- fully different trigger + workflow → new skill
- already well covered → skip
- ambiguous → flag for the user (controller asks during approval)

## Direct creation (Pass 2, after approval)

This skill creates/patches the skill file directly. Follow writing-skills conventions
(name, trigger-rich description, procedure, verification). Record with
`record-skill --state created`. User-deferred candidates: `record-skill --state candidate`.

## Destination (project-local)

Detect: `<PROJECT_ROOT>/.agents/skills/` and `<PROJECT_ROOT>/.claude/skills/`.
- one exists → use it
- both exist → host-aware (Claude → `.claude/skills`, Codex → `.agents/skills`)
- neither → create the host-default dir

## Optional tools (mention only)

`/skill-creator` (Claude) / `$skill-creator` (Codex) are optional helpers the user may
use; direct creation is the default. Not enforced routing.

## skill.candidate brief fields

`summary`, `rationale` (which of 3-of-5), `kind` (new|patch), `patchTarget`,
`briefOutline` (trigger / steps / verification), `dest`.
