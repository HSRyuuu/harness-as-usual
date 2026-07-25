---
name: run-topic
description: Use when AsUsual work is classified as a topic — development that needs the requirements agreed first. Owns the topic pipeline and routes each phase to its step skill.
---

# Run Topic

Owns the `topic` pipeline: development where the requirements have to be agreed
before anything is built.

This skill is a declaration, not a procedure. Each step is owned by its own
skill; this file says which steps apply, in what order, at what strength, and
which gates stand between them. Read `as-usual-rules/core-rules.md` first.

## Pipeline

```text
gathering-context → write-requirements → write-plan → execute-plan
                  → review-execution → cleanup-code? → finalize → git-action?
```

| Phase | Step skill | Applies | Strength |
| --- | --- | --- | --- |
| `gathering-context` | `gathering-context` | required | settle scope, constraints, and acceptance before writing anything |
| `write-requirements` | `write-requirements` | required | full `requirements.md` |
| `write-plan` | `write-plan` | required | full `plan.md`, ending in the pre-approval critical review |
| `execute-plan` | `execute-plan` | required | — |
| `review-execution` | `review-execution` | proposed by default | offer it; the user decides |
| `cleanup-code` | `cleanup-code` | optional | only on explicit approval |
| `finalize` | `finalize` | required | `report.md` + closure |
| `git-action` | `git-action` | on explicit choice only | — |

## Gates

- **Requirements before plan.** A topic that skips agreeing its requirements is
  not a topic — it is `direct-work`. If the work turns out not to need
  requirements, say so and let the user decide whether to keep the heavier path.
- **Plan review before execution approval** (core rule 7). `write-plan` runs it
  and records a `review` entry; the record helper refuses the execution approval
  without one.
- **Execution approval before executing.** Explicit, from the user.
- **Verification evidence before any completion claim** (core rule 3).
- **Finalize before a git action**, and only the action the user chose.

## Routing

Derive state, then route to the phase that owns it:

```bash
python3 <plugin-root>/scripts/as-usual-record.py status --dir <work-dir> --json
```

- The user asks for a later phase whose gate is not met: name the missing gate,
  record it, and stop. Do not silently obey and do not silently refuse.
- A completed artifact needs a change before the next approval: hand back to its
  owner skill (`write-requirements` for `requirements.md`, `write-plan` for
  `plan.md`), which decides whether to absorb it or reopen the earlier phase.
- The cause of something turns out to be unknown mid-topic: this topic stays as
  it is. Create a separate `issue` folder beside it and link the two
  (`core-rules.md` §7). Do not park the topic and do not guess the cause in
  `requirements.md`.

## Anti-Patterns

- Writing `requirements.md` for a bug whose cause is unconfirmed.
- Asking for execution approval before the plan has been critically reviewed.
- Treating `plan.md` as a progress ledger — progress belongs in `audit.jsonl`.
- Continuing into commit, PR, release, or deploy behavior after execution.
- Restating step procedures here instead of routing to the step skill.
