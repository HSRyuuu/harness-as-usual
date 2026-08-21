---
name: verify-as-usual-harness
description: Use when verifying AsUsual manifests, hook injection, the record helper, and the runtime surface as a smoke test. Run after changes to hooks, manifests, scripts, runtime rules, templates, or public skills.
disable-model-invocation: true
---

# Verify AsUsual Harness

## Purpose

The repeatable smoke test. Everything here is a command with an expected result —
semantic judgment belongs in `verify-runtime-workflow-consistency`.

1. Manifests and hook configs are valid JSON.
2. The SessionStart hook injects one sentence naming one entry point, and nothing more.
3. The record helper works end to end and its gates refuse.
4. Deleted surfaces have not come back.

## When To Run

- After changing `hooks/**`, `.claude-plugin/**`, `.codex-plugin/**`, `.agents/plugins/**`
- After changing `scripts/**`
- After changing `as-usual-rules/**`, `templates/**`, or `skills/**`
- After reloading the Codex plugin snapshot
- As the last check before a commit, PR, or release touching any of the above

## 1. Manifests

```bash
jq empty .claude-plugin/plugin.json .claude-plugin/marketplace.json \
        .codex-plugin/plugin.json .agents/plugins/marketplace.json \
        hooks/hooks.json hooks/hooks-codex.json
jq '.skills, .hooks' .codex-plugin/plugin.json
```

Expected: no output from `jq empty`; `./skills/` and `./hooks/hooks-codex.json`
from the second.

## 2. Hook injection

```bash
CLAUDE_PLUGIN_ROOT="$PWD" bash hooks/run-hook.cmd session-start | jq '{
  event: .hookSpecificOutput.hookEventName,
  oneEntryPoint: (.hookSpecificOutput.additionalContext | contains("using-as-usual")),
  isOneSentence: (.hookSpecificOutput.additionalContext | split(". ") | length <= 2),
  noSecondEntryPoint: (.hookSpecificOutput.additionalContext | test("find-cause|direct-execute|start-work") | not),
  noRulePath: (.hookSpecificOutput.additionalContext | contains("as-usual-rules/") | not),
  noCandidates: (.hookSpecificOutput.additionalContext | test("candidates|Active topic") | not)
}'
```

Expected: `SessionStart`, and `true` for every other field.

The hook announces capability and one entry point. It must never inject rules or
candidate work folders — the entry skill reads those from disk.

## 3. Record helper

```bash
python3 -m pytest scripts/tests/ -q
```

Expected: all pass.

Then the live smoke, in a scratch directory — the tests exercise the gates, this
exercises the CLI as a skill would call it:

```bash
D=$(mktemp -d)/.as-usual/topic/2026-01-01-smoke
R="python3 $PWD/scripts/as-usual-record.py"
$R init --dir "$D" --unit topic --request "smoke" --actor claude
$R add --dir "$D" --kind approval --summary "no review yet" --action execution   # expect: refused
$R add --dir "$D" --kind review --summary "reviewed" --data findings=0
$R add --dir "$D" --kind approval --summary "approved" --action execution        # expect: accepted
$R add --dir "$D" --kind verification --summary "no verdict"                     # expect: refused
$R status --dir "$D" --json
$R validate --dir "$D"
```

Expected: the two marked calls exit 2 with a message naming the rule; the rest
exit 0; `validate` reports valid.

## 4. Deleted surfaces

```bash
rg -l "topic-log|journal-log|core-workflow|find-cause-workflow|routing-rules|logging-rules|completion-rules|log-audit-commands" \
   as-usual-rules/ skills/ templates/ scripts/ hooks/
rg -l "start-work|hand-off|direct-execute|define-requirements|writing-plan|executing-plan" \
   as-usual-rules/ templates/ scripts/ hooks/
rg -l "topic\.md|question-c|problem\.md|journal\.jsonl|code-review-report|clean-up/|execute/task-" \
   as-usual-rules/ templates/ scripts/ hooks/
ls skills/
git ls-tree -r --name-only HEAD | rg '^(commands/|skills/as-usual-(interview|execute|test)/)'
```

Expected: no output from every `rg`. `ls skills/` shows exactly the fourteen:
`using-as-usual`, `run-topic`, `run-direct-work`, `run-issue`,
`gathering-context`, `write-requirements`, `write-plan`, `execute-plan`,
`review-execution`, `cleanup-code`, `finalize`, `git-action`,
`explore-codebase`, `manage-self-improvement`.

`skills/using-as-usual/SKILL.md` is the one allowed hit for the old artifact
names — it detects pre-v2 folders in order to refuse resuming them. Check the
context before reporting it.

## 5. Skill wiring

```bash
for f in skills/*/SKILL.md; do
  n=$(rg -o '^name: .*' "$f" | sed 's/name: //')
  d=$(basename "$(dirname "$f")")
  [ "$n" = "$d" ] || echo "MISMATCH: $d != $n"
done
```

Expected: no output. Every skill also needs a `description` that says when to use
it, since that is all the model sees before invoking.

## Report

```markdown
## Harness Smoke

- Result: pass | issues-found
- Ran: manifests | hook | record helper | deleted surfaces | skill wiring

### Failures

- <check> — <command> → <actual output>
```

Report the actual output of anything that failed. Never report a check as passing
without having run it.
