# Routing Rules

Single source of truth for how an active AsUsual topic routes each request: start-work gate routing, clarification routing, and the phase router. Other runtime files must reference this file instead of restating these rules.

Activation and first reads are owned by `using-as-usual` and `core-workflow.md`; this file applies after first reads. Skill descriptions and invocation conditions are owned by the Required Skills table in `core-workflow.md`. Recording routing decisions follows `as-usual-rules/logging-rules.md`.

## Routing Principle

- Choose the lightest sufficient gate for the current work instead of skipping gates.
- When borderline, choose the heavier gate.
- Derived status (`scripts/topic-log.py status --json`) is the default route source. An explicit user request for a later phase wins only when that phase's gate preconditions hold; otherwise name the missing gate, record it, and route through start-work gate routing instead of silently obeying either side.
- Record every routing decision in `audit.jsonl` through `scripts/topic-log.py`.

## 1. Start-Work Gate Routing

Purpose: after first reads, choose the lightest sufficient gate for the current request and topic status. `start-work` does not decide AsUsual activation; it is used only inside an already active AsUsual topic.

Route table:

| Route | Use When |
| --- | --- |
| `requirements` | The request is ambiguous, a user decision could change requirements/plan/implementation/risk/verification, or clear work still needs durable requirements review. |
| `plan` | There is a completed/current `requirements.md`, the user approved moving on to plan, and execution order, files/areas, and verification surface need to be defined. |
| `execute` | There are completed/current `requirements.md` and approved/current `plan.md`, the plan matches the latest request, and the user asked to execute. |
| `direct-execute` | The work is clear, trivial, low-risk, reversible, and does not create durable requirements/plan decisions. |
| `find-cause` | The request reports a bug or unexpected behavior whose root cause is unconfirmed, and the cause itself is the open question — writing `requirements.md` would mean guessing the cause. |

Detailed `direct-execute` allow and deny checks are owned by the `direct-execute` skill; `start-work` applies them when routing. Any high-risk operation denies `direct-execute`.

`find-cause` routes out of the coding topic into a separate work unit: record the routing decision in `audit.jsonl` through `scripts/topic-log.py`, then hand off to the `find-cause` skill, which owns the `.as-usual/issue/` investigation per `as-usual-rules/find-cause-workflow.md`. When the issue concludes, its `conclusion.md` feeds this topic's requirements (link both directions per that workflow's Conclusion rules). Do not write `requirements.md` for a cause-unknown bug instead of routing here.

`direct-execute` is a lightweight terminal path: it does not join the finalize/git-action path. If the user afterwards explicitly asks to commit or run another git action, handle it as ordinary chat; the `git-action` skill is for finalized topics only. Never run a git action without an explicit user request.

## 2. Clarification Routing

When a needed decision appears during requirements, plan, or execute writing or review, route it by shape:

- IF the decision involves a high-risk operation: use the High-Risk Operation Gate in `as-usual-rules/safety-rules.md`.
- ELSE IF it is broad ambiguity (multiple interdependent decisions, durable multi-option review, or topic-boundary change): route to `define-requirements` or `start-work`, record the routing through `scripts/topic-log.py`, and stop.
- ELSE (focused clarification, single decision resolvable in the current turn): ask in chat.
    - IF the answer is material: record it in `audit.jsonl` through `scripts/topic-log.py`, update the affected artifact (`requirements.md`/`plan.md`), and rerun the relevant review before continuing.
    - IF the answer is non-material: record it and continue.

The initial requirements question cycle is not clarification. Broad or initial define-requirements decisions always use file-backed `question-cN.md` cycles owned by `define-requirements`.

## 3. Phase Router

After first reads, route in this order. The router chooses which skill owns the request; procedure inside a phase (question cycles, chat-answer mapping, revision absorb-vs-route, finding dispositions) is owned by that skill.

```text
IF no topic folder exists:
    create the topic folder using the actual current date and lowercase kebab-case
    run scripts/topic-log.py init, confirm the initial request and topic.created event
    tell the user the topic path in one line
    apply start-work gate routing

IF the current request starts a new topic or the derived phase is unclear:
    apply start-work gate routing and invoke the routed skill
    IF route is DIRECT_EXECUTE: invoke direct-execute and STOP (terminal path, see §1)

IF the current request answers, confirms, or corrects question-cycle answers,
   or the user asks to write/update requirements:
    invoke define-requirements
    # it owns chat-answer mapping confirmation, answer validation,
    # next-cycle creation, and same-turn requirements synthesis

IF the topic is requirements-complete or plan-review AND the user requests a change
   to the completed artifact before the next approval:
    invoke the owner skill (define-requirements for requirements.md, writing-plan for plan.md)
    # its revision rules decide: absorb non-material changes and stay at the same status,
    # or follow Clarification Routing for material changes

IF the user approves moving from completed requirements to plan, or requests plan:
    IF requirements are missing, stale, or not requirements-complete:
        name the missing gate, record it, STOP
    ELSE:
        invoke writing-plan

IF the user requests execute:
    IF requirements.md or plan.md is missing:
        name the missing gate, record it, STOP
    IF the plan is stale or internally inconsistent:
        follow Clarification Routing (focused chat question for a single decision,
        otherwise route back to requirements/plan), STOP
    ELSE:
        invoke executing-plan
```

Post-execution routing is a lookup on derived status:

| Derived Phase | Next Action / Trigger | Route |
| --- | --- | --- |
| `execution-complete` | — | `review-execution` |
| `review-fixes-needed` | `address-review-findings` | `review-execution` (finding disposition rules owned there) |
| `review-complete` | `decide-code-cleanup` | `review-execution` |
| any review-recorded state | user approves code cleanup | `cleanup-code` |
| `review-complete` or `cleanup-complete` | `finalize` | `finalize` |
| `finalized` | `git-action-decision` + user chooses an action | `git-action` |

## 4. Failure Handling

When the same failure repeats, use this circuit breaker:

```text
IF the same action fails 3 times:
    STOP retrying the same approach
    record failure pattern through scripts/topic-log.py
    append audit event
    reassess whether the requirements, plan, environment, or assumption is wrong
    ask the user only if the next step requires a decision that files cannot answer
```

Reassessment is a routing decision: return to `executing-plan`, `writing-plan`, or `define-requirements` per Clarification Routing when an artifact or assumption is wrong. Do not hide failures with optimistic wording. Record the evidence and next required action per `as-usual-rules/logging-rules.md`.
