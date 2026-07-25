# Plan

<!--
Strength depends on the caller:
  topic       — all five sections.
  direct-work — Tasks and Verification Strategy alone are a complete plan.
                Do not inflate a checklist into a document.

This is a contract, not a ledger. Task progress belongs in audit.jsonl.
Do not add a review status block — the pre-approval review is recorded as an event.
-->

## Goal & Constraints

(What this plan achieves, and what bounds it — existing patterns to follow,
things that must not break, policy already agreed.)

## Approach

(The order of work and why. What has to land before what, and where the risk
sits. If the ordering is obvious, one or two lines is enough.)

## Tasks

### Task 1: <name>

**Purpose** — what this task achieves.

**Files** — the files it touches. Open them before naming them.

**Steps** — what to do, concretely enough to follow.

**Verification** — a runnable command and its expected result. For a behavior
change, this must exercise the changed behavior, not just prove it compiles.

**Safety** — any high-risk operation involved (see safety-rules.md) and its
rollback. Naming it here does not grant permission; it still needs fresh approval
immediately before it runs. Omit when there is none.

### Task 2: <name>

(…)

## Verification Strategy

(How the whole change gets checked, beyond the per-task commands — the end-to-end
check, what a regression would look like, anything that can only be verified
manually and by whom.)

## Acceptance Criteria Coverage

(Which task satisfies which acceptance criterion. A criterion with no task behind
it is a gap in the plan.)
