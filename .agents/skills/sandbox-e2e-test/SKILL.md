---
name: sandbox-e2e-test
description: Use when testing the AsUsual runtime harness end-to-end inside the hardcoded as-usual-test-project sandbox and writing a dated test report under docs/test.
---

# Sandbox E2E Test

## Overview

Run an end-to-end AsUsual runtime test in the local sandbox project:

```text
/Users/happyhsryu/dev/personal/as-usual-test-project
```

This is a maintainer-only project-local skill. It verifies the installed Codex snapshot or
repository-local Claude plugin by running fresh agent sessions inside the sandbox, allowing the
AsUsual hook and runtime skills to create and resume real `.as-usual/topic/...` artifacts.

## Boundary

This is AsUsual harness development and verification, not target-project feature delivery.

Do not:

- Move this skill into public `skills/`.
- Register this skill in plugin manifests.
- Copy runtime workflow rules into the sandbox.
- Commit sandbox `.as-usual/` artifacts or backend runtime logs.

## Hosts

Default host is `codex`. The runner also supports `--host claude`.

Reports must record the host. The default report directory includes the host suffix:

```text
docs/test/yyyy-MM-dd-<test-name>-codex/
```

Claude reports use the same shape with a `-claude` suffix:

```text
docs/test/yyyy-MM-dd-<test-name>-claude/
```

## What The Automation Tests

The default scenario asks AsUsual to add task priority support to the sandbox app.

The runner verifies that the agent can:

1. Reload the local Codex plugin snapshot through `turn-on-off-as-usual`.
2. Start a fresh topic in the sandbox.
3. Create file-backed define-requirements questions.
4. Fill `[Answer]:` fields automatically.
5. Resume from disk artifacts in later Codex sessions.
6. Write `requirements.md` and `plan.md`.
7. Execute the approved plan.
8. Run post-execution review/finalize flow as far as the harness permits.
9. Leave analyzable topic artifacts, backend logs, and sandbox diffs.
10. Write a report under `docs/test/`.

## Quick Run

Run from the AsUsual repository root:

```bash
.agents/skills/sandbox-e2e-test/scripts/run-sandbox-e2e.sh
```

Useful options:

```bash
.agents/skills/sandbox-e2e-test/scripts/run-sandbox-e2e.sh --test-name priority-e2e
.agents/skills/sandbox-e2e-test/scripts/run-sandbox-e2e.sh --host codex
.agents/skills/sandbox-e2e-test/scripts/run-sandbox-e2e.sh --host claude
.agents/skills/sandbox-e2e-test/scripts/run-sandbox-e2e.sh --host claude --claude-model sonnet
.agents/skills/sandbox-e2e-test/scripts/run-sandbox-e2e.sh --host claude --claude-setting-sources project --claude-plugin-dir "$PWD"
.agents/skills/sandbox-e2e-test/scripts/run-sandbox-e2e.sh --host claude --skip-claude-preflight
.agents/skills/sandbox-e2e-test/scripts/run-sandbox-e2e.sh --no-preclean
.agents/skills/sandbox-e2e-test/scripts/run-sandbox-e2e.sh --no-reset
.agents/skills/sandbox-e2e-test/scripts/run-sandbox-e2e.sh --idle-timeout 90
.agents/skills/sandbox-e2e-test/scripts/run-sandbox-e2e.sh --max-step-timeout 900
.agents/skills/sandbox-e2e-test/scripts/run-sandbox-e2e.sh --progress-interval 30
```

## Runner Behavior

The runner:

1. Checks the hardcoded sandbox exists.
2. Refuses to run unless the sandbox git root is exactly
   `/Users/happyhsryu/dev/personal/as-usual-test-project`.
3. Runs `.agents/skills/turn-on-off-as-usual/scripts/as-usual-toggle.sh reload --<host>`.
4. For Claude, runs a tiny preflight before touching sandbox artifacts unless
   `--skip-claude-preflight` is passed.
5. Precleans the dedicated sandbox by default:
   - saves preclean status/diff/untracked evidence under `logs/artifacts/`
   - archives any existing sandbox `.as-usual/` folder unless `--no-reset` is passed
   - runs `git restore --worktree --staged .`
   - runs `git clean -fd`
   - removes sandbox `.as-usual/` and stale backend AsUsual logs
6. Runs staged host prompts:
   - start topic and create questions
   - resume after automated question answers and write requirements
   - approve requirements and write plan
   - approve plan and execute
   - skip optional code cleanup and finalize/no git action
7. Copies topic artifacts, backend logs, and sandbox diffs under `logs/`.
8. Writes three root-level markdown files: `report.md`, `evidence.md`, and `improvement-plan.md`.
9. Keeps all other generated files under `logs/`, which is gitignored.

Use `--no-preclean` to preserve the current sandbox working tree for debugging. Use
`--allow-dirty-baseline` only when intentionally preserving an existing sandbox diff as baseline
noise; it disables precleaning.

## Answer Fixture Policy

The automated fixture fills each question by question number rather than copying one broad answer into every `[Answer]:` field.

The default priority scenario intentionally exercises:

- a recommended option match for full-stack scope
- a recommended option match for `LOW`, `MEDIUM`, `HIGH`
- a default compatibility decision for omitted priority
- a recommendation override for excluding priority update behavior
- a display-only list behavior decision

Reports should treat repeated identical answer bodies across all questions as a fixture-quality warning.

## Timeout Policy

The runner uses idle timeout plus a generous hard cap instead of a short fixed per-step timeout.

Defaults:

```text
--idle-timeout 90
--max-step-timeout 900
--progress-interval 30
```

When `--host claude` is used and `--idle-timeout` is not explicitly provided, the runner raises the
idle timeout to 600 seconds because Claude Code can stay quiet in `stream-json` output while a long
tool call or model turn is still active.

The Claude runner defaults to `--claude-model sonnet` to keep the long five-step E2E within typical
Claude Code session limits. Use `--claude-model <model>` when a different Claude Code model is
needed.

The Claude runner also defaults to `--claude-setting-sources project` plus `--claude-plugin-dir`
pointing at the AsUsual repository. This keeps the E2E focused on the repository-local AsUsual
plugin instead of loading every user-level plugin and hook, which can otherwise consume the Claude
session budget before the five-step workflow reaches finalize. Override these only when deliberately
testing the user's full installed Claude environment.

Before resetting sandbox `.as-usual` artifacts, the Claude runner performs a tiny `claude -p`
preflight. If Claude Code is currently rate-limited, the runner fails fast and leaves the sandbox
artifacts in place. Use `--skip-claude-preflight` only when deliberately testing failure handling or
when an external wrapper has already verified Claude availability.

- `idle-timeout`: stop a Codex step when no monitored log file changes for this many seconds.
- `max-step-timeout`: stop a Codex step when it exceeds this total duration, even if logs continue.
- `progress-interval`: print a terminal heartbeat while a Codex step is running so the run does not
  appear frozen when progress is only visible in JSONL logs. Set to `0` to disable heartbeat output.
- `logs/<host>/<step>-events.jsonl` is the primary progress signal because Codex and Claude
  both write stream events there.
- `logs/<host>/<step>-stderr.log` and `logs/<host>/<step>-last-message.md` are secondary
  progress signals. Stderr is useful for loader failures but should not be treated as strong
  proof of semantic progress by itself.
- Terminal logs record `timeout_kind: idle|max`, `last_log_update_at`, `idle_seconds`,
  `duration_seconds`, and `last_event_summary` when a timeout fires.
- Terminal logs also record heartbeat entries with elapsed seconds, idle seconds, event count,
  last log update time, source file, and last event summary.
- `--step-timeout` remains accepted as a deprecated alias for `--max-step-timeout`.

Reports must include enough metadata to distinguish a fresh run from a same-slug archived run:

- `preRunTopicArchived`
- `sandboxPrecleaned`
- `currentTopicCreatedAt`

## Agent Behavior Logging

The runner preserves three layers of evidence so a maintainer agent can debug failures after the run.
All log-like evidence lives under `logs/`, which is gitignored. Only `report.md`,
`evidence.md`, and `improvement-plan.md` remain outside `logs/` so they can be committed.

### CLI Execution Logs

Every important shell command writes a terminal log under `logs/terminal/` with:

- command name and arguments
- cwd
- UTC start and finish time
- duration
- exit code
- output, or pointers to captured stdout/stderr files when output is intentionally split

### Agent Transcript Logs

For Codex, each `codex exec` step writes:

- `logs/codex/<step>-events.jsonl`: full `codex exec --json` event stream
- `logs/codex/<step>-last-message.md`: `--output-last-message` output
- `logs/codex/<step>-stderr.log`: stderr and loader warnings
- `logs/terminal/<timestamp>-<step>.log`: command metadata, prompt, output paths, stderr, result

For Claude, each `claude -p` step writes:

- `logs/claude/<step>-events.jsonl`: full `claude -p --output-format stream-json` event stream
- `logs/claude/<step>-last-message.md`: last assistant/result text extracted from the stream
- `logs/claude/<step>-stderr.log`: stderr and loader warnings
- `logs/terminal/<timestamp>-<step>.log`: command metadata, prompt, output paths, stderr, result

### Raw Evidence Logs

The runner copies raw evidence under `logs/`:

- `.as-usual/topic/.../question-cN.md`
- `topic.md`
- `requirements.md`
- `plan.md`
- `audit.jsonl`
- sandbox `git diff`
- backend runtime log files from `backend/logs/`

Important excerpts from these raw files are compacted into root-level `evidence.md`.

Expected report layout:

```text
docs/test/yyyy-MM-dd-<test-name>-codex/
├── report.md
├── evidence.md
├── improvement-plan.md
├── logs/
│   ├── run.log
│   ├── terminal/
│   │   ├── 20260624-163000-reload-codex.log
│   │   ├── 20260624-163020-01-start-topic.log
│   │   └── ...
│   ├── <host>/
│   │   ├── 01-start-topic-events.jsonl
│   │   ├── 01-start-topic-last-message.md
│   │   ├── 01-start-topic-stderr.log
│   │   └── ...
│   ├── backend/
│   │   └── as-usual-backend-20260624-163500.log
│   ├── artifacts/
│   │   ├── copied-topic-files/
│   │   ├── sandbox-status-before-preclean.txt
│   │   ├── sandbox-status-after-preclean.txt
│   │   ├── sandbox-status-before.txt
│   │   ├── sandbox-status-after.txt
│   │   ├── sandbox.diff
│   │   └── sandbox-diff-stat.txt
│   └── sandbox-snapshots/
│       └── pre-run-dot-as-usual/
```

Report metadata must include:

```yaml
provider: codex
sandboxProject: /Users/happyhsryu/dev/personal/as-usual-test-project
asUsualRepo: /Users/happyhsryu/dev/personal/as-usual
startedAt: <run-id>
preRunTopicArchived: <true|false>
sandboxPrecleaned: <true|false>
currentTopicCreatedAt: <timestamp>
```

## Expected Report Contents

Each report should include:

- Host (`codex` by default)
- AsUsual repository path
- Sandbox path
- Topic path
- Overall result
- Prompt step exit codes, durations, idle/max timeout settings, and last log update time
- Heartbeat/progress behavior when a step runs quietly for a long time
- Artifact inventory
- Derived topic status, phase, and next action from `scripts/topic-log.py status --json`
- Question answer completeness
- Requirements/plan/review/finalize evidence
- Sandbox diff summary
- Backend AOP log evidence when available
- Problems found
- Suggested AsUsual improvements

`evidence.md` should include important raw excerpts as markdown code blocks:

- Step durations and exit codes
- Timeout kind, idle seconds, last log update time, and last event summary when available
- Final derived topic status
- Last audit events
- Sandbox `git diff --stat`
- Backend log excerpt when available
- Host last-message excerpts
- Pointer that full raw evidence is under gitignored `logs/`

`improvement-plan.md` should be written after both `report.md` and `evidence.md` and should
include:

- Source links to `report.md` and `evidence.md`
- Overall result, topic phase, and next action
- Priority for the next maintainer action
- Issue-linked actions derived from report problems and linter warnings
- Suggested improvements and evidence paths to recheck

## Verification

After editing this skill or its scripts, run:

```bash
bash -n .agents/skills/sandbox-e2e-test/scripts/run-sandbox-e2e.sh
python3 -m unittest discover -s .agents/skills/sandbox-e2e-test/tests -p 'test_*.py'
set +e
python3 .agents/skills/sandbox-e2e-test/scripts/e2e-report-linter.py \
  --report-dir docs/test/2026-06-24-priority-e2e-codex-20260624-215619 \
  --allow-dirty-baseline \
  --json-output /tmp/as-usual-e2e-lint-result.json
lint_status=$?
set -e
python3 - <<'PY'
import json
from pathlib import Path

data = json.loads(Path("/tmp/as-usual-e2e-lint-result.json").read_text())
assert "overallResult" in data
assert "segments" in data
assert "checks" in data
print(f"sandbox e2e linter smoke OK: overallResult={data['overallResult']}")
PY
```

Expected:

- shell syntax check exits 0
- unittest exits 0
- linter writes JSON with `overallResult`, `segments`, and `checks` present
- `lint_status` may be non-zero when the archived report intentionally contains issues that the current stricter linter now detects

Then run the actual sandbox E2E test when a real harness verification is desired:

```bash
.agents/skills/sandbox-e2e-test/scripts/run-sandbox-e2e.sh --test-name priority-e2e
```

Use `--allow-dirty-baseline` only when intentionally preserving an existing sandbox diff as baseline noise.
