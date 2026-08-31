---
unit: <topic | direct-work>
slug: <yyyy-MM-dd-slug>
created: <yyyy-MM-dd>
---

# Verification

## Verdict

(The unit's verdict — `PASS`, `FAIL`, or `INCONCLUSIVE` — and the count per
criterion. It matches the newest `verification` event, and it is not `PASS` while
any recorded `INCONCLUSIVE` or `FAIL` is still unresolved. No other vocabulary:
"excluded from verification" and "partially satisfied" are `INCONCLUSIVE` wearing
a friendlier name, which is the substitution `core-rules.md` §6 exists to stop.)

## Environment

(What was run, where, and against which data — the build or branch, the instance,
the database, anything external. Name **what you did not touch**: a port left
alone, a shared instance someone else was using. A reader reproducing this needs
to know where the boundary was.)

### Pitfalls

(What cost time here, or would mislead the next person, numbered. A missing
required header, a profile that changes which row is read, a field that differs
per request, a cache that has to be cleared first. Write the trap and its cause,
not just the symptom, so this unit's verification remains reproducible.)

### Commands

(The actual invocations, runnable as written. Someone else should be able to paste
them and get the same surface, without reconstructing headers or setup.)

## Data Setup

(The data the verification ran against, and **what that combination
distinguishes** — a case that separates two candidate causes proves something a
convenient case does not. Then what could not be obtained, and which criterion
each gap blocks. Omit the section when the surface needs no data setup.)

## Results

(Criterion, verdict, and evidence — one row each. Quote the criterion as
`requirements.md` states it; a row that paraphrases it into something easier is
judging a different criterion. Evidence cites the record as `#<seq>`, so a reader
can trace the claim back to the event that carries the actual output. A criterion
whose evidence is "read the code" is `INCONCLUSIVE`, not `PASS`, unless the code
is what the criterion is about.

A criterion you had to narrow to reach a pass is `INCONCLUSIVE` for the criterion
as written, with the narrower check recorded beside it as what was actually
covered. Narrowing and then passing is the substitution `core-rules.md` §6 stops,
made one step earlier than a softer verdict word.)

### Incidental Findings

(What was confirmed without being planned — behavior noticed while checking
something else. Real value that nothing else in the record will hold.)

## Gaps

(Verification gaps only: what is unverified, why, what would close it, and the
residual risk of shipping without it. Deployment order, planning questions still
open with another team, and out-of-scope improvements belong in `report.md` —
putting them here is how this section loses its shape.)

---

## After Sealing

(Verification that happened after the record was sealed. Append-only, each entry
dated, newest last.

**This band is outside the record.** `audit.jsonl` accepts nothing but links once
the unit is finalized, so nothing here is backed by a `verification` event, and
nothing here changes the Verdict above — that verdict is what the gate actually
judged.

When the follow-up verification turns into real work rather than one more check,
that is a new work unit linked to this one, not a longer band.)
