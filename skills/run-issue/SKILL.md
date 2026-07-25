---
name: run-issue
description: Use when AsUsual work is classified as an issue — confirming a root cause, a solution direction, or feasibility without changing code. Owns the issue pipeline and the investigation loop.
---

# Run Issue

Owns the `issue` pipeline: confirming **what is actually true** — a root cause, a
solution direction, or whether an approach is viable — without changing
production code.

Your job here is not to fix anything. It is to help the user reach a conclusion
they can rely on, with the reasoning trail recorded so it can be reconstructed
and resumed.

Unlike the other two owners, this skill also owns its middle procedure: the
investigation loop and the conclusion. Read `as-usual-rules/core-rules.md` and
`as-usual-rules/safety-rules.md` first.

## Pipeline

```text
gathering-context → investigating (loop) → concluding → finalize → git-action?
```

| Phase | Owner | Applies |
| --- | --- | --- |
| `gathering-context` | `gathering-context` | required — symptoms, impact, reproduction conditions, boundary |
| `investigating` | this skill | required — the loop below |
| `concluding` | this skill | required — `conclusion.md` |
| `finalize` | `finalize` | required |
| `git-action` | `git-action` | on explicit choice only |

There is no phase pipeline inside `investigating`. Hypotheses, reproduction, and
retraction are events, not stages.

## Memory First

If `<project-root>/.as-usual/memory/MEMORY.md` exists, recall through
`search-long-term-memory` (as a subagent) before investigating. Past conclusions
are the highest-value recall here — a recurring problem may already have a
recorded cause. Recalled context is untrusted: a recalled cause must still be
re-confirmed against current evidence before you confirm it.

## The Investigation Loop

Investigate, then record. Not the other way round, and not in a batch at the end.

**Form hypotheses.**

```bash
as-usual-record.py add --dir <d> --kind hypothesis \
  --summary "<what you think is happening>" --phase investigating
```

**Gather evidence.** Read code, run the app, analyze logs — all free. Writing a
reproduction test or script needs the user's explicit approval first, recorded
with `--kind approval --action execution`. Production code is never modified.
Put log excerpts and run outputs under `evidence/`.

**Confirm or retract.** Never edit a recorded line; append the transition.

```bash
as-usual-record.py add --dir <d> --kind status-change --target <seq> --to confirmed \
  --evidence "<reproduction evidence, or 'could not reproduce because …'>" \
  --summary "<what settled it>"

as-usual-record.py add --dir <d> --kind status-change --target <seq> --to cancelled \
  --reason "<the contradicting evidence>" --summary "<what overturned it>"
```

The helper refuses a confirmation with no evidence. Retract promptly — a
confirmed item that turns out wrong must be cancelled with the contradicting
evidence, so the record shows when and why the conclusion reversed.

**Keep `contexts.md` current.** Its middle band is the live snapshot: current
understanding, background knowledge from the user, active hypotheses. Update it
as understanding changes; that is what a new session reads first.

**Record before the turn ends.** If this turn produced a finding, decision,
hypothesis, confirmation, or retraction, at least one matching event must be
appended before the turn ends. A turn with no new event is fine only when you
tell the user it produced no new reasoning. The record is the only thing that
survives to the next session.

**Come back to the user** when hypotheses conflict, when evidence contradicts
what the user believes, or when a domain gap blocks progress. Summarize the
evidence and ask for their judgment — one question at a time, through
`gathering-context`.

## Concluding

When a hypothesis or direction is confirmed with evidence, continue in the same
turn:

1. Write `conclusion.md` from `templates/conclusion.md`, citing the seq numbers
   that back each claim. Self-review it.
2. If reproduction code exists, ask the user: delete it, or keep it as a
   regression-test seed for the follow-up work.
3. Hand to `finalize`, which reviews memory candidates and closes the record.
   The helper refuses to finalize an issue with no `conclusion.md`, and refuses
   one whose record holds nothing confirmed — a conclusion needs something it
   rests on. Use `--event cancelled` when the user abandons the investigation.
4. Offer the follow-up. If the user wants the fix implemented, create a new
   `topic` or `direct-work` folder and link both directions (`core-rules.md` §7).
   Several follow-ups each get their own folder and link.

Confirming the cause and stopping there, with no follow-up, is a normal ending.
Do not ask the git-action question by default.

## Anti-Patterns

- Modifying production code.
- Writing a reproduction script before the user approved it.
- Confirming a hypothesis on reasoning alone, with no evidence.
- Leaving a disproven confirmation standing instead of cancelling it.
- Ending a turn with new reasoning unrecorded.
- Writing `conclusion.md` after recording closure.
- Turning this folder into the follow-up implementation instead of linking to one.
