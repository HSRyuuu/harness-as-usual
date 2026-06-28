# Codex Plugin Setting

This document describes how to clone AsUsual and install it as a Codex local plugin.

## Prerequisites

- Codex CLI is installed and `codex plugin --help` works.
- `git` is installed.
- Use `jq` for JSON validation. If `jq` is unavailable, use `python3 -m json.tool <file>`.
- Public repository URL: `https://github.com/HSRyuuu/harness-as-usual.git`.

## Install From Git

Choose where to place the local plugin.

```bash
mkdir -p "$HOME/dev"
cd "$HOME/dev"
git clone https://github.com/HSRyuuu/harness-as-usual.git
export AS_USUAL_REPO="$HOME/dev/harness-as-usual"
```

If the repository already exists:

```bash
export AS_USUAL_REPO="$HOME/dev/harness-as-usual"
cd "$AS_USUAL_REPO"
git pull --ff-only
```

## Important Codex Model

Codex does not load a plugin just because a plugin entry exists in `~/.agents/plugins/marketplace.json`.

This local development install requires the following:

1. The marketplace file at `$AS_USUAL_REPO/.agents/plugins/marketplace.json`.
2. The plugin source path inside that marketplace: `./plugins/as-usual`.
3. The `$AS_USUAL_REPO/plugins/as-usual` symlink pointing back to the plugin root.
4. A marketplace entry registered in `~/.codex/config.toml`.
5. An installed plugin entry in `~/.codex/config.toml`.
6. A cache snapshot under `~/.codex/plugins/cache/as-usual-local/as-usual/<version>/`.

## Validate Repository Files

```bash
cd "$AS_USUAL_REPO"
mkdir -p plugins
ln -sfn .. plugins/as-usual
jq empty .agents/plugins/marketplace.json
jq empty .codex-plugin/plugin.json
jq empty hooks/hooks-codex.json
chmod +x hooks/session-start hooks/run-hook.cmd
test "$(readlink plugins/as-usual)" = ".."
```

Expected result: every command exits with `0`.

If `jq` is unavailable:

```bash
python3 -m json.tool "$AS_USUAL_REPO/.agents/plugins/marketplace.json" >/dev/null
python3 -m json.tool "$AS_USUAL_REPO/.codex-plugin/plugin.json" >/dev/null
python3 -m json.tool "$AS_USUAL_REPO/hooks/hooks-codex.json" >/dev/null
```

## Register Marketplace

```bash
codex plugin marketplace add "$AS_USUAL_REPO" --json
```

Expected output includes:

```json
{
  "marketplaceName": "as-usual-local"
}
```

This command writes a `[marketplaces.as-usual-local]` entry to `~/.codex/config.toml`.

## Install Plugin

```bash
codex plugin add as-usual@as-usual-local --json
```

Expected output includes:

```json
{
  "pluginId": "as-usual@as-usual-local",
  "version": "0.1.0"
}
```

This command writes `[plugins."as-usual@as-usual-local"]` to `~/.codex/config.toml` and creates a cache snapshot.

## Verify Codex Detects The Plugin

```bash
codex plugin marketplace list | grep -E 'as-usual|as-usual-local'
codex plugin list | grep -E 'as-usual|as-usual-local'
grep -E 'as-usual-local|as-usual' ~/.codex/config.toml
```

Expected result:

```text
as-usual-local
as-usual@as-usual-local  installed, enabled  0.1.0
```

## Verify Cache

```bash
test -f ~/.codex/plugins/cache/as-usual-local/as-usual/0.1.0/.codex-plugin/plugin.json
jq '.name,.version,.hooks' ~/.codex/plugins/cache/as-usual-local/as-usual/0.1.0/.codex-plugin/plugin.json
```

Expected manifest values:

```text
"as-usual"
"0.1.0"
"./hooks/hooks-codex.json"
```

## Verify Hook Loading

Run the hook directly from the installed plugin cache.

```bash
PLUGIN_ROOT="$HOME/.codex/plugins/cache/as-usual-local/as-usual/0.1.0" \
  "$HOME/.codex/plugins/cache/as-usual-local/as-usual/0.1.0/hooks/run-hook.cmd" session-start \
  | jq '{event: .hookSpecificOutput.hookEventName, injected: (.hookSpecificOutput.additionalContext | contains("AsUsual Harness Rules"))}'
```

Expected result:

```json
{
  "event": "SessionStart",
  "injected": true
}
```

## Restart Codex

Codex loads plugin manifests and hooks at session start. Start a new Codex session after installing.

If a new skill or hook change does not appear in a fresh session, the repository change is not reflected in the installed snapshot. Recreate the plugin snapshot.

```bash
codex plugin remove as-usual@as-usual-local --json
codex plugin add as-usual@as-usual-local --json
```

## Troubleshooting

Check these items directly.

```bash
cd "$AS_USUAL_REPO"
ln -sfn .. plugins/as-usual
chmod +x hooks/session-start hooks/run-hook.cmd
jq empty .codex-plugin/plugin.json .agents/plugins/marketplace.json hooks/hooks-codex.json
codex plugin marketplace add "$AS_USUAL_REPO" --json
codex plugin add as-usual@as-usual-local --json
codex plugin list | grep -E 'as-usual|as-usual-local'
```

After fixing settings or install state, start a new Codex session.

### Personal Marketplace Entry Shows "not installed"

Known failing form:

```text
~/.agents/plugins/marketplace.json
source.path = "./plugins/as-usual"
```

This form can make `codex plugin list` resolve the plugin relative to the home directory instead of the repository.

Fix:

- Use the repository-local marketplace at `$AS_USUAL_REPO/.agents/plugins/marketplace.json`.
- Run `codex plugin marketplace add "$AS_USUAL_REPO" --json`.
- Run `codex plugin add as-usual@as-usual-local --json`.

### Plugin Does Not Show Up In New Session

Check:

```bash
codex plugin list | grep -E 'as-usual|as-usual-local'
grep -E 'as-usual-local|as-usual' ~/.codex/config.toml
```

Both entries are required.

```text
[marketplaces.as-usual-local]
[plugins."as-usual@as-usual-local"]
```

If the marketplace exists but the plugin is not installed:

```bash
codex plugin add as-usual@as-usual-local --json
```

### Local Changes Do Not Appear

Codex installs a versioned cache snapshot. After changing manifests or hooks:

```bash
codex plugin remove as-usual@as-usual-local
codex plugin add as-usual@as-usual-local --json
```

If changes still do not appear, bump `.codex-plugin/plugin.json` version and reinstall.

### Hook Does Not Inject Context

Check:

- `.codex-plugin/plugin.json` contains `"hooks": "./hooks/hooks-codex.json"`.
- `hooks/hooks-codex.json` is valid JSON.
- `hooks/session-start` and `hooks/run-hook.cmd` are executable.
- The plugin cache contains `as-usual-rules/core-workflow.md`.

The hook does not force the AsUsual workflow onto every request. It injects a short capability summary, the full rule file path, the `using-as-usual` entrypoint, and active topic candidates. The agent reads the full rules only when the user mentions `as-usual`, `AsUsual`, `.as-usual/` artifacts, or resuming an active topic. Active topic state uses the `.as-usual/topic/yyyy-MM-dd-<topic>/state.json` format.

Manual check:

```bash
PLUGIN_ROOT="$HOME/.codex/plugins/cache/as-usual-local/as-usual/0.1.0" \
  "$HOME/.codex/plugins/cache/as-usual-local/as-usual/0.1.0/hooks/run-hook.cmd" session-start \
  | jq .
```

### Hook Trust Prompt Appears

Codex may ask whether to trust a newly installed plugin hook. In an interactive session, approve only after confirming the hook command points inside the installed AsUsual plugin cache or repository.

Bypass hook trust only for non-interactive smoke tests.

```bash
codex exec -C "$AS_USUAL_REPO" \
  --dangerously-bypass-hook-trust \
  --dangerously-bypass-approvals-and-sandbox \
  'Check whether the AsUsual plugin and SessionStart hook are loaded.'
```

Do not use `--dangerously-bypass-hook-trust` as a normal default.

## Agent Install Prompt

Give Codex this prompt.

```text
Clone and install the public AsUsual Codex plugin.
Repository URL: https://github.com/HSRyuuu/harness-as-usual.git
Follow docs/CODEX-PLUGIN-SETTING.md exactly.
Set AS_USUAL_REPO to the cloned repository path.
Use the repository-local marketplace, not ~/.agents/plugins/marketplace.json.
Run codex plugin marketplace add "$AS_USUAL_REPO" --json.
Run codex plugin add as-usual@as-usual-local --json.
Verify with codex plugin list, ~/.codex/config.toml, cache path, and the hook smoke test.
Do not overwrite unrelated Codex config.
```
