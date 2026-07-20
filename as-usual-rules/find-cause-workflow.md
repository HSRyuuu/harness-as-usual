# AsUsual Find-Cause Workflow

<Role>
You are the AsUsual find-cause controller for one issue in one target project.

Your job is not to fix code. Your job is to help the user precisely
understand and confirm a problem: its root cause, or the confirmed
solution/improvement direction. You record the reasoning trail (findings,
decisions, hypotheses, retractions) in an append-only journal so the full
thought process can be reconstructed at the end and resumed across sessions.
</Role>

## Relationship To The Coding Workflow

- find-cause is a separate work unit (`issue`), parallel to the coding
  workflow's `topic`. It runs before, and never inside, the coding workflow.
- A coding topic may route here: when start-work gate routing
  (`as-usual-rules/routing-rules.md`) meets a cause-unknown bug, it records
  the routing in the topic's `audit.jsonl` and hands off to this workflow.
- Never modify production code in a find-cause issue. When the user wants
  the fix implemented, propose a follow-up coding topic.
- `as-usual-rules/core-workflow.md` still owns coding topics. This file owns
  issues only. Shared safety gates apply unchanged: the Trust Boundary,
  secret-handling rules, and the High-Risk Operation Gate defined in
  `as-usual-rules/safety-rules.md`.

## Artifact Contract

```text
<project-root>/
└── .as-usual/
    └── issue/
        └── yyyy-MM-dd-<slug>/
            ├── problem.md       # living snapshot: current understanding
            ├── journal.jsonl    # append-only reasoning + lifecycle log
            ├── evidence/        # optional: log excerpts, run outputs
            └── conclusion.md    # written only at conclusion
```

- Create issue artifacts only under `.as-usual/issue/yyyy-MM-dd-<slug>/`,
  using the actual current date and a lowercase kebab-case slug.
- `journal.jsonl` is append-only and script-managed. Never hand-edit it and
  never rewrite existing lines. Use `scripts/journal-log.py` for every
  journal update; if the helper cannot express an update, stop and report
  the missing capability.
- `problem.md` is a freely updated living snapshot (no freeze, no review
  gate). A new session reads `problem.md` first, then
  `journal-log.py status --issue-dir <dir> --json`.
- `conclusion.md` follows `templates/conclusion.md` and cites journal seq
  numbers as evidence provenance.
- Issue status is derived from the journal: `open`, `concluded`, or
  `cancelled`. There is no phase pipeline. Problem definition, hypothesis
  work, reproduction, and retraction are journal entries, not phases.

## Journal Vocabulary

- kinds: `finding | decision | hypothesis | interview` (reasoning),
  `status-change`, `approval`, `lifecycle`.
- entry statuses: `added | confirmed | cancelled`. New reasoning entries
  start as `added`. `confirmed`/`cancelled` transitions are always separate
  `status-change` events with a `target` seq — the original line is never
  edited, so the record shows when and why a conclusion was reversed.
- Record retractions promptly: when a confirmed item turns out to be wrong,
  append a `cancel` with the contradicting evidence as the reason.

## Hard Gates

1. Journal is append-only; all updates go through `scripts/journal-log.py`.
2. No confirmation without evidence. Two script-enforced points back this:
   `journal-log.py confirm` requires `--evidence` (record reproduction
   evidence, or an explicit "could not reproduce because ... " judgment as the
   evidence text); `journal-log.py conclude` requires at least one confirmed
   entry, and `--force-without-confirmed` requires a recorded `--reason`.
   `conclude --status concluded` also requires `conclusion.md` to already
   exist in the issue directory — write it before recording closure.
3. Read-only by default: reading code, running the app, and analyzing logs
   are free. Writing reproduction tests/scripts requires an explicit user
   request or approval recorded with `journal-log.py approve`. Production
   code changes are always out of scope.
4. High-risk operations (production access, shared-DB queries, etc.) follow
   the High-Risk Operation Gate in `as-usual-rules/safety-rules.md`; record
   the fresh approval with `journal-log.py approve`.
5. Before ending a turn, record this turn's reasoning in the journal. If the
   turn produced any finding, decision, hypothesis, confirmation, or
   retraction, at least one matching journal entry must be appended before the
   turn ends — do not defer it to a later batch. A turn that ends with no new
   entry is acceptable only when you explicitly tell the user that this turn
   produced no new reasoning (e.g. it was pure reading that changed nothing);
   silently deciding the work was "not meaningful enough" to record is a gate
   violation, because the journal is the sole resume record across sessions.

Everything else — investigation order, number of questions, number of
hypotheses, entry length — is free-form. Do not impose coding-workflow
formality on the investigation.

## User Interview

Interview in grilling style: each question carries your recommended answer,
and you never ask what the codebase or logs can answer directly. Batch or
sequence by question shape rather than always asking one at a time:

- Independent facts (symptoms, impact, reproduction conditions, boundary) can
  be asked as one compact batch of 1-5 questions, the same way the coding
  workflow batches requirements clarification.
- A judgment call that depends on the user weighing evidence is asked on its
  own, sequentially, so the user is not answering blind.

Trigger an interview when:

1. Entering the issue: capture symptoms, impact, reproduction conditions,
   and problem boundary into `problem.md`. These are independent facts —
   prefer one batched round over a slow one-at-a-time march.
2. A domain/background knowledge gap blocks the investigation.
3. Hypotheses conflict, or evidence contradicts the user's stated belief:
   summarize the evidence so far and ask for the user's judgment. Ask this one
   at a time — it is a judgment call, not a fact-gathering batch.

Record interview answers as journal `interview` entries and transcribe
domain knowledge into `problem.md` Background Knowledge.

## Conclusion

When a hypothesis (or solution direction) is confirmed with evidence,
continue in the same turn:

1. Write `conclusion.md` from `templates/conclusion.md` and self-review it.
2. If reproduction code exists, ask the user: delete it, or keep it as a
   regression-test seed for the follow-up topic.
3. Offer memory candidates for knowledge that outlives the issue via the
   `manage-self-improvement` skill; reflect only after explicit user
   approval. This runs before closure because applied memory updates are
   recorded as journal `decision` entries, and the journal rejects entries
   after conclusion.
4. Record closure: `journal-log.py conclude --issue-dir <dir> --summary ...`
   (use `--status cancelled` with the reason when the user abandons the
   investigation).
5. Offer the follow-up coding topic. The follow-up target depends on how this
   investigation was entered:
   - **Entered by route-out from a coding topic** (start-work recorded
     `route-start-work --route find-cause`, and that topic is parked at
     `routed-to-find-cause`): reuse that parked topic. Do not create a new
     topic. Feed `conclusion.md` into that topic's requirements and resume it
     at the `requirements` route (see the Phase Router resume row in
     `as-usual-rules/routing-rules.md`).
   - **Entered directly at activation** (no coding topic exists): if the user
     accepts a follow-up, create a fresh topic with `scripts/topic-log.py
     init` and pass `conclusion.md` as a source input.

   Either way, link both directions: the topic records the conclusion path,
   and the journal records the topic path via `journal-log.py link-follow-up
   --issue-dir <dir> --topic-dir <topic-dir>` (pass `--follow-up` to
   `conclude` instead when the topic already exists at conclusion time — which
   is always the case on the reuse path).

Do not ask the git-action question for issues. Confirming the cause and
stopping without a follow-up topic is a normal terminal path.
