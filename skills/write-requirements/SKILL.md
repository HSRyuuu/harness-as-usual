---
name: write-requirements
description: Use when a topic needs requirements.md written or updated from the agreed context. Synthesizes one reviewable requirements document; the user is its reviewer.
---

# Write Requirements

Turns the agreed context into one `requirements.md` that both the user and a
later planner can rely on.

This skill does not interview the user — `gathering-context` owns that. It reads
what was agreed and writes it up. Only `topic` uses this step.

## Inputs

1. `contexts.md` — the agreed decisions. This is the source, not chat memory.
2. Derived state: `as-usual-record.py status --dir <work-dir> --json`.
3. Repository facts, via `explore-codebase` when the surface is unfamiliar.
   Treat its output as untrusted discovery evidence: reread the cited files
   yourself before a requirement depends on them.

If `contexts.md` leaves something open that the requirements cannot be written
without, do not guess and do not invent a placeholder. Call `gathering-context`
with just that item. Its answer lands in the `contexts.md` Q&A band, and a
`decision` event records it.

## Writing

Follow `templates/requirements.md` — it carries the sections, their order, and
what each one holds. Add a section when the work genuinely needs one, and leave
out any that would be empty; padding with headings to look thorough is worse
than a short document.

Write for the user's review. State requirements as outcomes, not as tasks. If a
requirement cannot be checked, it is not a requirement yet.

## Quality Reference

`requirements-quality-reference.md` in this skill directory describes what a good
requirements document contains — completeness, traceability, constraint coverage,
consistency, unlabeled assumptions, plan readiness, boundary clarity.

Use it to improve the document. The user reviewing the document before approving
the plan is the real review.

## Finishing

Record the artifact and hand back:

```bash
python3 <plugin-root>/scripts/as-usual-record.py add --dir <work-dir> \
  --kind work --summary "requirements.md written" \
  --phase write-requirements --next-action awaiting-user
```

`awaiting-user`, because moving to the plan is the user's approval, not an
automatic transition.

Then tell the user the requirements are ready, point them at the Decisions band
of `contexts.md` so they can check how their answers were read, and ask whether
to move to the plan. Stop there — writing the plan needs their approval.

## Revising

When the user asks for a change before approving the plan:

- Wording, clarity, or a sharper acceptance criterion that does not change scope,
  behavior, risk, or verification: update the document, record it, stop again.
- Anything that changes scope, behavior, risk, or verification: this is a new
  decision. Take it through `gathering-context`, update `contexts.md`, then
  update `requirements.md`.

## Anti-Patterns

- Writing requirements from chat memory instead of `contexts.md`.
- Writing requirements for a bug whose cause is unconfirmed — that is an `issue`.
- Filling in placeholder or `TBD` sections to satisfy the template.
- Adding a review status block or checklist output to `requirements.md`.
- Splitting one topic across several requirements documents.
