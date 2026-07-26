---
unit: <topic | direct-work | issue>
slug: <yyyy-MM-dd-slug>
created: <yyyy-MM-dd>
---

# Review

## Execution Review

**Reviewed** — the diff or changed files that were actually inspected.

**Verdict** — clean | findings | blocked

### Critical

(The work cannot honestly be called done with this outstanding. File and line,
why it matters, what to do. Each needs a disposition before the work closes:
fixed and re-reviewed, or rejected with a technical reason. One left standing
closes the unit as blocked.)

### Important

(Must be resolved before the work closes. Same dispositions as Critical, plus
accepted by the user after being told the risk in plain terms.)

### Minor

(Polish or follow-up. Never blocking; may simply be deferred.)

## Dispositions

(How each Critical and Important finding was resolved, and who decided. Fill this
as they are handled, not at the end.)

---

## Cleanup

**Mode** — independent (four lenses as separate subagents) | inline.

**Applied** — what changed, and why it is behavior-preserving.

**Not applied** — findings that failed the safety tests, kept as follow-up.

**Re-verification** — the command re-run after cleanup and its actual result.
