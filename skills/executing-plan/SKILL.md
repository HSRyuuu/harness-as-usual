---
name: executing-plan
description: Use when AsUsual is active, requirements.md and plan.md are current, and the user explicitly approves or requests execution of the plan.
---

# Executing Plan

This skill handles the AsUsual `executing-plan` workflow step. It executes a reviewed `plan.md` task by task, either inline or with bounded fresh subagents when the plan and host support that mode, and records progress, approvals, task review loops, blockers, and verification as audit events. It does not treat `plan.md` as a progress ledger.

For machine-readable audit records, use `executing` as the phase value. Do not write `executing-plan` into `audit.jsonl.phase`.

Use it only after `using-as-usual` has completed activation and first reads, `writing-plan` has produced a reviewed `plan.md`, and the user explicitly approves or requests execution.

The main agent remains the execution controller in every mode. Subagents may implement or review bounded tasks, but the controller owns task order, audit events, independent verification, and user-facing completion claims.

## Responsibility Boundary

| Skill | Responsibility |
| --- | --- |
| `writing-plan` | Produce one reviewed execution contract and stop at `plan-review` |
| `executing-plan` | Critically review the reviewed plan, execute tasks in order, and record progress, task review loops, and verification |
| `review-execution` | Review completed execution and changed code before finalization |

`executing-plan` does not write `requirements.md` or `plan.md`, and does not author new plans. If the plan must change, it returns to the owning phase.

File-backed `[Answer]:` fields are mandatory for `define-requirements` question cycles only. During execution, pause and ask focused chat clarifications when a missing decision can be resolved in the current turn; record the answer in `audit.jsonl` before continuing or routing back to `writing-plan`/`define-requirements`.

## Preconditions

Before executing, confirm:

- The Execute Rules in `core-workflow.md` have been checked.
- `topic.md` and `audit.jsonl` identify the current topic.
- `requirements.md` exists and is the basis of the plan.
- `plan.md` exists as the completed execution contract with dependency-ordered `## Task N` sections.
- When the plan has 4 or more tasks, `plan.md` includes `Execution Task Index` as a navigation summary that maps 1:1 to the detailed `## Task N` sections; smaller plans may omit it.
- `plan.md` declares an `Execution Mode` of `inline`, `subagent-driven`, or `mixed`, plus task-level execution modes when `mixed`.
- The user explicitly approved or requested execution in the current turn.

## Inputs

Read and use these sources in this order, from disk, before editing any implementation:

1. `topic.md`
2. `audit.jsonl`
3. Derived status from `scripts/topic-log.py status --json`, when available
4. `requirements.md`
5. `plan.md`

## Hard Gates

- Do not execute from a stale, incomplete, or internally inconsistent plan.
- Do not use subagent-driven execution unless the plan marks the mode and the host can dispatch fresh bounded subagents. If the plan requests subagents but the host cannot provide them, follow the plan's fallback or stop for user confirmation when the quality/risk tradeoff is material.
- Do not run high-risk operations without a matching plan Safety entry and fresh explicit user approval immediately before the operation.
- Completion judgment follows `as-usual-rules/completion-rules.md`: verification evidence by surface, `INCONCLUSIVE` handling, subagent `DONE` treated as a claim until controller-verified, and the completion claim gate.
- Do not mark a `test-required` task complete without a test target and passing-test evidence. For a bug fix, also require regression RED evidence (a failing test that reproduces the bug before the fix).
- Do not mark a `no-test` task complete without a recorded reason. `no-test` is only for genuinely untestable work (configuration, generated code, throwaway prototype); it needs no user approval but is not an escape hatch for awkward-to-test code.
- Do not skip `review-execution` after successful execution completion.

## Preferences

- Prefer the existing codebase's naming, formatting, test, and error-handling patterns.
- Prefer making the task boundary testable over choosing `no-test`.
- Prefer the planned verification command over ad hoc substitutes unless the plan is revised.
- Prefer subagent-driven execution for isolated, bounded tasks when the host supports it; use inline for tightly coupled or context-heavy tasks.
- Prefer stopping and routing back to the owning phase over improvising scope.

## Workflow

### Step 1: Critically Review The Plan

1. Re-read `topic.md`, `audit.jsonl`, `requirements.md`, and `plan.md` from disk.
2. Confirm the user's latest request still matches the plan.
3. Review the plan critically before touching implementation.

Stop before executing and record the gap through `scripts/topic-log.py blocker` or `note` when any of these is true:

- A task is missing a dependency note, file/area, interface, test strategy, step, or verification.
- The plan has 4 or more tasks but no `Execution Task Index`, or a present index uses checkboxes/status/progress notes, has rows that do not map 1:1 to detailed `## Task N: <name>` sections, or contradicts any detailed task section.
- The plan lacks `Execution Mode`, or a `mixed` plan lacks task-level execution modes.
- The plan introduces or changes an execution entrypoint, external dependency, time-based behavior, state changes outside the normal request/response path, or runtime metadata/resource dependency, but has no `Execution Surface` section or lacks a sufficient contract for invocation, required configuration/inputs, external dependencies, test environment/resource setup, time control when applicable, success/failure signals, or idempotency/retry behavior.
- A task is missing Safety fields: risk level, high-risk operations, reversibility, separate approval, or rollback/recovery notes.
- A task uses anything other than `test-required` or `no-test`.
- A `no-test` task lacks a concrete reason, or is used for testable code that was merely awkward to test.
- A high-risk operation is present but `Separate Approval Required` is not `yes`.
- A `Consumes` name has no matching `Produces` in an earlier task.
- The plan contradicts `requirements.md` or the latest request.
- The plan is stale relative to the current request.

If the gap is fixable from current artifacts, return to `writing-plan` for plan revision. If fixing it requires a new material user decision that can be resolved in the current turn, ask the user in chat, record the answer in `audit.jsonl`, then return to `writing-plan` or `define-requirements` as needed. Use `define-requirements` only for a durable multi-question decision cycle or topic-boundary change. When the plan changes in response, return to this step before resuming.

### Step 2: Select Execution Mode And Execute Tasks In Order

Before the first task, record that execution was approved from the current user turn with `approve-execution`. Then record task progress and verification only through audit events.

#### Recording Execution Approval (Required)

Use `scripts/topic-log.py approve-execution` when the user approves plan execution:

```bash
python3 <plugin-root>/scripts/topic-log.py approve-execution \
  --topic-dir .as-usual/topic/2026-06-24-task-priority \
  --approved-by user \
  --source "current user turn" \
  --actor user
```

Use `--actor user` for the approval event. Do not use the generic actor value `agent`.

#### User Approval Request Format

When execution needs fresh approval or a material user decision, ask with a compact terminal-readable block instead of one long paragraph. Use the user's current language for labels and prose, but keep exact paths, dependency coordinates, commands, and code identifiers unchanged.

Recommended shape:

```text
Approval request
- Task: Task N - <name>
- Action: <specific change or command needing approval>
- Reason: <why this is needed now>
- Scope: <files/resources touched>
- Impact: <test-only/runtime/production impact and risk level>
- Rollback: <exact way to undo or recover>
- Next: Reply with approval to continue, or tell me what to change.
```

For a test-only dependency, explicitly say that it is test scoped, whether production code or production data is affected, and the single line or file change needed to revert it.

#### Execution Mode

Use the mode approved in `plan.md`:

- `inline`: the controller implements each task in the current session.
- `subagent-driven`: the controller dispatches one fresh bounded implementer for each task, then runs one task-level review before moving on.
- `mixed`: each task declares `inherit`, `inline`, or `subagent-driven`; `inherit` uses the plan-level mode.

For subagent-driven tasks:

1. Use `implementer-prompt.md` from this skill directory as the implementer prompt. Fill it with only the task brief, relevant `requirements.md` excerpts, relevant `plan.md` task text, specific files/areas, and expected verification. Do not ask a subagent to read the whole conversation history.
2. Record the dispatch with `scripts/topic-log.py dispatch-task`.
3. If the subagent asks for context, answer or redispatch with more context; record material context decisions in `audit.jsonl`.
4. If the subagent returns `BLOCKED`, decide whether more context, a stronger model, task split, plan revision, or user input is required. Record the blocker or route-back before continuing.
5. The controller must inspect the resulting diff/evidence and run or confirm verification before recording task completion.

Example dispatch record:

```bash
python3 <plugin-root>/scripts/topic-log.py dispatch-task \
  --topic-dir <topic-dir> \
  --task "Task N: <name>" \
  --mode subagent-driven \
  --role implementer \
  --context "requirements.md,plan.md#Task-N,<relevant-file>" \
  --summary "Dispatched a fresh implementer for Task N with bounded context."
```

#### Recording High-Risk Operation Approval (Required)

For every high-risk operation that has fresh approval, use `approve-high-risk` before editing:

```bash
python3 <plugin-root>/scripts/topic-log.py approve-high-risk \
  --topic-dir .as-usual/topic/2026-06-24-task-priority \
  --operation-id "db-task-priority" \
  --description "Add persisted non-null Task.priority enum field and API/frontend priority contract" \
  --rollback "Revert backend task files, frontend task files, and TaskControllerTest changes; roll back tasks.priority in any persistent database according to DB migration policy" \
  --approved-by user \
  --actor user
```

Use `--actor user` for the approval event. Do not use the generic actor value `agent`.

Example — good compact high-risk approval block:

- 요청 작업: `npm install zod`
- 이유: Task 3 입력 검증에 사용
- 범위/파일: package.json, package-lock.json
- 위험/영향: 의존성 추가 (dependency change, high-risk)
- 롤백: 두 파일 git revert
- 필요한 선택: 이 설치를 승인하시겠습니까? (yes/no)

When the plan includes `Execution Task Index`, use it to orient task order, gates, and verification at a glance. Before starting or dispatching a task, read the full detailed `## Task N: <name>` section and treat that detailed task section as the execution contract. If the index and detailed task disagree, stop and return to `writing-plan`; do not choose one silently.

For each `## Task N` in plan order:

1. Record task start:

```bash
python3 <plugin-root>/scripts/topic-log.py audit \
  --topic-dir <topic-dir> \
  --event task.started \
  --actor codex \
  --phase executing \
  --next-action execute \
  --summary "Started Task N: <name>."
```

2. Determine the task mode from the task's `Execution Mode` section and the plan-level fallback.
3. Inspect nearby files for naming, formatting, error handling, testing, and integration style before editing or dispatching, then follow the surrounding project conventions.
4. If the task includes a high-risk operation, stop immediately before that operation and ask for fresh user approval using the approval request format above. Include the exact operation, target files/resources, reversibility, and rollback/recovery notes. Do not proceed until the approval is explicit in the current turn. Use `approve-high-risk` (above) to append `approval.high_risk`. If approval is denied or unclear, record a blocker and stop.
5. Follow the task's steps exactly. The plan is the contract; do not improvise scope.
6. Follow the task's `Test Strategy`.
   - For `test-required`, deliver passing tests that cover the task's behavior and record the passing-test evidence. For a **bug fix**, first write a regression test that fails against the current code (record that RED evidence), then implement the fix and record it passing (GREEN). Test-first behavior-by-behavior RED/GREEN is a good default technique, but for non-bug-fix work the required record is the passing test plus behavior coverage, not a RED-before-code trace.
   - If you cannot see how to test a behavior, assume the boundary is too coupled or unclear before assuming it is untestable. Try a simpler API, interface boundary, dependency injection, smaller unit, or existing harness. Choose `no-test` only when the work is genuinely untestable.
   - For `no-test`, confirm the work is genuinely untestable (configuration, generated code, throwaway prototype), record the reason, then run the planned verification or review evidence. No user approval is required.
7. Run the task's `Verification` command and compare the result to its expected result.
8. Record the exact command and outcome with `scripts/topic-log.py verification --verdict PASS|FAIL|INCONCLUSIVE`, including regression RED/GREEN evidence for bug fixes in the summary or task completion event. Apply `INCONCLUSIVE` consequences and surface-appropriate evidence per `as-usual-rules/completion-rules.md`.
9. If using subagent-driven mode, run one task-level review with `task-reviewer-prompt.md`. It covers requirements fit and quality/safety in a single pass. Review details go in `execute/task-<N>-review.md` with YAML frontmatter `task`, `verdict`, and `reviewedAt`.
10. Treat reviewer responses as receipts. The receipt status must be one of `passed | findings | blocked` and must match the review file frontmatter `verdict` and the `record-task-review --status` value. If the receipt status is outside the closed vocabulary or does not match frontmatter, invalidate the result, record a note, and request the review again. Include the review file in `record-task-review --artifacts`.
11. When review status is `findings` or `blocked` and any finding count is nonzero, include stable `--finding-ids` so fixes can resolve the findings.
12. If the task review finds issues, record `record-task-fix --status requested`, fix or redispatch the fix, record `record-task-fix --status completed --finding-id <id>`, then rerun the task review. Do not start Task N+1 while Critical or Important task findings remain unresolved. `complete-execution` fails when unresolved task findings remain in derived status.
13. If verification cannot be run, record the reason and the remaining work.
14. Use `scripts/topic-log.py complete-task --topic-dir <topic-dir> --task "Task N: <name>" --summary <summary> --mode test-required --test-target <target> --green-evidence <passing-test> --verification <verification-evidence> --result <result>` when a `test-required` task finishes; add `--red-evidence <regression-red>` for a bug fix. For untestable work, use `--mode no-test --no-test-reason <reason>` plus the planned verification or review evidence. Include changed artifacts with `--artifacts` when useful.
15. If a task-sized commit is created before finalization because the project/user explicitly wants commit boundaries during execution, record it with `record-task-commit`. Do not create commits merely because this skill is running; post-finalize git action remains the default AsUsual boundary.

Do not mutate `plan.md` to track progress. Progress lives in `audit.jsonl`. Edit `plan.md` only when the user explicitly asks for a plan revision, in which case return to `writing-plan`.

### Step 3: Stop Conditions

Stop and report, after recording an audit event, when:

- A blocker appears (missing dependency, failing setup, unclear instruction).
- A high-risk operation lacks explicit current-turn approval, rollback/recovery notes, or a matching plan Safety entry.
- The same verification or repair loop fails 3 times. Then follow the Failure Handling circuit breaker in `as-usual-rules/routing-rules.md` and record the command attempted, failure pattern, suspected cause, whether the requirements/plan/environment/assumptions may be wrong, and the next recommended phase.
- Implementation reveals a new user decision that could change requirements, plan, implementation, risk, or verification. Pause implementation, ask a focused chat clarification when it can be resolved in the current turn, record the answer in `audit.jsonl`, and return to `writing-plan` or `define-requirements` if artifacts must change. Use `define-requirements` only for a durable multi-question decision cycle or topic-boundary change.
- A requirements/plan contradiction appears. Return to the necessary earlier phase.

### Step 4: Execution Completion

Declare execution complete only after `audit.jsonl` records:

- completed work,
- verification performed, with exact commands and outcomes,
- task-level verification mappings in `task.completed` events when the plan has task test targets or regression RED/GREEN evidence,
- task dispatch/review/fix evidence when subagents or task-level review loops were used,
- final sweep evidence for stale references, mirror checks, or consistency scans required by the plan,
- verification skipped and why,
- troubleshooting,
- remaining issues.

Use `record-sweep` for final consistency evidence:

```bash
python3 <plugin-root>/scripts/topic-log.py record-sweep \
  --topic-dir <topic-dir> \
  --kind final \
  --command "<command>" \
  --result "<exact result and expected exit code>" \
  --summary "Final execution sweep completed."
```

After recording execution completion, prefer the `complete-execution` macro:

```bash
python3 <plugin-root>/scripts/topic-log.py complete-execution \
  --topic-dir .as-usual/topic/2026-06-24-task-priority \
  --summary "Execution completed; verification evidence and remaining issues are recorded." \
  --actor codex
```

If the host is Claude Code, use `--actor claude`.

The macro records:

1. An `execution.completed` event.
2. Derived phase `execution-complete`.
3. Derived next action `review-execution`.
4. Then invoke `review-execution` in the same turn.

Do not automatically enter commit, PR, release, deploy, or retrospective behavior; those remain outside this skill unless the topic explicitly decided them.

## Topic Log Commands

Execution progress, task starts, task completion, verification commands, blockers, and approvals are audit events. Do not update `topic.md` for high-churn execution progress. Use `scripts/topic-log.py` macros:

- `approve-execution`
- `approve-high-risk`
- `complete-task`
- `dispatch-task`
- `record-task-review`
- `record-task-fix`
- `record-task-commit`
- `record-sweep`
- `verification`
- `blocker`
- `complete-execution`

Prefer macro commands when they match the transition. Do not hand-edit `audit.jsonl`; if the helper cannot express an unusual transition, stop and report the missing helper capability.

## Long-Term Memory Capture

If the user states an explicit long-term rule during this phase ("always X", "in this
project always Y"), do not break the current flow and do not write memory now. Capture
it only as an audit candidate:

```bash
python3 <plugin-root>/scripts/topic-log.py record-memory-candidate \
  --topic-dir <topic-dir> --summary "<rule>" --source-phase executing --proposed-target memory
```

The actual review/approval/write happens later via `manage-self-improvement` at finalize.

## Anti-Patterns

- Executing without explicit user approval.
- Starting execution without recording the current-turn execution approval in `audit.jsonl`.
- Running a high-risk operation because it appears in `plan.md` but without fresh explicit approval immediately before the operation.
- Ignoring nearby project style, naming, test, and error-handling conventions.
- Skipping the critical plan review and starting on a plan with gaps.
- Using `plan.md` as a per-step progress ledger.
- Continuing past a blocker, repeated verification failure, or new material user decision without recording the stop and next phase.
- Continuing after a chat clarification without recording the answer in `audit.jsonl` and updating affected artifacts first.
- Declaring completion without verification evidence or an explicit "not verified because ..." record.
- Stopping after successful execution without invoking `review-execution`.
- Letting subagent output replace controller verification.
- Starting Task N+1 while Task N has unresolved task review findings.
- Treating "hard to test" as permission to choose `no-test` without first simplifying the boundary to make it testable.
- Entering commit, PR, release, deploy, or retrospective behavior the topic never decided.
