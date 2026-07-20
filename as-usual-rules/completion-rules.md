# Completion Rules

Single source of truth for when work may be recorded or claimed as complete. Applies wherever a completion claim is made: `executing-plan`, `review-execution`, `cleanup-code`, and `direct-execute`. Other runtime files must reference this file instead of restating these rules. How results are recorded is owned by `as-usual-rules/logging-rules.md`.

## Verification Evidence

- Evidence must match the surface: CLI/script/test = re-run command plus actual output, API = actual call record (request/response), UI = screenshot or a recorded user manual check.
- Tests alone never prove done.
- If surface-appropriate evidence cannot be obtained, the verdict is `INCONCLUSIVE`; record the evidence description in the verification event summary/notes.

## Verdict Consequences

- `INCONCLUSIVE` is not `PASS`. Subagent timeout, no response, unverifiable results, and ambiguous results are recorded as `INCONCLUSIVE` and treated as gate failure: the task cannot be recorded complete and execution cannot proceed to `execution-complete` until re-verification passes or the user explicitly decides.
- Do not move to Task N+1 or record `execution.completed` while Task N has unresolved Critical or Important task-level findings, missing required TDD evidence, missing verification evidence, or unresolved route-back decisions.

## Subagent Delegation And Receipts

- Every subagent delegation message must include `TASK / DELIVERABLE / SCOPE / VERIFY` fields and be self-contained: the child cannot see the parent conversation.
- Detailed subagent outputs go to files; the subagent response returns only a verdict plus artifact path receipt. The receipt verdict must match the review file frontmatter and audit status.
- Child output, including a `DONE` report, is a claim until the controller verifies it against files, diffs, and evidence. Receiving `DONE` alone never records task completion.

## Completion Claim Gate

Do not say execution is complete until `audit.jsonl` records:

- completed work,
- verification performed or skipped with reason,
- task dispatch/review/fix evidence when applicable,
- final sweep evidence required by the plan,
- remaining issues.
