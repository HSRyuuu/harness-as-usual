# Codex Plugin Setting

AsUsual uses marketplace `harness-as-usual` and plugin id `as-usual@harness-as-usual`.

## GitHub Install

```bash
codex plugin marketplace add HSRyuuu/harness-as-usual
codex plugin add as-usual@harness-as-usual
```

Verify:

```bash
codex plugin marketplace list | grep harness-as-usual
codex plugin list | grep as-usual@harness-as-usual
grep -E 'harness-as-usual|as-usual@harness-as-usual' ~/.codex/config.toml
```

## Update A GitHub Install

```bash
codex plugin marketplace upgrade harness-as-usual
```

Codex serves the installed snapshot from `~/.codex/plugins/cache/harness-as-usual/as-usual/<version>/`. The canonical version is `.codex-plugin/plugin.json`; publishing changes requires bumping it in lockstep with `.claude-plugin/plugin.json`. The marketplace `plugins[]` entry intentionally has no duplicate version.

Start a new Codex session after installing or updating. Existing sessions do not reload plugin state.

## Local Development Install

Use this instead of the GitHub source when editing AsUsual locally:

```bash
export AS_USUAL_REPO="$HOME/dev/harness-as-usual"
git clone https://github.com/HSRyuuu/harness-as-usual.git "$AS_USUAL_REPO"
cd "$AS_USUAL_REPO"

jq empty .agents/plugins/marketplace.json .codex-plugin/plugin.json hooks/hooks-codex.json
test "$(readlink plugins/as-usual)" = ".."
chmod +x hooks/session-start hooks/run-hook.cmd

codex plugin marketplace add "$AS_USUAL_REPO" --json
codex plugin add as-usual@harness-as-usual --json
```

The repository tracks `plugins/as-usual -> ..` because Codex resolves `.agents/plugins/marketplace.json` plugin sources as marketplace subpaths. A fresh clone already has the link.

Do not keep both a GitHub source and a local-directory source registered under different marketplace names; the same hook and skills can load twice.

## Reload A Local Development Snapshot

Codex runs the installed cache snapshot rather than the live repository tree. After local source changes, use:

```bash
.agents/skills/turn-on-off-as-usual/scripts/as-usual-toggle.sh reload --codex
```

The helper validates the repository marketplace, removes only `as-usual@harness-as-usual`, prunes only `~/.codex/plugins/cache/harness-as-usual/as-usual`, and re-adds the plugin. Start a new session afterward.

## Verify Hook Loading

Resolve the currently installed version instead of hardcoding it:

```bash
PLUGIN_ROOT="$(find "$HOME/.codex/plugins/cache/harness-as-usual/as-usual" -mindepth 1 -maxdepth 1 -type d | sort | tail -n 1)"
test -n "$PLUGIN_ROOT"
jq '.name,.version,.hooks' "$PLUGIN_ROOT/.codex-plugin/plugin.json"
PLUGIN_ROOT="$PLUGIN_ROOT" bash "$PLUGIN_ROOT/hooks/run-hook.cmd" session-start \
  | jq '{event: .hookSpecificOutput.hookEventName, hasUsingSkill: (.hookSpecificOutput.additionalContext | contains("using-as-usual")), hasFindCause: (.hookSpecificOutput.additionalContext | contains("find-cause")), hasNoFullCore: (.hookSpecificOutput.additionalContext | contains("## 8. Plan Rules") | not)}'
```

## Troubleshooting

### Legacy `as-usual-local` Identity Remains

```bash
codex plugin remove as-usual@as-usual-local --json || true
codex plugin marketplace remove as-usual-local || true
```

Then install `as-usual@harness-as-usual` again.

### Plugin Is Listed But Not Installed

Both config entries are required:

```text
[marketplaces.harness-as-usual]
[plugins."as-usual@harness-as-usual"]
```

If the marketplace exists but the plugin is not installed:

```bash
codex plugin add as-usual@harness-as-usual --json
```

### Local Changes Do Not Appear

Run the local reload helper above and start a new session. If a GitHub-installed update does not appear, confirm both plugin manifests were bumped and run `codex plugin marketplace upgrade harness-as-usual`.

### Hook Trust Prompt Appears

Approve only after confirming the hook command points inside the installed AsUsual repository or cache. Bypass hook trust only for controlled non-interactive smoke tests, never as a normal default.

### JSON Validation Without `jq`

```bash
python3 -m json.tool "$AS_USUAL_REPO/.agents/plugins/marketplace.json" >/dev/null
python3 -m json.tool "$AS_USUAL_REPO/.codex-plugin/plugin.json" >/dev/null
python3 -m json.tool "$AS_USUAL_REPO/hooks/hooks-codex.json" >/dev/null
```
