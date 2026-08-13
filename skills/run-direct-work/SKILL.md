---
name: run-direct-work
description: Use when AsUsual work is classified as direct-work — the outcome is already settled, so no requirements need agreeing, but the work is still recorded. Owns the direct-work pipeline.
---

# Run Direct Work

Owns the `direct-work` pipeline: development where **what to do is already
settled**, so agreeing requirements would be ceremony, but the work is still
worth a record.

The pipeline is short and often asks the user nothing. What stays fixed is that
the work leaves evidence behind.

This skill is a declaration, not a procedure. Read `as-usual-rules/core-rules.md`
first.

**Precondition**: a work folder with `contexts.md` and `audit.jsonl` exists. If it
does not — the user named the unit and came straight here — `using-as-usual`
creates it first (core rule 1 and 6). Being told the unit settles the
classification, not the record.

## Pipeline

```text
gathering-context → write-plan → execute-plan → review-execution? → cleanup-code?
                  → finalize? → git-action?
```

| Phase | Step skill | Applies | Strength |
| --- | --- | --- | --- |
| `gathering-context` | `gathering-context` | required | **zero questions is normal** — if nothing is open, record that and move on |
| `write-plan` | `write-plan` | required | checklist strength: steps + verification method, not a full plan document |
| `execute-plan` | `execute-plan` | required | `verification.md` when the evidence needs more than the record's summaries; the events alone are enough for a small change |
| `review-execution` | `review-execution` | optional | offer when the change is broad or touched something delicate |
| `cleanup-code` | `cleanup-code` | optional | only on explicit approval |
| `finalize` | `finalize` | optional | offer at the end; the record is complete without it |
| `git-action` | `git-action` | on explicit choice only | — |

## What Belongs Here

The work is clear, low-risk, and reversible. Size is not the test — a mechanical
rename across thirty files is direct-work; a two-line change to how sessions
expire is not.

Route back to `using-as-usual` for reclassification when, during gathering, the
work turns out to:

- need a decision between viable approaches,
- touch a contract or product surface — public API, data model, auth, migration,
  deployment, dependency policy, user-facing wording, business rules,
- be hard to reverse or hard to verify,
- have an unconfirmed cause behind it (that is an `issue`).

If nothing has been produced yet, `move` handles the relabel; the record helper
allows it until `plan.md` exists.

## Gates

- **Plan review before execution approval** (core rule 7). Lighter than a
  topic's, but it happens: read the checklist critically once, fix what you find,
  record a `review` entry. The helper refuses the approval without one.
- **High-risk operations need fresh approval** — and if the work is built around
  one, it is not direct-work. See `safety-rules.md`.
- **Verification evidence before any completion claim** (core rule 3). For a
  behavior change, the verification must actually exercise the changed behavior,
  not just confirm the code compiles.

## Closing

Report the result and the verification evidence in chat. If verification could
not be run, say `not verified because …` with the concrete reason and record
`INCONCLUSIVE`.

Then offer `finalize`, and `git-action` only if the user asks for it. Neither is
required — a direct-work unit whose last event is a passing verification is
complete.

## Anti-Patterns

- Executing without recording the pre-approval review.
- Carrying on with direct-work after discovering an open design decision.
- Claiming a behavior change works because it compiles.
- Running a git action that the user did not ask for.
