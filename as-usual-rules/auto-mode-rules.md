# Auto Mode Rules

Single source of truth for auto mode: what it decides on the user's behalf, what
it never decides, and how those judgments are recorded. Auto mode is a mode over
the three work units, not a fourth unit. `core-rules.md` points here.

This file owns rules only. The order of steps in a unit's pipeline is owned by
that unit's skill — `run-topic`, `run-direct-work`, `run-issue`. Auto mode
changes who answers at each step, never which steps exist or in what order.

## Where Auto Mode Sits

Below the seven core rules and `safety-rules.md`; above a step skill's stop
conditions.

The core rules and every gate in `safety-rules.md` hold unchanged under auto
mode. `core-rules.md` §8 already says the record cannot waive them — auto mode
cannot either. What auto mode does override is a step skill's "stop and wait for
the user": that is a workflow expectation, and the user turning on auto mode is
the current instruction that outranks it.

## Turning It On And Off

Auto mode is declared by `mode: auto` in the work folder's `contexts.md`
frontmatter:

```markdown
---
unit: direct-work
slug: 2026-07-28-clamp-helper
created: 2026-07-28
mode: auto
---
```

- **Only the user turns it on.** Never add the flag on your own initiative, and
  never infer it from a request that merely sounds urgent or self-contained.
  Recommending it is fine; enabling it is the user's call.
- **Only the user turns it off.** Halting under the rules below is not turning
  the mode off — the flag stays and the unit stays open.
- Record either change as a `decision` carrying `--data mode=auto` or
  `--data mode=manual`, so the record says when the mode changed and on whose
  word.
- The flag is on disk, so a later session resuming this folder is still in auto
  mode. There is no second state file to keep in sync.
- No flag means manual. That is the default and needs no declaration.

## Why Auto Mode Never Self-Starts

The flag lives in `contexts.md`, and `contexts.md` exists only after the unit is
decided (core rule 6). At classification time the flag therefore cannot exist,
and auto mode has no say in which unit a new request becomes. Classification
stays with `using-as-usual` and the user.

That asymmetry is the property that makes the mode safe: **auto mode can only
continue work the user already agreed to start.** It cannot pick up a fresh
request and run away with it. If the user wants a new request handled
automatically, they say so that turn — and that instruction, not the flag, is
what authorizes it.

## The Halt Line

Two things are never automated. Both are record-layer rules, and neither plan
detail nor user enthusiasm moves them.

**High-risk operations** (core rule 2). The list and the gate are owned by
`safety-rules.md` and are not restated here. Auto mode does not supply the fresh
approval — it stops and asks:

```bash
python3 <plugin-root>/scripts/as-usual-record.py add --dir <work-dir> \
  --kind blocker --summary "<the operation, its target, and what approval is needed>" \
  --phase blocked --next-action awaiting-user
```

The unit stays open. When the user approves, record the `high-risk` approval the
way `safety-rules.md` requires — with the user as actor, because they are the one
who approved — and continue.

**Git actions** (core rule 4). Auto mode never selects one. A unit finished in
auto mode ends with the work finalized and no git action taken; `git-action` runs
only on the user's explicit choice. Say what a sensible action would be and let
them choose it.

**A non-`PASS` verdict is not a third exception.** `INCONCLUSIVE` is a gate
failure (`core-rules.md` §6). Auto mode has no authority to close a unit on a
non-`PASS` verdict, and specifically may not use `--reason` to push one past
`finalize`. That escape hatch is for a user who has seen the evidence.

## What Auto Mode Answers

Wherever the pipeline would wait for the user, auto mode decides instead — with
the rigor the user's answer would have needed, and recorded so the decision can
be reviewed afterwards.

| Stop point | Normally the user | Under auto mode |
| --- | --- | --- |
| open items while gathering context | answers the questions | infers from the request, the codebase, and `docs/memory/`, records the answer, proceeds — see below |
| `requirements.md` written | confirms the scope | checks it against the initial request, records the confirmation, proceeds |
| `plan.md` written and critically reviewed | approves execution | records the `approval --action execution` after that review, then executes |
| execution finished | decides whether to review the changes | reviews by default; skipping needs a recorded reason |
| `review.md` written | decides what to fix | fixes what the review found, or records why a finding is left standing |
| cleanup proposed | approves or declines | may approve behavior-preserving cleanup; anything that changes behavior is not cleanup |
| work closing | approves finalizing | finalizes once the verification evidence is in the record |

An `issue` stops in different places, because it produces an understanding rather
than a change:

| Stop point | Normally the user | Under auto mode |
| --- | --- | --- |
| a reproduction test or script is needed | approves writing it | records the `approval --action execution` itself, then writes it — production code still is never modified |
| evidence contradicts what the user believes, or a domain gap blocks progress | resolves it | keeps investigating while evidence can still decide; halts when only the user can supply the missing knowledge |
| `conclusion.md` written, reproduction code exists | says delete it or keep it | keeps it and says so — deleting is on the halt line |
| a follow-up unit would fix the cause | decides whether to create it | proposes it and stops; creating a new unit is the user's call |

## Gathering Context Under Auto Mode

Do not go around `gathering-context`. Make its job empty before calling it.

Infer each open item from the request, the code, and `docs/memory/`, write the
result into the Decisions band of `contexts.md`, and record the material ones as
`decision` events. Then call `gathering-context` with the list. With nothing
actually open, it takes its own zero-questions path and returns.

An item that evidence cannot settle is not settled by picking. State the
assumption and its risk in `contexts.md`; if the work would be **wrong** rather
than merely narrower when the assumption is wrong, halt as on the halt line.

## No Plan Drift

For the units that have a plan — `topic` and `direct-work` — auto mode executes
the approved plan, and the approval was for that plan. When execution reveals that
the approach, the risk, or the verification has to change, return to `write-plan`,
revise it, record a new `review`, and record a new `approval --action execution`.
Core rule 7 holds unchanged here — the record helper requires a review newer than
the previous approval, so this is enforced rather than merely expected.

An implementation detail settled while writing the code is not drift. A different
approach, a newly discovered risk, or a different verification surface is.

## Self-Improvement Scope

Auto mode may write to `docs/memory/`. It may not change rules or skills on its
own: a change worth making to this workflow is recorded as a proposal for the
user, never applied unasked.

## Record Honesty

The record's job here is to let a later reader tell what a person decided from
what this mode decided. That distinction is worth more than a tidy history.

- Every automated judgment: `--actor claude` (or `--actor codex`) plus
  `--data mode=auto`.
- **Never `--actor user` for a decision the user did not make.** This is the one
  falsehood that makes the entire record untrustworthy.
- Record the mode entry early, so a reader knows from the first events which mode
  produced the rest.
- `report.md` carries a section listing the decisions auto mode made on the user's
  behalf and the assumptions behind them. Templates are a floor, so this section
  is required whether or not one shows it.
- Say what the evidence does not cover. An automated run that verified less than
  it claims is worse than one that admits the gap.

## Failure And Blocked

A failing verification gets at most **two** re-verification attempts. Record each
attempt as a `verification` event with its actual verdict — a failed attempt is
evidence, not noise.

If it still does not pass, stop: record a `blocker` with
`--phase blocked --next-action awaiting-user`, leave the unit open, and tell the
user three things — what blocked, how far the work got, and what is needed to
unblock it. The same failure reproducing a third time is an immediate halt;
retrying again is how a loop becomes a spin.

## Anti-Patterns

- Recording an automated decision as `--actor user`.
- Approving a high-risk operation on the user's behalf.
- Selecting a git action because the work happens to be finished.
- Closing a unit on a non-`PASS` verdict, with or without `--reason`.
- Adding the flag yourself because the request looked self-contained.
- Restating a unit's pipeline order here — the owner skill owns it.
- Claiming a completion whose evidence the run did not actually produce.
