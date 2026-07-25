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

Both `topic` and `direct-work` use this skill. The caller sets the strength; the
procedure is the same.

| Caller | Plan is |
| --- | --- |
| `run-topic` | a full `plan.md` — approach, task breakdown, verification strategy, acceptance coverage |
| `run-direct-work` | a checklist — the steps and how each will be verified. Two sections is a complete plan here |

Do not write a topic-weight document for direct-work. Do not write a checklist
for a topic.

## Inputs

- `requirements.md` (topic) or `contexts.md` (direct-work) — current content from
  disk, not memory.
- Derived state: `as-usual-record.py status --dir <work-dir> --json`.
- The actual code the plan will touch. A plan written without looking at the
  files it names is a guess.

If something is open that the plan cannot be written without, call
`gathering-context` with that single item rather than assuming.

## Writing

Follow `templates/plan.md`:

| Section | Holds |
| --- | --- |
| Goal & Constraints | what this plan achieves and what bounds it |
| Approach | the order of work and why — dependencies, what has to land first |
| Tasks | each with purpose, files, steps, verification, and safety |
| Verification Strategy | how the whole thing gets checked, not just per task |
| Acceptance Criteria Coverage | which task satisfies which criterion |

Per task, **verification must be runnable** — a command with an expected result,
not "confirm it works". For a behavior change, the verification has to exercise
the changed behavior.

Under **Safety**, name any high-risk operation the task involves (see
`safety-rules.md`) along with its rollback. Recording it here does not grant
permission: it still needs fresh approval immediately before it runs.

How the work gets executed — inline or delegated to subagents, how tests are
structured — is your call. Do not ask the user to choose.

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
- **how it will be executed** — state it, do not offer a menu:
  "인라인으로 실행합니다" / "태스크별 서브에이전트로 실행합니다",
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
- Writing the plan from memory or from stale requirements.
- Naming files without opening them.
- Verification that cannot be run, or that only proves the code compiles.
- Offering the user a choice of execution mode.
- Tracking task status inside `plan.md`.
- Deciding test, commit, release, or deploy policy the work never agreed.
