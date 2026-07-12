---
name: find-cause
description: Use when the user wants to investigate and confirm a problem's root cause or a solution/improvement direction without implementing code changes, or when resuming a `.as-usual/issue/` investigation.
---

# Find Cause

This skill owns the whole find-cause issue lifecycle. The canonical rules
live in `as-usual-rules/find-cause-workflow.md`; read that file fully before
acting, then follow it. This skill adds only operational defaults.

## First Reads

1. Read `as-usual-rules/find-cause-workflow.md` from the AsUsual plugin
   root (the parent directory of the `skills/` directory containing this
   skill, or the path announced by the SessionStart hook).
2. For an existing issue: read `problem.md`, then run
   `python3 <plugin-root>/scripts/journal-log.py status --issue-dir <dir> --json`,
   then read `conclusion.md` if it exists. Use `view --md` when you need the
   full reasoning trail.
3. For a new issue: choose `.as-usual/issue/yyyy-MM-dd-<slug>/` with the
   actual current date, then run
   `python3 <plugin-root>/scripts/journal-log.py init --issue-dir <dir>
   --initial-request "<request>" --actor claude` (use `--actor codex` on
   Codex), tell the user the issue path in one line, and start the entry
   interview.

## Operating Loop

- Interview first (one question at a time, with your recommended answer),
  then investigate, then record. Keep `problem.md` current as understanding
  changes.
- Record meaningful findings/decisions/hypotheses as journal entries when
  they happen, not in a batch at the end:
  `journal-log.py add --issue-dir <dir> --kind <kind> --content "..."
  [--evidence "..."]`.
- Confirm or cancel with `confirm --target <seq>` / `cancel --target <seq>
  --reason "..."`. Never edit journal lines.
- Enforce the hard gates from the workflow file: read-only default,
  approval-gated reproduction code (`approve`), evidence-gated confirmation,
  inherited high-risk gate, record-before-turn-end.

## Stop Conditions

Stop and tell the user the issue path and required input when:

- An interview question is waiting for the user's answer.
- Reproduction code needs user approval.
- A high-risk operation needs fresh approval.
- Conflicting hypotheses need the user's judgment.
- The conclusion is written and the follow-up topic decision is pending.
