---
name: turn-on-off-as-usual
description: AsUsual repository development skill. Use when developing as-usual and the user asks to turn the locally installed AsUsual Claude Code or Codex plugin/harness on or off so the runtime SessionStart harness does not interfere with plugin development.
---

# Turn On/Off AsUsual

## Overview

Toggle the developer's locally installed AsUsual plugin state for Claude Code and Codex while working inside the AsUsual repository. This skill lives in `.agents/skills/` on purpose; do not move it into the plugin's public `skills/` directory.

## Boundary

This is plugin development and local plugin administration. It is not an AsUsual runtime skill for target projects.

Do not:

- Start an AsUsual runtime topic.
- Create `.as-usual/topic/` artifacts.
- Apply the question/requirements/plan workflow just because the request mentions AsUsual.
- Copy this skill to `skills/` or expose it through `.codex-plugin/plugin.json`.

Turning the plugin off disables the SessionStart harness in future sessions. Because this skill is project-local under `.agents/skills/`, it should remain available while developing this repository even when the AsUsual plugin itself is disabled.

## First Reads

Before changing anything, read the relevant current docs:

- For Codex: `docs/CODEX-PLUGIN-SETTING.md`
- For Claude Code: `docs/CLAUDE-PLUGIN-SETTING.md`
- For development boundary: `README.md`

## Quick Commands

Run from the AsUsual repository root unless `--repo` is supplied.

```bash
.agents/skills/turn-on-off-as-usual/scripts/as-usual-toggle.sh status
.agents/skills/turn-on-off-as-usual/scripts/as-usual-toggle.sh off --all
.agents/skills/turn-on-off-as-usual/scripts/as-usual-toggle.sh on --all
.agents/skills/turn-on-off-as-usual/scripts/as-usual-toggle.sh reload --codex
```

Limit the surface when the user names one host:

```bash
.agents/skills/turn-on-off-as-usual/scripts/as-usual-toggle.sh off --codex
.agents/skills/turn-on-off-as-usual/scripts/as-usual-toggle.sh on --claude
.agents/skills/turn-on-off-as-usual/scripts/as-usual-toggle.sh reload --codex
```

## Behavior

For `off`:

- Codex: run `codex plugin remove as-usual@harness-as-usual --json` when Codex is available. Keep the repository-local marketplace intact.
- Claude Code: set `enabledPlugins["as-usual@harness-as-usual"] = false` in `~/.claude/settings.json`, preserving unrelated settings and writing a timestamped backup first.

For `on`:

- Codex: validate the repo-local plugin shape, ensure `plugins/as-usual -> ..`, register the repository-local marketplace, remove `as-usual@harness-as-usual`, delete the AsUsual cache snapshot under `~/.codex/plugins/cache/harness-as-usual/as-usual`, then add `as-usual@harness-as-usual` to force a fresh installed snapshot.
- Claude Code: register `extraKnownMarketplaces.harness-as-usual` against the repository path and set `enabledPlugins["as-usual@harness-as-usual"] = true`.

For `reload`:

- Codex: perform the same snapshot refresh used by `on --codex`. Use this after changing repository source code because Codex runs the installed cache snapshot, not the live repository tree.
- Claude Code: ensure the repository-local marketplace is registered and the plugin is enabled. A plugin version bump remains the reliable way to invalidate Claude's versioned snapshot; existing sessions still need a restart.

For `status`:

- Print Claude settings state when readable.
- Print `claude plugin list`, `codex plugin list`, and relevant config snippets when the CLIs are available.
- Do not mutate files.

## Reporting

After `on`, `off`, or `reload`, tell the user:

- Which host surfaces changed: Claude Code, Codex, or both.
- That existing sessions keep their already-loaded hook and skill context; start a fresh session for the change to take effect.
- If turning off, how to turn it back on manually:

```bash
cd /path/to/as-usual
.agents/skills/turn-on-off-as-usual/scripts/as-usual-toggle.sh on --all
```

## Verification

For non-mutating checks, run:

```bash
.agents/skills/turn-on-off-as-usual/scripts/as-usual-toggle.sh status
```

For a source-level validation after editing this skill or script, run:

```bash
bash -n .agents/skills/turn-on-off-as-usual/scripts/as-usual-toggle.sh
python3 /path/to/skill-creator/scripts/quick_validate.py .agents/skills/turn-on-off-as-usual
```
