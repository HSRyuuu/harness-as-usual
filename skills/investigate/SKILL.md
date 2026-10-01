---
name: investigate
description: Use when AsUsual work must establish a root cause, a solution direction, or feasibility from code, logs, or an experiment before anything changes. Runs the investigation loop and ends it with a conclusion, a carry-on into the change, or a split.
---

# Investigate

Establishes **what is actually true** — a root cause, a solution direction, or
whether an approach is viable — within the read-only default (`safety-rules.md`).

Your job here is not to fix anything. It is to help the user reach a conclusion
they can rely on, with the reasoning trail recorded so it can be reconstructed
and resumed. The phase is `investigate`. Read `as-usual-rules/core-rules.md` and
`as-usual-rules/safety-rules.md` first.

There is no phase pipeline inside `investigate`. Hypotheses, reproduction, and
retraction are events, not stages.

## The Investigation Loop

Investigate, then record. Not the other way round.

**Form hypotheses.**

```bash
python3 <plugin-root>/scripts/as-usual-record.py add --dir <work-dir> \
  --kind hypothesis --summary "<what you think is happening>" --phase investigate
```

**Gather evidence** within the read-only default (`safety-rules.md`, Read-Only
Default For Investigation). Put log excerpts and run outputs under
`evidence/`. A reproduction test or script needs the user's approval first,
recorded as:

```bash
python3 <plugin-root>/scripts/as-usual-record.py add --dir <work-dir> \
  --kind approval --action reproduction --actor user --status success \
  --summary "<what the reproduction covers, and the user's words>" --phase investigate
```

**Confirm or retract.** For a cause claim, connect the observed defect to the
reported symptom: trace the request, state changes, downstream handling, and
visible outcome, or reproduce the causal link. A local defect may be confirmed
while its relevance to the report remains a hypothesis. State which boundary
was not observed and keep investigating that link. An inability to reproduce
can establish a limitation under the tested conditions, not the suspected cause.

```bash
python3 <plugin-root>/scripts/as-usual-record.py add --dir <work-dir> \
  --kind status-change --target <seq> --to confirmed \
  --evidence "<observed evidence supporting this specific claim>" \
  --summary "<what settled it>"

python3 <plugin-root>/scripts/as-usual-record.py add --dir <work-dir> \
  --kind status-change --target <seq> --to cancelled \
  --reason "<the contradicting evidence>" --summary "<what overturned it>"
```

The helper refuses a confirmation with no evidence; it cannot judge whether the
evidence supports the claim. Retract promptly — a
confirmed item that turns out wrong must be cancelled with the contradicting
evidence, so the record shows when and why the conclusion reversed.

**Keep `contexts.md` current.** Update its middle band (`core-rules.md` §3) as
understanding changes; that is what a new session reads first.

**Record before the turn ends.** If this turn produced a finding, decision,
hypothesis, confirmation, or retraction, at least one matching event must be
appended before the turn ends. A turn with no new event is fine only when you
tell the user it produced no new reasoning. The record is the only thing that
survives to the next session.

**Come back to the user** when hypotheses conflict, when evidence contradicts
what the user believes, or when a domain gap blocks progress. Summarize the
evidence and ask for their judgment through `gathering-context`.

## Ending

When the investigation's question is answered with evidence, end it; an
incidental defect alone does not answer a root-cause question. Three endings are
possible. If the recorded request boundary already settles it — investigation
only means conclusion only (`core-rules.md` §2) — follow that. Otherwise present
them once, in terms of what happens to this work rather than by name, and mark
the one the evidence points at:

```text
1. conclusion only  — the question is answered. Nothing gets built now.
2. carry on         — the same scope becomes the change, in this folder.
3. split            — the finding opens several separate pieces of work.
```

**Confirming the cause and stopping there is a normal ending, and often the
right one.** Do not present 2 or 3 as what is expected. If the user picks
against the recommendation, follow it without arguing.

An investigation that ends "there is nothing wrong" still ends. That answer is
the deliverable, so it gets a `conclusion.md` and a close like any other — not a
folder left `open` with the finding sitting in `audit.jsonl`. `--event
cancelled` is for an investigation the user abandons, not for one that reached
an unexciting answer.

If reproduction code exists, ask under every ending: delete it, or keep it as a
regression-test seed.

### 1 — conclusion only

1. Write `conclusion.md` from `templates/conclusion.md`, citing `#<seq>` for
   what backs each claim (`core-rules.md` §3). Self-review it.
2. Hand to `finalize`, which checks and closes the record.
   The helper refuses to finalize a `conclusion.md` whose record holds nothing
   confirmed — a conclusion needs something it rests on.

### 2 — carry on

The work continues in this folder; nothing is moved or linked. Record the
handoff in the same turn, naming the next phase by the `run-work` matrix —
`write-requirements` when the requirements need agreeing, `write-plan`
otherwise:

```bash
python3 <plugin-root>/scripts/as-usual-record.py add --dir <work-dir> \
  --kind decision --summary "investigation answered; carrying on into the change" \
  --phase investigate --next-action <write-requirements | write-plan>
```

Extend the request boundary in the Decisions band only on the user's explicit
request (`core-rules.md` §2). No `conclusion.md` unless the user wants one — what
was found is already in `contexts.md` and in the confirmed entries, and that is
what the next step reads. Say in the handoff that gathering already ran and what
it settled, so the next step asks only for what a code change now needs —
acceptance, constraints, risk — instead of re-interviewing from the top.

Writing the fix is a code change: it goes through `write-plan` and execution
approval like any other. A kept reproduction is the failure reproduced before
the fix (`core-rules.md` §6).

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

Then, after the record is closed, create each row the user wants as its own work
folder through `using-as-usual`, copying the row's scope into its `contexts.md`
boundary, and link both directions (`core-rules.md` §7). Rows the user declines
stay in the table with the reason.

Nothing enforces the table — no gate reads it. It holds only because it is
written before the record closes.
