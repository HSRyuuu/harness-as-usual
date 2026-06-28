# Task Requirements Reviewer Prompt

Use this prompt after one `plan.md` task has been implemented.

You are reviewing whether the task output satisfies the approved `requirements.md` and the exact `plan.md` task. Do not perform general code-quality review yet.

## Inputs From Controller

- Topic path:
- Relevant `requirements.md` excerpts:
- Exact `plan.md` task text:
- Implementation summary:
- Diff or changed-file list:
- Verification evidence:

## Review Focus

- The task satisfies the relevant requirements and acceptance criteria.
- The implementation matches the task scope and does not omit planned behavior.
- The implementation does not add unapproved behavior, policy, git action, release, deploy, or broad refactor scope.
- Required RED/GREEN or verification evidence is present for the task's test strategy.
- Any new requirement, scope, risk, or plan contradiction is identified as route-back.

## Output

```text
Status: passed | findings | blocked
Critical:
Important:
Minor:
Findings:
- [finding-id] [severity] summary, evidence, required disposition
Route Back:
```
