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

If there is no work folder — no `contexts.md` and `audit.jsonl` to record into —
this skill has nothing to write to. Route to `using-as-usual`, which decides the
unit and creates it (core rule 6), and come back.

This skill returns when every item is settled or the user chose to proceed on a
stated assumption. **Zero questions is a valid outcome** — when nothing on the
list is actually open, record that and return immediately. Do not manufacture
questions to justify the step.

That licenses a short interview, never a silent one. An item the user owns is
open until they answer it, however obvious their answer seems.

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
- **Always ask what is the user's to decide, however clear the evidence looks.**
  Looking things up settles *facts*. It never settles *ownership*. These stay the
  user's no matter what the code says:
  - **what is in and out of scope** — which files, directories, and surfaces this
    unit covers, and what is deliberately left out;
  - **how far "done" reaches** — what gets verified, and what is left to a later
    unit;
  - **anything whose cost lands outside this repository** — a deploy step, a
    manual operation, another team's work.

  Evidence shapes your *recommendation* on these. It never replaces the answer.
  "The reason was clear in the code" is a reason to recommend confidently, not a
  reason to skip the question.
- **An assumption is not a substitute for a question.** Proceeding on a stated
  assumption is what happens *after* asking and failing to converge — never
  instead of asking. Writing an unasked scope decision into "Constraints &
  Assumptions" and moving on is the specific failure this rule exists to stop:
  the user never saw the choice, and the record reads as though they agreed to it.
- **Report what you decided under delegation.** When the user hands you a
  judgment — "you decide", "use your judgment" — the decision is yours but the
  report is not optional. Say in chat what you chose, what you excluded, and why.
  A decision the user can only discover by reading `contexts.md` later was not
  delegated to you; it was hidden from them.
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
**which unit this work is**. Ask what the two questions in `core-rules.md` §2
ask, in that order and in those terms — do not paraphrase them into a different
test here. Once it is clear, record the decision, tell the caller, and let it
`move` the folder.

## Stop Conditions

Stop and wait when a question is outstanding. Do not answer your own question and
proceed.

## Anti-Patterns

- Deciding scope alone because the evidence looked clear.
- Recording an unasked decision as an assumption, a constraint, or a risk.
- Exercising a delegated judgment without telling the user what it excluded.
- Branching on the calling unit (`if topic … if issue …`).
- Appending a reversed decision below the old one instead of editing it.
- Editing the append-only Q&A band.
- Continuing past an unanswered question by assuming the answer.
