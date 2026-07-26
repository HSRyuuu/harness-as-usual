---
name: write-plan
description: Use when a topic or direct-work unit needs plan.md. Writes the execution contract, critically reviews it, fixes what the review finds, then asks for execution approval.
---

# Write Plan

Produces the execution contract and — this is the part that cannot be skipped —
**reviews it critically and fixes what the review finds before the user is asked
to approve anything.**

The user approves a plan that has already been checked. That is the point of
core rule 7.

## Strength

Both `topic` and `direct-work` use this skill and the procedure is the same. The
caller sets the strength, and its own matrix row states it — read that row rather
than inferring the weight from the request. Writing a topic-weight document for a
`direct-work` checklist, or a checklist for a topic, means the row was not read.

## Inputs

- `requirements.md` (topic) or `contexts.md` (direct-work) — current content from
  disk, not memory.
- Derived state: `as-usual-record.py status --dir <work-dir> --json`.
- The actual code the plan will touch. A plan written without looking at the
  files it names is a guess.

If something is open that the plan cannot be written without, call
`gathering-context` with that single item rather than assuming.

## Writing

Follow `templates/plan.md` — it carries the sections and what each one holds.
The calling unit's matrix says how much of it to write; a `direct-work`
checklist leaves out what it does not need. Replace the frontmatter placeholders
with the real `unit`, `slug`, and `created` (`core-rules.md` §3).

Per task, **verification must be runnable** — a command with an expected result,
not "confirm it works". For a behavior change, the verification has to exercise
the changed behavior.

Under **Safety**, name any high-risk operation the task involves (see
`safety-rules.md`) along with its rollback. Recording it here does not grant
permission: it still needs fresh approval immediately before it runs.

Decide yourself how the work gets executed — inline or delegated to subagents,
how tests are structured. Do not ask the user to choose.

`plan.md` is a contract, not a ledger. Progress goes in `audit.jsonl`.

## The Review (required)

After writing, before asking for anything:

1. **Read the plan critically**, as if reviewing someone else's work. Does each
   task actually do what it claims? Are the file paths real? Do the tasks compose
   — does task 3 depend on something task 2 never produces? Is every acceptance
   criterion covered? Is any verification unrunnable? Does anything contradict
   the requirements?
   `plan-quality-reference.md` in this directory lists what to look for. Use it
   as a reference; there is no checklist to fill in.
2. **Fix what you find.** The point is a better plan, not a list of findings.
3. **Record it.**

```bash
python3 <plugin-root>/scripts/as-usual-record.py add --dir <work-dir> \
  --kind review --summary "<what was found and what changed>" \
  --phase write-plan --data findings=<n>
```

The record helper refuses execution approval when no review entry exists, so
skipping this blocks the work rather than speeding it up.

Do not add a review status section to `plan.md`. The event is the record.

## Asking For Approval

Then, in one compact block:

- what the plan will do, in a line or two,
- anything risky in it, with the rollback,
- **how it will be executed** — inline or delegated per task. State it in the
  user's language; do not offer a menu,
- what you need: approval to execute.

Stop and wait. If the user wants a different execution approach, they will say
so; follow it.

## Revising Before Approval

- Non-material (clearer wording, a corrected path, reordering that changes
  nothing): update `plan.md`, re-check the affected part, record the revision,
  stop again.
- Material (scope, risk, strategy, acceptance, or verification policy): take it
  through `gathering-context`, update `requirements.md` if it moved, then rewrite
  the affected plan section and review again.

## Anti-Patterns

- Asking for execution approval before the review is recorded.
- Treating the review as a formality — reading the plan and finding nothing every
  time.
- Verification that cannot be run, or that only proves the code compiles.
- Tracking task status inside `plan.md`.
- Deciding test, commit, release, or deploy policy the work never agreed.
