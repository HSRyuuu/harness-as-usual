# Requirements Quality Reference

What a good `requirements.md` contains. Use it to make the document better; it
produces no checklist, no review status, and no review section inside
`requirements.md`. The user reviewing the requirements before approving the plan
is the real review.

## What To Look At

- `contexts.md` — the decisions the requirements are supposed to reflect
- the current `requirements.md`
- `templates/requirements.md`
- project files the requirements depend on

## Qualities

| Category | What To Check |
| --- | --- |
| Completeness | Required template sections are filled with concrete content. No `TBD`, unexplained `TODO`, placeholder bracket such as `<...>`, leftover example trace, or empty required section remains. |
| Human readability | A human developer can scan the document and understand what should be built, what should not be built, and what rules/constraints matter. |
| Agent readiness | An agent can use `requirements.md` as the single source for `plan.md` without relying on chat memory or a separate `spec.md`. |
| Source traceability | Initial request comes from the Initial Request section of `contexts.md`; user decisions trace to the Decisions section of `contexts.md` or recorded `decision` events. |
| Decision coverage | Every material decision in `contexts.md` is reflected in scope, requirements, risk, acceptance criteria, or constraints. |
| Domain rule clarity | `Domain Requirements` contains grouped, concrete business/domain rules rather than vague implementation wishes. |
| Constraint coverage | Important validation, state transition, concurrency, duplicate/conflict prevention, integration, side-effect, failure, authorization, timing, and verification constraints are explicit when relevant. |
| Consistency | Goal, scope, domain requirements, functional requirements, risks, and acceptance criteria do not contradict each other. |
| Technical decision consistency | The requirements do not describe two incompatible mechanisms for the same behavior. If repository inspection reveals a technical fact that would force a different implementation mechanism, the requirement, risk, or accepted constraint records it before planning. |
| Material ambiguity | No unresolved user decision could change implementation, risk, verification, or plan scope. |
| Assumptions | Any claim the requirements depend on but the user did not explicitly confirm appears in `Assumptions` with its source and the risk if it is wrong. Block unlabeled assumptions embedded in other sections. |
| Affected surface | `Affected Surface` is filled when the work is code-facing and the area is knowable, or set to a user-language none/N/A statement with a concrete reason. |
| Plan readiness | A planner can infer likely files/areas, dependencies, constraints, and verification direction from `requirements.md` alone. |
| Boundary clarity | Out-of-scope prevents accidental expansion. |
| None / N/A handling | Optional sections may be explicitly none. Accept none/N/A statements written in the user's language. Do not require invented NFRs, risks, assumptions, or affected files. |
| User-language consistency | Structural/canonical headings may stay canonical English or be consistently translated to the user's language, with order and count fixed; status values, source traces, code identifiers, commands, and paths stay canonical. Other user-facing prose should follow the user's preferred language. |
| YAGNI | The requirements do not add unrequested features or process beyond the topic. |

## Calibration

Worth fixing: anything that would cause a flawed plan, a wrong implementation, or a
misunderstanding by the user.

Not worth fixing: style preferences, minor wording, or a section being short when it
is still clear.

## Using This Reference

When something here is missing from `requirements.md` and it matters, fix the
document. When it needs a decision only the user can make, take that single item
through `gathering-context`, record the `decision`, then update the document.

Do not write a review status block, a checklist, or a findings list into
`requirements.md`. Improving the document is the entire output.
