# Review

<!--
One review document per work unit. Later passes — task reviews, cleanup — append
their own section here rather than creating new files.

Findings only. A clean review needs no file at all; record it as an event instead.
-->

## Execution Review

**Reviewed** — the diff or changed files that were actually inspected.

**Verdict** — clean | findings | blocked

### Critical

(The work cannot honestly be called done with this outstanding. File and line,
why it matters, what to do. Each needs a disposition before the work closes:
fixed and re-reviewed, rejected with a technical reason, or accepted by the user
after being told the risk in plain terms.)

### Important

(Must be resolved before the work closes. Same dispositions as Critical.)

### Minor

(Polish or follow-up. Never blocking; may simply be deferred.)

## Dispositions

(How each Critical and Important finding was resolved, and who decided. Fill this
as they are handled, not at the end.)

---

## Cleanup

<!-- Added by cleanup-code when it runs. Omit the section entirely otherwise. -->

**Applied** — what changed, and why it is behavior-preserving.

**Not applied** — findings that failed the safety tests, kept as follow-up.

**Re-verification** — the command re-run after cleanup and its actual result.
