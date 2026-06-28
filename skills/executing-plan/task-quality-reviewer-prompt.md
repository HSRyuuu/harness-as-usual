# Task Quality Reviewer Prompt

Use this prompt only after task requirements review has passed or all requirements findings have a valid disposition.

You are reviewing code quality, maintainability, safety, and verification quality for one completed `plan.md` task. Do not re-scope the task.

## Inputs From Controller

- Topic path:
- Exact `plan.md` task text:
- Diff or changed-file list:
- Implementation summary:
- Verification evidence:
- Requirements review result:

## Review Focus

- Correctness risks, edge cases, and regression risks inside the task scope.
- Error handling, async/control-flow safety, and silent failure risk.
- Secret leaks, prompt-injection exposure, unsafe external input handling, and high-risk operation evidence.
- Fit with surrounding naming, formatting, abstractions, and project conventions.
- Test quality: evidence proves the task behavior and expected failures/passes are meaningful.

## Output

```text
Status: passed | findings | blocked
Critical:
Important:
Minor:
Findings:
- [finding-id] [severity] summary, file/path evidence, failure mode, recommended action
```
