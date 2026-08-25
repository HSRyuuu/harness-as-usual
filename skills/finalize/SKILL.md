---
name: finalize
description: Use when a work unit is closing. Checks the record can carry a fresh session, optionally proposes a reusable project-local skill improvement, writes report.md, seals the record, and asks which git action to run.
---

# Finalize

Closes a work unit: checks that the record can stand on its own, writes the
summary, and seals the record.

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

## 1. Optional Skill-Improvement Pass

When the work exposed a reusable, non-trivial procedure that could improve a
project-local skill, hand it to `manage-self-improvement` before sealing (prefer
a subagent).

Facts, decisions, preferences, and one-off lessons remain in this work unit's
artifacts. A candidate belongs here only when it is a repeatable procedure
suitable for a project-local skill.

The pass proposes; the user approves item by item; only then is a skill created
or patched. Skip the pass when there is no credible skill candidate.

A cancelled unit may still yield a reusable procedure, but cancellation alone
does not require this pass.

## 2. Record Check

Confirm the record could carry a fresh session that has none of this context:

- what was done,
- verification: `verification.md` where the unit keeps one, otherwise the exact
  commands and their outcomes, or what was skipped and why. Any `INCONCLUSIVE` or
  `FAIL` still open has to be re-verified with `--resolves` or accepted by the
  user with `--actor user --reason` on the close — the helper refuses otherwise
  (`core-rules.md` §6). A `topic` also needs `verification.md` on disk before it
  can close at all,
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

Write `report.md` from `templates/report.md`, with the frontmatter placeholders
replaced by real values (`core-rules.md` §3), unless the folder already holds the
unit's own closing document — a `conclusion.md` is that document, and a second
summary beside it only splits the story. Skip it for a cancelled close too. It
is the readable summary for a person, not a replacement for the record: what was
built, the decisions that matter, the verification outcome, the review outcome,
and what remains.

Where `review.md` or `verification.md` exists, the report links it and states the
outcome in a line. Restating its findings or its per-criterion results creates a
second copy that drifts from the first — and `verification.md` is written to keep
changing after this report is frozen, so the copy would be the stale one.

Then seal:

```bash
python3 <plugin-root>/scripts/as-usual-record.py add --dir <work-dir> \
  --kind lifecycle --event finalized \
  --summary "<outcome in one line>" --phase finalize --next-action none
```

Use `--event cancelled` with the reason for an abandoned unit. Closing over a
verification the user accepted as still open adds `--actor user --reason "<why>"`.
An `inbox` folder has no completion to declare: `move` it into a unit first, or
cancel it.

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
- Moving facts or one-off lessons out of the work unit during close-out.
- Applying a project-local skill change without approval.
- Running git commands, creating a PR, releasing, or deploying from here.
