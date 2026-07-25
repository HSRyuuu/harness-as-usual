---
name: cleanup-code
description: Use when the user explicitly approves code cleanup after execution review. Applies behavior-preserving improvements to the change surface and re-verifies.
---

# Cleanup Code

Improves the code that was just written without changing what it does: reuse
what already exists, cut ceremony, avoid waste, sit at the right level of
abstraction.

This runs **only on the user's explicit approval**, and only after the
correctness review. It is not a bug hunt — if it turns up a correctness problem,
that goes back through `review-execution`.

## Preconditions

- Execution is complete and its verification is recorded.
- `review-execution` ran, and its Critical and Important findings have
  dispositions.
- The user approved cleanup in this turn.
- The diff or changed files can be inspected.

## Reviewing

Four lenses — reuse, simplification, efficiency, and abstraction.
`cleanup-reviewer-prompt.md` in this directory defines them and the reviewer
contract: reviewers only report; applying and recording stay here.

Run them as parallel subagents when the host supports it, otherwise inline. All
four lenses get applied either way.

**Review only the changed code and the context needed to judge it.** Cleanup that
wanders into untouched code is scope creep wearing a different hat.

## Applying

Apply a finding only when it is:

- behavior-preserving,
- inside the approved change surface,
- consistent with what the work agreed,
- lower-risk than leaving the code alone,
- verifiable with the verification that already exists or something clearly
  related.

Do not apply speculative rewrites, architecture changes, new dependencies, public
API changes, schema changes, or anything that needs a new product decision. If a
finding is worth doing but fails these tests, note it as follow-up instead.

"No safe cleanup found" is a perfectly good outcome. Record it and move on.

## Re-Verifying

If any file changed, re-run the verification for the affected work — the commands
already recorded, or narrower ones that still cover the change.

```bash
python3 <plugin-root>/scripts/as-usual-record.py add --dir <work-dir> \
  --kind verification --verdict PASS \
  --summary "<command + actual result>" --phase cleanup-code
```

If it cannot be re-run, record `INCONCLUSIVE` with the reason. Behavior-preserving
is a claim about the code; the re-run is the evidence for it.

## Recording

When something was applied, append the cleanup outcome as a section in
`review.md` — the same document the execution review used. Do not create
separate per-lens files, and do not create `review.md` just to say nothing was
found; that outcome is the event below and nothing more.

```bash
python3 <plugin-root>/scripts/as-usual-record.py add --dir <work-dir> \
  --kind review --summary "cleanup: <what changed, or none>" --phase cleanup-code
```

Then route to `finalize`.

## Anti-Patterns

- Running without the user's explicit approval.
- Running before the correctness review.
- Using cleanup as the bug finder.
- Claiming behavior is preserved without re-running verification.
