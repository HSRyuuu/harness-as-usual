# Memory Update Rules

## Store vs do-not-store

Store (in `MEMORY.md`): short facts, durable rules, user preferences, project judgment
criteria, generalized lessons reusable next session.

Do NOT store: one-off topic logs, dated incidents, conversation history, one-time fixes,
unverified guesses, long procedures (those become skills).

## Two write moments

- Immediate capture: during requirements/plan/execute, when the user states an explicit
  long-term rule ("always X", "in this project always Y"), append `memory.candidate`
  only (no write, no approval). Use `record-memory-candidate`.
- Finalize batch: this skill re-validates and applies after approval.

## Candidate re-validation (run in Pass 1)

For each candidate ask: "Given the final result, is this still true AND worth reusing
next time?" Drop candidates that were reversed during the work, duplicate existing
memory, or are low-value. Record the drop reason.

## Budget & overflow (consolidation-first)

- Budget: 3000 characters for `MEMORY.md`. Not append-only.
- On update: simplify → consolidate → dedup BEFORE adding.
- If still over budget after consolidation: split a dominant domain into
  `<domain>_MEMORY.md`, add a one-line entry under `## Domain Memory Index`.
- After a split exists, route new entries: domain match → that `*_MEMORY.md`,
  otherwise → `MEMORY.md`.

## Few-shot

Good: `User is a Java/Spring Boot backend developer and prefers polite Korean technical explanations.`

Consolidate (before → after):
- before: `User uses Java.` / `User uses Spring Boot.` / `User prefers Korean polite style.`
- after: `User is a Java/Spring Boot backend developer and prefers polite Korean technical explanations.`

Bad (do not store): `2026-06-28 user asked about kafka; I explained localhost:9092 vs event-kafka:9092.`

## Approval wording (controller presents)

"다음 memory를 추가/갱신하려 합니다 — 승인할 항목을 알려주세요:" followed by an
item-by-item list. Apply only approved items.
