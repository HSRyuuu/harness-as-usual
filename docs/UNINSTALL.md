# Uninstall

Remove the AsUsual local plugin from Claude Code and Codex. See
[INSTALL.md](INSTALL.md) for the matching install flow.

Plugin / marketplace names:

- Plugin id: `as-usual@as-usual-local`
- Marketplace name: `as-usual-local`

## 1. Remove From Claude Code

```bash
claude plugin disable as-usual@as-usual-local
claude plugin uninstall as-usual@as-usual-local
claude plugin marketplace remove as-usual-local
```

`uninstall` removes the installed plugin; `marketplace remove` drops the
`as-usual-local` source from `~/.claude/settings.json`.

## 2. Remove From Codex

```bash
codex plugin remove as-usual@as-usual-local --json
codex plugin marketplace remove as-usual-local
```

`codex plugin remove` clears the `[plugins."as-usual@as-usual-local"]` and hook-state
entries from `~/.codex/config.toml`; `marketplace remove` clears
`[marketplaces.as-usual-local]`.

Optionally prune the cache snapshot (safe to remove; only the AsUsual entry):

```bash
rm -rf "$HOME/.codex/plugins/cache/as-usual-local/as-usual"
```

## 3. Verify Removal

```bash
claude plugin list             | grep as-usual || echo "claude: removed"
claude plugin marketplace list | grep as-usual-local || echo "claude marketplace: removed"
codex plugin list              | grep as-usual || echo "codex: removed"
grep -E 'as-usual-local|as-usual@as-usual-local' "$HOME/.codex/config.toml" || echo "codex config: clean"
```

## 4. Local Workspace Cleanup (Optional)

The `plugins/as-usual` symlink is a gitignored local workspace. Remove it if you no
longer develop the plugin from this clone.

```bash
rm -f "$AS_USUAL_REPO/plugins/as-usual"
```

## 5. Restart Sessions

Claude Code and Codex keep already-loaded plugins, skills, and hooks for the current
session. Start a new session in each host to fully drop AsUsual.
