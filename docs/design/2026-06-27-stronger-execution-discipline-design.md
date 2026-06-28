# Stronger Execution Discipline Design

## Purpose

This design defines how AsUsual should strengthen plan execution by adopting
the most relevant parts of the Superpowers execution model: stronger TDD,
sequential subagent-driven task execution, task-level early review, finding
disposition, and route-back to requirements or plan when execution reveals a
bad assumption.

The current runtime already moved from a spec-centered workflow to a
requirements-centered, audit-first workflow:

- `question-cN.md`
- `requirements.md`
- `plan.md`
- `topic.md`
- `audit.jsonl`

The audit-first runtime model is already implemented: `state.json` is removed,
`audit.jsonl` is the machine-readable event source, `topic.md` is the
human-readable topic record, and `scripts/topic-log.py status --json` derives
current phase, next action, blockers, approvals, task evidence, review state,
and artifacts. That audit-first model is not the product goal by itself; it is
the supporting recording and resume architecture needed to make stronger
execution discipline durable and resumable.

## Design Goals

- Add Superpowers-style sequential task execution with implementer, requirements
  review, quality review, finding disposition, and no next-task progression
  while blocking findings remain.
- Strengthen TDD so behavior/API/domain logic, bugfix, and refactor tasks use
  strict RED/GREEN evidence unless the plan records a justified exception.
- Support `subagent-driven` execution without making subagent execution
  parallel or uncontrolled.
- Keep final execution review mandatory even when each task has early review.
- Preserve user control over requirements, risk, execution, review, and git
  actions.
- Keep `requirements.md` as the single requirements source for `plan.md`.
- Keep commit, push, PR, release, and deploy actions explicit and post-finalize.
- Use `topic-log.py` status derivation plus the audit tail to make the stronger
  execution loop resumable without `state.json`.

## Non-Goals

- Do not make audit-first runtime the primary feature of this design; it is the
  supporting recording model for stronger execution.
- Do not keep backward compatibility with `state.json`.
- Do not introduce a renamed `state.json` such as `snapshot.json`.
- Do not make `topic.md` a mutable state board with current gate or next action
  fields.
- Do not dispatch multiple implementation subagents in parallel.
- Do not let task-level early review replace final `review-execution`.
- Do not adopt Superpowers task-level commit behavior; git actions remain
  AsUsual-controlled after finalization.
- Do not use a flat `execution/task-N-*.md` layout for task evidence; each task
  gets its own subdirectory so larger plans remain navigable.

## Supporting Audit-First Artifact Layout

The execution discipline relies on the following audit-first topic layout:

```text
.as-usual/
└── topic/
    └── yyyy-MM-dd-<topic>/
        ├── topic.md
        ├── audit.jsonl
        ├── question-c1.md
        ├── question-c2.md
        ├── requirements.md
        ├── plan.md
        ├── execution/
        │   └── task-1/
        │       ├── brief.md
        │       ├── implementer-report.md
        │       ├── requirements-review.md
        │       ├── quality-review.md
        │       └── disposition.md
        ├── code-review-report.md
        └── report.md
```

### `topic.md`

`topic.md` is the human-readable topic record.

It stores:

- initial user request,
- important user decisions,
- topic-level notes,
- changes in user intent,
- major risks or constraints worth preserving for human readers,
- links to core artifacts.

It does not store:

- current gate,
- current phase,
- next action,
- task progress,
- computed status.

Those are derived from `audit.jsonl`.

### `execution/`

`execution/` stores task-level evidence. Each task gets a directory:

```text
execution/
└── task-1/
    ├── brief.md
    ├── implementer-report.md
    ├── requirements-review.md
    ├── quality-review.md
    └── disposition.md
```

The directory name uses the stable plan task number. If a task is renamed during
plan revision, the task directory remains tied to the task number and the audit
event records the updated task heading.

### `code-review-report.md` And `report.md`

`code-review-report.md` is created by final `review-execution` only when that
review records findings. It is the topic-level review report and does not
replace task-level early review files.

`report.md` is created during `finalize`. It is the final user-facing handoff
summary: implemented changes, important decisions, verification evidence,
task-level and final review outcome, code cleanup decision, remaining issues, and
post-finalize git action status. It does not replace `topic.md` or
`audit.jsonl`.

### `audit.jsonl`

`audit.jsonl` is the only machine-readable runtime source of truth.

It stores append-only events for:

- topic creation,
- question file creation and answer validation,
- requirements completion,
- plan writing and approval,
- execution approval,
- high-risk operation approval or block,
- task starts,
- TDD RED/GREEN evidence,
- implementation reports,
- verification results,
- task-level requirements review,
- task-level quality review,
- findings and dispositions,
- final sweeps,
- execution completion,
- final execution review,
- code cleanup decisions,
- finalization,
- selected post-finalize git actions.

## Resume Model

Resume is based on `audit.jsonl`, not `state.json`. This matters for execution
discipline because task review loops may stop between tasks, between review and
disposition, or after a route-back decision.

When resuming an active topic, the agent should:

1. Read `topic.md` for human context and durable decisions.
2. Read `audit.jsonl`.
3. Run `scripts/topic-log.py status --topic-dir <topic-dir> --json`.
4. Use the derived phase, next action, blockers, approvals, artifacts,
   verification, task review evidence, and sweeps as the current machine state.
5. Read the linked artifacts needed for that action.
6. Continue through the appropriate runtime skill.

The derived status is an acceleration point, not a replacement for evidence.
When a decision is sensitive, the agent still reads the relevant audit events
and linked artifacts before acting.

## Runtime Flow Context

The macro workflow remains:

```text
start-work
-> define-requirements
-> writing-plan
-> executing-plan
-> review-execution
-> finalize
-> git-action
```

The stronger execution work mainly changes `executing-plan`; the rest of the
macro workflow exists to keep requirements, plan approval, final review,
finalization, and git action approval intact.

## Superpowers-Style Execution Loop

`executing-plan` should support two execution modes:

- `inline`
- `subagent-driven`

The task contract should be the same for both modes.

### Execution Mode Selection

`plan.md` should include an `Execution Mode` entry in `Execution Design`.

Allowed values:

- `inline`
- `subagent-driven`
- `mixed`

The plan proposes the mode based on task independence, host support, and review
needs. The user's execution approval confirms or overrides that mode. If the
plan proposes `subagent-driven` but the host lacks subagent support, execution
must either fall back to `inline` with an audit event explaining the fallback or
stop for user confirmation when the quality/risk tradeoff is material.

For `mixed`, each task records its planned mode in the task brief. Use
`subagent-driven` only for tasks with enough context isolation to hand to a
fresh implementer. Tightly coupled or high-risk tasks can remain `inline` while
still using the same early review gates.

For each `## Task N` in `plan.md`:

1. Create `execution/task-N/brief.md`.
2. Start the task and append `task.started`.
3. If using `subagent-driven`, dispatch one fresh implementer subagent with the
   task brief and required context.
4. Enforce the task's TDD/test strategy.
5. Record implementation output in `execution/task-N/implementer-report.md`.
6. Run the task verification command.
7. Append verification events and evidence links.
8. Run requirements compliance review.
9. Run code quality review.
10. If findings exist, record them.
11. Resolve each required finding through fix, rejection with reason,
    user-accepted risk, block, or route-back.
12. Re-review after fixes when needed.
13. Record `execution/task-N/disposition.md`.
14. Append `task.completed`.
15. Append task review/fix/sweep evidence before moving to the next task when applicable.

The controller must not start Task N+1 while Task N has unresolved Critical or
Important findings, unresolved route-back decisions, missing required TDD
evidence, or missing verification evidence.

### Review Order

Task-level review order follows the Superpowers pattern:

1. Requirements compliance review.
2. Code quality review.

Code quality review starts only after requirements compliance passes or all
requirements findings have a valid disposition.

### Subagent Rules

- Use one implementation subagent per task.
- Do not dispatch multiple implementation subagents in parallel.
- Do not make subagents read the whole conversation history.
- Give each subagent a task brief, relevant requirements, relevant plan task,
  and exact files or context.
- If a subagent asks for context, the controller answers or redispatches with
  more context.
- If a subagent is blocked because the plan is wrong, route back to
  `writing-plan` or `define-requirements`.

## Stronger TDD Rules

Plan tasks should use the strongest realistic test mode.

`strict-tdd` should be the default for:

- backend/domain behavior,
- API contract behavior,
- parser or transformer behavior,
- bug fixes with reproducible failure,
- refactors that can be protected by automated behavior tests.

`strict-tdd` requires:

- RED test command,
- expected RED failure,
- GREEN verification command,
- expected GREEN pass,
- refactor check,
- evidence to record.

Execution must not write production implementation for a `strict-tdd` task
before RED evidence is recorded through `task_tdd_red_recorded`.

Execution must not mark a `strict-tdd` task complete before GREEN evidence is
recorded through `task_tdd_green_recorded`.

When a task uses `verification-only` or `manual-qa`, the plan must include a
`TDD Exception Reason` explaining why stricter test-first execution is not
realistic for that task.

TDD violations are task-level early review findings.

## Finding Disposition Model

Task findings should record:

- finding id,
- task,
- reviewer type,
- severity,
- summary,
- evidence,
- affected artifact or file,
- recommended action.

Severity:

- `critical`: blocks task completion and next task progression.
- `important`: blocks next task progression unless fixed, technically
  rejected, blocked, or explicitly accepted by the user.
- `minor`: may proceed after recording, unless the plan or reviewer marks it as
  blocking.

Disposition:

- `fixed`: the implementation or artifact was changed and the relevant review
  passed after re-review.
- `rejected-with-reason`: the controller rejects the finding as technically
  incorrect or not applicable, with evidence. Use this only when the finding
  itself is wrong or outside the approved scope.
- `user-accepted-risk`: the finding is valid, but the user explicitly accepts
  the remaining risk. Use this for Important findings that the user chooses not
  to fix before proceeding.
- `blocked`: work cannot proceed until external input, environment, dependency,
  or user decision changes.
- `routed-to-plan`: the finding changes task order, file surface, interfaces,
  test strategy, or execution policy and must be handled by `writing-plan`.
- `routed-to-requirements`: the finding changes requirements, acceptance
  criteria, risk, or topic boundary and must be handled by
  `define-requirements`.

If a finding changes requirements, acceptance criteria, risk, or topic boundary,
route to `define-requirements`.

If a finding changes task order, file surface, interfaces, test strategy, or
execution policy, route to `writing-plan`.

## Audit Event Families

Initial event families:

```text
topic.created
note.recorded
decision.recorded
question.created
question.answered
artifact.recorded
requirements.completed
plan.completed
approval.execution
approval.high_risk
task.started
task.dispatched
task.review_completed
task.fix_requested
task.fix_completed
task.commit_recorded
task.completed
verification.recorded
sweep.completed
execution.completed
review.completed
code_cleanup.skipped
code_cleanup.completed
topic.finalized
git_action.selected
blocker.recorded
blocker.resolved
```

Event schema should be strict enough to validate required fields but flexible
enough to avoid recreating a state object inside every event.

## Tooling

The audit-first runtime helper is:

```text
scripts/topic-log.py
```

Responsibilities:

- initialize topic artifacts,
- append validated events,
- derive resume status from `audit.jsonl`,
- validate audit schema,
- validate required artifact existence,
- record task dispatch, task review, task fix, task commit, and sweep evidence.

It should not maintain a separate state file.

## Runtime Surface Changes

The rewrite affects:

- `as-usual-rules/core-workflow.md`
- `skills/using-as-usual/SKILL.md`
- `skills/start-work/SKILL.md`
- `skills/define-requirements/SKILL.md`
- `skills/writing-plan/SKILL.md`
- `skills/executing-plan/SKILL.md`
- `skills/review-execution/SKILL.md`
- `skills/cleanup-code/SKILL.md`
- `skills/finalize/SKILL.md`
- `skills/git-action/SKILL.md`
- `templates/question.md`
- `templates/requirements.md`
- `templates/plan.md`
- `templates/report.md`
- new `templates/topic.md`
- delete `templates/state.json`
- delete `scripts/state-machine.py`
- add `scripts/topic-log.py`
- hook payload and active topic detection
- sandbox E2E tests
- runtime workflow consistency verification
- runtime surface verification
- harness verification
- project identity verification
- maintainer docs and public docs

## Migration Strategy

This is a breaking rewrite. Do not maintain compatibility with existing
`state.json` topics.

Implementation should happen in this order:

1. Audit-first foundation: completed by the current runtime branch.
2. Define the stronger execution contract in `plan.md`: execution mode, TDD
   exception reason, task review policy, and task evidence requirements.
3. Extend `topic-log.py` with task dispatch/review/fix/commit/sweep events.
4. Rewrite `executing-plan` around the Superpowers-style task loop while
   keeping the main agent as controller.
5. Add task implementer, requirements reviewer, and quality reviewer prompt
   files.
6. Update core workflow, plan template, writing-plan, and reviewer checks.
7. Update sandbox E2E and verification skills.
8. Update durable docs and project identity when public behavior changes.
9. Sync `.agents/skills` to `.claude/skills` if maintainer skills changed.

## Self Review

### Placeholder Scan

Pass. No placeholder fields, TODO markers, or incomplete sections remain.

### Internal Consistency

Pass. The design consistently treats stronger execution discipline as the main
feature and audit-first artifacts as the supporting recording and resume model.
It uses `requirements.md` as the requirements source, `plan.md` as the execution
contract, `topic.md` as the human record, and `audit.jsonl` as the
machine-readable event source.

### Scope Check

Pass. The design is one coherent breaking rewrite. It is large, but it is not a
bundle of unrelated subsystems; stronger TDD, subagent-driven execution,
task-level early review, finding disposition, audit evidence, and derived-status
resume are coupled by the same execution-discipline model.

### Ambiguity Check

Pass. The helper direction is decided and implemented: `scripts/state-machine.py`
is deleted and replaced with `scripts/topic-log.py`; stronger execution uses
dotted audit event names and derived status rather than a mutable state object.
