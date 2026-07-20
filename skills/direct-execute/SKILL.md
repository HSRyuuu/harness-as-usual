---
name: direct-execute
description: Use when the user directly invokes direct-execute for fast clear low-risk work, or when start-work routes an active AsUsual topic to direct-execute.
---

# Direct Execute

## Overview

This skill owns the complete `direct-execute` contract: the allow and deny conditions, the start-work-routed execution path, and the recordless direct entrypoint.

It is a lightweight terminal path for clear, low-risk, reversible work. The gate is ambiguity and risk, not size: a larger but unambiguous, low-risk, reversible change can go direct. It does not join the `review-execution`, `finalize`, or `git-action` pipeline.

A behavior change is not categorically excluded. What is excluded is contract and product surface — public API, data model, auth/security, migration, deployment, dependency policy, user-facing UX/wording, business rules, and acceptance criteria — and anything ambiguous, risky, or hard to reverse. An internal behavior change with one obviously correct outcome and an immediate runnable check (for example, fixing an internal off-by-one covered by a test, or correcting a log level) is gated on that risk profile, not on the "behavior change" label. When in doubt about whether a behavior change touches a protected surface, route to the gated path.

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
- It does not change a protected contract or product surface: public API, data model, auth/security, migration, deployment, or dependency policy, and no user-facing UX, product wording, business rule, or acceptance criterion (those are denied below).
- Any behavior change it makes is internal, has one obviously correct outcome, and is exercised by the immediate verification below — not defended by reasoning alone.
- It does not include any high-risk operation from `as-usual-rules/safety-rules.md`.
- There is no decision the user must make among multiple viable approaches.
- The verification method is clear and can be run or recorded immediately. For a behavior change, that verification must actually exercise the changed behavior (a runnable test or check), not merely confirm the code compiles.
- Failure would be easy to reverse.

Scope size is not an allow condition. A change that spans several files or is non-trivial in volume still qualifies when it is unambiguous, low-risk, and reversible. What disqualifies it is ambiguity (an open design decision) or risk, not size.

Examples include documentation typo fixes, obvious formatting cleanup, comment/copy corrections, read-only inspection, a mechanical rename across several files, an internal-only behavior fix with an obviously correct outcome and a runnable test, or a small step inside an already approved plan.

## Deny Conditions

Do not use `direct-execute` if any condition below is true.

- It is a new feature, API change, schema change, or permission/security change. An internal behavior fix is not disqualified merely for being a behavior change, but it must clear the protected-surface, obvious-outcome, and immediate-verification allow conditions above.
- It is a behavior change whose correct outcome is not obvious, or that has no immediate runnable check exercising the changed behavior.
- It requires an unresolved design decision (which approach, which interface, which trade-off). A change that touches many files but has one obvious correct shape is not disqualified by this.
- It could change user-facing UX, product wording, business rules, or acceptance criteria.
- It asks for a test, release, commit, PR, or deploy policy that the topic has not yet decided.
- It includes file deletion, bulk formatting, package installation, dependency changes, DB migration or schema changes, environment/secret changes, CI/CD changes, deploy/release, git push, or force push.
- The latest request conflicts with an existing `requirements.md` or `plan.md`.
- The verification method is unclear or failure risk is high.
- There is no skip rationale to record in `audit.jsonl` beyond "it seems simple".

The high-risk operation definition in `as-usual-rules/safety-rules.md` is a hard gate. High-risk work is never allowed through either entry path.

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

1. Execute the approved work.
2. Run the clear, immediate verification method recorded by `start-work`. Verification evidence follows `as-usual-rules/completion-rules.md`: evidence must match the surface, and an unverifiable result is `INCONCLUSIVE`, not done.
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
2. **Active-topic scope overlap**: if an active (non-finalized) topic exists under `.as-usual/topic/` and the requested work falls within that topic's scope (its files/areas, requirements, or plan), do not execute recordless. Recordless direct entry may not silently change files that an active topic's `audit.jsonl` makes claims about, because that desyncs the topic record from the working tree and breaks later hand-off/resume. Route to `using-as-usual` / `start-work` so the change is recorded on the topic. This is a hard route, not an ask-once confirmation. Checking this is a minimal glance at whether an active topic exists and whether the target files are its subject — not full first reads.
3. **One or more non-high-risk deny conditions present**: show the deny reasons once and ask exactly once whether to proceed directly or route through `using-as-usual` / `start-work`.
   - If the user chooses direct execution, perform the work and verify it.
   - If the user chooses routing, hand off to the normal AsUsual workflow; topic creation and audit recording begin only after that handoff.
4. **All allow conditions satisfied**: execute immediately and verify the result.

Once the checks above allow direct execution (the work is not within any active topic's scope), the direct entry path is recordless:

- Do not create a topic folder.
- Do not create or update `audit.jsonl`. An active topic may coexist, but its records stay untouched precisely because work overlapping its scope was already routed out by check 2 above — recordless direct work is only for changes outside any active topic's subject.
- Do not call `scripts/topic-log.py` for the direct work.
- The direct work is not a hand-off or resume target.

After execution, report the result and the verification evidence in chat. If verification could not be run, report `not verified because ...` with the concrete reason.

## Anti-Patterns

- Repeating the deny confirmation more than once or trying to persuade the user after their choice.
- Allowing a high-risk operation after confirmation.
- Creating topic artifacts or audit records from Direct Entry.
- Executing recordless Direct Entry work that falls within an active topic's scope instead of routing it back so the change is recorded on that topic.
- Copying the allow/deny condition lists into `start-work`, `core-workflow.md`, or another runtime file.
- Omitting the `direct-execute-complete` terminal record from Routed Entry.
- Running a git action without an explicit user request.
