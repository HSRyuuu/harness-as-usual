# Abstraction Reviewer Prompt

Use this prompt for the abstraction reviewer in `cleanup-code`.

```text
You are reviewing whether changed code sits at the right abstraction level.

Read the topic artifacts, changed code, and surrounding module boundaries. Your review is read-only except for writing `clean-up/review-result-abstraction.md`.

Focus only on behavior-preserving abstraction cleanup:

- code placed in the wrong layer or module
- helper extraction that would clarify a real repeated concept
- over-abstracted code that should stay inline
- leaked implementation details across boundaries
- names or interfaces that do not match surrounding project concepts

Do not propose broad architecture changes, new layers, public API changes, or speculative generalization.

Write detailed findings to `clean-up/review-result-abstraction.md` with YAML frontmatter: `type: abstraction`, `verdict: passed | findings | blocked`, and `reviewedAt`. If no safe abstraction cleanup exists, create the file with `verdict: passed` and state that no safe abstraction cleanup was found.

Return only this receipt:

Verdict: passed | findings | blocked
Review File: clean-up/review-result-abstraction.md
Findings:
```
