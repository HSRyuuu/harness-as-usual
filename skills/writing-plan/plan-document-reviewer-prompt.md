# Plan Document Reviewer Prompt

Use this prompt after `writing-plan` has written or updated `plan.md`.

You are reviewing an AsUsual topic plan. Your job is to decide whether the plan is a complete, dependency-ordered execution contract that a separate executor can follow without chat memory. This is the last review gate before implementation. Do not implement the plan.

## Inputs

- Active topic `topic.md`
- Active topic `audit.jsonl`
- `requirements.md`
- All answered `question-cN.md` files in cycle order
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
| Decision contract clarity | Classification, parser, dispatch, logging, state transition, retry/idempotency, and malformed/unknown-input behavior are precise enough for executor and tests to agree. Use ordered decision tables, allowed values, token sets, or examples when prose would leave edge cases open. |
| Dependency ordering | `Dependency Analysis` and `Ordering Rationale` identify prerequisites, interfaces, produced artifacts, migrations, and verification dependencies, and the task order follows them. |
| No placeholders | No `TBD`, unexplained `TODO`, `<...>` placeholder, "handle edge cases" without scope, or "similar to Task N" stand-in remains. |
| File surface | Each task names concrete files/areas to create or modify. |
| Interface consistency | Every later-task `Consumes` name matches an earlier-task `Produces` name; types, signatures, and identifiers agree across tasks. |
| Execution mode fit | `Execution Design` chooses `inline`, `subagent-driven`, or `mixed`; task-level execution modes are compatible with task boundaries and host fallback notes. Subagent-driven tasks have bounded context that can be handed to a fresh implementer. |
| Execution surface | If the plan introduces or changes an execution entrypoint, external dependency, time-based behavior, state changes outside the normal request/response path, or runtime metadata/resource dependency, `Execution Surface` specifies invocation, required configuration/inputs, external dependencies, test environment/resource setup, time control when applicable, success/failure signals, idempotency/retry behavior, and metadata/config/annotation/route verification when relevant. If none apply, the section explicitly says `None`. |
| Safety gate coverage | Each task has a `Safety` section. High-risk operations are explicit, reversibility is classified, separate approval is required for high-risk operations, and rollback/recovery notes are concrete. Local/test-only reversible schema-like code changes are not over-classified as high risk unless production/shared data, destructive migration, data migration, or data deletion is involved. |
| Test strategy fit | Each task uses `tdd`, or has a human-approved `approved-tdd-exception` with category `throwaway-prototype`, `generated-code`, or `configuration`. `tdd` tasks include RED/GREEN/refactor evidence requirements. Exception tasks include the approval source and concrete verification or review evidence. A task that claims testing is impractical must show that the plan first considered a simpler API, interface boundary, dependency injection, or smaller testable unit. |
| Verification evidence mapping | Each task names a `Test target` and the evidence execution should record through `verification.recorded` or `task.completed` events, including RED/GREEN evidence when applicable. |
| Source traceability | Initial request comes from `topic.md#Initial Request` and `topic.created`; user decisions trace to answered question files or `decision.recorded` events. |
| Approval quality | High-risk work has planned approval points so execution can record `approval.high_risk` events with operation description, approver, and rollback. |
| Verification surface | Each task's `Verification` has a runnable command and an expected result, not just a description. |
| Execution task index | `Execution Task Index` exists, each row maps 1:1 to a detailed `## Task N: <name>` section, task names match exactly, and the row summaries are consistent with each task's outcome, dependencies, edit surface, gates, and verification. It has no checkboxes, status fields, completion marks, or progress notes. |
| Executor readiness | A separate executor can implement the tasks in order from `plan.md` alone, without chat memory and without editing the plan to track progress. |
| Policy restraint | The plan does not decide test, CI, commit, PR, release, or deploy policy beyond what the requirements/plan already decided. Verification commands that are part of task success checks are allowed. |
| Progress-ledger restraint | Task identity is the `## Task N: <name>` heading. The plan does not use per-task status fields as a progress ledger. |
| Single-plan scope | One topic produces one `plan.md`. The plan does not tell the reader to split the topic into multiple plan files. |
| User-language readability | User-facing plan prose follows the user's current or clearly preferred language, while canonical headings and technical identifiers stay stable. |
| User-language consistency | Canonical headings, task headings, status values, mode values, risk values, file paths, commands, and code identifiers may stay canonical. User-facing prose, section-internal helper labels, none/N/A values, rollback notes, expected-result descriptions, review notes, findings, actions, and check result values should follow the user's preferred language. |
| YAGNI | The plan does not add tasks or process beyond the requirements scope. |

## Calibration

Only block completion for issues that would cause a flawed or non-executable implementation.

Do not block for style preferences, minor wording, or a section being concise when it is still clear and executable.

## Reviewer Actions

If an issue is fixable from existing topic artifacts, fix `plan.md` and rerun the relevant checks.

If the issue reveals a material decision that could change scope, requirements, risk, implementation strategy, acceptance criteria, or verification policy, ask a focused chat clarification when it can be resolved in the current turn, record the answer in `audit.jsonl`, then update `plan.md` and rerun the relevant checks. Return to `define-requirements` when the answer changes the approved requirements or requires a durable multi-question decision cycle or topic-boundary change.

## Output Format

Record the review result in the existing `## Review Status` area of `plan.md`. Do not create a separate review block; write into the template's `Review Status` structure.
Use markdown checkboxes for `Plan Review Checks`: `[x]` for passed checks and `[ ]` for checks that remain failed or blocked.
Blocking checks must cite concrete evidence (file/section/quote or concrete reason); Advisory checks may use a short localized pass note. The `evidence:` label shown in the example below may stay canonical English or be consistently translated into the user's language; the check names, `[x]`/`[ ]` markers, and status values stay canonical.

```markdown
## Review Status

- Status: plan-complete | blocked
- Reviewed At: <timestamp>
- Reviewer Result: passed | issues-fixed | blocked
- Review Notes: <one line in the user's language>

### Plan Review Checks

#### Blocking

- [x] Requirements coverage — evidence: <file/section/quote or concrete reason>
- [x] Requirements-plan consistency — evidence: <file/section/quote or concrete reason>
- [x] Acceptance criteria matrix — evidence: <file/section/quote or concrete reason>
- [x] Decision contract clarity — evidence: <file/section/quote or concrete reason>
- [x] Dependency ordering — evidence: <file/section/quote or concrete reason>
- [x] No placeholders — evidence: <file/section/quote or concrete reason>
- [x] File surface — evidence: <file/section/quote or concrete reason>
- [x] Interface consistency — evidence: <file/section/quote or concrete reason>
- [x] Execution surface — evidence: <file/section/quote or concrete reason>
- [x] Safety gate coverage — evidence: <file/section/quote or concrete reason>
- [x] Test strategy fit — evidence: <file/section/quote or concrete reason>
- [x] Verification evidence mapping — evidence: <file/section/quote or concrete reason>
- [x] Verification surface — evidence: <file/section/quote or concrete reason>
- [x] Executor readiness — evidence: <file/section/quote or concrete reason>
- [x] Policy restraint — evidence: <file/section/quote or concrete reason>

#### Advisory

- [x] Execution mode fit: <localized pass>
- [x] Source traceability: <localized pass>
- [x] Approval quality: <localized pass>
- [x] Execution task index: <localized pass>
- [x] Progress-ledger restraint: <localized pass>
- [x] Single-plan scope: <localized pass>
- [x] User-language readability: <localized pass>
- [x] User-language consistency: <localized pass>
- [x] YAGNI: <localized pass>

### Plan Review Findings

- <finding or user-language none value>

### Plan Review Actions Taken

- <fix, clarification, or user-language none value>
```

Set `Status` and `Reviewer Result` together: `passed` or `issues-fixed` map to `Status: plan-complete`; a remaining blocking issue maps to `Status: blocked` and `Reviewer Result: blocked`.
