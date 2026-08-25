---
name: verify-project-identity
description: Verifies that the durable AsUsual project documents still describe the system that actually exists. Use after broad runtime, skill, template, hook, or verification-coverage changes.
---

# Verify Project Identity

## Purpose

`PROJECT_IDENTITY.md`, `AGENTS.md`, `CLAUDE.md`, `README.md`, and
`docs/ARCHITECTURE-WORKFLOW.md` are what a future agent reads to understand this
project before touching it. When they describe a system that no longer exists,
every session afterwards starts from a wrong model.

This check is about **agreement**, not completeness: the durable documents and the
runtime surface must describe one system.

## When To Run

- After changing the runtime contract: `as-usual-rules/**`, `skills/**`,
  `templates/**`, `scripts/**`, `hooks/session-start`
- After adding, removing, or renaming a work unit, artifact, phase, or skill
- After creating, deleting, or renaming a verification skill under `.agents/skills/**`
- Before finishing a broad refactor that a future maintainer would need explained

## Durable Documents

| File | Role |
| --- | --- |
| `PROJECT_IDENTITY.md` | why AsUsual exists, the failure modes it prevents, the principles that outlive any refactor |
| `AGENTS.md` | project knowledge base for maintainer agents — structure, code map, conventions, anti-patterns |
| `CLAUDE.md` | `@AGENTS.md` reference plus Claude Code host specifics only |
| `README.md` | public overview |
| `docs/ARCHITECTURE-WORKFLOW.md` | detailed architecture and workflow map |

`AGENTS.md` is the single knowledge base; `CLAUDE.md` references it with
`@AGENTS.md` and adds only Claude-host surfaces (manifests, hook config,
`.claude/skills/` mirror, install and reload). Host-agnostic content duplicated
into `CLAUDE.md` is a finding.

## Checks

### 1. The current model is described correctly

Every durable document that describes the workflow must agree on:

- **three peer work units** — `topic`, `direct-work`, `issue` — under
  `.as-usual/<unit>/yyyy-MM-dd-<slug>/`, plus `inbox/` for unclassified work,
- **two required files per unit**: `contexts.md` and `audit.jsonl`,
- **one entry point**, `using-as-usual`, which classifies once and hands off to a
  unit owner,
- **the seven core rules** as the only mandatory gates, with everything else left
  to the agent's judgment,
- **one record helper**, `scripts/as-usual-record.py`, over `as-usual.record.v1`,
- **transitions**: `move` while the unit has produced no output, a new folder plus
  a two-way link afterwards.

### 2. Removed concepts are gone

No durable document should still present these as current: `topic.md`,
`question-cN.md`, `problem.md`, `journal.jsonl`, `code-review-report.md`,
`topic-log.py`, `journal-log.py`, `start-work`, `hand-off`, `find-cause`,
`direct-execute`, `core-workflow.md`, `find-cause-workflow.md`,
`routed-to-find-cause`, mandatory execution review, execution-mode selection, the
question-file cycle.

```bash
rg -n 'topic\.md|question-c|problem\.md|journal\.jsonl|code-review-report|topic-log|journal-log|start-work|hand-off|find-cause|direct-execute|core-workflow|routing-rules|logging-rules|completion-rules' \
  PROJECT_IDENTITY.md AGENTS.md CLAUDE.md README.md docs/ARCHITECTURE-WORKFLOW.md
```

Hits are only acceptable where the document explicitly describes history or a
migration. Read the surrounding sentence before reporting.

### 3. Identity survived the refactor

`PROJECT_IDENTITY.md` states what AsUsual is for. A refactor changes structure,
not purpose — check that the principles still hold and still match the
implementation:

- decisions live in files so the agent does not guess the user's work style,
- the record layer is non-negotiable regardless of model strength; the judgment
  layer is not,
- completion needs evidence, not assertion,
- high-risk actions need fresh approval,
- the harness never runs a git action the user did not choose.

If a refactor genuinely changed the intent, the identity document is what should
be updated — not quietly contradicted by the code.

### 4. Code map matches the tree

```bash
ls skills/ as-usual-rules/ templates/ scripts/
rg -n '^\|' AGENTS.md | rg 'skills/|as-usual-rules/|templates/|scripts/'
```

Every file in the map exists; every public skill, rules file, and template appears
in the map. A stale row sends the next agent to a deleted file.

### 5. Verification coverage is registered

Changed surfaces need a verification skill that covers them, and the registries in
`.agents/skills/verify-implementation/SKILL.md` and
`.agents/skills/manage-skills/SKILL.md` must list the same skills with the same
scopes. Mirrors under `.claude/skills/` must match `.agents/skills/`.

### 6. Maintainer and runtime boundaries stay separate

Durable maintainer documents may discuss plugin development freely. What they must
not do is describe the runtime workflow differently from
`as-usual-rules/core-rules.md` — when they disagree, the rules file is the
authority and the document is the defect.

## Report

```markdown
## Project Identity

- Result: pass | issues-found
- Checked: PROJECT_IDENTITY.md, CLAUDE.md, AGENTS.md, README.md, docs/ARCHITECTURE-WORKFLOW.md

### Issues

- <file:line> — <what it claims> vs <what the runtime surface actually does>
```
