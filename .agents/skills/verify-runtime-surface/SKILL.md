---
name: verify-runtime-surface
description: Verifies that runtime-facing AsUsual surfaces contain no plugin-maintainer guidance. Use after changing hooks, runtime rules, public skills, templates, or scripts.
disable-model-invocation: true
---

# Verify Runtime Surface

## Purpose

A user who installs AsUsual sees the hook output, the rules, the public skills,
and the templates. None of those may tell them how to develop the AsUsual plugin
itself.

The failure this catches is subtle: maintainer instructions leaking into runtime
prompts make the agent try to "fix AsUsual" inside someone else's project.

## When To Run

- After changing `hooks/session-start` or `hooks/run-hook.cmd`
- After changing `as-usual-rules/**`, `skills/**`, `templates/**`, or `scripts/**`
- After changing runtime workflow descriptions in `README.md` or `docs/**`
- Before a PR that touches any runtime-facing file

## Runtime-Facing Surfaces

`hooks/session-start` · `as-usual-rules/**` · `skills/**` (all fifteen, plus their
prompt and reference files) · `templates/**` · `scripts/**`

Maintainer-only surfaces, which may contain this guidance freely:
`AGENTS.md` · `CLAUDE.md` · `.agents/skills/**` · `.claude/skills/**` ·
`docs/DEVELOPMENT.md` · `PROJECT_IDENTITY.md`

## 1. Hook output

```bash
CLAUDE_PLUGIN_ROOT="$PWD" bash hooks/run-hook.cmd session-start \
  | jq -r '.hookSpecificOutput.additionalContext' \
  | rg -n 'AGENTS\.md|CLAUDE\.md|dev-as-usual|plugin development|marketplace|install|reload|maintainer' \
  && echo "FAIL: maintainer guidance in hook output" || echo "PASS"
```

The hook announces capability and one entry point. Anything about developing,
installing, or reloading the plugin belongs in maintainer docs.

## 2. Runtime prompts

```bash
rg -n 'AGENTS\.md|dev-as-usual|plugin development|AsUsual plugin itself|the AsUsual repo|marketplace|codex plugin|plugin\.json|DEVELOPING-AS-USUAL' \
  hooks/session-start as-usual-rules/ skills/ templates/ \
  && echo "FAIL" || echo "PASS"
```

A runtime skill naming `AGENTS.md` or telling the agent about plugin manifests is
a leak. Move it to a maintainer surface — `CLAUDE.md`/`AGENTS.md` or `.agents/skills/`.

## 3. Maintainer skills stay out of the public plugin

```bash
ls skills/ | rg 'verify-|manage-skills|publish-|turn-on-off|reference-search|dev-as-usual' \
  && echo "FAIL: maintainer skill in public skills/" || echo "PASS"
git ls-tree -r --name-only HEAD | rg '^(commands/|skills/as-usual-(interview|execute|test)/)' \
  && echo "FAIL: draft surface committed" || echo "PASS"
```

`skills/` is public plugin surface. Maintainer skills live in `.agents/skills/`
and `.claude/skills/`.

## 4. No private paths in public docs

```bash
rg -n '/Users/|/home/[a-z]' README.md docs/ skills/ templates/ as-usual-rules/ \
  && echo "FAIL: machine-specific path in public surface" || echo "PASS"
```

Install docs use `https://github.com/HSRyuuu/harness-as-usual.git` and
`AS_USUAL_REPO`, never someone's home directory.

## 5. Vocabulary is user-facing

Read the runtime prompts and check they speak about the user's work — work units,
decisions, plans, verification — rather than about this repository's internals.
References to `scripts/as-usual-record.py` are fine: that is the runtime helper a
target project actually invokes.

## Report

```markdown
## Runtime Surface

- Result: pass | issues-found

### Leaks

- <file:line> — <what maintainer guidance appeared on a runtime surface>
- Fix: move to <maintainer surface>
```
