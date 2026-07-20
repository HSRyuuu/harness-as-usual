# Logging Rules

Single source of truth for how AsUsual topic records are written, read, and interpreted. Other runtime files must reference this file instead of restating these rules. Command syntax is owned by `as-usual-rules/log-audit-commands.md`. Completion judgment (when a result may be recorded as done) is owned by `as-usual-rules/completion-rules.md`.

## Record Surfaces

- `topic.md` is a low-churn resume document for durable context: topic name, initial request, topic boundary, durable decisions, constraints, and linked question/requirements/plan/review/report/audit files. Do not use it as a current snapshot, task list, progress ledger, or verification log.
- `audit.jsonl` is the canonical append-only event history. Record facts, not a polished summary.
- Current state is derived, not remembered: phase, next action, linked artifacts, blockers, approvals, verification evidence, and remaining issues come from `scripts/topic-log.py status --topic-dir <topic-dir> --json`.

## Write Rules

- Update `topic.md` and `audit.jsonl` only through `scripts/topic-log.py`. Never hand-edit them. If the helper cannot express a needed runtime update, stop and report the missing helper capability.
- Prefer the phase-transition macro that matches the transition over composing multiple low-level `audit` calls.
- Initialize a new topic with `scripts/topic-log.py init`, which creates `topic.md`, creates `audit.jsonl`, records the initial request, and appends the first `topic.created` event.
- Use host-specific audit actors such as `codex` or `claude`; do not use the generic actor value `agent`.
- Append, never overwrite history with a summary.
- New audit events include typed observation fields: `status` (`success`, `warning`, or `error`), `summary`, `phase`, `nextAction`, and when applicable `errorKind`, `retryHint`, and `stopCondition`.
- `verification.recorded` events must include the `verification --verdict` value (`PASS | FAIL | INCONCLUSIVE`) in event data.
- Run `scripts/topic-log.py validate --topic-dir <topic-dir>` before claiming a topic is structurally complete. Use `scripts/topic-log.py record-sweep` for E2E, stale-reference, mirror, or harness quality evidence.

## Read Rules

- Re-read topic files from disk before phase decisions. Chat memory is supporting context only.
- Derive current state with `status --json` when the helper is available instead of hand-scanning raw events.
- Review detail files record their canonical verdict in YAML frontmatter `verdict`, and that verdict must match the corresponding audit status. This file/frontmatter/audit consistency applies regardless of host or subagent availability.

## Closed Vocabularies

These are the only valid recorded values. Their gate consequences are defined in `as-usual-rules/completion-rules.md`.

- Review verdicts: `passed | findings | blocked`
- Verification verdicts: `PASS | FAIL | INCONCLUSIVE`
- Implementer completion: `DONE | NEEDS_CONTEXT | BLOCKED`

## Audit Events

Topic lifecycle:

- `topic.created`
- `start_work.routed`
- `topic.finalized`
- `git_action.selected`

Requirements and plan:

- `question.created`
- `question.answered`
- `requirements.completed`
- `plan.completed`

Approvals:

- `approval.execution`
- `approval.high_risk`

Execution tasks:

- `task.started`
- `task.dispatched`
- `task.review_completed`
- `task.fix_requested`
- `task.fix_completed`
- `task.commit_recorded`
- `task.completed`
- `verification.recorded`
- `sweep.completed`
- `execution.completed`

Review and cleanup:

- `review.completed`
- `code_cleanup.skipped`
- `code_cleanup.completed`

Cross-cutting:

- `note.recorded`
- `decision.recorded`
- `blocker.recorded`
- `blocker.resolved`
- `artifact.recorded`

Self-improvement (finalize):

- `memory.candidate`
- `memory.recorded`
- `skill.created`
- `skill.candidate`

Failure control flow (the repeated-failure circuit breaker) is owned by `as-usual-rules/routing-rules.md`; recording the failure evidence follows the Write Rules above.
