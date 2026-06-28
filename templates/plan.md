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

- 선행 조건:
- 이후 작업 전에 만들어야 할 인터페이스 또는 산출물:
- 마이그레이션, 빌드, 테스트 순서:

### Ordering Rationale

-

### Verification Strategy

-

### Acceptance Criteria Coverage Matrix

| AC | Covered By | Evidence | Assertion / Expected Evidence |
| --- | --- | --- | --- |
| AC1 |  |  |  |

### Execution Mode

- Mode: inline | subagent-driven | mixed
- Rationale:
- Host fallback when subagents are unavailable:

### Execution Surface

- Applicability: Required when this plan introduces or changes an execution entrypoint, external dependency, time-based behavior, state changes outside the normal request/response path, or runtime metadata/resource dependency. Otherwise `None`.
- Entrypoint:
- Invocation:
- Required configuration / inputs:
- External dependencies:
- Test environment:
- Time control:
- Success / failure signal:
- Idempotency / retry behavior:

### Decision Contracts

- None

## Execution Task Index

<!-- Navigation summary only. Do not use checkboxes, status fields, or progress notes here. Each row must map 1:1 to one detailed `## Task N: <name>` section. If this index conflicts with a detailed task section, fix the plan before execution. -->

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

- 없음

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
- Expected result: 사용자 언어로 성공 기준 작성

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
