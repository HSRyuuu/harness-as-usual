# Claude Plugin Setting

This document describes how to clone AsUsual and install it as a Claude Code local plugin.

## Prerequisites

- Claude Code is installed and `claude plugin --help` works.
- `git` is installed.
- Use `jq` for JSON validation. If `jq` is unavailable, use `python3 -m json.tool <file>`.
- Public repository URL: `https://github.com/HSRyuuu/as-usual.git`.

## Install From Git

Choose where to place the local plugin.

```bash
mkdir -p "$HOME/dev"
cd "$HOME/dev"
git clone https://github.com/HSRyuuu/as-usual.git
export AS_USUAL_REPO="$HOME/dev/as-usual"
```

If the repository already exists:

```bash
export AS_USUAL_REPO="$HOME/dev/as-usual"
cd "$AS_USUAL_REPO"
git pull --ff-only
```

## Validate Repository Files

```bash
cd "$AS_USUAL_REPO"
jq empty .claude-plugin/plugin.json
jq empty .claude-plugin/marketplace.json
jq empty hooks/hooks.json
chmod +x hooks/session-start hooks/run-hook.cmd
```

Expected result: every command exits with `0`.

## Register The Local Marketplace

Create `~/.claude/settings.json` if it does not exist, and keep a backup.

```bash
mkdir -p ~/.claude
test -f ~/.claude/settings.json || printf '{}\n' > ~/.claude/settings.json
cp ~/.claude/settings.json ~/.claude/settings.json.as-usual.bak
```

Merge the AsUsual marketplace into Claude settings.

```bash
node <<'NODE'
const fs = require('fs');
const repo = process.env.AS_USUAL_REPO;
if (!repo) {
  throw new Error('AS_USUAL_REPO is required');
}
const settingsPath = `${process.env.HOME}/.claude/settings.json`;
const settings = fs.existsSync(settingsPath)
  ? JSON.parse(fs.readFileSync(settingsPath, 'utf8'))
  : {};
settings.extraKnownMarketplaces = settings.extraKnownMarketplaces && typeof settings.extraKnownMarketplaces === 'object'
  ? settings.extraKnownMarketplaces
  : {};
settings.extraKnownMarketplaces['as-usual-local'] = {
  source: {
    source: 'directory',
    path: repo
  }
};
settings.enabledPlugins = settings.enabledPlugins && typeof settings.enabledPlugins === 'object'
  ? settings.enabledPlugins
  : {};
settings.enabledPlugins['as-usual@as-usual-local'] = true;
fs.writeFileSync(settingsPath, JSON.stringify(settings, null, 2) + '\n');
NODE
```

Validate:

```bash
jq empty ~/.claude/settings.json
```

## Verify Claude Detects The Plugin

```bash
claude plugin marketplace list | grep -E 'as-usual|as-usual-local'
claude plugin list | grep -E 'as-usual|as-usual-local'
claude plugin details as-usual@as-usual-local
```

Expected result:

```text
as-usual-local
as-usual@as-usual-local
Hooks: SessionStart
```

## Verify Hook Loading

Run the hook directly from the installed plugin repository.

```bash
cd "$AS_USUAL_REPO"
CLAUDE_PLUGIN_ROOT="$AS_USUAL_REPO" hooks/run-hook.cmd session-start \
  | jq '{event: .hookSpecificOutput.hookEventName, injected: (.hookSpecificOutput.additionalContext | contains("AsUsual Harness Rules"))}'
```

Expected result:

```json
{
  "event": "SessionStart",
  "injected": true
}
```

## Restart Claude Code

Claude Code loads plugins at session start. Close the current Claude Code session and start a new one.

## Troubleshooting

Check these items directly.

```bash
cd "$AS_USUAL_REPO"
chmod +x hooks/session-start hooks/run-hook.cmd
jq empty .claude-plugin/plugin.json .claude-plugin/marketplace.json hooks/hooks.json
claude plugin marketplace add "$AS_USUAL_REPO"
claude plugin install as-usual@as-usual-local
claude plugin enable as-usual@as-usual-local
claude plugin details as-usual@as-usual-local
```

After fixing settings or install state, restart Claude Code.

### Plugin Does Not Appear

Check:

- `AS_USUAL_REPO` is set to an absolute path.
- `~/.claude/settings.json` is valid JSON.
- `extraKnownMarketplaces.as-usual-local.source.path` points to the cloned repository.
- `enabledPlugins` uses exactly the `as-usual@as-usual-local` key.
- `.claude-plugin/plugin.json` contains `"name": "as-usual"`.
- `.claude-plugin/marketplace.json` contains `"name": "as-usual-local"` and plugin `"source": "./"`.
- Claude Code was restarted after settings changed.

If `claude plugin details as-usual@as-usual-local` appears in the CLI but the current Claude session does not load the skill or hook, start a new session. Plugins and hooks load at session start.

### Hook Does Not Inject Harness Context

The hook injects a short AsUsual capability summary, the installed `as-usual-rules/core-workflow.md` path, the `using-as-usual` entrypoint, and active topic candidates. It does not inject the full core workflow. The target project should not contain a runtime workflow prompt file.

The hook does not force the AsUsual workflow onto every request. It tells the agent to read the full rules and topic artifacts only when the user mentions `as-usual`, `AsUsual`, `.as-usual/` artifacts, or resuming an active topic. Active topic state uses the `.as-usual/topic/yyyy-MM-dd-<topic>/state.json` format.

### JSON Merge Breaks Settings

Restore the backup.

```bash
cp ~/.claude/settings.json.as-usual.bak ~/.claude/settings.json
```

Then rerun the merge command above. Do not paste duplicate top-level `enabledPlugins` or `extraKnownMarketplaces` objects.

### `jq` Is Not Installed

Use Python's built-in JSON parser.

```bash
python3 -m json.tool ~/.claude/settings.json >/dev/null
python3 -m json.tool "$AS_USUAL_REPO/.claude-plugin/plugin.json" >/dev/null
python3 -m json.tool "$AS_USUAL_REPO/.claude-plugin/marketplace.json" >/dev/null
python3 -m json.tool "$AS_USUAL_REPO/hooks/hooks.json" >/dev/null
```

## Agent Install Prompt

Give Claude Code this prompt.

```text
Clone and install the public AsUsual Claude plugin.
Repository URL: https://github.com/HSRyuuu/as-usual.git
Follow docs/CLAUDE-PLUGIN-SETTING.md exactly.
Set AS_USUAL_REPO to the cloned repository path.
Do not overwrite unrelated settings; register as-usual-local in ~/.claude/settings.json.
Verify with claude plugin marketplace list, claude plugin list, claude plugin details, and the hook smoke test.
```
