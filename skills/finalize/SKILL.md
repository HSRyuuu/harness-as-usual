---
name: finalize
description: Use when a work unit is closing. Reviews memory candidates, checks the record can carry a fresh session, writes report.md, seals the record, and asks which git action to run.
---

# Finalize

Closes a work unit: reviews what is worth remembering, checks that the record can
stand on its own, writes the summary, and seals the record.

`topic` and `issue` require this. `direct-work` offers it — a direct-work unit
whose last event is a passing verification is already complete.

Finalize implements no new work, runs no git commands, and never rewrites past
events.

## Preconditions

- The unit's own outcome exists: execution and a recorded verification for
  `topic` and `direct-work`; `conclusion.md` plus something confirmed for
  `issue`. The record helper refuses to finalize without these.
- For `topic`, the review's Critical and Important findings have dispositions.
- Remaining issues and any skipped verification are explicit.

**Cancelled is different.** When the user abandons the work, none of the above
applies — any unit can close as cancelled from any phase. What is required is the
user's explicit decision and the reason. Check the working tree for leftover
changes and ask whether to revert or keep them before closing. Cancelling is not
a way past a gate: resuming the work later means a new unit or an explicit
resume, never quiet implementation after the close.

## 1. Memory Pass

Before sealing, hand to `manage-self-improvement` (prefer a subagent).

Candidates accumulate as `memory` events throughout the work, so this pass is a
review, not a hunt. It proposes; the user approves item by item; only then is
anything written to `docs/memory/`. If nothing survives, record that — "no
candidates" is a real result.

Run this for a cancelled close too. An abandoned unit often carries the most
useful lesson, such as why it was scoped wrong in the first place.

## 2. Record Check

Confirm the record could carry a fresh session that has none of this context:

- what was done,
- verification: the exact commands and their outcomes, or what was skipped and why,
- review findings and their dispositions,
- decisions and constraints that still bind,
- remaining issues, or explicitly none.

Also confirm the approvals that had to exist do: execution approval before
execution, a fresh high-risk approval per high-risk operation.

```bash
python3 <plugin-root>/scripts/as-usual-record.py validate --dir <work-dir>
```

If something is missing, route back to the phase that owns it. Fill gaps from
recorded artifacts — never invent a verification result.

## 3. Report And Close

Write `report.md` from `templates/report.md`, unless the folder already holds the
unit's own closing document — a `conclusion.md` is that document, and a second
summary beside it only splits the story. Skip it for a cancelled close too. It
is the readable summary for a person, not a replacement for the record: what was
built, the decisions that matter, the verification with its actual commands and
results, the review outcome, and what remains.

Then seal:

```bash
python3 <plugin-root>/scripts/as-usual-record.py add --dir <work-dir> \
  --kind lifecycle --event finalized \
  --summary "<outcome in one line>" --phase finalize --next-action none
```

Use `--event cancelled` with the reason for an abandoned unit.

State the outcome plainly. If the work ended blocked or with issues outstanding,
say that — a sealed record that overstates what happened is worse than no record.

After sealing, the record accepts nothing but links. Further work needs a new
unit.

## 4. Git Action

Ask which git action to run. Never choose for the user, and never run one
unasked (core rule 4).

Ask in the user's language, and offer exactly these four:

```text
- none
- commit
- commit + push
- commit + push + PR
```

When they choose, invoke `git-action`. For an `issue`, do not ask this by
default — confirming a cause and stopping is a normal ending, and there is
usually nothing to commit.

## Anti-Patterns

- Closing as cancelled without the user's explicit decision and a reason.
- Continuing the abandoned work after a cancelled close.
- Inventing verification results to fill the report.
- Writing memory directly instead of delegating, or reflecting without approval.
- Running git commands, creating a PR, releasing, or deploying from here.
