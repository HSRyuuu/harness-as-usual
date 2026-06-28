# Install

Quick guide to install AsUsual as a local plugin for both Claude Code and Codex,
using the plugin CLIs directly. For host-specific detail and troubleshooting, see
[CLAUDE-PLUGIN-SETTING.md](CLAUDE-PLUGIN-SETTING.md) and
[CODEX-PLUGIN-SETTING.md](CODEX-PLUGIN-SETTING.md).

Plugin / marketplace names used throughout:

- Plugin id: `as-usual@as-usual-local`
- Marketplace name: `as-usual-local`

## Prerequisites

- `claude plugin --help` and `codex plugin --help` both work.
- `git` is installed. Use `jq` for JSON validation (or `python3 -m json.tool <file>`).
- The AsUsual repository is cloned locally and `AS_USUAL_REPO` points at it.

```bash
export AS_USUAL_REPO="$HOME/dev/harness-as-usual"
# If it is not cloned yet:
# git clone https://github.com/HSRyuuu/harness-as-usual.git "$AS_USUAL_REPO"
cd "$AS_USUAL_REPO"
```

## 1. Validate Repository Files

```bash
cd "$AS_USUAL_REPO"
jq empty .claude-plugin/plugin.json .claude-plugin/marketplace.json \
         .codex-plugin/plugin.json .agents/plugins/marketplace.json \
         hooks/hooks.json hooks/hooks-codex.json
chmod +x hooks/session-start hooks/run-hook.cmd
```

Expected result: every command exits with `0`.

## 2. Install For Claude Code

The Claude marketplace source is the repository root (`./`), so no symlink is needed.

```bash
claude plugin marketplace add "$AS_USUAL_REPO"
claude plugin install as-usual@as-usual-local
claude plugin enable as-usual@as-usual-local
claude plugin details as-usual@as-usual-local
```

Expected: `claude plugin details as-usual@as-usual-local` lists the AsUsual skills and
one `SessionStart` hook.

## 3. Install For Codex

The Codex marketplace source path is `./plugins/as-usual`, a symlink back to the
repository root. Create it before registering the marketplace.

```bash
cd "$AS_USUAL_REPO"
mkdir -p plugins
ln -sfn .. plugins/as-usual
test "$(readlink plugins/as-usual)" = ".."

codex plugin marketplace add "$AS_USUAL_REPO" --json
codex plugin add as-usual@as-usual-local --json
codex plugin list | grep -E 'as-usual'
```

Expected: `codex plugin list` shows `as-usual@as-usual-local  installed, enabled`.

> The `plugins/as-usual` symlink is gitignored (local-only workspace), so a fresh
> clone does not have it. Recreate it after every clone before installing on Codex.

## 4. Verify Both Hosts

```bash
claude plugin marketplace list | grep -A1 as-usual-local
claude plugin list             | grep as-usual@as-usual-local
codex plugin marketplace list  | grep as-usual-local
codex plugin list              | grep as-usual@as-usual-local
```

Both marketplace roots should point at `$AS_USUAL_REPO`.

## 5. Restart Sessions

Claude Code and Codex load plugins, skills, and hooks at session start. Start a new
session in each host after installing.

## Re-point An Existing Install To A Different Repo Path

When `as-usual-local` is already registered at an old path (for example after moving
or re-cloning the repository), remove it and re-add from the new `AS_USUAL_REPO`.

```bash
export AS_USUAL_REPO="$HOME/dev/harness-as-usual"   # new repo path
cd "$AS_USUAL_REPO"

# Claude Code
claude plugin marketplace remove as-usual-local
claude plugin marketplace add "$AS_USUAL_REPO"
claude plugin install as-usual@as-usual-local
claude plugin enable as-usual@as-usual-local

# Codex
mkdir -p plugins && ln -sfn .. plugins/as-usual
codex plugin remove as-usual@as-usual-local --json
codex plugin marketplace remove as-usual-local
codex plugin marketplace add "$AS_USUAL_REPO" --json
codex plugin add as-usual@as-usual-local --json
```

Then verify with the commands in section 4 and start new sessions.

## Agent Install Prompt

```text
Install the AsUsual plugin locally for Claude Code and Codex.
Set AS_USUAL_REPO to the cloned repository path.
Follow docs/INSTALL.md exactly.
For Codex, create the plugins/as-usual symlink before registering the marketplace.
Verify both hosts with their plugin marketplace list / plugin list, then restart sessions.
```
