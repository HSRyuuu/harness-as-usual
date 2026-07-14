# Install

AsUsual supports the same marketplace identity for GitHub installs and local-directory development installs.

- Marketplace name: `harness-as-usual`
- Plugin id: `as-usual@harness-as-usual`
- Repository: `https://github.com/HSRyuuu/harness-as-usual`

Choose exactly one source on a machine. Registering both GitHub and a local clone as separate marketplaces can load the same skills and hooks twice.

When switching between GitHub and a local directory, uninstall the current plugin and remove the `harness-as-usual` marketplace first, then add the new source. The plugin id stays the same.

## Option 1: Install From GitHub

No manual clone is required. Each host downloads the repository into its plugin cache.

### Claude Code

Run in Claude Code:

```text
/plugin marketplace add HSRyuuu/harness-as-usual
/plugin install as-usual@harness-as-usual
```

Verify in a terminal:

```bash
claude plugin marketplace list | grep harness-as-usual
claude plugin list | grep as-usual@harness-as-usual
```

### Codex

Run in a terminal:

```bash
codex plugin marketplace add HSRyuuu/harness-as-usual
codex plugin add as-usual@harness-as-usual
codex plugin list | grep as-usual@harness-as-usual
```

Start a new Claude Code or Codex session after installation so the skills and `SessionStart` hook load.

## Update A GitHub Install

Third-party marketplaces do not necessarily update automatically. Refresh them explicitly:

```bash
# Claude Code: refresh the catalog, then install the new plugin version.
claude plugin marketplace update harness-as-usual
claude plugin update as-usual@harness-as-usual

# Codex: refresh the marketplace snapshot.
codex plugin marketplace upgrade harness-as-usual
```

Both hosts use the plugin manifest `version` as a cache key. Publishing repository changes therefore requires bumping `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` to the same new version. Do not add a duplicate `version` to either marketplace `plugins[]` entry; the plugin manifests are canonical.

Start new sessions after every update. Already-running sessions keep their loaded hook and skill context.

## Option 2: Install From A Local Clone

Use this flow when developing AsUsual itself. Local and GitHub installs use the same marketplace and plugin id, so switching source does not change commands.

```bash
export AS_USUAL_REPO="$HOME/dev/harness-as-usual"
git clone https://github.com/HSRyuuu/harness-as-usual.git "$AS_USUAL_REPO"
cd "$AS_USUAL_REPO"

jq empty .claude-plugin/plugin.json .claude-plugin/marketplace.json \
         .codex-plugin/plugin.json .agents/plugins/marketplace.json \
         hooks/hooks.json hooks/hooks-codex.json
test "$(readlink plugins/as-usual)" = ".."
chmod +x hooks/session-start hooks/run-hook.cmd
```

The tracked `plugins/as-usual -> ..` symlink lets Codex resolve the repository root from `.agents/plugins/marketplace.json`. A fresh clone already contains it.

### Claude Code Local Directory

Run in Claude Code:

```text
/plugin marketplace add /absolute/path/to/harness-as-usual
/plugin install as-usual@harness-as-usual
```

### Codex Local Directory

```bash
codex plugin marketplace add "$AS_USUAL_REPO" --json
codex plugin add as-usual@harness-as-usual --json
```

You can also run the local installer from the clone:

```bash
bash docs/INSTALL.sh
```

For a local Codex source refresh, use the maintainer reload helper, which re-registers the directory marketplace and recreates only the AsUsual installed snapshot:

```bash
.agents/skills/turn-on-off-as-usual/scripts/as-usual-toggle.sh reload --codex
```

For Claude Code, bumping the plugin version is the reliable cache refresh. If a local cache is stale during development, the helper keeps the directory marketplace enabled, but a new session is still required.

## Migrate An Older `as-usual-local` Install

Remove the old plugin identity before installing the new marketplace identity:

```bash
claude plugin disable as-usual@as-usual-local || true
claude plugin uninstall as-usual@as-usual-local || true
claude plugin marketplace remove as-usual-local || true

codex plugin remove as-usual@as-usual-local --json || true
codex plugin marketplace remove as-usual-local || true
```

Then follow either installation option above.

## Host-Specific Troubleshooting

- [Claude Code setup](CLAUDE-PLUGIN-SETTING.md)
- [Codex setup](CODEX-PLUGIN-SETTING.md)
- [Uninstall](UNINSTALL.md)

## Agent Install Prompt

```text
Install AsUsual from the HSRyuuu/harness-as-usual marketplace for Claude Code and Codex.
Use plugin id as-usual@harness-as-usual.
Do not also register a local clone unless I explicitly choose the local development flow.
Verify both plugin lists, then tell me to start new sessions.
```
