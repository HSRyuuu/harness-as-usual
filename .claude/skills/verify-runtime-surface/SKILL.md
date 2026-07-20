---
name: verify-runtime-surface
description: Verifies that runtime-facing AsUsual plugin surfaces do not contain maintainer/plugin-development guidance. Use after hook, core workflow, public runtime skill, or template changes.
disable-model-invocation: true
---

# Verify Runtime Surface

## Purpose

Runtime surfaces seen or executed by a target-project user who installed the AsUsual plugin must not include plugin maintainer guidance.

1. Confirm that SessionStart hook output injects only target-project runtime guidance.
2. Confirm that both runtime workflow prompts, public runtime skills, and templates do not contain plugin development routing.
3. Confirm that project-local maintainer skills are not exposed through public plugin `skills/`.
4. Confirm that runtime docs and hook payloads use only user-facing workflow vocabulary.

## When To Run

- After changing `hooks/session-start` or `hooks/run-hook.cmd`
- After changing `as-usual-rules/core-workflow.md`
- After changing public plugin `skills/**` or `templates/**`
- After changing runtime helper scripts under `scripts/**`
- After changing runtime workflow descriptions in README or public docs
- Before a PR, when checking for runtime prompt leakage

## Related Files

| File | Purpose |
|------|---------|
| `hooks/session-start` | SessionStart context injection source |
| `hooks/run-hook.cmd` | hook runner used for smoke output |
| `as-usual-rules/core-workflow.md` | canonical runtime workflow entrypoint read when AsUsual activates |
| `as-usual-rules/routing-rules.md`, `as-usual-rules/logging-rules.md`, `as-usual-rules/completion-rules.md`, `as-usual-rules/safety-rules.md`, `as-usual-rules/log-audit-commands.md` | runtime-facing single-source rule files |
| `as-usual-rules/find-cause-workflow.md` | canonical find-cause issue workflow |
| `skills/using-as-usual/SKILL.md` | public runtime activation skill |
| `skills/hand-off/SKILL.md` | public runtime hand-off resume skill |
| `skills/find-cause/SKILL.md` | public find-cause issue lifecycle skill |
| `skills/start-work/SKILL.md` | public runtime gate routing skill |
| `skills/direct-execute/SKILL.md` | public runtime direct-execute gate and execution skill |
| `skills/define-requirements/SKILL.md` | public runtime question cycle and requirements writing skill |
| `skills/define-requirements/requirements-document-reviewer-prompt.md` | public runtime requirements review prompt |
| `skills/writing-plan/SKILL.md` | public runtime plan writing skill |
| `skills/writing-plan/plan-document-reviewer-prompt.md` | public runtime plan review prompt |
| `skills/executing-plan/SKILL.md` | public runtime plan execution skill |
| `skills/review-execution/SKILL.md` | public runtime execution review skill |
| `skills/review-execution/code-reviewer-prompt.md` | public runtime execution review prompt |
| `skills/cleanup-code/SKILL.md` | public runtime code cleanup skill |
| `skills/cleanup-code/*.md` | public runtime code cleanup prompts |
| `skills/finalize/SKILL.md` | public runtime finalization skill |
| `skills/git-action/SKILL.md` | public runtime selected git action skill |
| `templates/question.md` | requirements question artifact template |
| `templates/requirements.md` | requirements artifact template |
| `templates/plan.md` | plan artifact template |
| `templates/code-review-report.md` | conditional code review findings report template |
| `templates/report.md` | final topic handoff report template |
| `templates/topic.md` | low-churn topic resume template |
| `scripts/topic-log.py init` | creates `topic.md` and `audit.jsonl` |
| `scripts/topic-log.py` | runtime helper for topic/audit updates and derived status |
| `scripts/journal-log.py` | runtime helper entrypoint for issue journal updates |
| `scripts/as_usual_journal_log/` | issue journal implementation |
| `README.md` | public project overview |
| `docs/CLAUDE-PLUGIN-SETTING.md` | public Claude install guide |
| `docs/CODEX-PLUGIN-SETTING.md` | public Codex install guide |
| `.agents/skills/dev-as-usual/SKILL.md` | allowed maintainer-only development guidance |
| `.agents/skills/manage-skills/SKILL.md` | registered verification skill list |
| `.agents/skills/verify-implementation/SKILL.md` | aggregate verification skill list |
| `AGENTS.md` | maintainer-only project knowledge base |

## Workflow

### Step 1: Hook Output Leakage Check

**Tool:** Bash

Run:

```bash
tmp_file="$(mktemp)"
CLAUDE_PLUGIN_ROOT="$PWD" bash hooks/run-hook.cmd session-start \
  | jq -r '.hookSpecificOutput.additionalContext' > "$tmp_file"
if rg -n 'AGENTS\.md|dev-as-usual|plugin development|AsUsual plugin itself|hook, manifest, docs, skill, install, reload|install, reload|diagnose requests|repository' "$tmp_file"; then
  echo "FAIL: maintainer guidance leaked into hook output"
else
  echo "PASS: hook output is runtime-facing"
fi
rm -f "$tmp_file"
```

PASS:

- `rg` finds no matches in injected hook context.
- Hook context mentions only target-project runtime usage: activation, topic path, first reads, artifact gates, topic.md/audit.jsonl, and derived status.

FAIL:

- Hook context tells the agent to follow `AGENTS.md`, `dev-as-usual`, plugin development rules, install/reload rules, or maintainer repository workflow.

Fix:

- Move maintainer guidance to `AGENTS.md`, `.agents/skills/dev-as-usual`, or project-local docs.
- Keep hook output focused on AsUsual runtime usage in target projects.

### Step 2: Runtime Prompt Surface Check

**Tool:** Bash

Run:

```bash
rg -n 'AGENTS\.md|dev-as-usual|plugin development|AsUsual plugin itself|hook, manifest, docs, skill, install, reload|diagnose requests|DEVELOPING-AS-USUAL' \
  hooks/session-start \
  as-usual-rules \
  skills/using-as-usual/SKILL.md \
  skills/hand-off/SKILL.md \
  skills/find-cause/SKILL.md \
  skills/start-work/SKILL.md \
  skills/direct-execute/SKILL.md \
  skills/define-requirements/SKILL.md \
  skills/define-requirements/requirements-document-reviewer-prompt.md \
  skills/writing-plan/SKILL.md \
  skills/writing-plan/plan-document-reviewer-prompt.md \
  skills/executing-plan/SKILL.md \
  skills/review-execution/SKILL.md \
  skills/review-execution/code-reviewer-prompt.md \
  skills/cleanup-code/SKILL.md \
  skills/cleanup-code/reuse-reviewer-prompt.md \
  skills/cleanup-code/simplification-reviewer-prompt.md \
  skills/cleanup-code/efficiency-reviewer-prompt.md \
  skills/cleanup-code/abstraction-reviewer-prompt.md \
  skills/finalize/SKILL.md \
  skills/git-action/SKILL.md \
  templates \
  scripts/topic-log.py \
  scripts/journal-log.py \
  scripts/as_usual_journal_log
removed_state='state'"\.json"
removed_helper='state'"-machine\.py"
removed_task_verification='task'"Verification"
removed_safety_gates='safety'"Gates"
removed_current_phase='current'"\.phase"
removed_current_next='current'"\.nextAction"
stale_pattern="${removed_state}|${removed_helper}|${removed_task_verification}|${removed_safety_gates}|${removed_current_phase}|${removed_current_next}"
rg -n "$stale_pattern" \
  hooks/session-start \
  as-usual-rules \
  skills \
  templates \
  scripts/topic-log.py \
  scripts/journal-log.py \
  scripts/as_usual_journal_log
```

PASS:

- No matches in runtime prompt, hook, public runtime skills, or templates.
- No stale audit-first matches appear in live runtime surfaces, except explicit anti-pattern text that says the old surface must not be used.

FAIL:

- Runtime prompt or runtime skill includes maintainer-only routing, `AGENTS.md`, `dev-as-usual`, plugin install/reload diagnosis, or repository development instructions.
- Runtime prompt, hook, public runtime skill, template, or helper still requires the removed JSON state artifact, removed helper, removed task verification array, removed safety gate object, or removed current status fields operationally.

Fix:

- Remove the maintainer text from runtime surface.
- If the rule is still needed for repository development, keep it in `AGENTS.md` or `.agents/skills/dev-as-usual/SKILL.md`.

### Step 3: Public Skill Boundary Check

**Tool:** Bash

Run:

```bash
find skills -maxdepth 2 -name SKILL.md -print | sort
test ! -e skills/dev-as-usual/SKILL.md
test ! -e skills/manage-skills/SKILL.md
test ! -e skills/verify-runtime-surface/SKILL.md
```

PASS:

- Public `skills/` contains only skills intended for target-project users.
- Maintainer-only skills remain under `.agents/skills/`.

FAIL:

- Project-local development or verification skills are exposed through public plugin `skills/`.

Fix:

- Move maintainer-only skills back to `.agents/skills/`.
- Keep public plugin `skills/` limited to target-project runtime or explicitly user-facing support skills.

### Step 4: Public Docs Boundary Check

**Tool:** Bash

Run:

```bash
rg -n 'dev-as-usual|project-local `dev-as-usual`|repository `AGENTS\.md`|plugin development work|not runtime workflow' \
  README.md docs/CLAUDE-PLUGIN-SETTING.md docs/CODEX-PLUGIN-SETTING.md
```

PASS:

- Public docs do not instruct installed-plugin users to route ordinary plugin usage through maintainer-only skills.
- Install docs may describe install or reload commands, but not as runtime workflow instructions.

FAIL:

- Public docs contain maintainer-only routing instructions for target-project runtime usage.

Fix:

- Move maintainer-only instructions to `AGENTS.md` or `.agents/skills/dev-as-usual/SKILL.md`.
- Keep public docs about installation and usage from the target-project user's perspective.

## Output Format

```markdown
## verify-runtime-surface Report

| Check | Status | Evidence |
|-------|--------|----------|
| Hook output leakage | PASS/FAIL | ... |
| Runtime prompt surface | PASS/FAIL | ... |
| Public skill boundary | PASS/FAIL | ... |
| Public docs boundary | PASS/FAIL | ... |

### Findings

| File | Line | Problem | Fix |
|------|------|---------|-----|
| `path/to/file` | 12 | Maintainer guidance leaked into runtime surface | Move to `.agents/skills/dev-as-usual` |
```

## Exceptions

1. `AGENTS.md` and `.agents/skills/**` may contain maintainer/plugin-development guidance.
2. `docs/CLAUDE-PLUGIN-SETTING.md` and `docs/CODEX-PLUGIN-SETTING.md` may mention install and reload commands when explaining setup or troubleshooting.
