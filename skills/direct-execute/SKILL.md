---
name: direct-execute
description: Use when the user directly invokes direct-execute for fast trivial work, or when start-work routes an active AsUsual topic to direct-execute.
---

# Direct Execute

## Overview

This skill owns the complete `direct-execute` contract: the allow and deny conditions, the start-work-routed execution path, and the recordless direct entrypoint.

It is a lightweight terminal path for clear, trivial, low-risk, reversible work. It does not join the `review-execution`, `finalize`, or `git-action` pipeline.

## Responsibility Boundary

| Skill | Responsibility |
| --- | --- |
| `using-as-usual` | Activate AsUsual, perform first reads, and initialize a topic before normal workflow routing |
| `start-work` | Read and apply this skill's allow/deny conditions, select the lightest sufficient route, and record the route |
| `direct-execute` | Own allow/deny conditions and execute either the routed topic path or the recordless direct entry path |

The allow and deny conditions below are the single source of truth. `start-work` references and applies them when routing; do not keep a second copy in another runtime file.

## Allow Conditions

Use `direct-execute` only when all conditions below are true.

- The request and expected outcome are clear.
- The change scope is small and isolated.
- It does not change public API, data model, auth/security, migration, deployment, dependency policy, or user-visible behavior.
- It does not include any high-risk operation from `core-workflow.md`.
- There is no decision the user must make among multiple viable approaches.
- The verification method is clear and can be run or recorded immediately.
- Failure would be easy to reverse.

Examples include documentation typo fixes, obvious formatting cleanup, single-file comment/copy corrections, read-only inspection, or a small mechanical step inside an already approved plan.

## Deny Conditions

Do not use `direct-execute` if any condition below is true.

- It is a new feature, behavior change, API change, schema change, or permission/security change.
- It requires a multi-file or multi-component design decision.
- It could change user-facing UX, product wording, business rules, or acceptance criteria.
- It asks for a test, release, commit, PR, or deploy policy that the topic has not yet decided.
- It includes file deletion, bulk formatting, package installation, dependency changes, DB migration or schema changes, environment/secret changes, CI/CD changes, deploy/release, git push, or force push.
- The latest request conflicts with an existing `requirements.md` or `plan.md`.
- The verification method is unclear or failure risk is high.
- There is no skip rationale to record in `audit.jsonl` beyond "it seems simple".

The high-risk operation definition in `core-workflow.md` is a hard gate. High-risk work is never allowed through either entry path.

## Entry Selection

- **Routed Entry**: use when `start-work` selected the `direct-execute` route for an active topic and recorded the route.
- **Direct Entry**: use when the user explicitly invokes `/as-usual:direct-execute` without going through `using-as-usual` and `start-work`.

Do not silently switch entry paths. A routed entry keeps its topic and audit contract; a direct entry remains recordless unless the user chooses the normal start-work route after a deny decision.

## Routed Entry

### Preconditions

- `start-work` read and applied this skill's allow/deny conditions.
- `start-work` recorded `route-start-work --route direct-execute` with the allow-condition rationale, skipped gates, and verification plan.
- The active topic directory is available.

### Workflow

1. Execute the approved trivial work.
2. Run the clear, immediate verification method recorded by `start-work`.
3. Record the result, verification outcome, and terminal next action:

```bash
python3 <plugin-root>/scripts/topic-log.py audit \
  --topic-dir <topic-dir> \
  --phase direct-execute-complete \
  --next-action none \
  --summary "<result and verification>"
```

4. Report the result and verification evidence to the user.

This is a lightweight terminal path. Do not continue to `review-execution`, `finalize`, or `git-action`. If the user later explicitly asks for a commit or another git action, handle it as ordinary chat, and never run a git action without that explicit request.

## Direct Entry

Direct entry does not activate the topic workflow or perform AsUsual first reads. Apply the following checks in order; the first matching rule wins.

1. **High-risk operation present**: refuse direct execution. Explain the high-risk reason and guide the user to the normal `using-as-usual` / `start-work` gated path. Do not offer a confirmation that can override the refusal.
2. **One or more non-high-risk deny conditions present**: show the deny reasons once and ask exactly once whether to proceed directly or route through `using-as-usual` / `start-work`.
   - If the user chooses direct execution, perform the work and verify it.
   - If the user chooses routing, hand off to the normal AsUsual workflow; topic creation and audit recording begin only after that handoff.
3. **All allow conditions satisfied**: execute immediately and verify the result.

The direct entry path is recordless:

- Do not create a topic folder.
- Do not create or update `audit.jsonl`, even when an active topic already exists.
- Do not call `scripts/topic-log.py` for the direct work.
- The direct work is not a hand-off or resume target.

After execution, report the result and the verification evidence in chat. If verification could not be run, report `not verified because ...` with the concrete reason.

## Anti-Patterns

- Repeating the deny confirmation more than once or trying to persuade the user after their choice.
- Allowing a high-risk operation after confirmation.
- Creating topic artifacts or audit records from Direct Entry.
- Copying the allow/deny condition lists into `start-work`, `core-workflow.md`, or another runtime file.
- Omitting the `direct-execute-complete` terminal record from Routed Entry.
- Running a git action without an explicit user request.
