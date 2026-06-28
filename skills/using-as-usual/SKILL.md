---
name: using-as-usual
description: Use when the user mentions running AsUsual, .as-usual artifacts, topic.md/audit.jsonl/question/requirements/plan files, or resuming an active topic.
---

# Using AsUsual

This skill is the entry-point helper for activation and first reads in the AsUsual runtime workflow. Do not force AsUsual onto every request just because the hook announced AsUsual capability or a `.as-usual/` folder exists.

## Responsibility Boundary

| Skill | Responsibility |
| --- | --- |
| `using-as-usual` | Identify activation, confirm `core-workflow.md`, perform `.as-usual/topic/` first reads, and initialize new topic `topic.md`/`audit.jsonl` |
| `start-work` | After first reads, route a new topic or unclear current phase to requirements, plan, execute, or direct-execute |
| `define-requirements` | Create/validate `question-cN.md` files when needed, write/review `requirements.md`, and ask for plan approval |
| `writing-plan` | Analyze dependencies, write/review `plan.md`, and ask for execution approval |
| `executing-plan` | Execute the reviewed plan using the approved execution mode and record progress, review loops, sweeps, and verification |
| `review-execution` | Review completed execution, ask about optional code cleanup, and route to finalization |
| `cleanup-code` | Run approved cleanup review and behavior-preserving simplification before finalization |
| `finalize` | Close the topic record and ask which post-close git action to run |
| `git-action` | Run the selected post-finalize git action |

`using-as-usual` does not directly finalize gate routing. After first reads, if a new topic is starting or the next phase is unclear, use `start-work`; the canonical phase rules are in `as-usual-rules/core-workflow.md`.

## Activation

Treat the request as AsUsual work when any of these is true:

- The user explicitly says `as-usual` or `AsUsual`.
- The user mentions `.as-usual/`, `topic.md`, `audit.jsonl`, `question-cN.md`, `requirements.md`, `plan.md`, or topic artifacts.
- The user asks to resume an active topic with phrasing like "I answered", "write the requirements", "write the plan", or "continue".

## Required First Reads

When the request is AsUsual work, before answering or executing:

1. Read the full `as-usual-rules/core-workflow.md` from the plugin root path announced by the SessionStart hook.
2. Locate the active topic under `.as-usual/topic/`.
3. For an existing topic, read `topic.md` first for durable resume context.
4. Read `audit.jsonl`.
5. Run `python3 scripts/topic-log.py status --topic-dir <topic-dir> --json` when the helper is available.
6. Read linked artifacts needed for the derived next action, such as question files, `requirements.md`, `plan.md`, review report, or final report.
7. If this is a new topic, choose a `yyyy-MM-dd-<topic>` slug using the actual current date and lowercase kebab-case.
8. For a new topic, immediately create the topic folder and run `scripts/topic-log.py init` to initialize `topic.md` and `audit.jsonl`, record the initial user request, append a `topic.created` audit event, tell the user the topic path in one line, then route with `start-work`.

For topics with many or large artifacts, you may delegate artifact inventory and status summarization to a subagent to keep the controller's context clean when the host supports it. This does not replace controller first reads: before any gate decision, approval request, artifact edit, or completion claim, the controller must directly read the canonical artifact or exact excerpt needed for that decision. The controller remains the owner of gate decisions, approvals, artifact edits, and completion claims, and does not delegate those.

## Canonical Topic Path

```text
.as-usual/topic/yyyy-MM-dd-<topic>/
```

Create runtime artifacts only under this path.

- `question-cN.md`
- `requirements.md`
- `plan.md`
- `topic.md`
- `audit.jsonl`

Do not use project-global topic records under `.as-usual/`, `.as-usual/topics/`, the `yyyyMMdd-<topic>` format, or a separate `spec.md` for new runtime artifacts.

## New Topic Initialization

When no active topic exists and the user is starting a new topic:

1. Choose the topic folder name as `yyyy-MM-dd-<topic>` using the actual current date and a lowercase kebab-case slug.
2. Create the topic folder under `.as-usual/topic/`.
3. Run `python3 <as-usual-plugin-root>/scripts/topic-log.py init --topic-dir <topic-dir> --topic <yyyy-MM-dd-topic> --initial-request <request> --summary <summary> --actor codex`. If the host is Claude Code, use `--actor claude`.
4. Confirm the script created `topic.md`, created `audit.jsonl`, recorded the initial request in `topic.md#Initial Request`, and appended the `topic.created` event.
5. Tell the user the topic path in one line so they can correct the slug or topic if needed.
6. Continue to `start-work`.

## Workflow Summary

### Define Requirements

Requirements definition is owned by `define-requirements`.

If the request is ambiguous or requires a user decision that could change requirements, plan, implementation, risk, or verification, create the next `question-cN.md` from `templates/question.md`, record it through `scripts/topic-log.py artifact` and a `question.created` audit event, tell the user which file to answer, and stop.

When the user returns saying they answered, reread `question-c1.md`, `question-c2.md`, ... from disk. If answers validate, write or update `requirements.md` from `templates/requirements.md`, run the local reviewer prompt, run `scripts/topic-log.py complete-requirements`, ask the user to review `requirements.md` before plan approval, and stop.

### Plan

Plan writing is owned by `writing-plan`. When the user approves moving from completed requirements to plan, confirm `requirements.md` is current and derived status or `audit.jsonl` shows `requirements.completed`, then invoke `writing-plan`.

### Execute

Plan execution is owned by `executing-plan`. When the user explicitly approves or requests execution, invoke `executing-plan`. It rereads `topic.md`, `audit.jsonl`, `requirements.md`, and `plan.md`, critically reviews the plan, executes tasks in the approved `inline`, `subagent-driven`, or `mixed` mode, records audit events for progress, task review loops, sweeps, and verification, and invokes `review-execution` after execution completion.

### Review, Code Cleanup, Finalize

Execution review is mandatory after execution completes. `review-execution` reviews actual changed code and recorded evidence against `requirements.md` and `plan.md`, records findings, then asks whether to run optional code cleanup. If code cleanup is skipped or complete, `finalize` closes the topic and asks which post-close git action to run.

## Topic Log And Audit

- `topic.md` is the low-churn resume document. It carries the initial request, topic boundary, and durable notes, not high-churn progress.
- `audit.jsonl` is an append-only event log.
- Derive phase, next action, artifacts, blockers, approvals, and verification with `python3 scripts/topic-log.py status --topic-dir <topic-dir> --json`.
- Prefer source traces such as `topic.md#Initial Request`, `topic.created`, `question-c1.md Q1`, and `decision.recorded`.
- Update `topic.md` and `audit.jsonl` only through `scripts/topic-log.py` when the helper can express the transition. Prefer macro commands such as `route-start-work`, `complete-requirements`, `complete-plan`, `complete-task`, `verification`, `blocker`, `complete-execution`, `record-review`, `skip-code-cleanup`, `finalize-topic`, and `select-git-action`.

## Stop Conditions

Stop and tell the user the file path and required action when:

- A question file was created or updated.
- Requirements are complete and need plan approval.
- Plan review is needed.
- Execution review or code cleanup decision is needed.
- Finalization needs git action decision.
- Answers are empty or contradictory.
- The plan is stale or has a gap that blocks execution.
- The next step requires an undecided policy decision such as verification/test/git action policy.
