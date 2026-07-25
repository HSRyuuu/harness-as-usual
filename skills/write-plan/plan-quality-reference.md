# Plan Quality Reference

What a good `plan.md` contains, and what the pre-approval critical review in
`write-plan` should be looking for. This is a **reference, not a checklist to
fill in** — the review is required (core rule 7), but its output is a better
plan plus one `review` event, never a review section inside `plan.md`.

A good plan is a complete, dependency-ordered execution contract: a separate
executor could implement the tasks in order from `plan.md` alone, without chat
memory and without editing the plan to track progress.

## What To Check

Read `contexts.md`, `requirements.md` (when the unit has one), the current
`plan.md`, and the project files the plan cites. Then check:

- **Coverage** — every accepted acceptance criterion maps to a task, and the
  Acceptance Criteria Coverage section shows which. A criterion with no task
  behind it is a gap; a task with no criterion or agreed scope behind it is
  scope creep.
- **Consistency** — the plan does not silently replace, reinterpret, or
  contradict a mechanism the requirements describe. If inspecting the project
  forced a different mechanism, that decision was recorded before the plan was
  finished.
- **Ordering** — the task order respects real dependencies: what each task
  produces, what later tasks consume, names and interfaces agreeing across
  tasks.
- **Concreteness** — each task names real files (opened, not guessed), and no
  `TBD`, placeholder, or "similar to Task N" stand-in remains. Behavior with
  edge cases — parsing, dispatch, state transitions, malformed input — is
  specified precisely enough that executor and tests would agree; use a small
  table or examples where prose leaves room.
- **Verification** — each task's Verification is a runnable command with an
  expected result, exercising the changed behavior rather than proving it
  compiles. The Verification Strategy covers the change end to end and names
  anything only checkable manually.
- **Safety** — high-risk operations (`safety-rules.md`) are named in the task's
  Safety section with a concrete rollback, and naming them grants nothing —
  each still needs fresh approval immediately before it runs. Local,
  reversible, test-only work is not over-classified as high risk.
- **Restraint** — the plan decides no test, CI, commit, PR, release, or deploy
  policy the work never agreed, and carries no progress ledger or review
  status block.

## Calibration

Worth fixing: anything that would make the implementation wrong or the plan
non-executable.

Not worth fixing: style preferences, minor wording, or a section being short
when it is still clear and executable.

## Using This Reference

When something here is wrong in `plan.md`, fix the plan — a better plan is the
point, not a list of findings. When the fix needs a decision only the user can
make, take that item through `gathering-context`, record it, update
`requirements.md` if it moved, then revise the plan.

Record one `review` event summarizing what you found and what you changed. Do
not write a review status block or checklist into `plan.md`.
