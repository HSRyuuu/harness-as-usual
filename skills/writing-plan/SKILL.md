---
name: writing-plan
description: Use when AsUsual is active, requirements.md is requirements-complete, and the user approves moving from requirements to plan or asks to write or update plan.md.
---

# Writing Plan

This skill handles the AsUsual `writing-plan` phase. It turns a completed `requirements.md`, derived topic status, and answered question files into one reviewable `plan.md` that a separate executor can follow without chat memory, then reviews that plan with the local reviewer prompt before asking the user to approve execution.

Use it only after `using-as-usual` has completed activation and first reads, and after either:

- `start-work` routes the topic to `plan`.
- The topic is `requirements-complete` and the user approves moving from requirements to plan.
- The user asks to write or update `plan.md` and the requirements are current.

## Responsibility Boundary

| Skill | Responsibility |
| --- | --- |
| `using-as-usual` | Identify activation, find or initialize the active topic, and perform first reads |
| `start-work` | Route the topic to the lightest sufficient gate |
| `define-requirements` | Write `requirements.md`, run requirements review, and stop at `requirements-complete` |
| `writing-plan` | Analyze dependencies, write `plan.md`, run plan review, and stop at `plan-review` |
| `executing-plan` | Execute the reviewed plan inline or subagent-driven as approved, while recording progress, review loops, and verification as audit events |

`writing-plan` does not execute work and does not write `requirements.md`. It produces one reviewed execution contract and stops before any implementation.

File-backed `[Answer]:` fields belong to the `define-requirements` file-cycle exception only; do not use them here. Follow Clarification Routing in `as-usual-rules/routing-rules.md` for any decision discovered here.

## Preconditions

Before writing the plan, confirm:

- The Plan Rules in `core-workflow.md` have been checked.
- The active topic folder is under `.as-usual/topic/yyyy-MM-dd-<topic>/`.
- `topic.md` and `audit.jsonl` exist.
- `requirements.md` exists.
- `python3 <plugin-root>/scripts/topic-log.py status --topic-dir <topic-dir> --json` shows `phase=requirements-complete` and `nextAction=approve-plan`, or `audit.jsonl` contains a successful `requirements.completed` event.
- The user explicitly approved moving from requirements to plan in the current turn, or asked to write or update the plan.
- The plan is based on current `requirements.md` content, not chat memory.

If any precondition fails, explain the gap, record a `blocker.recorded` or `note.recorded` event when useful, and stop. Do not write the plan from memory or from stale requirements.

## Inputs

Read and use these sources in this order:

1. `topic.md`
2. `question-c1.md`, `question-c2.md`, ... in cycle order
3. `audit.jsonl`
4. Derived status from `scripts/topic-log.py status --json`, when available
5. `requirements.md`
6. Existing `plan.md`, if updating
7. `templates/plan.md`
8. Relevant project files or docs named by topic, requirements, or question context

When affected files, interfaces, call flow, test targets, or local conventions are
unknown, use the `explore-codebase` skill before dependency analysis. Prefer
dispatching it as a fresh bounded subagent when the host supports subagents; otherwise
run it inline. Treat its `UNTRUSTED CODEBASE EXPLORATION RESULT` as hints only, and
reread cited files or exact excerpts before using them in `plan.md`.

## Scope Check

Confirm one topic can produce one coherent `plan.md` before writing it.

- If the topic is still coherent, decompose it into multiple `## Task N` sections and order them by dependencies. Do not split one topic into multiple plan files.
- If the topic is too large or bundles independent topics, stop. Ask a focused chat clarification when scope reduction can be decided in the current turn, then route to `define-requirements` as needed. Record the reason and answer in `audit.jsonl`, and stop.

## Hard Gates

- Do not write a plan that hides high-risk operations inside ordinary steps. Classify them explicitly in each task's `Safety` section.
- Do not use execution approval as blanket permission for high-risk operations. The executor must still ask for fresh approval immediately before running each high-risk operation.
- Do not plan `direct-execute` for any task that includes a high-risk operation.

## Preferences

- Prefer the strongest realistic task-level test strategy.
- Prefer narrowly scoped tasks that align with existing project boundaries.
- Prefer existing project patterns, helpers, naming, and error-handling style over new abstractions.

## Write Or Update Plan

Create or update `plan.md` from `templates/plan.md`. The template is the single source of truth for the plan's section list, order, each section's shape, and the detailed per-section authoring rules (carried as in-template comments). Do not maintain a second copy of those rules here, and do not create multiple plan files for one topic.

Fill the template's YAML front matter with plan input provenance (topic folder, requirements, topic file, audit, status command, answered question files in cycle order). Do not recreate the old `### Inputs` subsection under `## Overview`.

Write the plan content the user must review in the user's current or clearly preferred conversation language unless the user requests another language. Preserve canonical section headings, task headings (`## Task N: <name>`), status values, mode values, risk values, file paths, commands, code identifiers, and quoted source text exactly; translate user-facing helper labels and prose. `plan.md` is a reviewed execution contract, not a progress ledger; execution progress belongs in `audit.jsonl` through `scripts/topic-log.py`.

### Authoring Steps

1. Extract `Global Constraints` from the requirements and answered question decisions, copying project-wide values verbatim. Then analyze the dependency graph — prerequisites, interfaces, generated artifacts, migrations, build/test order — record it in `Dependency Analysis` and `Ordering Rationale`, and decide task order from it. If the implementation mechanism would contradict or materially reinterpret `requirements.md`, stop and follow Clarification Routing in `as-usual-rules/routing-rules.md`.
2. Choose the plan-level `Execution Mode` (`inline`, `subagent-driven`, or `mixed`). Prefer `subagent-driven` only when tasks have bounded context and the host can dispatch fresh subagents; otherwise use `inline` or record an explicit fallback.
3. Write each `## Task N: <name>` following the template's task section shape (`Purpose`, task-level `Execution Mode`, `Depends On`, `Files`, `Interfaces`, `Safety`, `Test Strategy`, `Steps`, `Verification` with a runnable command and expected result, `Notes`). Default `Test Strategy` to `test-required` with a named `Test target`; see Test Strategy and Safety below.
4. Fill the cross-cutting sections per the template comments: `Acceptance Criteria Coverage Matrix` (always), `Execution Surface` and `Decision Contracts` (conditional — see Conditional Sections), `Execution Task Index` (only when the plan has 4 or more tasks), `Verification Strategy`, and the `Review And Handoff` sections.
5. Keep execution progress out of the plan: no checkboxes, per-task status fields, completion marks, or progress notes anywhere. Task identity is the `## Task N: <name>` heading; progress belongs in `audit.jsonl`.

### Conditional Sections

The template comments own the trigger lists and field-level rules; this is the routing summary:

- `Acceptance Criteria Coverage Matrix`: always required. One row per `AC<N>`; do not complete the plan while any row has an unresolved gap — record the gap and route back instead.
- `Execution Surface`: required when the plan introduces or changes an execution entrypoint, external dependency, time-based behavior, state changes outside the normal request/response path, or runtime metadata/resource dependency. Delete the section when no signal applies.
- `Decision Contracts`: required when implementation behavior depends on classification, dispatch/routing, state transition, retry/idempotency, logging or output formatting tests depend on, or malformed-input fallback. Delete the section when none apply.
- `Execution Task Index`: required only when the plan has 4 or more tasks; delete it for smaller plans. When present, it is a navigation summary whose rows map 1:1 to detailed `## Task N: <name>` sections.

A signal that applies with no matching section is a plan defect, the same as a missing required section.

### Interface Consistency

A task implementer may read tasks out of order and sees only their own task. The `Consumes` and `Produces` fields are how neighboring tasks learn each other's exact names and types.

- `Produces`: name the exact functions, types, files, or artifacts later tasks rely on.
- `Consumes`: name what this task uses from earlier tasks, using the same names those tasks `Produce`.
- A name used in a later task's `Consumes` must match an earlier task's `Produces`. A function called `clearLayers()` in one task and `clearFullLayers()` in another is a defect.

### No Placeholders

Every task must contain the concrete content an executor needs. These are plan defects; do not leave them:

- `TBD`, `TODO`, "implement later", "fill in details".
- "add appropriate error handling", "add validation", "handle edge cases" without concrete scope.
- "similar to Task N" instead of the actual content (the executor may read tasks out of order).
- references to types, functions, or files not defined in any task.
- a `Verification` block without a runnable command and an expected result.

### Test Strategy

Choose a test strategy mode for every task. This is task-level verification design, not a project-wide test/CI policy.

Tests are required for implementation tasks; test-first (write the failing test before the code) is a technique, not a mandate. The distinction is by task kind, not ceremony:

| Mode | Use When | Plan Must Include |
| --- | --- | --- |
| `test-required` | Any feature, behavior change, bug fix, refactor, parser/transformer behavior, API contract logic, CLI/UI behavior with a test harness, integration boundary, or other testable code. | Test target and the passing-test evidence to record. For a **bug fix**, also a regression RED test (a failing test that reproduces the bug before the fix) — the regression proof is mandatory for bug fixes and optional otherwise. |
| `no-test` | Genuinely untestable or not-worth-testing work: configuration, generated code, or a throwaway prototype. | The reason tests are skipped, to record. No separate user approval is required. |

Reach for `no-test` only when the work is truly untestable, not when a testable boundary feels awkward — first try a simpler API, interface seam, dependency injection point, or smaller unit. If the mode choice could change scope, risk, or acceptance criteria, ask a focused clarification and record the answer before completing the plan.

### Safety

For every task, classify risk and reversibility before execution approval.

- `Risk Level`: use `low`, `medium`, or `high`.
- `High-Risk Operations`: list any high-risk operation from `core-workflow.md`, or `None`.
- `Reversibility`: use `reversible`, `partially reversible`, or `irreversible`.
- `Separate Approval Required`: use `yes` for any high-risk operation and `no` only when none are present.
- `Rollback / Recovery Notes`: name the concrete rollback path, backup, migration rollback, restore command, or "not safely reversible - user must approve risk".

For schema-related work, distinguish runtime data risk from code shape:

- Use high risk only for production/shared DB migrations, destructive schema changes, data migrations, or data deletion.
- Use medium risk, `High-Risk Operations: None`, and `Separate Approval Required: no` for local/test-only reversible schema-like code changes, such as adding a JPA field used only with an in-memory H2 sandbox or changing a test fixture schema, when no production/shared data is touched and rollback is a normal file revert.
- If the task may run against persistent user data, shared environments, or an unknown database, classify it as high risk until clarified.

If a high-risk operation is needed but the requirements did not decide it, ask a focused chat clarification when it can be resolved in the current turn; otherwise route to `define-requirements`. Record the answer in `audit.jsonl` before completing the plan.

### Policy Restraint

Do not silently decide test, CI, commit, PR, release, or deploy policy unless the approved requirements or plan already decided it.

- Verification commands are allowed when they are part of a task's success check.
- Commit, PR, release, and deploy behavior stays outside this plan unless the topic explicitly specified it. If the topic needs such a policy and it is undecided, ask a focused chat clarification when it can be resolved in the current turn; otherwise route to `define-requirements` instead of inventing one.

## Self Review

After writing the complete plan, use `plan-document-reviewer-prompt.md` as the canonical checklist and fix obvious issues in `plan.md`.

Do not maintain a second copy of the review criteria in this skill. The reviewer prompt owns:

- the Blocking vs Advisory checklist,
- the evidence required to pass each check,
- the `Review Status` output shape,
- the mapping from `passed` or `issues-fixed` to `Status: plan-complete`,
- the mapping from unresolved blocking issues to `Status: blocked`.

Follow Clarification Routing in `as-usual-rules/routing-rules.md` for any decision discovered here.

## Reviewer Prompt

After self-review passes, read `plan-document-reviewer-prompt.md` from this skill directory and follow it as a reviewer prompt in the current session.

Do not require a subagent. The reviewer prompt is a portable prompt file so Claude and Codex can both run the same review.

If the reviewer finds fixable issues, update `plan.md` directly and rerun the relevant reviewer checks. Follow Clarification Routing in `as-usual-rules/routing-rules.md` for any decision discovered here.

## Complete Plan

When self-review and reviewer-prompt checks pass:

1. Fill `plan.md` `Review Status`: set `Status: plan-complete`, `Reviewer Result: passed` (or `issues-fixed` if the reviewer fixed findings), `Reviewed At` to the current timestamp, and a one-line `Review Notes` in the user's language. Fill `Plan Review Checks` as a markdown checkbox list, using `[x]` for passed checks and `[ ]` only for unresolved checks. Then fill `Plan Review Findings` and `Plan Review Actions Taken`; write check result values, findings, and actions in the user's language unless they are canonical status values.
2. Run `scripts/topic-log.py complete-plan` to record `plan.completed`.
3. Confirm derived status now routes to execution approval.
4. Tell the user the plan is ready and ask them to review `plan.md` before approving execution. Respond in the user's current conversation language. Canonical English form: `The plan is ready for review. Please review plan.md; if it looks good, approve execution and I will run it.`
5. Stop.

Use:

```bash
python3 <plugin-root>/scripts/topic-log.py complete-plan \
  --topic-dir <topic-dir> \
  --plan plan.md \
  --summary "<summary>"
```

Do not compose separate low-level audit calls when the macro command can express the transition. Do not hand-edit `audit.jsonl`; if the helper cannot express the update, stop and report the missing helper capability.

Do not start execution until the user explicitly approves, for example by saying "go ahead" or "execute".

## Plan Revision Before Execute Approval

When the topic is `plan-review` and the user requests a change before approving execution, route by impact:

- If the change is non-material (wording, clearer steps, exact file path correction, ordering clarification that does not change scope, requirements, risk, implementation strategy, or verification policy), update `plan.md` here, rerun self-review and the relevant reviewer checks, refresh `Review Status`, record the revision in `audit.jsonl`, and stop at `plan-review` again.
- If the change affects scope, requirements, risk, implementation strategy, acceptance criteria, or verification policy, stop before editing `plan.md` and follow Clarification Routing in `as-usual-rules/routing-rules.md`. Update `plan.md` and rerun plan review only after the decision is routed and recorded.

Example — non-material (absorb here): "Task 순서 설명을 더 분명히", "파일 경로 오타 수정". → update plan.md, rerun self-review + reviewer checks, stay plan-review.

Example — material (route via Clarification Routing): "DB 마이그레이션 방식을 in-memory H2에서 공유 스테이징으로 변경" (changes risk + acceptance + verification). → ask focused clarification; route to define-requirements if requirements change.

## Long-Term Memory Capture

If the user states an explicit long-term rule during this phase ("always X", "in this
project always Y"), do not break the current flow and do not write memory now. Capture
it only as an audit candidate:

```bash
python3 <plugin-root>/scripts/topic-log.py record-memory-candidate \
  --topic-dir <topic-dir> --summary "<rule>" --source-phase writing-plan --proposed-target memory
```

The actual review/approval/write happens later via `manage-self-improvement` at finalize.

## Anti-Patterns

- Executing work instead of stopping at `plan-review`.
- Splitting one topic into multiple plan files.
- Tracking task completion with per-task status fields inside `plan.md`.
- Leaving placeholders, undefined references, or a verification block without a runnable command and expected result.
- Mismatched `Consumes`/`Produces` names or signatures across tasks.
- Omitting Safety fields or marking a high-risk operation as not needing separate approval.
- Omitting a conditional section (`Execution Surface`, `Decision Contracts`, `Execution Task Index`) when its trigger applies, or padding the plan with empty conditional sections when it does not.
- Restating the template's per-section authoring rules inside `plan.md` instead of just following them.
- Silently deciding test, CI, commit, PR, release, or deploy policy the requirements/plan never decided.
- Writing the plan from memory or from stale requirements.
- Skipping the reviewer prompt because self-review passed.
