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

- Treat the High-Risk Operation Gate in `core-workflow.md` as a hard gate.
- Route to `requirements` when material ambiguity exists or the work needs a reviewed `requirements.md`.
- Route to `plan` when `requirements.md` is complete/current, the user approved moving on to plan, and execution order or verification needs definition.
- Route to `execute` when `requirements.md` and approved/current `plan.md` exist and the user asks to execute.
- Route to `direct-execute` only for very simple, low-risk, reversible work.
- When borderline, choose the heavier gate.

## Route Table

Use the canonical Route table in `core-workflow.md` §4 (Start Work Gate Routing) to choose the route. Do not maintain a second copy here.

## Direct Execute Allow Conditions

Use `direct-execute` only when all conditions below are true.

- The request and expected outcome are clear.
- The change scope is small and isolated.
- It does not change public API, data model, auth/security, migration, deployment, dependency policy, or user-visible behavior.
- It does not include any high-risk operation from `core-workflow.md`.
- There is no decision the user must make among multiple viable approaches.
- The verification method is clear and can be run or recorded immediately.
- Failure would be easy to reverse.

Examples include documentation typo fixes, obvious formatting cleanup, single-file comment/copy corrections, read-only inspection, or a small mechanical step inside an already approved plan.

## Direct Execute Deny Conditions

Do not use `direct-execute` if any condition below is true.

- It is a new feature, behavior change, API change, schema change, or permission/security change.
- It requires a multi-file or multi-component design decision.
- It could change user-facing UX, product wording, business rules, or acceptance criteria.
- It asks for a test, release, commit, PR, or deploy policy that the topic has not yet decided.
- It includes file deletion, bulk formatting, package installation, dependency changes, DB migration or schema changes, environment/secret changes, CI/CD changes, deploy/release, git push, or force push.
- The latest request conflicts with an existing `requirements.md` or `plan.md`.
- The verification method is unclear or failure risk is high.
- There is no skip rationale to record in `audit.jsonl` beyond "it seems simple".

## Required Record

When a route is selected, record:

- selected route
- route reason
- skipped gates, if any
- next action, such as `answer-questions`, `write-requirements`, `approve-plan`, `write-plan`, `approve-execute`, `execute`, `review-execution`, `decide-code-cleanup`, `finalize`, or `git-action-decision`
- for direct-execute, the allow-condition rationale and verification plan
- for direct-execute completion, the result, verification outcome, and terminal next action

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
