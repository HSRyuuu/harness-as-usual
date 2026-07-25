---
name: analyze-e2e-results
description: Use when reviewing an existing AsUsual sandbox E2E test result directory under docs/test/date-name-host/ to find harness, workflow, artifact, timeout, transcript, or report-quality problems from report.md, evidence.md, improvement-plan.md, and logs/.
---

# Analyze E2E Results

## Overview

Review an existing AsUsual sandbox E2E result as maintainer evidence. First parse the report directory in a deterministic order, then use qualitative judgment to identify real harness problems, weak evidence, and likely next improvements.

This skill does not run the sandbox E2E. Use `sandbox-e2e-test` when the task is to create a new run.

## Input

Accept either:

- a report directory, usually `docs/test/yyyy-MM-dd-<test-name>-<host>/`
- a specific `report.md`, `evidence.md`, or `improvement-plan.md` file inside such a directory

If the input is a file, treat its parent directory as the report directory.

## Expected Result Shape

Use this structure as the deterministic parsing contract:

```text
docs/test/yyyy-MM-dd-<test-name>-<host>/
├── report.md
├── evidence.md
├── improvement-plan.md
└── logs/
    ├── run.log
    ├── analysis/
    │   ├── artifact-review.md
    │   ├── issues.md
    │   └── runtime-log-review.md
    ├── artifacts/
    │   ├── copied-topic-files/
    │   │   ├── question-cN.md
    │   │   ├── topic.md
    │   │   ├── audit.jsonl
    │   │   ├── requirements.md
    │   │   ├── plan.md
    │   │   └── report.md
    │   ├── sandbox-status-before.txt
    │   ├── sandbox-status-after.txt
    │   ├── sandbox.diff
    │   └── sandbox-diff-stat.txt
    ├── backend/
    │   └── *.log
    ├── codex/
    │   ├── <step>-events.jsonl
    │   ├── <step>-exit-code
    │   ├── <step>-last-message.md
    │   └── <step>-stderr.log
    ├── claude/
    │   ├── <step>-events.jsonl
    │   ├── <step>-exit-code
    │   ├── <step>-last-message.md
    │   └── <step>-stderr.log
    └── terminal/
        └── <timestamp>-<step>.log
```

Host-specific logs may contain `codex/` or `claude/`; parse the host from `report.md` metadata first, then fall back to whichever directory exists.

## Parsing Workflow

1. Identify the report root.
   - Confirm `report.md` and `evidence.md` exist.
   - List `logs/` one level deep to see which evidence classes are available.
   - Treat missing expected files as report-quality issues, not automatic harness failures.

2. Parse `report.md`.
   - Read the opening YAML block for `provider`, `sandboxProject`, `asUsualRepo`, `startedAt`, and `topicDir`.
   - Read `## Metadata` for topic status, phase, and next action.
   - Parse the `## Checks` table into check name, status, and evidence.
   - Read `## Problems Found`, `## Improvement Ideas`, and `## Artifacts`.

3. Parse `evidence.md`.
   - Read `## Step Durations And Exit Codes` as the execution timeline.
   - Read `## Topic Status` or equivalent `topic-log.py status --json` output as JSON when present.
   - Read `## Last Audit Events` as JSONL when present.
   - Read sandbox diff, backend log, timeout, and host last-message excerpts when present.

4. Parse `improvement-plan.md` when present.
   - Read the opening YAML block for `sourceReport`, `sourceEvidence`, `overallResult`, `topicPhase`, and `nextAction`.
   - Compare `## Issue-Linked Actions` and `## Suggested Improvements` against report problems and linter warnings.
   - Treat a missing `improvement-plan.md` in new reports as a report-quality issue; older reports may predate this artifact.

5. Parse copied topic artifacts.
   - Prefer `logs/artifacts/copied-topic-files/topic.md` and inspect it for initial request, topic boundary, durable notes, and artifact orientation.
   - Prefer `logs/artifacts/copied-topic-files/audit.jsonl` and parse each line as JSON.
   - Prefer captured `topic-log.py status --json` output when present; otherwise derive phase and next-action expectations from audit events.
   - Inspect `question-cN.md` for `[Answer]:` markers and empty answers.
   - Inspect `requirements.md`, `plan.md`, `report.md`, and review/finalize artifacts if present.

6. Parse host transcript logs.
   - For each `<step>-exit-code`, record success, failure, and timeout codes.
   - For each `<step>-events.jsonl`, sample the beginning, end, and any error/timeout events.
   - For each `<step>-stderr.log`, distinguish loader warnings from actual execution blockers.
   - For each `<step>-last-message.md`, compare what the agent claimed with copied artifacts.

7. Parse terminal and runtime logs.
   - Use `logs/terminal/*.log` for command cwd, duration, timeout kind, prompt text, output paths, and exit code.
   - Use `logs/run.log` for runner-level ordering and setup failures.
   - Use `logs/backend/*.log` only as runtime behavior evidence; absence is a coverage gap when the scenario expected backend interaction.

## Review Principles

Use the generated `logs/analysis/*.md` files as hints, not as authority. Reconstruct the finding from raw evidence before reporting it.

Look for problems in these categories:

- **Runner failure:** command failure, timeout, stale plugin snapshot, dirty sandbox baseline, missing copied evidence, or report generation defects.
- **Workflow failure:** phase skipped, gate bypassed, chat answer used when file-backed answer was required, requirements/plan/execute/review/finalize order broken, or next action inconsistent with `topic-log.py status`.
- **Artifact failure:** missing canonical topic path, missing or empty `topic.md`, invalid `audit.jsonl`, missing topic status output, empty answers, missing requirements/plan/report, or audit events that do not explain transitions.
- **Agent behavior failure:** final message claims work that artifacts do not support, ignores required stop points, implements target code before approval, or fails to reread answered question files.
- **Verification failure:** task-level tests absent, verification evidence too vague, backend/frontend evidence missing for a scenario that should touch them, or sandbox diff inconsistent with the requested change.
- **Report-quality failure:** root report hides a failed step, evidence excerpts are too thin to debug, metadata is incomplete, host/run identity is ambiguous, or generated issues are not traceable.

Prefer findings that are actionable for AsUsual maintainers. Do not overfit to one run's exact task text unless the problem reveals a harness or runner weakness.

## Output Format

Lead with findings ordered by severity:

```markdown
## E2E Result Review

### Findings

| Severity | Area | Evidence | Problem | Suggested fix |
| --- | --- | --- | --- | --- |
| High | Workflow | `report.md` check X + `topic-log.py status` field Y | ... | ... |

### Evidence Read

- `report.md`
- `evidence.md`
- `improvement-plan.md`
- `logs/artifacts/copied-topic-files/topic.md`
- `logs/artifacts/copied-topic-files/audit.jsonl`
- captured `topic-log.py status --json` output, when present
- ...

### Residual Risk

- Evidence that was missing or not inspected.
```

When no serious issue is found, say so clearly and still list weak evidence or residual risks.

## Boundaries

- Do not edit the E2E result unless the user explicitly asks for report cleanup.
- Do not create or modify runtime topic artifacts while reviewing a result.
- Do not treat `logs/analysis/issues.md` as sufficient evidence by itself.
- Do not recommend moving this skill into public `skills/`; this is maintainer-only project tooling.
