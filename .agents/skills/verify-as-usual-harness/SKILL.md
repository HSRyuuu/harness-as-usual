---
name: verify-as-usual-harness
description: Use when verifying AsUsual runtime workflow, hook injection, and plugin manifest smoke tests. Run after changes to runtime workflow, hooks, runtime templates, public runtime skills, or plugin manifests.
disable-model-invocation: true
---

# Verify AsUsual Harness

## Purpose

Run the same smoke tests repeatedly after AsUsual harness changes.

1. Verify that JSON manifests and hook configs are valid.
2. Verify that `as-usual-rules/core-workflow.md` and `as-usual-rules/find-cause-workflow.md` are the canonical coding-topic and find-cause workflows.
3. Verify that the SessionStart hook injects only a one-sentence AsUsual capability summary with the runtime entrypoint, without injecting the full core workflow, rule path, topic candidates, memory content, or static artifact rules.
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
| `as-usual-rules/core-workflow.md`                   | canonical runtime workflow entrypoint |
| `as-usual-rules/routing-rules.md`                   | single-source routing rules       |
| `as-usual-rules/logging-rules.md`                   | single-source record rules        |
| `as-usual-rules/completion-rules.md`                | single-source completion rules    |
| `as-usual-rules/log-audit-commands.md`              | canonical topic-log command set   |
| `as-usual-rules/find-cause-workflow.md`              | canonical find-cause workflow     |
| `hooks/session-start`                               | SessionStart context injection    |
| `hooks/run-hook.cmd`                                | hook runner                       |
| `hooks/hooks.json`                                  | Claude hook config                |
| `hooks/hooks-codex.json`                            | Codex hook config                 |
| `.claude-plugin/plugin.json`                        | Claude plugin manifest            |
| `.claude-plugin/marketplace.json`                   | Claude marketplace manifest       |
| `.codex-plugin/plugin.json`                         | Codex plugin manifest             |
| `.agents/plugins/marketplace.json`                  | Codex marketplace manifest        |
| `skills/using-as-usual/SKILL.md`                    | runtime activation skill          |
| `skills/hand-off/SKILL.md`                          | runtime hand-off resume skill     |
| `skills/find-cause/SKILL.md`                         | runtime find-cause issue skill    |
| `skills/start-work/SKILL.md`                        | runtime gate routing skill        |
| `skills/direct-execute/SKILL.md`                    | runtime direct-execute gate and execution skill |
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
| `scripts/journal-log.py`                            | issue journal CLI entrypoint |
| `scripts/as_usual_journal_log/`                     | issue journal implementation |
| `scripts/tests/test_journal_log.py`                 | issue journal behavior and gate tests |
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
test -s as-usual-rules/find-cause-workflow.md
test -s as-usual-rules/routing-rules.md
test -s as-usual-rules/logging-rules.md
test -s as-usual-rules/completion-rules.md
test -s as-usual-rules/log-audit-commands.md
```

PASS:

- Both canonical workflow files and the single-source rule files exist and are non-empty.

FAIL:

- Any canonical workflow or rule file is missing or empty.

Fix:

- keep runtime workflow rules under `as-usual-rules/` (`core-workflow.md` entrypoint plus the single-source rule files); do not scatter them elsewhere.

### Step 3: Hook Injection Smoke Test

Run:

```bash
CLAUDE_PLUGIN_ROOT="$PWD" bash hooks/run-hook.cmd session-start \
  | jq '{
      event: .hookSpecificOutput.hookEventName,
      hasUsingSkill: (.hookSpecificOutput.additionalContext | contains("using-as-usual")),
      hasFindCause: (.hookSpecificOutput.additionalContext | contains("find-cause")),
      isOneSentence: (.hookSpecificOutput.additionalContext | split(". ") | length <= 2),
      hasNoRuleSource: (.hookSpecificOutput.additionalContext | contains("Harness rule source:") | not),
      hasNoActiveCandidates: (.hookSpecificOutput.additionalContext | contains("Active topic candidates:") | not),
      hasNoMemoryContent: (.hookSpecificOutput.additionalContext | contains("Project memory:") | not),
      hasNoArtifactRules: (.hookSpecificOutput.additionalContext | contains("AsUsual artifact rules") | not),
      hasNoFullCore: (.hookSpecificOutput.additionalContext | contains("## 8. Plan Rules") | not),
      oldPath: (.hookSpecificOutput.additionalContext | contains(".as-usual/topics/yyyyMMdd-<topic>/"))
    }'
```

PASS:

- `event` is `SessionStart`.
- `hasUsingSkill` is `true`.
- `hasFindCause` is `true`.
- `isOneSentence` is `true`.
- `hasNoRuleSource` is `true`.
- `hasNoActiveCandidates` is `true`.
- `hasNoMemoryContent` is `true`.
- `hasNoArtifactRules` is `true`.
- `hasNoFullCore` is `true`.
- `oldPath` is `false`.

FAIL:

- hook output is not valid JSON.
- required bootstrap markers are false.
- `hasNoFullCore` is false, which means the hook is injecting detailed core workflow sections again.
- `hasNoRuleSource`, `hasNoActiveCandidates`, or `hasNoMemoryContent` is false, which means the hook is again doing file-backed bootstrap work that belongs in `using-as-usual`.
- `oldPath` is true.

Fix:

- update `hooks/session-start` so hook output stays to one sentence that points to `using-as-usual`, while `using-as-usual` owns rule and topic discovery.

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
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
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

- journal helper unittest exits 0.
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
