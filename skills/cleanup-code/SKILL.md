---
name: cleanup-code
description: Use when AsUsual is active and the user approves code cleanup after execution review.
---

# Cleanup Code

This skill performs optional post-review cleanup for an AsUsual topic. It looks for cleanup opportunities in changed code after correctness review has completed, applies safe simplifications, reruns relevant verification, and records the result.

Use it only after `review-execution` has recorded execution review and the user explicitly approves code cleanup.

## Responsibility Boundary

| Skill | Responsibility |
| --- | --- |
| `review-execution` | Correctness review, code cleanup consent, and routing |
| `cleanup-code` | Cleanup review across reuse, simplification, efficiency, and abstraction level |
| `finalize` | Close the topic record and ask which git action to run |
| `git-action` | Run the selected post-finalize git action |

`cleanup-code` is not a bug-finding gate. If cleanup review discovers a correctness issue, record it as a review finding and route back to `review-execution` or the user's chosen fix path.

## Preconditions

Before code cleanup, confirm:

- The Code Cleanup rules in `core-workflow.md` have been checked.
- `topic.md`, `audit.jsonl`, `requirements.md`, and `plan.md` have been read from disk.
- `audit.jsonl` records execution completion and execution review completion.
- The user explicitly approved code cleanup.
- A current diff or changed-file list is available, or the limitation is recorded.

If approval is missing, return to `review-execution` to ask. Do not run cleanup automatically.

## Inputs

Read and use these sources in this order:

1. `topic.md`
2. `audit.jsonl`
3. Derived status from `scripts/topic-log.py status --json`, when available
4. `requirements.md`
5. `plan.md`
6. Current diff or changed-file list
7. Relevant surrounding project files needed to identify existing helpers and patterns

## Workflow

### Step 1: Run Four Cleanup Reviews

When the host supports subagents, run these four review agents in parallel using the prompt files in this skill directory:

| Review | Prompt | Focus |
| --- | --- | --- |
| Reuse | `reuse-reviewer-prompt.md` | Existing helpers, utilities, shared APIs, and duplicated local logic |
| Simplification | `simplification-reviewer-prompt.md` | Unnecessary branching, ceremony, indirection, or over-engineering |
| Efficiency | `efficiency-reviewer-prompt.md` | Wasteful loops, repeated work, avoidable I/O, expensive rendering, or needless allocations |
| Abstraction | `abstraction-reviewer-prompt.md` | Whether code sits at the right level of abstraction for the surrounding codebase |

Each review writes a file under `clean-up/`: `clean-up/review-result-reuse.md`, `clean-up/review-result-simplification.md`, `clean-up/review-result-efficiency.md`, or `clean-up/review-result-abstraction.md`. Each file must include YAML frontmatter `type`, `verdict`, and `reviewedAt`. The receipt verdict must be one of `passed | findings | blocked` and must match the file frontmatter `verdict`.

If subagents are unavailable, run the four reviews sequentially in the current session and record that limitation. The four `clean-up/review-result-<type>.md` files and frontmatter are still required; only subagent receipt responses are omitted.

Review only changed code and nearby context needed to judge cleanup. Do not expand into unrelated refactors.

### Step 2: Synthesize Cleanup Plan

Read the four review files and combine reviewer findings into one cleanup set.

Apply only findings that are:

- behavior-preserving,
- local to the approved change surface,
- consistent with `requirements.md` and `plan.md`,
- lower-risk than leaving the code as-is, and
- verifiable with existing task verification or a clearly related command.

Do not apply speculative rewrites, broad architecture changes, new dependencies, public API changes, schema changes, behavior changes, or cleanup that would require a new product decision.

### Step 3: Apply Safe Cleanup

Apply accepted cleanup changes directly. Keep edits focused.

If no safe cleanup exists:

1. Record `code_cleanup.completed` through `scripts/topic-log.py audit`.
2. Route to `finalize`.

### Step 4: Re-Verify

If cleanup changes files, rerun relevant verification:

- Prefer the verification commands already recorded for the affected tasks.
- Rerun narrower commands when they cover the cleanup safely.
- If verification cannot be rerun, record why and what remains.

Record exact commands and outcomes with `scripts/topic-log.py verification --verdict PASS|FAIL|INCONCLUSIVE`. Completion judgment follows `as-usual-rules/completion-rules.md`: verification evidence by surface and `INCONCLUSIVE` handling.

### Step 5: Record And Route

Record:

- which cleanup reviewers ran,
- findings accepted and rejected,
- files changed,
- verification rerun and outcome,
- remaining cleanup follow-ups, if any.

Append a `code_cleanup.completed` audit event with phase `cleanup-complete` and next action `finalize`, then invoke `finalize` in the same turn.

## Anti-Patterns

- Running code cleanup before correctness review.
- Treating cleanup review as bug review.
- Applying broad refactors unrelated to the topic.
- Changing behavior, public API, schema, dependencies, or product decisions as "cleanup".
- Accepting every reviewer suggestion without checking risk.
- Skipping re-verification after cleanup changes files.
