---
name: gathering-context
description: Use as the first step of any AsUsual work unit, and whenever context has to be gathered from the user. Interviews the user to settle open items and records the agreed decisions in contexts.md.
---

# Gathering Context

Every work unit starts here. This skill owns **all** conversation with the user
about what the work is: the questions, their shape, their order, and where the
answers land.

It is a general engine. It does not know which unit called it and must never
branch on one. The caller passes **a list of items that must be settled**; this
skill talks with the user until that list is settled, records the outcome, and
returns.

## Contract With The Caller

The caller provides:

- the work folder,
- the list of items to settle (what the caller cannot proceed without),
- anything already known, so it is not asked again.

This skill returns when every item is settled or the user chose to proceed on a
stated assumption. **Zero questions is a valid outcome** — when nothing on the
list is actually open, record that and return immediately. Do not manufacture
questions to justify the step.

## How To Ask

Interview in grilling style. The point is to reach a shared understanding, not to
fill a form.

- **Every question carries your recommended answer with its reason.** A question
  without a recommendation pushes the decision back to the user without helping
  them make it.
- **A recommendation is not an answer.** A bare approval — "go", "ok", or its
  local equivalent — accepts nothing in particular. When the reply does not
  identify what the user chose, ask that one question again rather than
  recording your own recommendation as their decision.
- **Never ask what the codebase, logs, or git history can answer.** Look it up.
  Use `explore-codebase` when the surface is unfamiliar.
- **Batch independent facts** when the answers do not depend on each other.
- **Ask judgment calls one at a time.** When the user must weigh evidence or
  trade-offs, a batch makes them answer blind. Ask, wait, then use the answer to
  shape the next question.
- **Resolve dependencies in order.** When one answer changes what the next
  question even is, do not ask both.
- Ask in chat. Never make the user open a file and write into it.

Stop when the list is settled. If a question keeps failing to converge after
about three rounds, say so plainly, state the assumption you would proceed on and
its risk, and let the user accept it or decide.

## Where Answers Go

Everything agreed goes into `contexts.md` in the work folder — one document, no
matter which stage produced it.

The three bands and their mutability are defined in `core-rules.md` §3. What
matters while writing them: the Decisions band holds what was agreed, not a
transcript — what was decided, and enough of why that a later session does not
re-litigate it. Never leave two contradicting decisions side by side for the
reader to resolve.

**Record each material decision** as you go:

```bash
python3 <plugin-root>/scripts/as-usual-record.py add --dir <work-dir> \
  --kind decision --summary "<what was decided>" --phase gathering-context
```

Material means it could change the requirements, the plan, the implementation
approach, the risk, or the verification. Wording and typo fixes are not.

## Deciding The Unit

When called from an `inbox` folder, the list to settle is exactly one item:
**which unit this work is**. Ask only what separates them — is the outcome code
or an understanding; is the approach already settled or does it need agreeing.
Once it is clear, record the decision, tell the caller, and let it `move` the
folder.

## Stop Conditions

Stop and wait when a question is outstanding. Do not answer your own question and
proceed.

## Anti-Patterns

- Branching on the calling unit (`if topic … if issue …`).
- Appending a reversed decision below the old one instead of editing it.
- Editing the append-only Q&A band.
- Continuing past an unanswered question by assuming the answer.
