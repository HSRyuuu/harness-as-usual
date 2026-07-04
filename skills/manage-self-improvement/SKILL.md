---
name: manage-self-improvement
description: Use when AsUsual finalize triggers the self-improvement pass to analyze a completed topic and, after user approval, update long-term memory and add/patch project-local skills.
---

# Manage Self-Improvement

Self-improvement analysis + apply pass. Triggered by `finalize` before the topic
record is closed. NOT a workflow phase — it adds no phase/next-action.

`finalize` owns the approval gate; this skill owns the actual writes (memory record,
skill create/patch). `finalize` itself must not implement topic work.

## Inputs (read in order)

`topic.md`, `audit.jsonl`, `question-c*.md`, `requirements.md`, `plan.md`,
`code-review-report.md`, `report.md` (if already written; finalize runs this pass
*before* writing `report.md`, so on the first finalize use the recorded execution/review
evidence and any draft summary instead), current diff summary, existing
`.as-usual/memory/*`, existing project-local skills (`.agents/skills/`, `.claude/skills/`).

Focus on the gap: initial intent (question/requirements) → plan → actual result (diff/review evidence).

## Two-pass procedure

Subagents are headless, so approval happens in the controller (finalize) between passes.
Prefer dispatching each pass as a subagent; inline fallback when subagents are unavailable.

### Pass 1 — propose (read-only)

1. Collect candidates: `memory.candidate` audit events + candidates discovered from the
   intent→result gap.
2. Re-validate each candidate per `references/memory-update.md` ("still true & reusable?").
   Drop invalidated/duplicate/low-value candidates with a reason.
3. Dedup memory candidates against existing `.as-usual/memory/*`.
4. Evaluate skill candidates per `references/skill-improvement.md` (3-of-5 + overlap
   analysis → patch / new / skip; flag ambiguous ones for the user).
5. Return the proposal (memory additions + skill create/patch + ambiguous items). No writes.

### Approval (controller = finalize)

finalize presents the proposal item-by-item, asks the user, and asks directly about
any ambiguous-flagged item.

### Pass 2 — apply (this skill)

For approved items only:
1. Update memory per `references/memory-update.md` (simplify/consolidate/dedup, budget
   3000). If `.as-usual/memory/MEMORY.md` does not exist yet, create
   `.as-usual/memory/` and initialize `MEMORY.md` from the AsUsual plugin template
   at `<plugin-root>/templates/MEMORY.md` first. If the template file is
   unavailable, recreate the same section shape from the installed skill/template
   instructions before adding entries. Record with `record-memory --summary ... --files ...`.
2. Create new skill or patch existing skill in the project-local skills dir per
   `references/skill-improvement.md` (writing-skills conventions). Record `record-skill --state created`.
3. Record user-deferred skill candidates with `record-skill --state candidate`.
4. Self-validate outputs: skill front matter/description/steps present; MEMORY.md within
   budget, store-form==inject-form, no dedup violations. Record results in audit.

If no candidates survive, record a "no candidates" note and return.

## See also

- `references/memory-update.md`
- `references/skill-improvement.md`
