# Claude Plugin Setting

AsUsual uses marketplace `harness-as-usual` and plugin id `as-usual@harness-as-usual`.

## GitHub Install

Run in Claude Code:

```text
/plugin marketplace add HSRyuuu/harness-as-usual
/plugin install as-usual@harness-as-usual
```

Verify in a terminal:

```bash
claude plugin marketplace list | grep harness-as-usual
claude plugin list | grep as-usual@harness-as-usual
claude plugin details as-usual@harness-as-usual
```

Expected: the plugin details list the AsUsual skills and one `SessionStart` hook.

## Update A GitHub Install

```bash
claude plugin marketplace update harness-as-usual
claude plugin update as-usual@harness-as-usual
```

Claude Code serves installed skills from `~/.claude/plugins/cache/harness-as-usual/as-usual/<version>/`. The canonical version is `.claude-plugin/plugin.json`; publishing changes requires a version bump. The marketplace `plugins[]` entry intentionally has no duplicate version.

Start a new Claude Code session after installing or updating. Existing sessions do not reload plugin state.

## Local Development Install

Use this instead of the GitHub source when editing AsUsual locally:

```bash
export AS_USUAL_REPO="$HOME/dev/harness-as-usual"
git clone https://github.com/HSRyuuu/harness-as-usual.git "$AS_USUAL_REPO"
cd "$AS_USUAL_REPO"
jq empty .claude-plugin/plugin.json .claude-plugin/marketplace.json hooks/hooks.json
chmod +x hooks/session-start hooks/run-hook.cmd
```

Run in Claude Code, replacing the path with the absolute clone path:

```text
/plugin marketplace add /absolute/path/to/harness-as-usual
/plugin install as-usual@harness-as-usual
```

Do not keep both a GitHub source and a local-directory source registered under different marketplace names; the same hook and skills can load twice.

## Verify Hook Loading

Run the hook directly from the repository during development:

```bash
cd "$AS_USUAL_REPO"
CLAUDE_PLUGIN_ROOT="$AS_USUAL_REPO" bash hooks/run-hook.cmd session-start \
  | jq '{event: .hookSpecificOutput.hookEventName, hasUsingSkill: (.hookSpecificOutput.additionalContext | contains("using-as-usual")), hasFindCause: (.hookSpecificOutput.additionalContext | contains("find-cause")), hasNoFullCore: (.hookSpecificOutput.additionalContext | contains("## 8. Plan Rules") | not)}'
```

## Troubleshooting

### Legacy `as-usual-local` Identity Remains

```bash
claude plugin disable as-usual@as-usual-local || true
claude plugin uninstall as-usual@as-usual-local || true
claude plugin marketplace remove as-usual-local || true
```

Then install `as-usual@harness-as-usual` again.

### Plugin Details And Invoked Skill Differ

`claude plugin details` can reflect marketplace source while an invocation still uses a versioned cache snapshot. First confirm `.claude-plugin/plugin.json` was bumped and run the update commands. For local development only, the maintainer helper can re-register the directory marketplace, but a fresh session is still required:

```bash
.agents/skills/turn-on-off-as-usual/scripts/as-usual-toggle.sh reload --claude
```

### Hook Does Not Inject Harness Context

The hook intentionally injects only a one-sentence capability summary containing `using-as-usual` and `find-cause`. It does not inject the full workflow or force AsUsual onto ordinary requests.

Check that `hooks/hooks.json`, `hooks/session-start`, and `hooks/run-hook.cmd` exist in the installed version, then start a new session.

### JSON Validation Without `jq`

```bash
python3 -m json.tool "$AS_USUAL_REPO/.claude-plugin/plugin.json" >/dev/null
python3 -m json.tool "$AS_USUAL_REPO/.claude-plugin/marketplace.json" >/dev/null
python3 -m json.tool "$AS_USUAL_REPO/hooks/hooks.json" >/dev/null
```
