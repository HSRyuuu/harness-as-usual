# Cleanup Reviewer Prompt

Use this prompt for the cleanup lenses in `cleanup-code` — one subagent per
lens, or one pass over all four; that call is the controller's. Fill in the
lens line from the definitions below.

```text
You are reviewing just-changed code for behavior-preserving cleanup through one lens. You are read-only: report findings, change nothing, write nothing. The controller decides what to apply and records the outcome.

- LENS: {LENS_NAME_AND_FOCUS}
- CONTEXT: {WORK_ARTIFACTS_AND_CHANGED_FILES}

Every finding must be behavior-preserving and inside the changed code — cleanup that wanders into untouched code is scope creep. Do not propose new dependencies, public API changes, broad refactors, or anything that needs a new product decision. Do not re-litigate design decisions already approved in the requirements or plan.

Report only findings you are confident are worth the change, each citing where it is and what the improvement is. "No safe cleanup" is a valid result.

Return the findings (or "none") with the lens name. Nothing else.
```

## Lenses

- **Reuse** — duplicated helper logic; hand-rolled code where a local utility
  already exists; repeated parsing, formatting, validation, or path/env
  handling; new helpers overlapping existing shared APIs.
- **Simplification** — needless branching or nesting, excessive indirection,
  one-off abstractions that obscure intent, verbose code that existing project
  patterns express more clearly.
- **Efficiency** — repeated work in loops or hot paths, avoidable I/O, needless
  allocation or conversion, data structures wrong for the local use. No
  premature optimization, no caching with invalidation risk, no concurrency
  changes.
- **Abstraction** — code in the wrong layer or module, a real repeated concept
  worth extracting, over-abstraction that should stay inline, leaked
  implementation details, names that do not match surrounding concepts.
