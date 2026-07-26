# Record Commands

Command reference for `scripts/as-usual-record.py`, the only writer of
`audit.jsonl`. Rules about *what* to record are owned by `core-rules.md`; this
file is *how*.

`<plugin-root>` is the installed AsUsual plugin root — the directory containing
`scripts/` and `skills/`. Resolve it from the SessionStart hook announcement or
from the parent of the running skill's directory.

```bash
python3 <plugin-root>/scripts/as-usual-record.py <command> --dir <work-dir> ...
```

`--dir` is always the work folder itself (`.as-usual/topic/2026-07-25-slug/`),
never the project root.

## init

Creates the folder, `contexts.md` from the template, and `audit.jsonl` with the
first `lifecycle:created` event.

```bash
as-usual-record.py init \
  --dir .as-usual/<unit>/yyyy-MM-dd-<slug> \
  --unit topic|direct-work|issue|inbox \
  --request "<the user's request, verbatim>" \
  --actor claude|codex
```

Use `--unit inbox` only when the user could not choose a unit yet.

Refuses if the folder already holds `contexts.md`, `audit.jsonl`,
`requirements.md`, `plan.md`, or `conclusion.md` — sealing and the move
restriction are both derived from the record, so re-initializing over one would
reset both. Use a different slug for new work, `move` to relabel the folder, or
delete it if it was created by mistake.

## add

Appends one event. The unit is taken from the record, so it is never passed again.

`--summary` is a one-line index entry, not the reasoning. Someone scanning the
record should be able to tell what happened and find the detail elsewhere —
grounds and consequences go in `--data` or in the artifact the event is about,
usually `contexts.md`. Nothing enforces this; a summary that has grown into a
paragraph is a copy of the artifact that will drift from it.

```bash
as-usual-record.py add --dir <work-dir> --kind <kind> --summary "<one line>" \
  [--actor claude|codex|user|system] [--status success|warning|error] \
  [--phase <phase>] [--next-action <phase>|awaiting-user|none] \
  [--data key=value ...]
```

Kind-specific flags:

| Kind | Required | Flags |
| --- | --- | --- |
| `lifecycle` | `--event` | `created` · `unit-selected` · `finalized` · `cancelled` · `linked`. `--event finalized` also takes `--reason` when the newest verdict is not `PASS` |
| `verification` | `--verdict` | `PASS` · `FAIL` · `INCONCLUSIVE` |
| `approval` | `--action` | `high-risk` · `execution` · `git-action` |
| `status-change` | `--target <seq>`, `--to` | `--to confirmed` needs `--evidence`; `--to cancelled` needs `--reason` |
| `blocker` | — | `--resolves <seq>` marks an earlier blocker resolved |
| others | — | free-form `--summary`, extra fields via `--data` |

Examples:

```bash
# a decision agreed with the user (update contexts.md in the same turn)
# summaries are prose: write them in the user's language, like the artifacts
add --dir <d> --kind decision --summary "retries settled on exponential backoff" \
    --phase gathering-context --next-action write-requirements

# the pre-approval plan review that core rule 7 requires
add --dir <d> --kind review --summary "plan review: 2 findings, both fixed" \
    --phase write-plan --data findings=2

# execution approval (refused unless a review entry already exists)
# --actor user: the approval belongs to whoever gave it, not to the recorder
add --dir <d> --kind approval --action execution --actor user \
    --summary "<what the user approved>"

# verification with real output
add --dir <d> --kind verification --verdict PASS \
    --summary "pytest -q: 12 passed"

# confirming a hypothesis in an issue
add --dir <d> --kind status-change --target 2 --to confirmed \
    --evidence "reproduced 100% at 50 concurrent requests" --summary "hypothesis confirmed"

# closing
add --dir <d> --kind lifecycle --event finalized --summary "closed" --next-action none
```

## move

Relabels a folder that has not yet produced its own output.

```bash
as-usual-record.py move --dir <work-dir> --to topic|direct-work|issue [--slug <new-slug>]
```

Moves the folder and appends `lifecycle:unit-selected` with the old and new
paths. Refused when `requirements.md`, `plan.md`, or `conclusion.md` exists —
create a new folder and `link` instead. No redirect file is left behind; if a
stale path is given later, scan `.as-usual/` instead.

## link

Records a two-way link between work units.

```bash
as-usual-record.py link --dir <work-dir> --to-dir <other-work-dir> [--summary "<why>"]
```

Allowed even after a record is closed — a concluded issue must be able to point
at the follow-up it spawned. Also add the path to both `contexts.md` top bands.

Paths are recorded relative to the project root (`.as-usual/topic/…`) so the
record survives the repository moving or being cloned elsewhere. A target
outside the project keeps its absolute path, since relativizing it would only
produce `../..` noise. `move` records its old and new paths the same way.

## status

Derives current state. This is the resume entry point, not a file scan.

```bash
as-usual-record.py status --dir <work-dir> [--json]
```

Returns unit, state (`open`/`finalized`/`cancelled`), phase, nextAction, open
blockers, approvals, latest verification, confirmed/cancelled seqs, links,
artifacts present, and whether `move` is still allowed.

## validate

Structural audit of an existing record: duplicate or non-increasing seqs,
vocabulary violations, missing payloads, appends after closure, and a
`contexts.md` whose declared unit disagrees with the record. Use it when a
record looks hand-edited or a concurrent write is suspected.

Retired vocabulary is accepted here and refused by `add`: a value that was legal
when it was written keeps auditing clean, while nothing new can be written with
it. The record is append-only, so shrinking the vocabulary must not reach
backwards.

```bash
as-usual-record.py validate --dir <work-dir>
```

## Refusals

The script refuses rather than warns. Each message names the rule:

| Refusal | Fix |
| --- | --- |
| `verification requires --verdict` | record `INCONCLUSIVE` if evidence is unobtainable |
| `confirming requires --evidence` | attach reproduction evidence, or an explicit "could not reproduce because …" |
| `the plan must be critically reviewed before execution approval` | run the review, record it, then approve. On a second approval the review must be newer than the previous one |
| `cannot finalize without a recorded verification` | record the verification (`INCONCLUSIVE` when evidence is unobtainable), or close with `--event cancelled` |
| `cannot finalize on a FAIL/INCONCLUSIVE verification` | re-verify and record the passing run, accept it with `--reason "<why>"`, or close with `--event cancelled` |
| `cannot init … it already holds …` | use a different slug, `move` to relabel the folder, or delete it if it was a mistake |
| `issue cannot be finalized without conclusion.md` | write the conclusion, or close with `--event cancelled` |
| `issue cannot be finalized without a confirmed entry` | confirm what the conclusion rests on, or close with `--event cancelled` |
| `record is finalized … only lifecycle link entries may be appended` | the work is closed; start a new unit |
| `cannot move … it already produced …` | create a new folder for the other unit and `link` |
| `phase X is not used by unit Y` | use a phase from that unit's pipeline |
