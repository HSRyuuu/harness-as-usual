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
