---
unit: <topic | direct-work | issue>
slug: <yyyy-MM-dd-slug>
created: <yyyy-MM-dd>
---

# Conclusion

## Confirmed Cause / Direction

(The confirmed root cause, or the confirmed solution or improvement direction.
State it as what is now known to be true, not as what is suspected.)

## Supporting Evidence

(What established it, citing seq numbers — e.g. #12, #18. If a hypothesis was
confirmed and later overturned, say so and cite both.)

## Reproduction

(How the problem was reproduced. If it could not be, say so explicitly and why —
"could not reproduce because …" is a legitimate result, not a gap to hide.)

## Decomposition

(Only when the finding opens **more than one** piece of follow-up work. A single
follow-up with the same boundary is a `move`, not a split — omit this section.)

| # | Unit & slug | Scope | Depends on | Covers |
| --- | --- | --- | --- | --- |
| 1 | `topic/yyyy-MM-dd-<slug>` | what it changes, and its boundary | — | which findings above |

Every finding above lands in exactly one row. A row covering nothing is not
follow-up work — drop it. A finding no row covers is either out of scope and
said to be, or the table is incomplete.

**Scope** is what each follow-up's `contexts.md` boundary is copied from, so two
rows never claim the same files. **Depends on** is the row that must land first,
by `#`.

The rows are a recommendation; the user decides which get created. When one is
declined, say so here with the reason, so a later session does not re-propose it
as if it were new.

## Recommended Verification Plan

(How the follow-up work should prove the fix worked. This is what a regression
test would need to catch. With a decomposition above, say which row each check
belongs to.)
