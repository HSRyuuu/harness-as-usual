# Uninstall

Remove the AsUsual plugin and marketplace from Claude Code and Codex.

- Plugin id: `as-usual@harness-as-usual`
- Marketplace name: `harness-as-usual`

## Claude Code

```bash
claude plugin disable as-usual@harness-as-usual
claude plugin uninstall as-usual@harness-as-usual
claude plugin marketplace remove harness-as-usual
```

## Codex

```bash
codex plugin remove as-usual@harness-as-usual --json
codex plugin marketplace remove harness-as-usual
```

Optionally remove only the AsUsual cache snapshots:

```bash
rm -rf "$HOME/.claude/plugins/cache/harness-as-usual/as-usual"
rm -rf "$HOME/.codex/plugins/cache/harness-as-usual/as-usual"
```

Do not delete either host's entire plugin cache tree.

## Remove A Legacy Local Install

Older releases used `as-usual@as-usual-local`:

```bash
claude plugin disable as-usual@as-usual-local || true
claude plugin uninstall as-usual@as-usual-local || true
claude plugin marketplace remove as-usual-local || true

codex plugin remove as-usual@as-usual-local --json || true
codex plugin marketplace remove as-usual-local || true
```

## Verify Removal

```bash
claude plugin list             | grep as-usual || echo "claude: removed"
claude plugin marketplace list | grep harness-as-usual || echo "claude marketplace: removed"
codex plugin list              | grep as-usual || echo "codex: removed"
grep -E 'harness-as-usual|as-usual@harness-as-usual' "$HOME/.codex/config.toml" || echo "codex config: clean"
```

Already-running sessions keep their loaded skills and hook context. Start new sessions to fully drop AsUsual.
