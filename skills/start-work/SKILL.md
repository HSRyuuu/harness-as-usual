---
name: start-work
description: Use after AsUsual is active and first reads are complete to route a new or resumed topic to requirements, plan, execute, or direct-execute.
---

# Start Work

This skill handles gate routing for the AsUsual runtime workflow.

Use it only after `using-as-usual` has completed activation and first reads. For a new topic, `using-as-usual` must already have created `topic.md` and `audit.jsonl`, recorded the initial request in `topic.md`, and appended the `topic.created` audit event.

The goal of `start-work` is not to skip gates; it is to choose the lightest sufficient gate for the current work.

## Inputs

Before routing, confirm:

- current user request
- active topic `topic.md`
- active topic `audit.jsonl`
- `topic.md#Initial Request` and `topic.created` capture the initial request for this topic
- derived status from `python3 <plugin-root>/scripts/topic-log.py status --topic-dir <topic-dir> --json`, when available
- linked `question-cN.md`, `requirements.md`, and `plan.md`
- minimum target project context needed for routing
- freshness of the latest request versus existing artifacts

## Routing Principle

Use the canonical routing principle and Route table in `as-usual-rules/routing-rules.md` (Start-Work Gate Routing); do not maintain a second copy here. Treat the High-Risk Operation Gate as a hard gate, and when borderline, choose the heavier gate.

## Route Table

Use the canonical Route table in `as-usual-rules/routing-rules.md` (Start-Work Gate Routing) to choose the route. Do not maintain a second copy here.

## Direct Execute Gate Reference

The `direct-execute` allow and deny conditions have a single source in `skills/direct-execute/SKILL.md`. Read and apply those conditions when routing, and do not maintain a copy here. Any high-risk operation denies `direct-execute`.

## Required Record

When a route is selected, record:

- selected route
- route reason
- skipped gates, if any
- next action, such as `answer-questions`, `write-requirements`, `approve-plan`, `write-plan`, `approve-execute`, `execute`, `review-execution`, `decide-code-cleanup`, `finalize`, or `git-action-decision`
- for direct-execute, the allow-condition rationale and verification plan

Use `scripts/topic-log.py route-start-work` from the plugin root for route recording:

```bash
python3 <plugin-root>/scripts/topic-log.py route-start-work \
  --topic-dir <topic-dir> \
  --route <requirements|plan|execute|direct-execute> \
  --reason "<reason>"
```

Do not hand-edit `audit.jsonl`.

For the `requirements` route, the helper defaults `nextAction` to `answer-questions` because material ambiguity is the safer default. If no question cycle is needed and the request is ready for a durable requirements draft, call `route-start-work --next-action write-requirements`.

When the route is `requirements`, hand off to `define-requirements`. It creates/validates `question-cN.md` when needed, writes/reviews `requirements.md`, and stops at `requirements-complete`.

When the route is `plan`, hand off to `writing-plan`. It analyzes dependencies, writes/reviews `plan.md`, records `plan.completed`, asks for execution approval, and stops.

When the route is `execute`, hand off to `executing-plan`. It rereads topic/audit/requirements/plan artifacts, critically reviews the plan, executes tasks in the approved execution mode, records audit events for progress, task review loops, sweeps, and verification, then invokes `review-execution` after successful execution completion or stops at a blocker.

When the route is `direct-execute`, hand off to `direct-execute`. It executes the trivial work and records the result, verification, and terminal completion (`direct-execute-complete`).
