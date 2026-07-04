---
name: finalize
description: Use when AsUsual is active and execution review is complete before closing a topic or asking which git action to run.
---

# Finalize

This skill closes the AsUsual topic record after execution and review. It summarizes what happened, records the final topic status, and asks the user which git action to run.

Use it only after `using-as-usual` has completed activation and first reads, `executing-plan` has completed, and `review-execution` has recorded its review result plus the code cleanup decision.

## Responsibility Boundary

| Skill | Responsibility |
| --- | --- |
| `executing-plan` | Implement the approved plan and record task-level verification |
| `review-execution` | Review changed code and handle optional code cleanup |
| `cleanup-code` | Apply approved cleanup and rerun relevant verification |
| `finalize` | Close the topic record and ask which git action to run |
| `git-action` | Run the selected post-finalize git action |
| `manage-self-improvement` | Analyze the topic and, after finalize gathers approval, record memory and create/patch skills |

`finalize` does not implement new work, run code review, run git commands, decide git policy alone, create PRs, release, deploy, or rewrite prior audit history. `finalize` gathers user approval for self-improvement candidates but delegates the actual memory record and skill create/patch to `manage-self-improvement`. The "no new work" rule applies to topic implementation, not to delegated self-improvement meta-artifacts.

## Preconditions

Before finalizing, confirm:

- The Finalize rules in `core-workflow.md` have been checked.
- `topic.md`, `audit.jsonl`, `requirements.md`, and `plan.md` have been read from disk.
- Execution completion is recorded.
- Review result is recorded.
- Code cleanup was either skipped or completed.
- Remaining issues and skipped verification are explicit.

If execution review or code cleanup decision is missing, return to `review-execution`. Do not close the topic optimistically.

## Inputs

Read and use these sources in this order:

1. `topic.md`
2. `audit.jsonl`
3. Derived status from `scripts/topic-log.py status --json`, when available
4. `requirements.md`
5. `plan.md`
6. Current git status and diff summary, when git is available

## Workflow

### Step 0: Self-Improvement Pass

Do not proceed to Step 1 until this pass has a recorded result (applied, skipped with reason, or "no candidates").

Before closing the record, trigger the `manage-self-improvement` skill (prefer a
subagent; inline fallback):

1. Pass 1 (propose, read-only): it returns proposed memory additions, skill
   create/patch candidates, and ambiguous items.
2. Approval: present the proposal item-by-item; ask the user directly about ambiguous
   items. finalize does not write self-improvement artifacts itself.
3. Pass 2 (apply): `manage-self-improvement` records approved memory (`record-memory`)
   and creates/patches skills (`record-skill --state created`), recording deferred
   candidates as `record-skill --state candidate`.

If nothing survives, record a "no candidates" note. Do not proceed to close without a
recorded self-improvement result.

### Step 1: Final Record Check

Confirm `topic.md` plus `audit.jsonl` can support a fresh-session resume:

- completed work
- verification performed, with exact commands and outcomes
- verification skipped and why
- execution review findings and disposition
- code cleanup decision and result
- troubleshooting
- lessons, when useful
- remaining issues or `None`

Also confirm these audit records are present when applicable:

- `approval.execution` exists before execution work.
- `approval.high_risk` exists for each approved high-risk operation.
- `review.completed` includes mode `independent`, `self`, or `local-prompt`.
- Host-generated events use host actor values such as `codex` or `claude`, not generic `agent`.
- User approval and selection helper commands may record `actor` as `user` when the user is the actor for that event.
- `audit.jsonl` events include monotonic `seq` values.

If these fields are missing, route back to the owning phase or record the missing helper capability. Do not finalize optimistically.

Run the structural validator and treat a failure as a blocker:

```bash
python3 <plugin-root>/scripts/topic-log.py validate --topic-dir <topic-dir>
```

If validation fails, route back to the owning phase or report the missing helper capability. Do not finalize while `validate` fails.

Fill missing operational details from recorded artifacts. Do not invent verification results.

### Step 2: Set Final Topic Status

Choose one status:

| Status | Use When |
| --- | --- |
| `complete` | Execution, verification, review, and code cleanup decision are recorded, with no remaining blocking issues. |
| `follow-up-needed` | The core topic work is usable, but remaining non-blocking Minor findings, accepted non-blocking risks, or deferred cleanup exist. Critical and Important findings must be fixed and re-reviewed or the topic is `blocked`. |
| `blocked` | The topic cannot be completed without external input, failed verification, missing dependency, or unresolved Critical/Important review findings. |

Create or update `report.md` in the topic folder using `templates/report.md`. This is the concise user-facing final report, not a replacement for `audit.jsonl`. Write user-facing prose in the user's current or clearly preferred language, while preserving exact commands, paths, status values, and technical identifiers.

Include:

- topic status, phase, timestamps, and next action
- implemented changes
- important decisions and constraints
- exact verification commands and outcomes
- execution review result and `code-review-report.md` link or `None`
- code cleanup decision and result
- remaining issues or `None`
- git action decision/request status

Use:

```bash
python3 scripts/topic-log.py finalize-topic \
  --topic-dir <topic-dir> \
  --status <complete|follow-up-needed|blocked> \
  --summary "<summary>" \
  --report report.md
```

This records `topic.finalized`, derives phase `finalized`, derives next action `git-action-decision`, and records the report artifact.

After `finalize-topic`, confirm `status --json` derives phase `finalized`, then re-run the structural validator so the finalize invariants are checked:

```bash
python3 <plugin-root>/scripts/topic-log.py validate --topic-dir <topic-dir>
```

If validation fails, route back to the owning phase or report the missing helper capability. Do not treat the topic as finalized while `validate` fails.

### Step 3: Ask Git Action Decision

Ask the user which git action to run. Do not run git commands automatically.

Canonical prompt:

```text
Topic finalized. Which git action would you like me to run?

- none
- commit
- commit + push
- commit + push + PR
```

If the user chooses an action in a later turn, invoke `git-action`. Keep commit/push/PR/release/deploy behavior outside this skill.

## State And Audit

Use `scripts/topic-log.py` from the plugin root for every audit update. Prefer `finalize-topic` for topic closure. Do not hand-edit `audit.jsonl`; if the helper cannot express the finalization update, stop and report the missing helper capability.

Append facts to `audit.jsonl`; do not rewrite old events into a summary.

## Anti-Patterns

- Finalizing before execution review is recorded.
- Treating code cleanup as mandatory.
- Marking `complete` while Critical review findings remain unresolved.
- Asking a broad "what next?" instead of the git action decision.
- Running git commands, creating a PR, releasing, or deploying from `finalize`.
- Treating `commit`, `push`, or `PR` as selected before the user chooses an action.
- Closing the topic without running the self-improvement pass.
- Writing memory or creating skills directly from `finalize` instead of delegating to `manage-self-improvement`.
- Reflecting candidates without explicit user approval.
