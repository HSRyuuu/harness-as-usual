---
name: run-work
description: Use once AsUsual work is set up — a work folder with contexts.md and audit.jsonl exists. The owner of every AsUsual work record; routes each phase to its step skill by what the work needs.
---

# Run Work

Owns the pipeline of an AsUsual work record. Which steps apply is decided by
what the work needs, not by a label chosen up front.

This skill is a declaration, not a procedure. Each step is owned by its own
skill; this file says which steps apply, under what condition, at what strength,
and which gates stand between them. Read `as-usual-rules/core-rules.md` first.

**Precondition**: a work folder with `contexts.md` and `audit.jsonl` exists. If it
does not — the user came straight here — `using-as-usual` creates it first (core
rules 1 and 6).

## Pipeline

```text
gathering-context → investigate? → write-requirements? → write-plan → execute-plan
                  → review-execution? → cleanup-code? → finalize → git-action?
```

Every path stops at the request boundary recorded in the `contexts.md` Decisions
band (`core-rules.md` §2).

| Phase | Step skill | Applies when | Strength |
| --- | --- | --- | --- |
| `gathering-context` | `gathering-context` | always | settle what the later steps need: scope, constraints, and acceptance for a change; symptoms, impact, reproduction conditions, and boundary for an investigation. **Zero questions is normal** when nothing is open — record that and move on |
| `investigate` | `investigate` | a cause, direction, or feasibility must be established from code, logs, or an experiment before anything changes — including a bug whose cause is unconfirmed, however small the eventual fix | read-only by default; ends in one of `investigate`'s three endings |
| `write-requirements` | `write-requirements` | the requirements need agreeing: a decision between viable approaches; a contract or product surface — public API, data model, auth, migration, deployment, dependency policy, user-facing wording, business rules; hard to reverse or hard to verify; built around a high-risk operation (`safety-rules.md`). Size is not the test | full `requirements.md` |
| `write-plan` | `write-plan` | the work changes code | full `plan.md` when `requirements.md` exists; checklist strength — steps and verification method — otherwise. Ends in the pre-approval critical review either way |
| `execute-plan` | `execute-plan` | the user approved execution | evidence in `verification.md` when `requirements.md` exists; otherwise `verification.md` only when the evidence needs more than the record's summaries |
| `review-execution` | `review-execution` | execution finished | proposed by default when `requirements.md` exists; otherwise offered when the change is broad or touched something delicate. The user decides |
| `cleanup-code` | `cleanup-code` | the user explicitly approves cleanup | — |
| `finalize` | `finalize` | the record holds `conclusion.md`, or an approved execution with `requirements.md`: required. An approved execution without `requirements.md`: offered — a record whose last event is a passing verification is complete without it. Neither an approved execution nor `conclusion.md` (a plan-only or requirements-only boundary): the record stays open at `awaiting-user`, or is cancelled — the helper refuses to finalize it | `report.md` + closure; no `report.md` when the conclusion is the whole deliverable (no approved execution) |
| `git-action` | `git-action` | the user explicitly chooses one | `finalize` does not ask by default when the work ended in a conclusion only — there is usually nothing to commit |

The conditions are re-read as the work learns. A change that looked settled and
turns out to need a decision, to touch a contract surface, or to be hard to
reverse enters `write-requirements` before the plan is approved. An open
investigation's question is answered before `write-requirements` — the cause of a
bug is found, not agreed.

## Gates

- **Cause before requirements.** Do not write `requirements.md` for a bug whose
  cause is unconfirmed; that is `investigate`.
- **Plan review before execution approval** (core rule 7). `write-plan` runs it
  and records a `review` entry — lighter for a checklist, but it happens. The
  record helper refuses the execution approval without one.
- **Execution approval before executing.** Explicit, from the user.
- **High-risk operations need fresh approval** (`safety-rules.md`).
- **Verification evidence before any completion claim** (core rule 3). For a
  behavior change, the verification must exercise the changed behavior, not just
  confirm the code compiles.
- **When finalize runs, it runs before the git action**, and only the action the
  user chose runs.

## Routing

Derive state, then route to the phase that owns it:

```bash
python3 <plugin-root>/scripts/as-usual-record.py status --dir <work-dir> --json
```

- The user asks for a later phase whose gate is not met: name the missing gate,
  record it, and stop. Do not silently obey and do not silently refuse.
- A completed artifact needs a change before the next approval: hand back to its
  owner skill (`write-requirements` for `requirements.md`, `write-plan` for
  `plan.md`), which decides whether to absorb it or reopen the earlier phase. A
  change the user directs during execution follows `core-rules.md` §4 instead.
- The cause of something turns out to be unknown mid-change: when it lies inside
  this record's boundary, enter `investigate` in this folder. When it is separate
  work, create a separate folder beside this one and link the two
  (`core-rules.md` §7). Do not guess the cause in `requirements.md`.
- Gathering shows there is nothing to do — it is already done, already correct,
  or the premise is false: that finding is the record's whole output. Write it
  into the `contexts.md` Decisions band, then close with `--event cancelled` and
  its `--reason`. Leaving the folder `open` parks a `nextAction` that outlives
  the question, and the finding stays buried in `audit.jsonl` where the next
  session will not meet it. An investigation that reaches "nothing is wrong" is
  different: it ends with `conclusion.md` (`investigate`).

## Closing Without Finalize

When `finalize` is only offered, report the result and the verification evidence
in chat. If verification could not be run, say `not verified because …` with the
concrete reason and record `INCONCLUSIVE`. Then offer `finalize`, and
`git-action` only if the user asks for it.

## Anti-Patterns

- Writing `requirements.md` for a bug whose cause is unconfirmed.
- Asking for execution approval before the plan has been critically reviewed.
- Carrying on with a checklist plan after discovering an open design decision.
- Treating `plan.md` as a progress ledger — progress belongs in `audit.jsonl`.
- Claiming a behavior change works because it compiles.
- Continuing into commit, PR, release, or deploy behavior after execution.
- Restating step procedures here instead of routing to the step skill.
