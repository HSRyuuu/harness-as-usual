---
unit: <topic | direct-work | issue>
slug: <yyyy-MM-dd-slug>
created: <yyyy-MM-dd>
---

# Plan

## Goal & Constraints

(What this plan achieves, and what bounds it — existing patterns to follow,
things that must not break, policy already agreed.)

## Approach

(The order of work and why. What has to land before what, and where the risk
sits. If the ordering is obvious, one or two lines is enough.

For changes to existing behavior, connect the observed flow, the proposed
change, and behavior that must remain intact. Cite the current implementation
and any analogue being reused; explain relevant differences instead of copying
it wholesale. Distinguish the checkout being changed from reference checkouts.)

## Tasks

### Task 1: <name>

**Purpose** — what this task achieves.

**Files** — the files it touches. Open them before naming them.

**Steps** — what to do, concretely enough to follow. Name the actual reuse point
and behavior this task must preserve when applicable.

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

(Which task satisfies which acceptance criterion, and what proves it — the
command, review, or manual check. A criterion with no task behind it is a gap in
the plan; one whose task verification never exercises it is the same gap wearing
a task number.)
