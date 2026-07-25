# Plan Quality Reference
What a good `plan.md` contains, and what the pre-approval critical review in
`write-plan` should be looking for. This is a **reference, not a checklist to
fill in** — the review is required (core rule 7), but its output is a better plan
plus one `review` event, never a review section inside `plan.md`.

You are reviewing an AsUsual topic plan. Your job is to decide whether the plan is a complete, dependency-ordered execution contract that a separate executor can follow without chat memory. This is the last review gate before implementation. Do not implement the plan.

## Inputs

- `contexts.md`
- `audit.jsonl`
- `requirements.md`
- Current `plan.md`
- `templates/plan.md`
- Relevant project files explicitly cited by the topic artifacts

## Review Checks

Blocking checks (must cite concrete evidence — file/section/quote or concrete reason — to pass): Requirements coverage, Requirements-plan consistency, Acceptance criteria matrix, Decision contract clarity, Dependency ordering, No placeholders, File surface, Interface consistency, Execution surface, Safety gate coverage, Test strategy fit, Verification evidence mapping, Verification surface, Executor readiness, Policy restraint. All other checks below are Advisory and may pass on a short localized note.

| Category | What To Check |
| --- | --- |
| Requirements coverage | Every acceptance criterion in `requirements.md` maps to at least one `## Task N` section. No required requirements behavior is missing from the plan. |
| Requirements-plan consistency | The plan does not silently replace, reinterpret, or contradict a mechanism described by `requirements.md`. If project inspection forces a different mechanism, the requirement, risk, or focused clarification has been recorded before plan completion. |
| Acceptance criteria matrix | `Acceptance Criteria Coverage Matrix` contains one row for every `AC<N>` in `requirements.md`, mapping it to task, test/review/manual evidence, and exact assertion or evidence. No row has an unresolved gap. |
| Decision contract clarity | Classification, parser, dispatch, logging, state transition, retry/idempotency, and malformed/unknown-input behavior are precise enough for executor and tests to agree. Use ordered decision tables, allowed values, token sets, or examples when prose would leave edge cases open. A missing `Decision Contracts` section while such behavior exists in the plan is a blocking defect; if no such behavior exists, the section is omitted. |
| Dependency ordering | `Dependency Analysis` and `Ordering Rationale` identify prerequisites, interfaces, produced artifacts, migrations, and verification dependencies, and the task order follows them. |
| No placeholders | No `TBD`, unexplained `TODO`, `<...>` placeholder, "handle edge cases" without scope, or "similar to Task N" stand-in remains. |
| File surface | Each task names concrete files/areas to create or modify. |
| Interface consistency | Every later-task `Consumes` name matches an earlier-task `Produces` name; types, signatures, and identifiers agree across tasks. |
| Execution mode fit | `Execution Design` chooses `inline`, `subagent-driven`, or `mixed`; task-level execution modes are compatible with task boundaries and host fallback notes. Subagent-driven tasks have bounded context that can be handed to a fresh implementer. |
| Execution surface | If the plan introduces or changes an execution entrypoint, external dependency, time-based behavior, state changes outside the normal request/response path, or runtime metadata/resource dependency, `Execution Surface` exists and specifies invocation, required configuration/inputs, external dependencies, test environment/resource setup, time control when applicable, success/failure signals, idempotency/retry behavior, and metadata/config/annotation/route verification when relevant. A missing section while any signal applies is a blocking defect. If none apply, the section is omitted. |
| Safety gate coverage | Each task has a `Safety` section. High-risk operations are explicit, reversibility is classified, separate approval is required for high-risk operations, and rollback/recovery notes are concrete. Local/test-only reversible schema-like code changes are not over-classified as high risk unless production/shared data, destructive migration, data migration, or data deletion is involved. |
| Test strategy fit | Each task uses `test-required`, or `no-test` with a concrete reason (configuration, generated code, or throwaway prototype). `test-required` tasks name a test target and passing-test evidence; bug-fix tasks also include regression RED evidence (a failing test reproducing the bug before the fix). A task that claims testing is impractical must show that the plan first considered a simpler API, interface boundary, dependency injection, or smaller testable unit before choosing `no-test`. |
| Verification evidence mapping | Each task names a `Test target` (or a `no-test` reason) and the evidence execution should record through `verification.recorded` or `task.completed` events, including regression RED evidence for bug fixes. |
| Source traceability | Initial request comes from the Initial Request section of `contexts.md`; user decisions trace to the Decisions section of `contexts.md` or recorded `decision` events. |
| Approval quality | High-risk work has planned approval points so execution can record `approval.high_risk` events with operation description, approver, and rollback. |
| Verification surface | Each task's `Verification` has a runnable command and an expected result, not just a description. |
| Execution task index | `Execution Task Index` exists when the plan has 4 or more tasks (smaller plans omit it). When present, each row maps 1:1 to a detailed `## Task N: <name>` section, task names match exactly, and the row summaries are consistent with each task's outcome, dependencies, edit surface, gates, and verification. It has no checkboxes, status fields, completion marks, or progress notes. |
| Executor readiness | A separate executor can implement the tasks in order from `plan.md` alone, without chat memory and without editing the plan to track progress. |
| Policy restraint | The plan does not decide test, CI, commit, PR, release, or deploy policy beyond what the requirements/plan already decided. Verification commands that are part of task success checks are allowed. |
| Progress-ledger restraint | Task identity is the `## Task N: <name>` heading. The plan does not use per-task status fields as a progress ledger. |
| Single-plan scope | One topic produces one `plan.md`. The plan does not tell the reader to split the topic into multiple plan files. |
| User-language readability | User-facing plan prose follows the user's current or clearly preferred language, while canonical headings and technical identifiers stay stable. |
| User-language consistency | Canonical headings, task headings, status values, mode values, risk values, file paths, commands, and code identifiers may stay canonical. User-facing prose, section-internal helper labels, none/N/A values, rollback notes, expected-result descriptions, review notes, findings, actions, and check result values should follow the user's preferred language. |
| YAGNI | The plan does not add tasks or process beyond the requirements scope. |

## Calibration

Worth fixing: anything that would make the implementation wrong or the plan
non-executable.

Not worth fixing: style preferences, minor wording, or a section being short when it
is still clear and executable.

## Using This Reference

When something here is wrong in `plan.md`, fix the plan — a better plan is the
point, not a list of findings. When the fix needs a decision only the user can
make, take that item through `gathering-context`, record it, update
`requirements.md` if it moved, then revise the plan.

Record one `review` event summarizing what you found and what you changed. Do not
write a review status block or checklist into `plan.md`.
