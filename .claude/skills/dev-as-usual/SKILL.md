---
name: dev-as-usual
description: Use when requests involve developing, modifying, verifying, or documenting the AsUsual harness itself, especially plugin development, core-workflow, hook, manifest, docs, templates, skills changes, or deciding whether a skill belongs in project-local .agents/skills or public plugin skills.
---

# Dev AsUsual

## Overview

When this skill is active, classify the current request as development of the AsUsual harness itself, not as a command to use the AsUsual runtime workflow.

## Classification

1. Treat AsUsual harness development requests as plugin development.
2. Do not automatically start the `.as-usual/topic/` artifact workflow for plugin development.
3. Changes to `as-usual-rules/core-workflow.md`, hooks, plugin manifests, docs, templates, and stable skills are plugin development work.
4. Apply the runtime topic workflow only when the user explicitly says to run this plugin development work as an AsUsual topic.

## Development Rules

- Keep runtime workflow rules in `as-usual-rules/core-workflow.md`.
- Do not copy the runtime workflow file into target projects.
- Do not mix plugin development guidance into `as-usual-rules/core-workflow.md`.
- Keep changes small and explicit.
- Verify the touched surface before finishing.

## Skill Placement

Before creating or moving a skill, classify its audience.

| Audience | Location | Rule |
| --- | --- | --- |
| AsUsual repository maintainer | `.agents/skills/<skill-name>/` | Keep it project-local. Do not expose it through plugin manifests or move it into public `skills/`. |
| Target-project user running AsUsual | `skills/<skill-name>/` | Treat it as stable plugin surface. It may be included in `.codex-plugin/plugin.json` and Claude plugin discovery. |

- Put skills for AsUsual development, reference search while designing AsUsual, local plugin administration, and anything explicitly under `.agents/skills/` in `.agents/skills/`.
- Put skills that a target-project agent should use after installing the AsUsual plugin in `skills/`.
- Keep reference-analysis skills development-only unless the user explicitly asks to add them to the public plugin surface.

## When Adding Rules

Add new rules to this file briefly. If a rule becomes long, split related files, verification commands, and exception conditions into separate sections while keeping this skill focused on harness development classification and development-time rules.
