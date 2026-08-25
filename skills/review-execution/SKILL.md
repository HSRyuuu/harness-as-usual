---
name: review-execution
description: Use after execution completes to review the actual changes against what was asked. Records findings in review.md and drives them to a disposition before the work closes.
---

# Review Execution

Reviews what was actually built against what was asked, by reading the real diff
rather than the summary of it.

`topic` offers this by default; `direct-work` offers it when the change was broad
or touched something delicate. Either way the user decides whether it runs — but
once it runs, its findings have to reach a disposition before the work closes.

## Preconditions

- Execution is recorded complete, with verification evidence (or a recorded
  reason it could not be obtained).
- `requirements.md` / `plan.md` and `contexts.md` have been read from disk.
- The diff or the changed files can be inspected.

If execution did not finish, go back to `execute-plan`. Never review from chat
memory. When the diff genuinely cannot be inspected, review against the files
`plan.md` and `audit.jsonl` name, and record that the coverage was reduced and
why — a review run on less evidence must not read like a full one.

## Reviewing

**Read the actual changes.** `git diff` or the changed files themselves. An
execution summary is a claim about the diff, not the diff.

`code-reviewer-prompt.md` in this directory holds the reviewer brief — what to
check and what counts as a reportable finding. Use it when dispatching a
separate reviewer; the reviewer reports, and recording stays here.

Fill `{SAFETY_RULES_PATH}` with the installed plugin's own
`as-usual-rules/safety-rules.md` — resolve `<plugin-root>` the same way the
record commands do and pass the resolved absolute path, not a repo-relative one.
The reviewer reads the gate from the authority instead of from a copy that
drifts. If it returns `blocked` because that file was unreadable, treat the
safety half of the review as not done: fix the path and re-run it, or record
that the coverage was reduced and why. A `blocked` reviewer is not a clean one.

**The implementer does not clear their own work.** When the host supports it,
run the review as a separate agent or subagent, giving it the artifacts, the
diff, and the recorded evidence — not the conversation. When reviewing inline,
the verdict has to come from re-reading the files, diff, and evidence, not from
restating what you believed while writing them.

A review that finds nothing is a real result when the implementation matches the
requirements, the plan, and the surrounding code. Prefer few high-confidence
findings over speculative noise, and cite file and line.

## Recording

Write findings to `review.md` in the work folder, following `templates/review.md`,
with the frontmatter placeholders replaced by real values (`core-rules.md` §3).
One document per work unit: later task reviews and cleanup reviews append their
own sections to it rather than creating new files.

| Severity | Meaning |
| --- | --- |
| `Critical` | the work cannot honestly be called done with this outstanding |
| `Important` | must be resolved before the work closes |
| `Minor` | polish or follow-up; never blocking |

```bash
python3 <plugin-root>/scripts/as-usual-record.py add --dir <work-dir> \
  --kind review --summary "<verdict + counts + what matters>" \
  --phase review-execution --data critical=0 --data important=1 --data minor=2 \
  --data mode=independent
```

`mode` is `independent` when a separate agent reviewed, `inline` when you did.
Record the one that happened: a later session reads this to know how hard the
work was actually checked, and an inline pass summarized as an independent one
tells it the opposite. The verdict in the event and the one in `review.md` are
the same word — two answers in the record is worse than either.

When there are no findings, record that; do not create an empty `review.md`.

## Dispositions

Every Critical and Important finding reaches one of these before the work closes:

- **fixed** — and re-reviewed to a clean result,
- **rejected** — with a concrete technical reason, and re-reviewed.

An `Important` finding has one more way out: **accepted by the user** — the user
was told the risk in plain terms and chose to ship anyway. Record the decision
and who made it. `Critical` has no such door: consent decides whether to ship,
not whether the work is done.

`Minor` findings may simply be deferred.

If fixes need implementation, route back: `execute-plan` when the existing plan
covers them, otherwise `write-plan` or `write-requirements`. Do not implement
fixes inside this skill and then review your own fix in the same breath.

If a Critical finding is left unresolved, record a `blocker` and set the unit to
`--phase blocked --next-action awaiting-user`. It stays **open** — blocked is a
unit waiting on a decision, not a way to close one, and there is no closing event
for it. Say so plainly; it is a real state, not a failure to report.

## Handing Back

Summarize for the user in this order: what was implemented, what the verification
showed, what the review found. Put the next decision at the bottom, not the top.

Then offer cleanup, in the user's language — clean up now, or close the work.
Code cleanup is optional and never runs on its own.

Cleanup is reuse, simplification, efficiency, and abstraction level — not bug
hunting. If cleanup later turns up a correctness bug, that comes back through
here, not through cleanup's own disposition.

Invoke the AsUsual `cleanup-code` skill when approved. Do not call a host slash
command such as `/simplify`.

## Anti-Patterns

- Creating a separate report file per review instead of appending to `review.md`.
- Asking about cleanup while a Critical finding has no disposition.
- Recording `accepted by the user` without having told them the actual risk, or
  recording it at all for a Critical finding.
- Treating cleanup as the bug finder.
- Forcing fixes for Minor findings.
