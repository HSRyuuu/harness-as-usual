---
name: manage-self-improvement
description: Use when finalize triggers the self-improvement pass, or when the user asks to reflect what was learned into long-term memory. Proposes memory and skill updates, then applies the approved ones.
---

# Manage Self-Improvement

Turns what a work unit taught into something the next one can use.

Triggered by `finalize` for any unit, or directly whenever the user asks to
reflect what was learned. Not a workflow phase — it adds no phase or next action.

The caller owns the approval gate; this skill owns the writes.

## Inputs

Same shape for all three units. Read in this order:

1. `contexts.md` — what was agreed, and what changed along the way.
2. The record: `as-usual-record.py status --dir <work-dir> --json`, plus the
   `memory` events already accumulated during the work.
3. The unit's own output — `requirements.md` / `plan.md` / `review.md` for
   development work, `conclusion.md` for an issue.
4. The current diff summary, when the work changed code.
5. Existing `.as-usual/memory/*` and existing project-local skills
   (`.agents/skills/`, `.claude/skills/`).

Look at **the gap**: what was intended, what was planned, what actually happened.
That gap is where the reusable lesson lives. For an issue, the highest-value
material is the confirmed cause pattern, domain knowledge the user supplied, and
diagnostic steps worth repeating.

## Two Passes

Candidates were already recorded as `memory` events while the work happened
(core rule: record as you go, do not break the flow to write memory). So pass 1
is a review of those plus whatever the gap analysis surfaces — not a hunt from
scratch.

Prefer running each pass as a subagent; inline is fine when subagents are not
available.

### Pass 1 — propose (read-only)

1. Collect the recorded `memory` candidates and anything the intent→result gap
   surfaced.
2. Re-validate each against `references/memory-update.md`: is it still true, and
   is it reusable beyond this one work unit? Drop what is not, with a reason.
3. Deduplicate against existing `.as-usual/memory/*`.
4. Evaluate skill candidates against `references/skill-improvement.md` — patch an
   existing skill, create a new one, or skip. Flag the ambiguous ones.
5. Return the proposal. Write nothing.

### Approval — the caller

The caller presents the proposal item by item and asks about anything flagged
ambiguous. Nothing is written without the user saying so.

### Pass 2 — apply

For approved items only:

1. Update memory per `references/memory-update.md` — simplify, consolidate,
   deduplicate, and stay inside the 3000-character budget for `MEMORY.md`.
   If `.as-usual/memory/MEMORY.md` does not exist, create the directory and
   initialize it from `<plugin-root>/templates/MEMORY.md`.
2. Create or patch project-local skills per `references/skill-improvement.md`.
3. Record what was written:

```bash
python3 <plugin-root>/scripts/as-usual-record.py add --dir <work-dir> \
  --kind memory --summary "<what was reflected, and where>" \
  --data files=.as-usual/memory/MEMORY.md
```

4. Self-check: skill frontmatter and description present, `MEMORY.md` within
   budget, no duplicated entries.

If nothing survives, record a "no candidates" note. That is a real outcome, not a
failure.

## Timing

Run before the record is sealed — a finalized record accepts no further events.
If the unit is already sealed and the user asks to reflect something later, write
the memory anyway and tell them it is recorded in `.as-usual/memory/` without a
unit event, since that unit's record is closed.

## Anti-Patterns

- Writing memory without the user's approval.
- Interrupting the work to write memory instead of recording a candidate.
- Reflecting something that only applies to this one work unit.
- Duplicating what `.as-usual/memory/` already says.
- Blowing the `MEMORY.md` budget instead of consolidating.
- Trying to append to a sealed record.

## See Also

- `references/memory-update.md`
- `references/skill-improvement.md`
