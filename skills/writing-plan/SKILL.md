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

File-backed `[Answer]:` fields are mandatory for `define-requirements` question cycles only. Follow Clarification Routing in `core-workflow.md` for any decision discovered here.

## Preconditions

Before writing the plan, confirm:

- The Plan Rules in `core-workflow.md` have been checked.
- The active topic folder is under `.as-usual/topic/yyyy-MM-dd-<topic>/`.
- `topic.md` and `audit.jsonl` exist.
- `requirements.md` exists.
- `python3 scripts/topic-log.py status --topic-dir <topic-dir> --json` shows `phase=requirements-complete` and `nextAction=approve-plan`, or `audit.jsonl` contains a successful `requirements.completed` event.
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

Create or update `plan.md` from `templates/plan.md`. `templates/plan.md` is the single source of truth for the plan's section list and order; do not maintain a separate section list here. Do not create multiple plan files for one topic.

Write the plan content the user must review in the user's current or clearly preferred conversation language unless the user requests another language. Preserve canonical task headings (`## Task N: <name>`), status values, mode values, risk values, file paths, commands, code identifiers, and quoted source text exactly. Do not preserve English helper labels or default values inside sections when they are user-facing prose; translate or rewrite them in the user's language.

Preserve canonical section headings and canonical task headings (`## Task N: <name>`) for agent readability. `plan.md` is a reviewed execution contract, not a progress ledger; execution progress belongs in `audit.jsonl` through `scripts/topic-log.py`.

### Plan Metadata Front Matter

Use the YAML front matter at the top of `templates/plan.md` for plan input provenance:

- `topic`: the current `yyyy-MM-dd-<topic>` folder name.
- `requirements`: `requirements.md`.
- `topicFile`: `topic.md`.
- `audit`: `audit.jsonl`.
- `statusCommand`: `scripts/topic-log.py status --json`.
- `questionFiles`: answered `question-cN.md` files in cycle order, or `[]` when no question files exist.

Do not recreate the old `### Inputs` subsection under `## Overview`. Source inputs belong in front matter so the body can stay focused on the execution contract.

### Authoring Steps

1. Extract `Global Constraints` from the requirements and answered question decisions. Copy project-wide values (version floors, naming/copy rules, platform requirements, "do not change" notes) verbatim. Every task implicitly inherits this section.
2. Analyze the dependency graph before fixing task order: prerequisites, interfaces, generated artifacts, migrations, and build/test order. Record this in `Dependency Analysis` and `Ordering Rationale`. Use user-language sublabels and prose inside these sections; do not copy English labels such as `Upstream prerequisites` unless the user's preferred language is English.
3. If dependency analysis reveals that the implementation mechanism would contradict or materially reinterpret `requirements.md`, stop. Do not silently absorb the contradiction into the plan. Follow Clarification Routing in `core-workflow.md` for any decision discovered here.
4. Decide task order from the dependency analysis, then write each `## Task N: <name>`.
5. Choose `Execution Mode` for the plan: `inline`, `subagent-driven`, or `mixed`. Prefer `subagent-driven` only when tasks have bounded context and the host can dispatch fresh subagents; otherwise use `inline` or record an explicit fallback.
6. Fill `Execution Surface` when the plan introduces or changes an execution entrypoint, external dependency, time-based behavior, state changes outside the normal request/response path, or runtime metadata/resource dependency. If none apply, write `Applicability: None` and keep the remaining fields concise or `None`.
7. Fill `Acceptance Criteria Coverage Matrix` so every `AC<N>` from `requirements.md` maps to a task, test target or review evidence, and exact assertion/evidence. If an acceptance criterion cannot be verified, record the gap and route back before completing the plan.
8. Fill `Decision Contracts` when the plan includes classification, parsing, dispatch/routing, state transition, retry/idempotency, logging, or output formatting logic. Use an ordered decision table, token set, allowed values, or concrete examples so executors do not infer edge cases from prose. If none apply, write `None`.
9. For each task, fill `Purpose`, task-level `Execution Mode`, `Depends On`, `Files`, `Interfaces` (`Consumes` / `Produces`), `Safety`, `Test Strategy`, `Steps`, `Verification` (a command and its expected result), and `Notes`. In `Test Strategy`, default to `tdd` and name the `Test target` that execution should record through `verification.recorded` or `task.completed` events. Use `approved-tdd-exception` only for a human-approved exception in one allowed category: `throwaway-prototype`, `generated-code`, or `configuration`. Keep canonical field names and enum/status values stable, but write explanations, expected results, rollback notes, and review notes in the user's language.
10. Fill `Execution Task Index` after detailed tasks are drafted. It is a navigation summary, not a replacement for `## Task N` sections or task `Steps`. Each row must map 1:1 to one detailed `## Task N: <name>` section and summarize `Outcome`, `Depends On`, `Edit Surface`, `Gate`, and `Verification` from that task using compact user-language prose.
11. Do not use checkboxes, status fields, completion marks, or progress notes in `Execution Task Index`; execution progress belongs in `audit.jsonl`.
12. Keep task identity in the `## Task N: <name>` heading. Do not add per-task status fields; execution progress belongs in `audit.jsonl`.
13. Fill `Verification Strategy` and the `Review And Handoff` sections (`Manual QA Gate`, `Recovery Notes`, `Completion Criteria`).

### Execution Task Index

Use this section to improve executor readiness and context budgeting. It gives the controller a quick action-space map before reading the detailed task contracts.

Rules:

- Keep it as a markdown table with `Task`, `Outcome`, `Depends On`, `Edit Surface`, `Gate`, and `Verification`.
- The `Task` value must exactly match the detailed task heading, such as `Task 1: Add Booking.createdAt`.
- `Outcome` states the intended result, not progress.
- `Depends On` summarizes task ordering. Use `None` or a localized none value for independent tasks.
- `Edit Surface` names the main files, modules, or directories at a compact level.
- `Gate` names approvals or blockers the executor must remember, such as `None`, `Fresh high-risk approval before dependency change`, or a localized equivalent.
- `Verification` names the task's runnable verification command or a compact reference to it.
- If the index conflicts with a detailed task section, treat that as a plan defect and fix `plan.md` before execution.
- Do not put task steps, detailed safety analysis, rollback notes, RED/GREEN evidence, or review findings here; those belong in detailed task sections, review sections, or `audit.jsonl`.

### Execution Surface

Use this section to make runtime behavior testable without hard-coding technology-specific rules into AsUsual.

Fill it when any of these signals appear in the requirements, question answers, project files, or planned tasks:

- A new or changed execution entrypoint, such as an API endpoint, CLI command, batch job, scheduled task, worker, message consumer, webhook, migration script, or one-off script.
- An external dependency, such as a relational/NoSQL database, message broker, cache, lock service, object storage, search index, third-party API, mounted filesystem, or framework runtime metadata tables/resources.
- Time-based behavior, such as expiration, TTL, retry delay, scheduling, settlement date, debounce/throttle windows, or time-window queries.
- State changes outside the normal request/response path, such as direct SQL updates, async consumers, background workers, batch updates, repair scripts, or migration/backfill code.

When applicable, specify:

- `Entrypoint`: the concrete runtime entrypoint name and type.
- `Invocation`: how a human, scheduler, test, or runtime calls it.
- `Required configuration / inputs`: env vars, properties, arguments, job parameters, topics, schema names, or required resources.
- `External dependencies`: required services/resources, whether they are real, embedded, mocked, fake, or containerized in tests.
- `Test environment`: how schema, fixture data, topics, metadata tables, buckets, queues, or equivalent resources are prepared without accidentally using production/shared resources.
- `Time control`: how tests make time deterministic, such as a fixed clock, injected clock, explicit timestamp parameter, or fixed fixture timestamps.
- `Success / failure signal`: response, exit code, job status, emitted event, DB state, output file, log/metric, or assertion.
- `Idempotency / retry behavior`: what happens on re-run, duplicate delivery, partial completion, timeout, stale locks, already-processed state, or retry.

If the appropriate technical choice can be inferred from the existing project patterns, choose it and record the reasoning. Ask the user only when the choice changes scope, risk, cost, operational policy, acceptance criteria, or verification policy.

### Acceptance Criteria Coverage Matrix

Use this section to prevent requirements coverage from becoming a vague claim.

Rules:

- Include one row for every `AC<N>` in `requirements.md`.
- Map each acceptance criterion to the task that satisfies it.
- Name the test target, command, review step, or manual QA evidence that proves it.
- Name the exact assertion, token, state, output, or inspection evidence. For logs and text output, specify the token set or message template that tests may depend on.
- If the only evidence is a final sweep or code review, say that explicitly.
- Do not complete the plan while any row has an unresolved gap.

### Decision Contracts

Use this section when implementation behavior depends on an ordered choice or classification that prose could leave ambiguous.

Include a decision contract when the plan contains any of these:

- payload, parser, validation, or file-format classification,
- event or message dispatch,
- state transition,
- conflict, duplicate, retry, or idempotency behavior,
- logging or user-visible output formatting that tests depend on,
- fallback behavior for malformed, unknown, missing, or contradictory inputs.

Use the lightest precise format: an ordered table, allowed-value list, logging token set, API response examples, or before/after examples. For ordered tables, say that the first matching row wins. If a decision contract would change or contradict requirements, return to `define-requirements` instead of completing the plan.

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

TDD is mandatory for implementation tasks. The plan should assume behavior-by-behavior RED/GREEN/REFACTOR, not one large batch of all failing tests. If a task looks hard to test, treat that as a design signal first: define a simpler API, interface seam, dependency injection point, or smaller unit that can be driven by a failing test. Exploratory code may be used only as throwaway learning; the actual implementation returns to TDD.

| Mode | Use When | Plan Must Include |
| --- | --- | --- |
| `tdd` | Any feature, behavior change, bug fix, refactor, parser/transformer behavior, API contract logic, UI behavior with a test harness, CLI behavior, integration boundary, or other code where implementation can be driven by tests. | Test target, RED failing test command and expected failure, GREEN implementation/pass command, refactor check, and evidence to record. |
| `approved-tdd-exception` | Only when the human explicitly approves skipping TDD for `throwaway-prototype`, `generated-code`, or `configuration`. | Exception category, approval source, verification command or review evidence, expected result, and evidence to record. |

Do not plan `approved-tdd-exception` just because the task feels awkward to test. First make the boundary testable. If an exception is still needed, ask the user and record the approval source. If the selected mode could change scope, risk, or acceptance criteria, ask a focused clarification and record the answer before completing the plan.

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

Follow Clarification Routing in `core-workflow.md` for any decision discovered here.

## Reviewer Prompt

After self-review passes, read `plan-document-reviewer-prompt.md` from this skill directory and follow it as a reviewer prompt in the current session.

Do not require a subagent. The reviewer prompt is a portable prompt file so Claude and Codex can both run the same review.

If the reviewer finds fixable issues, update `plan.md` directly and rerun the relevant reviewer checks. Follow Clarification Routing in `core-workflow.md` for any decision discovered here.

## Complete Plan

When self-review and reviewer-prompt checks pass:

1. Fill `plan.md` `Review Status`: set `Status: plan-complete`, `Reviewer Result: passed` (or `issues-fixed` if the reviewer fixed findings), `Reviewed At` to the current timestamp, and a one-line `Review Notes` in the user's language. Fill `Plan Review Checks` as a markdown checkbox list, using `[x]` for passed checks and `[ ]` only for unresolved checks. Then fill `Plan Review Findings` and `Plan Review Actions Taken`; write check result values, findings, and actions in the user's language unless they are canonical status values.
2. Run `scripts/topic-log.py complete-plan` to record `plan.completed`.
3. Confirm derived status now routes to execution approval.
5. Tell the user the plan is ready and ask them to review `plan.md` before approving execution. Respond in the user's current conversation language. Canonical English form: `The plan is ready for review. Please review plan.md; if it looks good, approve execution and I will run it.`
6. Stop.

Use:

```bash
python3 scripts/topic-log.py complete-plan \
  --topic-dir <topic-dir> \
  --plan plan.md \
  --summary "<summary>"
```

Do not compose separate low-level audit calls when the macro command can express the transition. Do not hand-edit `audit.jsonl`; if the helper cannot express the update, stop and report the missing helper capability.

Do not start execution until the user explicitly approves, for example by saying "go ahead" or "execute".

## Plan Revision Before Execute Approval

When the topic is `plan-review` and the user requests a change before approving execution, route by impact:

- If the change is non-material (wording, clearer steps, exact file path correction, ordering clarification that does not change scope, requirements, risk, implementation strategy, or verification policy), update `plan.md` here, rerun self-review and the relevant reviewer checks, refresh `Review Status`, record the revision in `audit.jsonl`, and stop at `plan-review` again.
- If the change affects scope, requirements, risk, implementation strategy, acceptance criteria, or verification policy, stop before editing `plan.md` and follow Clarification Routing in `core-workflow.md`. Update `plan.md` and rerun plan review only after the decision is routed and recorded.

Example — non-material (absorb here): "Task 순서 설명을 더 분명히", "파일 경로 오타 수정". → update plan.md, rerun self-review + reviewer checks, stay plan-review.

Example — material (route out): "DB 마이그레이션 방식을 in-memory H2에서 공유 스테이징으로 변경" (changes risk + acceptance + verification). → ask focused clarification; route to define-requirements if requirements change.

## Anti-Patterns

- Executing work instead of stopping at `plan-review`.
- Splitting one topic into multiple plan files.
- Tracking task completion with per-task status fields inside `plan.md`.
- Leaving placeholders, undefined references, or a verification block without a runnable command and expected result.
- Mismatched `Consumes`/`Produces` names or signatures across tasks.
- Omitting Safety fields or marking a high-risk operation as not needing separate approval.
- Silently deciding test, CI, commit, PR, release, or deploy policy the requirements/plan never decided.
- Writing the plan from memory or from stale requirements.
- Skipping the reviewer prompt because self-review passed.
