---
name: verify-as-usual-harness
description: Use when verifying AsUsual runtime workflow, hook injection, and plugin manifest smoke tests. Run after changes to runtime workflow, hooks, runtime templates, public runtime skills, or plugin manifests.
disable-model-invocation: true
---

# Verify AsUsual Harness

## Purpose

Run the same smoke tests repeatedly after AsUsual harness changes.

1. Verify that JSON manifests and hook configs are valid.
2. Verify that `as-usual-rules/core-workflow.md` is the canonical runtime workflow.
3. Verify that the SessionStart hook injects a short AsUsual capability summary, full workflow file path, runtime entrypoint, and active topic candidates without injecting the full core workflow or static artifact rules.
4. Verify that old paths or removed workflow skills do not remain on the runtime surface.

## When To Run

- After changing `as-usual-rules/core-workflow.md`
- After changing `hooks/`, `hooks/hooks*.json`, or `hooks/run-hook.cmd`
- After changing manifests under `.codex-plugin/`, `.claude-plugin/`, or `.agents/plugins/`
- After changing runtime artifact templates under `templates/`
- After changing public runtime skills under `skills/**`
- After reloading the Codex plugin snapshot
- As the final smoke test before a PR, release, or commit that touches the runtime workflow, hook injection, runtime templates, public runtime skills, or plugin manifests

## Related Files

| File                                                | Purpose                           |
| --------------------------------------------------- | --------------------------------- |
| `as-usual-rules/core-workflow.md`                   | canonical runtime workflow        |
| `hooks/session-start`                               | SessionStart context injection    |
| `hooks/run-hook.cmd`                                | hook runner                       |
| `hooks/hooks.json`                                  | Claude hook config                |
| `hooks/hooks-codex.json`                            | Codex hook config                 |
| `.claude-plugin/plugin.json`                        | Claude plugin manifest            |
| `.claude-plugin/marketplace.json`                   | Claude local marketplace manifest |
| `.codex-plugin/plugin.json`                         | Codex plugin manifest             |
| `.agents/plugins/marketplace.json`                  | Codex local marketplace manifest  |
| `skills/using-as-usual/SKILL.md`                    | runtime activation skill          |
| `skills/start-work/SKILL.md`                        | runtime gate routing skill        |
| `skills/define-requirements/SKILL.md`                    | runtime question cycle and requirements writing skill      |
| `skills/define-requirements/requirements-document-reviewer-prompt.md` | runtime requirements review prompt     |
| `skills/writing-plan/SKILL.md`                      | runtime plan writing skill        |
| `skills/writing-plan/plan-document-reviewer-prompt.md` | runtime plan review prompt     |
| `skills/executing-plan/SKILL.md`                    | runtime plan execution skill      |
| `skills/review-execution/SKILL.md`                  | runtime execution review skill    |
| `skills/review-execution/code-reviewer-prompt.md`   | runtime execution review prompt   |
| `skills/cleanup-code/SKILL.md`                | runtime code cleanup skill    |
| `skills/cleanup-code/*.md`                    | runtime code cleanup prompts  |
| `skills/finalize/SKILL.md`                          | runtime finalization skill        |
| `skills/git-action/SKILL.md`                        | runtime selected git action skill |
| `skills/manage-self-improvement/SKILL.md`           | runtime finalize-triggered self-improvement skill |
| `skills/search-long-term-memory/SKILL.md`           | runtime long-term memory recall utility |
| `templates/question.md`                            | question artifact template        |
| `templates/requirements.md`                                 | requirements artifact template            |
| `templates/plan.md`                                 | plan artifact template            |
| `templates/code-review-report.md`                   | code review findings report template |
| `templates/report.md`                               | final topic handoff report template |
| `templates/topic.md`                                | low-churn topic resume template   |
| `scripts/topic-log.py`                              | topic/audit helper and status derivation |
| `.agents/skills/sandbox-e2e-test/scripts/e2e-report-linter.py` | sandbox E2E report linter |
| `.agents/skills/sandbox-e2e-test/scripts/fill-question-answers.py` | sandbox E2E question answer fixture helper |
| `.agents/skills/sandbox-e2e-test/tests/test_e2e_report_linter.py` | linter unit tests |
| `.agents/skills/sandbox-e2e-test/tests/test_fill_question_answers.py` | answer fixture helper unit tests |
| `.agents/skills/sandbox-e2e-test/tests/test_runtime_surface_manifest.py` | runtime skill, manifest, marketplace, and hook drift tests |

## Workflow

### Step 1: Manifest JSON Validation

Run:

```bash
jq empty .claude-plugin/plugin.json .claude-plugin/marketplace.json .codex-plugin/plugin.json .agents/plugins/marketplace.json hooks/hooks.json hooks/hooks-codex.json
```

PASS:

- command exits 0.

FAIL:

- any JSON parse error appears.

Fix:

- repair the reported JSON file and rerun this step.

### Step 2: Runtime Workflow File Check

Run:

```bash
test -s as-usual-rules/core-workflow.md
```

PASS:

- `as-usual-rules/core-workflow.md` exists and is non-empty.

FAIL:

- `core-workflow.md` is missing or empty.

Fix:

- keep runtime rules in `as-usual-rules/core-workflow.md` only.

### Step 3: Hook Injection Smoke Test

Run:

```bash
CLAUDE_PLUGIN_ROOT="$PWD" hooks/run-hook.cmd session-start \
  | jq '{
      event: .hookSpecificOutput.hookEventName,
      hasHarnessRules: (.hookSpecificOutput.additionalContext | contains("AsUsual Harness Rules")),
      hasRuleSource: (.hookSpecificOutput.additionalContext | contains("Harness rule source:")),
      hasUsingSkill: (.hookSpecificOutput.additionalContext | contains("using-as-usual")),
      hasActiveCandidates: (.hookSpecificOutput.additionalContext | contains("Active topic candidates:")),
      hasNoArtifactRules: (.hookSpecificOutput.additionalContext | contains("AsUsual artifact rules") | not),
      hasNoFullCore: (.hookSpecificOutput.additionalContext | contains("## 8. Plan Rules") | not),
      oldPath: (.hookSpecificOutput.additionalContext | contains(".as-usual/topics/yyyyMMdd-<topic>/"))
    }'
```

PASS:

- `event` is `SessionStart`.
- `hasHarnessRules` is `true`.
- `hasRuleSource` is `true`.
- `hasUsingSkill` is `true`.
- `hasActiveCandidates` is `true`.
- `hasNoArtifactRules` is `true`.
- `hasNoFullCore` is `true`.
- `oldPath` is `false`.

FAIL:

- hook output is not valid JSON.
- required bootstrap markers are false.
- `hasNoFullCore` is false, which means the hook is injecting detailed core workflow sections again.
- `oldPath` is true.

Fix:

- update `hooks/session-start` so hook output stays short and points to `as-usual-rules/core-workflow.md`, `using-as-usual`, and active topic candidates.

### Step 4: Removed Surface Check

Run:

```bash
rg -n "\\.as-usual/topics/yyyyMMdd|as-usual-interview|as-usual-execute" \
  -g '!docs/**/plans/**' \
  -g '!docs/**/2026-*'
```

PASS:

- no active runtime dependency on removed files or old paths.
- mentions are acceptable only when explicitly documenting anti-patterns or "do not use" guidance.

FAIL:

- install docs, hook, runtime workflow, templates, or skills still require removed files, removed skills, or old paths.

Fix:

- update the active runtime surface to use `as-usual-rules/core-workflow.md` and `.as-usual/topic/yyyy-MM-dd-<topic>/`.

### Step 5: Sandbox E2E Linter Smoke Test

Run a direct topic helper smoke first:

```bash
tmp_dir="$(mktemp -d)"
topic_dir="$tmp_dir/.as-usual/topic/2026-06-27-audit-first"
removed_state_artifact="state"".json"
python3 scripts/topic-log.py init \
  --topic-dir "$topic_dir" \
  --topic 2026-06-27-audit-first \
  --initial-request "Audit-first smoke." \
  --summary "Smoke test."
test -f "$topic_dir/topic.md"
test -f "$topic_dir/audit.jsonl"
test ! -e "$topic_dir/$removed_state_artifact"
python3 scripts/topic-log.py status --topic-dir "$topic_dir" --json \
  | jq -e '.phase == "start-work" and .nextAction == "route"'
python3 scripts/topic-log.py validate --topic-dir "$topic_dir"
rm -rf "$tmp_dir"
```

Run:

```bash
python3 -m unittest discover -s .agents/skills/sandbox-e2e-test/tests -p 'test_*.py'
if python3 .agents/skills/sandbox-e2e-test/scripts/e2e-report-linter.py \
  --report-dir docs/test/2026-06-24-priority-e2e-codex-20260624-215619 \
  --allow-dirty-baseline \
  --json-output /tmp/as-usual-e2e-lint-result.json; then
  echo "sandbox e2e linter fixture result passed"
else
  echo "sandbox e2e linter fixture reported archived findings; continuing JSON schema smoke"
fi
python3 - <<'PY'
import json
from pathlib import Path

data = json.loads(Path("/tmp/as-usual-e2e-lint-result.json").read_text())
assert "overallResult" in data
assert "segments" in data
assert "checks" in data
print(f"sandbox e2e linter JSON smoke OK: {data['overallResult']}")
PY
```

PASS:

- unittest exits 0.
- runtime surface manifest tests keep public skill names, plugin manifest paths, marketplace metadata, and SessionStart hook commands aligned.
- linter emits parseable JSON with `overallResult`, `segments`, and `checks`. The archived fixture may report PASS or FAIL; this smoke checks the linter output contract, not that a historical E2E report is clean.

FAIL:

- unittest fails.
- public runtime skill names, frontmatter, plugin manifest paths, marketplace metadata, or hook command paths drift apart.
- linter emits no JSON for the archived report fixture.
- required top-level JSON fields are missing from the emitted JSON.

## Output Format

```markdown
## verify-as-usual-harness Report

| Check                 | Status    | Evidence |
| --------------------- | --------- | -------- |
| Manifest JSON         | PASS/FAIL | ...      |
| Runtime workflow file | PASS/FAIL | ...      |
| Hook injection        | PASS/FAIL | bootstrap markers + no full core |
| Removed surface       | PASS/FAIL | ...      |

### Summary

- PASS: ...
- FAIL: ...
- Follow-up: ...
```

## Exceptions

1. `.as-usual/topics/yyyyMMdd` may appear in documentation only as an old-path anti-pattern.
2. `as-usual-interview` and `as-usual-execute` may appear in changelog/history only if not required by runtime manifests or skills.
3. Historical handoff docs under `docs/**` may contain implementation commands that search for old paths or removed surfaces.
