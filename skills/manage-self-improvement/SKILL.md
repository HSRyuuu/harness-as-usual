---
name: manage-self-improvement
description: Use when finalize finds a reusable procedure worth turning into a project-local skill, or when the user asks to improve a project-local skill from what was learned. Proposes skill changes, then applies the approved ones.
---

# Manage Self-Improvement

Turns a reusable procedure learned from a work unit into a project-local skill.

Triggered by `finalize` when a credible skill candidate exists, or directly when
the user asks to improve a project-local skill from what was learned. Not a
workflow phase — it adds no phase or next action.

The caller owns the approval gate; this skill owns the writes.

## Inputs

Same shape for all three units. Read in this order:

1. `contexts.md` — what was agreed, and what changed along the way.
2. The record: `as-usual-record.py status --dir <work-dir> --json`.
3. The unit's own output — `requirements.md` / `plan.md` / `review.md` for
   development work, `conclusion.md` for an issue.
4. The current diff summary, when the work changed code.
5. Existing project-local skills (`.agents/skills/`, `.claude/skills/`).

Look at **the gap**: what was intended, what was planned, what actually happened.
That gap is where the reusable lesson lives. For an issue, the highest-value
material is a diagnostic sequence worth repeating.

## Two Passes

Prefer running each pass as a subagent; inline is fine when subagents are not
available.

### Pass 1 — propose (read-only)

Review the gap analysis and keep only reusable procedures that satisfy
`references/skill-improvement.md`. Compare them with existing project-local
skills, decide patch, create, or skip, and flag ambiguous cases. Facts, judgment
criteria, preferences, and one-off lessons stay in the unit artifacts. Return the
proposal; write nothing.

### Approval — the caller

The caller presents the proposal item by item and asks about anything flagged
ambiguous. Nothing is written without the user saying so.

### Pass 2 — apply

For approved items only:

1. Create or patch project-local skills per `references/skill-improvement.md`.
2. When an open work unit exists, record what was written before sealing:

```bash
python3 <plugin-root>/scripts/as-usual-record.py add --dir <work-dir> \
  --kind work --summary "<project-local skill created or patched>" \
  --phase finalize --data files=<changed-skill-paths>
```

3. Self-check: skill frontmatter and trigger-rich description are present, the
   procedure has a verification method, and host mirrors follow the target
   project's convention.

If nothing survives, make no change and report why each candidate was skipped.

## Timing

When finalize invokes this skill, run before the record is sealed so the skill
change can be recorded. If the unit is already sealed or no work unit exists,
apply an explicitly approved skill change without appending to that record and
report the changed paths in chat.

## Anti-Patterns

- Turning a short fact or preference into a procedural skill.
- Turning a rejected skill candidate into another cross-unit artifact.
- Applying a skill change without the user's approval.
- Trying to append to a sealed record.

## See Also

- `references/skill-improvement.md`
