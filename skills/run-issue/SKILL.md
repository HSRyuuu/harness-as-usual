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

**Precondition**: a work folder with `contexts.md` and `audit.jsonl` exists. If it
does not — the user named the unit and came straight here — `using-as-usual`
creates it first (core rule 1 and 6). Being told the unit settles the
classification, not the record.

## Pipeline

```text
gathering-context → investigating (loop) → concluding → finalize → git-action?
                                                     └→ move → the new unit's owner
```

| Phase | Owner | Applies |
| --- | --- | --- |
| `gathering-context` | `gathering-context` | required — symptoms, impact, reproduction conditions, boundary |
| `investigating` | this skill | required — the loop below |
| `concluding` | this skill | required — one of the three endings below |
| `finalize` | `finalize` | required, unless the ending was `move` |
| `git-action` | `git-action` | on explicit choice only |

There is no phase pipeline inside `investigating`. Hypotheses, reproduction, and
retraction are events, not stages.

## The Investigation Loop

Investigate, then record. Not the other way round, and not in a batch at the end.

**Form hypotheses.**

```bash
python3 <plugin-root>/scripts/as-usual-record.py add --dir <work-dir> \
  --kind hypothesis --summary "<what you think is happening>" --phase investigating
```

**Gather evidence.** Read code, run the app, analyze logs — all free. Writing a
reproduction test or script needs the user's explicit approval first, recorded
with `--kind approval --action execution --actor user`. Production code is never modified.
Put log excerpts and run outputs under `evidence/`.

**Confirm or retract.** Never edit a recorded line; append the transition.

```bash
python3 <plugin-root>/scripts/as-usual-record.py add --dir <work-dir> \
  --kind status-change --target <seq> --to confirmed \
  --evidence "<reproduction evidence, or 'could not reproduce because …'>" \
  --summary "<what settled it>"

python3 <plugin-root>/scripts/as-usual-record.py add --dir <work-dir> \
  --kind status-change --target <seq> --to cancelled \
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

When a hypothesis or direction is confirmed with evidence, the investigation is
over. Three endings are possible. Present them once, in terms of what happens to
this work rather than by name, and mark the one the evidence points at:

```text
1. conclusion only  — the question is answered. Nothing gets built now.
2. carry on         — the same scope becomes the work. This folder changes unit.
3. split            — the finding opens several separate pieces of work.
```

**Confirming the cause and stopping there is a normal ending, and often the
right one.** Do not present 2 or 3 as what is expected. If the user picks
against the recommendation, follow it without arguing.

An investigation that ends "there is nothing wrong" still ends. That answer is
the deliverable an issue exists to produce, so it gets a `conclusion.md` and a
close like any other — not a folder left `open` with the finding sitting in
`audit.jsonl`. `--event cancelled` is for an investigation the user abandons,
not for one that reached an unexciting answer.

If reproduction code exists, ask under every ending: delete it, or keep it as a
regression-test seed.

### 1 — conclusion only

1. Write `conclusion.md` from `templates/conclusion.md`, with the frontmatter
   placeholders replaced by real values, citing `#<seq>` for what backs each
   claim (`core-rules.md` §3). Self-review it.
2. Hand to `finalize`, which checks and closes the record.
   The helper refuses to finalize an issue with no `conclusion.md`, and refuses
   one whose record holds nothing confirmed — a conclusion needs something it
   rests on. Use `--event cancelled` when the user abandons the investigation.

Do not ask the git-action question by default.

### 2 — carry on

Do this **before `conclusion.md` is written**. The move gate closes the moment
it is on disk, and closure seals the record — after either, ending 3 is the only
one left (`core-rules.md` §7).

```bash
python3 <plugin-root>/scripts/as-usual-record.py move --dir <work-dir> \
  --to <topic | direct-work> [--slug <yyyy-MM-dd-new-slug>]
```

`move` carries no phase, so until something else does, `status` keeps deriving
`investigating` — a phase the new unit does not use, and `status` is what a
resuming session reads. Land the handoff in the same turn:

```bash
python3 <plugin-root>/scripts/as-usual-record.py add --dir <new-work-dir> \
  --kind decision --summary "carried on from the investigation as <unit>" \
  --phase gathering-context --next-action gathering-context
```

Then hand to `run-topic` or `run-direct-work` and tell the user the new path.

Do not write `conclusion.md` — the folder is not an issue any more, and what was
found is already in `contexts.md` and in the confirmed entries. That is what
`write-requirements` reads. Say in the handoff that gathering already ran and
what it settled, so the new owner asks only for what a code change now needs —
acceptance, constraints, risk — instead of re-interviewing from the top.

Use this only when the follow-up is **one** piece of work with the **same**
boundary. A wider scope, or more than one deliverable, is ending 3.

### 3 — split

Ending 1 first — the conclusion is what the follow-ups are built on — with its
**Decomposition** table filled in. That table is the only place the split exists
on disk: `link` records a follow-up once it is created, so a follow-up that was
identified and not created leaves no trace anywhere else. Writing it down is
what lets a later session pick up the rest.

Fill it from the findings, not from the code you happened to read. Every finding
lands in exactly one row; a row covering nothing is not follow-up work. If the
rows are not obvious — where one boundary ends, whether two belong together —
that is a question for `gathering-context`, not something to settle alone.

Then, after the record is closed, create each row the user wants as its own
`topic` or `direct-work` folder, copying the row's scope into its `contexts.md`
boundary, and link both directions (`core-rules.md` §7). `link` is allowed after
closure precisely for this. Rows the user declines stay in the table with the
reason.

Nothing enforces the table — no gate reads it. It holds only because it is
written before the record closes.

## Anti-Patterns

- Modifying production code.
- Writing a reproduction script before the user approved it.
- Confirming a hypothesis on reasoning alone, with no evidence.
- Leaving a disproven confirmation standing instead of cancelling it.
- Ending a turn with new reasoning unrecorded.
- Writing `conclusion.md` after recording closure.
- Writing `conclusion.md` when the work is carrying straight on, then creating a
  second folder for what a `move` would have covered.
- `move`-ing into a follow-up that is wider than what was investigated, or into
  the first of several — that is a link, not a move.
- Turning a concluded folder into the follow-up implementation instead of
  linking to one.
