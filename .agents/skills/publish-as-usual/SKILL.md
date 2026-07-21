---
name: publish-as-usual
description: AsUsual repository release skill. Use only when the maintainer explicitly asks to publish/release AsUsual — run the release loop in order: verify, commit, bump the plugin version in lockstep, push main, then update the GitHub-installed plugin on this machine.
---

# Publish AsUsual

## Overview

Run the AsUsual release loop in one order: verify, commit, bump the plugin
version, push `main`, then update the GitHub-installed plugin on this machine.

This is plugin development and release administration, not an AsUsual runtime
skill. Do not start a `.as-usual/topic/` workflow for it, and do not move this
skill into the public `skills/` tree. See `dev-as-usual` for the
development-vs-runtime boundary.

Distribution model (`docs/CLAUDE-PLUGIN-SETTING.md`, `docs/CODEX-PLUGIN-SETTING.md`):
machines install via `/plugin marketplace add HSRyuuu/harness-as-usual` and
`/plugin install as-usual@harness-as-usual`. Both hosts serve the installed
snapshot keyed by **plugin version**:

- Claude Code: `~/.claude/plugins/cache/harness-as-usual/as-usual/<version>/`
- Codex: `~/.codex/plugins/cache/harness-as-usual/as-usual/<version>/`

Pushing commits alone changes nothing for installed machines — the version bump
is the release. The canonical versions are `.claude-plugin/plugin.json` (Claude)
and `.codex-plugin/plugin.json` (Codex); they must move together. The
marketplace `plugins[]` entry intentionally carries no version.

This skill is intentionally explicit-only. Do not infer it from a normal request
such as "commit", "push", or "reload".

## Required Sub-skills / References

Before acting, read and follow:

- `CLAUDE.md` / `AGENTS.md` CONVENTIONS for commit discipline: stage paths
  explicitly (never `git add .`), never commit `.as-usual/topic/`,
  `.as-usual/issue/`, `.codegraph/`, or installed-plugin cache output
  (`.as-usual/memory/` is the one commit-target exception, not relevant here).
  Use the repository's existing Conventional Commits style (`feat:`, `fix:`,
  `docs:`, `refactor:`, `test:`, `chore:`).
- `verify-implementation` for the pre-publish verification gate (it runs the
  registered AsUsual verification skills in sequence).
- `turn-on-off-as-usual` only for troubleshooting when a host still shows the
  old version after update, or when this machine runs the local-directory
  development install instead of the GitHub install.

## Preconditions

- The target repository must be AsUsual (`harness-as-usual` marketplace, plugin
  name `as-usual`).
- The active branch must be `main`.
- Push only to `origin main`.
- Never force push.
- Do not bump or push if verification or commit fails.
- Do not switch branches, stash, rebase, pull, or resolve conflicts unless the
  user explicitly asks.

Confirm the repository before mutating state:

```bash
jq -r '.name' .claude-plugin/plugin.json      # expect: as-usual
jq -r '.name' .codex-plugin/plugin.json        # expect: as-usual
jq -r '.name' .claude-plugin/marketplace.json  # expect: harness-as-usual
test -d skills && test -d as-usual-rules
git branch --show-current                       # expect: main
git status --short
```

If the plugin name is not `as-usual`, the marketplace is not `harness-as-usual`,
or the branch is not `main`, stop and report the reason.

## Workflow

### 1. Verify

Run the pre-publish verification gate before committing. Stop on any failure.

- Validate every manifest and hook config:

  ```bash
  jq empty .claude-plugin/plugin.json .claude-plugin/marketplace.json
  jq empty .codex-plugin/plugin.json .agents/plugins/marketplace.json
  jq empty hooks/hooks.json hooks/hooks-codex.json
  ```

- Smoke-test the SessionStart hook:

  ```bash
  CLAUDE_PLUGIN_ROOT="$PWD" bash hooks/run-hook.cmd session-start \
    | jq '{event: .hookSpecificOutput.hookEventName,
           hasUsingSkill: (.hookSpecificOutput.additionalContext | contains("using-as-usual")),
           hasFindCause: (.hookSpecificOutput.additionalContext | contains("find-cause"))}'
  ```

- Run the script test suites:

  ```bash
  python3 -m unittest scripts.tests.test_journal_log scripts.tests.test_topic_log_verdict
  ```

- Guard public surface: no private absolute paths in public install docs,
  manifests, or the public `skills/` tree (maintainer-only `.agents/skills/`
  and `.claude/skills/` legitimately hardcode dev-machine paths, so they are
  out of scope), and maintainer skills stay mirrored between `.agents/skills/`
  and `.claude/skills/` (see `skill-registry-sync`):

  ```bash
  git grep -n '/Users/' -- \
    'docs/CLAUDE-PLUGIN-SETTING.md' 'docs/CODEX-PLUGIN-SETTING.md' \
    'docs/INSTALL*' 'docs/UNINSTALL.md' \
    '.claude-plugin/*.json' '.codex-plugin/*.json' '.agents/plugins/*.json' \
    'skills/**' \
    && echo "PRIVATE PATH LEAK" || echo "no private path in public surface"
  python3 .agents/skills/skill-registry-sync/scripts/sync-maintainer-skills.py
  ```

- Run the aggregate `verify-implementation` skill for broader consistency
  (runtime-surface, harness smoke, workflow consistency, project identity).

### 2. Commit

Use the commit discipline referenced above.

- Inspect `git status --short`, `git diff --stat`, and relevant diffs.
- Stage only files related to the current task with explicit paths.
- If there are no working tree changes, do not create an empty commit. Continue
  only if `main` has unpushed commits to publish.
- Use the repository's existing Conventional Commits style.

### 3. Bump Plugin Version

The plugin version is the cache key on both hosts, so a release without a bump is
invisible to installed machines.

If any commit being published changes plugin-visible content (`skills/`,
`as-usual-rules/`, `templates/`, `hooks/`, `scripts/`, or either plugin manifest)
and the version was not already bumped in those commits:

- Bump `version` in **both** `.claude-plugin/plugin.json` and
  `.codex-plugin/plugin.json` to the **same value**. Patch bump by default;
  minor when the user says the release is feature-level.
- Never add a `version` to `.claude-plugin/marketplace.json` or
  `.agents/plugins/marketplace.json` `plugins[]` — the `plugin.json` value
  silently wins and the mismatch confuses cache debugging.
- Verify lockstep, then commit in the existing style:

  ```bash
  test "$(jq -r .version .claude-plugin/plugin.json)" = "$(jq -r .version .codex-plugin/plugin.json)" \
    && echo "versions match" || echo "VERSION MISMATCH"
  ```

  Commit message: `chore: bump plugin version to X.Y.Z`.

If nothing plugin-visible changed (repo docs only, local-only files), skip the
bump and say so in the report.

### 4. Push Main

Push the current `main` branch directly:

```bash
git push origin main
```

If the push fails, stop. Do not force push and do not update plugins.

### 5. Update Installed Plugins

Third-party marketplaces do not auto-update, so run the update explicitly after a
successful push. If one host CLI is unavailable, report that host as skipped and
continue with the other.

```bash
# Claude Code — refresh catalog, then update the plugin
claude plugin marketplace update harness-as-usual
claude plugin update as-usual@harness-as-usual
claude plugin details as-usual@harness-as-usual

# Codex — refresh the marketplace snapshot
codex plugin marketplace upgrade harness-as-usual
codex plugin list
```

- Confirm the reported version equals the version just pushed. "Already at the
  latest version" **with the old version number** means the bump commit did not
  reach `origin main` — fix the push, do not prune caches.
- Do not remove cache directories in this flow; the version bump makes both hosts
  fetch a fresh snapshot on update.
- **Local-development machine caveat:** if this machine registered the AsUsual
  marketplace from a local directory (the development install) rather than from
  GitHub, the commands above target the GitHub catalog and will not reflect
  live repo edits. Refresh the local snapshot instead with
  `turn-on-off-as-usual` (`... as-usual-toggle.sh reload --codex` / `reload --claude`).
- Other machines are updated by running the GitHub update commands there; they
  are not reachable from this loop.

### 6. New Session

Both hosts load the new snapshot only in a fresh session. Tell the user to
restart Claude Code and Codex sessions before expecting changed skills, hooks,
rules, or manifests.

## Report

Report:

- verification result (manifests, hook smoke, tests, mirror/private-path guard,
  `verify-implementation` outcome)
- commit hash(es) and message(s), or that no commit was needed
- version bump `old → new` (confirmed identical in both manifests), or why the
  bump was skipped
- push target and result
- per-host update result with the version each host reports, or why a host was
  skipped
- reminder that new sessions are required on every machine, and that other
  machines must run the update commands themselves
