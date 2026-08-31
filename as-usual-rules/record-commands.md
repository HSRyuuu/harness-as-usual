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
first `lifecycle:created` event. The document holds the request and nothing else:
a band is written the first time it has something to hold, never as a placeholder
waiting to be filled.

```bash
as-usual-record.py init \
  --dir .as-usual/<unit>/yyyy-MM-dd-<slug> \
  --unit topic|direct-work|issue|inbox \
  --request "<the user's request, verbatim>" \
  --actor claude|codex
```

Use `--unit inbox` only when the user could not choose a unit yet.

Refuses if the folder already holds `contexts.md` or `audit.jsonl` — sealing and
the move restriction are both derived from the record, so re-initializing over
one would reset both. Use a different slug for new work, `move` to relabel the
folder, or delete it if it was created by mistake.

A folder holding only artifacts — a `plan.md` written past the helper, with no
record beside it — is adopted rather than refused. It was never a record, so
there is nothing to reset, and refusing it left the folder unable to acquire the
record it was missing. `init` says what it adopted; `move` is closed from then
on, as it is for any unit that has produced output.

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
| `lifecycle` | `--event` | `created` · `unit-selected` · `finalized` · `cancelled` · `linked`. `--event finalized` also takes `--reason` when a verification is still open, and that door is the user's: `--actor user --status success` (`core-rules.md` §6) |
| `verification` | `--verdict` | `PASS` · `FAIL` · `INCONCLUSIVE`. `--resolves <seq>` marks an earlier `INCONCLUSIVE` or `FAIL` verification re-verified |
| `approval` | `--action` | `high-risk` · `execution` · `git-action`, each with `--actor user --status success` |
| `status-change` | `--target <seq>`, `--to` | `--to confirmed` needs `--evidence`; `--to cancelled` needs `--reason`. The target is any reasoning entry — `decision`, `hypothesis`, `review`, `work`, `note` — so this is how a reversed decision is retracted, not an `issue`-only move |
| `blocker` | — | `--resolves <seq>` marks an earlier, still-open blocker resolved. With `--status success` the entry is a pure resolution and stops counting as open; `warning` or `error` means something still blocks, and it stays visible |
| others | — | free-form `--summary`, extra fields via `--data` |

`--resolves` belongs to `verification` and `blocker` only, and closes one entry
of its own kind that is still open: a verification resolves a verification, a
blocker resolves a blocker, and neither may close a target something else
already closed. Every other kind is refused — record what an entry relates to in
`--summary` or `--data`. "A is cleared but B now blocks us" is one event: record
it as a `warning` or an `error` and it stays visible in `status`, because the
status is what separates a compound blocker from a plain resolution.

The script refuses rather than warns, and each message names the rule it is
enforcing and how to satisfy it; read the refusal rather than guessing at the
flag. One recovery it cannot state as a flag: `record is finalized … only
lifecycle link entries may be appended` means the unit is closed, so the work
continues in a new unit linked to it (`core-rules.md` §7), never by reopening
this one.

Examples:

```bash
# a decision agreed with the user (update contexts.md in the same turn)
# summaries are prose: write them in the user's language, like the artifacts
add --dir <d> --kind decision --summary "retries settled on exponential backoff" \
    --phase gathering-context --next-action write-requirements

# the pre-approval plan review that core rule 7 requires
# --phase write-plan --status success: only this shape clears the approval gate
add --dir <d> --kind review --summary "plan review: 2 findings, both fixed" \
    --phase write-plan --data findings=2

# execution approval (refused without plan.md and a newer successful plan review)
# --actor user: the approval belongs to whoever gave it, not to the recorder,
# and every approval action is refused without it
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

# closing over a verification the user accepted as still open
add --dir <d> --kind lifecycle --event finalized --actor user \
    --reason "<why this is being closed anyway>" --summary "closed" --next-action none
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

Records a two-way link between work units, in the record and in both documents.

```bash
as-usual-record.py link --dir <work-dir> --to-dir <other-work-dir> [--summary "<why>"]
```

Appends the entry to each side's `## Linked Work` band, creating it when the
document does not have one yet. If a document is too damaged to place it — no
frontmatter and no `# Context` title — the events are still recorded and the
command says which file to fix by hand.

Allowed even after a record is closed, and this is the point: a sealed unit
cannot mark its own decision superseded, so the link is the only channel a later
correction has. A concluded issue points at the follow-up it spawned the same
way. Say in `--summary` what the other unit supersedes, so a reader who lands on
the stale decision meets the correction on the same page.

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
blockers, approvals, the verdict that stands, the latest verification event,
confirmed and cancelled reasoning entries, links, artifacts present, and whether
`move` is still allowed.

`verification` is the verdict that stands for the unit, not merely the newest
one: while any `FAIL` or `INCONCLUSIVE` is unresolved it reads `INCONCLUSIVE` and
names what downgraded it. `latestVerification` is the newest event itself. The
two answer different questions and both are reported, so neither has to be
reconstructed from `openVerifications`.

`confirmed` and `cancelled` carry the target's summary and the reason or evidence
given, so a superseded decision can be read without opening `audit.jsonl`.

## validate

Structural audit of an existing record: duplicate or non-increasing seqs,
vocabulary violations, missing payloads, appends after closure, and a
`contexts.md` whose declared unit disagrees with the record. Use it when a
record looks hand-edited or a concurrent write is suspected.

It also re-judges a sealed unit against today's finalize gate and reports what
that gate would now refuse — a unit closed over an open verification with no
`--reason` or with someone other than the user's, a sealed `topic` with no
`verification.md`, a sealed `issue` with no `conclusion.md`. These are
`warning:` lines and never reach the exit code. The append gates only run when a
unit closes, so a record sealed before a gate existed is not made retroactively
invalid by it — the same promise retired vocabulary keeps.

Retired vocabulary is accepted here and refused by `add`: a value that was legal
when it was written keeps auditing clean, while nothing new can be written with
it. The record is append-only, so shrinking the vocabulary must not reach
backwards.

```bash
as-usual-record.py validate --dir <work-dir>
```
