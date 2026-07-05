# AsUsual Topic Log Audit Commands

Canonical reference for the `scripts/topic-log.py` commands that write `topic.md` and `audit.jsonl`. `core-workflow.md` and the runtime skills reference this file; do not maintain a second command list elsewhere.

`<plugin-root>` is the installed AsUsual plugin root (the directory containing `scripts/` and `skills/`); resolve it from the SessionStart hook announcement or the parent directory of the running skill:

```bash
python3 <plugin-root>/scripts/topic-log.py <command> --topic-dir <topic-dir> ...
```

## Usage Rules

- Write `topic.md` and `audit.jsonl` only through `scripts/topic-log.py`. Never hand-edit them.
- Prefer the highest-level command that matches the transition over composing multiple low-level `audit` calls.
- If the helper cannot express a needed update, stop and report the missing helper capability so the helper can be extended. Do not hand-edit as a workaround.

## Command Categories

Commands are grouped by role. **Phase-transition macros** move the topic across a phase boundary and are the preferred way to record those transitions. **In-phase recorders** append one evidence/event during a phase without changing the overall phase. **Read-only** commands derive or validate state and write nothing.

### Initialization

- `init`: create `topic.md` and `audit.jsonl`, record the initial request, and append the first `topic.created` event.

### Phase-Transition Macros (preferred)

Each sets phase and next action, links the phase artifact, and appends the typed event in one call.

- `route-start-work`: record the start-work route, reason, skipped gates, and next action.
- `complete-requirements`: record `requirements-complete`, link `requirements.md`, and append typed audit.
- `complete-plan`: record `plan-review`, link `plan.md`, and append typed audit.
- `complete-execution`: record `execution-complete` and route to review.
- `record-review`: record `review-complete` (when `--status passed`) or `review-fixes-needed`, link `code-review-report.md` when present, and route to the code cleanup decision or review follow-up.
- `skip-code-cleanup`: record the explicit code cleanup skip decision and route to finalize.
- `finalize-topic`: record final status, link `report.md`, and request the git action.
- `select-git-action`: record the chosen post-finalize git action.

### Requirements-Phase Recorders

- `record-question`: record one `question.created` event for a `question-cN.md` file (next action `answer-questions`).
- `answer-question`: record one `question.answered` event for a `question-cN.md` file; keeps next action at `answer-questions` until answers are validated.
- `decision`: record a durable decision extracted from validated answers, with its source trace.

### Execution-Phase Recorders

- `approve-execution`: record the fresh execution approval.
- `approve-high-risk`: record a fresh high-risk operation approval with operation id, description, approver, and rollback.
- `dispatch-task`: record one `task.dispatched` event for a subagent-driven task.
- `complete-task`: record one execution task result and optional verification evidence.
- `record-task-review`: record one task-level review verdict with finding counts.
- `record-task-fix`: record a task fix request or completion for a specific finding.
- `record-task-commit`: record a task commit boundary with its SHA.
- `record-sweep`: record final or task sweep evidence (E2E, stale-reference, mirror, or harness quality).
- `verification`: record one verification event with command, result, and `--verdict` (`PASS | FAIL | INCONCLUSIVE`). The verdict value must appear in event data.

### Cross-Cutting Recorders

- `note`: record a freeform note; use `--durable-topic-note` for durable `topic.md` context.
- `blocker`: record a blocker event with its id.
- `artifact`: record or append one artifact link.

### Self-Improvement Recorders (finalize)

- `record-memory-candidate`: propose a memory or skill candidate for later review.
- `record-memory`: record an approved long-term memory write.
- `record-skill`: record a created or candidate skill (new or patch).

### Low-Level Escape Hatch

- `audit`: append one generic audit event when no higher-level command fits. Prefer a phase macro or recorder when one matches; use `audit` only for events the macros do not cover.

### Read-Only (no writes)

- `status` (`--json`): derive phase, next action, linked artifacts, blockers, approvals, verification evidence, and remaining issues.
- `validate`: validate `topic.md` and `audit.jsonl` structure before claiming a topic is structurally complete.

### Deprecated

- `skip-simplify`: deprecated alias for `skip-code-cleanup`; use `skip-code-cleanup`.
