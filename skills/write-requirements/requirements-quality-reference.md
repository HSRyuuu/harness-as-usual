# Requirements Quality Reference

What a good `requirements.md` contains. Use it to make the document better; it
produces no checklist, no review status, and no review section inside
`requirements.md`. The user reviewing the requirements before approving the plan
is the real review.

## What To Check

Read `contexts.md` — the decisions the requirements are supposed to reflect —
the current `requirements.md`, and the project files it depends on. Then check:

- **Traceability** — the initial request comes from the top band of
  `contexts.md`, and every user decision traces to its Decisions band or a
  recorded `decision` event. Nothing material that was agreed is missing from
  scope, requirements, risks, constraints, or acceptance criteria.
- **Concreteness** — sections hold real content, not `TBD`, an unexplained
  `TODO`, a `<placeholder>`, or leftover example text. Requirements are grouped,
  specific rules rather than implementation wishes.
- **Constraint coverage** — validation, state transitions, concurrency,
  duplicate and conflict prevention, integrations, side effects, failure
  handling, authorization, and timing are explicit wherever they apply.
- **Consistency** — no two sections describe incompatible mechanisms for the
  same behavior. When inspecting the repository turns up a fact that would force
  a different mechanism, that lands in the requirements, a risk, or an accepted
  constraint before planning starts.
- **Labelled assumptions** — anything the requirements depend on but the user
  never confirmed appears under `Constraints & Assumptions` with its source and
  the risk if it is wrong. An unlabelled assumption buried in another section is
  the one to catch.
- **No open material decision** — nothing unresolved could still change the
  implementation, the risk, the verification, or the plan's scope.
- **Plan readiness** — a planner can infer the likely files, dependencies,
  constraints, and verification direction from this document alone, without chat
  memory and without a separate `spec.md`. Out Of Scope is specific enough to
  stop accidental expansion.

A section that has nothing in it is left out, and a section may be explicitly
none in the user's language. Do not manufacture risks, assumptions, or
non-functional requirements to fill one.

## Calibration

Worth fixing: anything that would cause a flawed plan, a wrong implementation, or
a misunderstanding by the user.

Not worth fixing: style preferences, minor wording, or a section being short when
it is still clear.

## Using This Reference

When something here is missing from `requirements.md` and it matters, fix the
document. When it needs a decision only the user can make, take that single item
through `gathering-context`, record the `decision`, then update the document.

Do not write a review status block, a checklist, or a findings list into
`requirements.md`. Improving the document is the entire output.
