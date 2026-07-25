---
name: execute-plan
description: Use when the user has approved execution of a reviewed plan. Executes the tasks in order and records progress, approvals, and verification evidence.
---

# Execute Plan

Executes an approved plan without drifting from it, and leaves behind evidence
that it actually worked.

The plan arrives already reviewed — `write-plan` did that before the user
approved it. Do not re-review it here. If something in the plan turns out to be
wrong once you are in the code, that is a route back, not a review pass.

## Preconditions

- `plan.md` exists and is current.
- The user explicitly approved execution, and that approval is recorded.
- The user's latest request still matches the plan.

If any of these is missing, name it and stop.

## Executing

Work the tasks in the plan's order. You remain the controller throughout: task
order, records, verification, and anything said to the user are yours, whether or
not subagents did the typing.

**Per task:**

1. Do the work as the plan describes it.
2. Run the task's verification. What counts as evidence is owned by
   `core-rules.md` §6 — it must match the surface, and tests alone never prove
   done.
3. Record it.

```bash
as-usual-record.py add --dir <d> --kind work --summary "Task N: <what changed>" --phase execute-plan
as-usual-record.py add --dir <d> --kind verification --verdict PASS \
  --summary "<command + actual result>" --phase execute-plan
```

If the surface cannot produce evidence, the verdict is `INCONCLUSIVE`, not
`PASS`, and the task is not done. Do not move to the next task on top of an
unverified one.

**High-risk operations** need fresh approval immediately before they run, even
though the plan describes them (`safety-rules.md`):

```bash
as-usual-record.py add --dir <d> --kind approval --action high-risk --actor user \
  --summary "<operation, target, rollback, what the user approved>"
```

When you hand a task to a subagent, the message must be self-contained — the
child cannot see this conversation. Give it TASK, DELIVERABLE, SCOPE, VERIFY,
and SAFETY: which high-risk operations the task involves and whether each is
already approved, since the child cannot read `safety-rules.md`.
`implementer-prompt.md` and `task-reviewer-prompt.md` in this directory hold
ready-made versions of that contract.

A subagent's `DONE` is a claim. Check it against the diff and the evidence before
recording anything. If you cannot verify it, it is `INCONCLUSIVE`.

## When The Plan Is Wrong

Plans meet reality. When a task cannot be done as written:

- **Small and obvious** — a path moved, a helper is named differently: adapt,
  record a `note` saying what differed, carry on.
- **Changes the approach, risk, or verification**: stop. Ask the user through
  `gathering-context`, record the decision, update `plan.md`, then resume.
- **Same failure three times**: stop repeating it. Record the pattern as a
  `blocker` and reassess whether the plan, an assumption, or the environment is
  wrong. Ask the user only if files cannot answer it.

Do not quietly widen the scope, and do not hide a failure behind optimistic
wording.

## Finishing

When every task is done and verified, record completion and hand back to the
owner skill:

```bash
as-usual-record.py add --dir <d> --kind work --summary "execution complete: <summary>" \
  --phase execute-plan --next-action awaiting-user
```

`awaiting-user`, because what happens next — a review, cleanup, or closing — is
the owner's proposal and the user's decision, not an automatic transition.

Say what was done and what the evidence was. Do not claim completion while any
task is unverified, any blocker is open, or any high-risk step ran unapproved.

Stop there. Do not continue into review, commit, PR, release, or deploy on your
own — the owner skill decides what comes next.

## Anti-Patterns

- Recording `PASS` for something you could not actually check.
- Accepting a subagent's `DONE` as fact.
- Tracking progress inside `plan.md`.
- Rolling into a git action after execution.
