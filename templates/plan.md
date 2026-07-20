---
topic: yyyy-MM-dd-<topic>
requirements: requirements.md
topicFile: topic.md
audit: audit.jsonl
statusCommand: "scripts/topic-log.py status --json"
questionFiles: []
---

# yyyy-MM-dd-<topic> Plan

## Overview

### Goal

-

### Global Constraints

-

## Execution Design

### Dependency Analysis

- Prerequisites:
- Interfaces or artifacts required before later work:
- Migration, build, and test ordering:

### Ordering Rationale

-

### Verification Strategy

-

### Acceptance Criteria Coverage Matrix

<!--
Always required. One row per AC<N> in requirements.md. Map each AC to the task
that satisfies it, the test/review/manual-QA evidence that proves it, and the
exact assertion, token, state, or output. For logs and text output, name the
token set or message template tests may depend on. If the only evidence is a
final sweep or code review, say so explicitly. Do not complete the plan while
any row has an unresolved gap.
-->

| AC | Covered By | Evidence | Assertion / Expected Evidence |
| --- | --- | --- | --- |
| AC1 |  |  |  |

### Execution Mode

- Mode: inline | subagent-driven | mixed
- Rationale:
- Host fallback when subagents are unavailable:

### Execution Surface

<!--
Conditional: keep this section only when the plan introduces or changes an
execution entrypoint (API endpoint, CLI command, batch/scheduled job, worker,
message consumer, webhook, migration or one-off script), an external dependency
(database, broker, cache, lock service, object storage, search index,
third-party API, mounted filesystem, framework runtime metadata), time-based
behavior (expiration/TTL, retry delay, scheduling, debounce/throttle,
time-window queries), or state changes outside the normal request/response path
(direct SQL updates, async consumers, background workers, batch/repair/backfill
code). Delete the whole section when no signal applies.
Infer technical choices from existing project patterns and record the
reasoning; ask the user only when the choice changes scope, risk, cost,
operational policy, acceptance criteria, or verification policy.
-->

- Entrypoint:
- Invocation:
- Required configuration / inputs:
- External dependencies:
- Test environment:
- Time control:
- Success / failure signal:
- Idempotency / retry behavior:

### Decision Contracts

<!--
Conditional: keep this section only when implementation behavior depends on
payload/parser/validation/file-format classification, event or message
dispatch, state transitions, conflict/duplicate/retry/idempotency behavior,
logging or user-visible output formatting that tests depend on, or fallback
behavior for malformed/unknown/missing/contradictory inputs. Delete the whole
section when none apply.
Use the lightest precise format: an ordered decision table (first matching row
wins), allowed-value list, logging token set, API response examples, or
before/after examples. If a contract would change or contradict requirements,
return to define-requirements instead of completing the plan.
-->

-

## Execution Task Index

<!--
Conditional: include only when the plan has 4 or more tasks; delete this
section for smaller plans. Navigation summary only — no checkboxes, status
fields, completion marks, or progress notes. Each row maps 1:1 to one detailed
`## Task N: <name>` section: `Task` matches the heading exactly, `Outcome`
states the intended result, `Depends On` summarizes ordering (`None` for
independent tasks), `Edit Surface` names the main files/modules, `Gate` names
approvals or blockers the executor must remember, `Verification` names the
task's runnable check. If the index conflicts with a detailed task section,
fix the plan before execution. Task steps, safety analysis, rollback notes,
RED/GREEN evidence, and review findings belong in detailed task sections,
review sections, or audit.jsonl.
-->

| Task | Outcome | Depends On | Edit Surface | Gate | Verification |
| --- | --- | --- | --- | --- | --- |
| Task 1: <name> |  |  |  |  |  |

## Task 1: <name>

### Purpose

-

### Execution Mode

- Mode: inherit | inline | subagent-driven
- Subagent role/context, if used:

### Depends On

- None

### Files

-

### Interfaces

- Consumes:
- Produces:

### Safety

- Risk Level: low | medium | high
- High-Risk Operations: None | file deletion | bulk formatting | package/dependency change | production/shared DB migration | destructive schema/data change | environment/secret change | CI/CD change | deploy/release | git push/force push
- Reversibility: reversible | partially reversible | irreversible
- Separate Approval Required: yes | no
- Rollback / Recovery Notes:

### Test Strategy

- Mode: tdd | approved-tdd-exception
- Test target:
- RED:
- GREEN:
- Refactor check:
- Exception Category: None | throwaway-prototype | generated-code | configuration
- Exception Approval:
- Evidence to record:

### Steps

1.

### Verification

- Command:
- Expected result: <!-- Write the success criteria here in the user's language. -->

### Notes

-

## Review And Handoff

### Manual QA Gate

-

### Recovery Notes

-

### Completion Criteria

-

### Review Status

- Status: draft | plan-complete | blocked
- Reviewed At:
- Reviewer Result: not-run | passed | issues-fixed | blocked
- Review Notes:

<!--
Plan Review Checks (Blocking/Advisory), Review Findings, and Review Actions Taken
are written into this section by writing-plan review.

The canonical check item list, the evidence required to pass each check, and the exact
output shape are owned by skills/writing-plan/plan-document-reviewer-prompt.md
(Output Format). Do not maintain a second copy of the check items in this template.
-->
