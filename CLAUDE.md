# CLAUDE.md

@AGENTS.md

The project knowledge base above is host-agnostic. Everything below is what is
true only when the host is Claude Code.

## CLAUDE-SPECIFIC SURFACES

| Surface | Location | Codex counterpart |
| --- | --- | --- |
| Plugin manifest | `.claude-plugin/plugin.json` | `.codex-plugin/plugin.json` |
| Marketplace manifest | `.claude-plugin/marketplace.json` | `.agents/plugins/marketplace.json` |
| Hook config | `hooks/hooks.json` | `hooks/hooks-codex.json` |
| Maintainer skills | `.claude/skills/**` (mirror) | `.agents/skills/**` (source) |
| Install doc | `docs/CLAUDE-PLUGIN-SETTING.md` | `docs/CODEX-PLUGIN-SETTING.md` |

`.agents/skills/**` is the source of truth. After changing it, mirror to
`.claude/skills/**` — `skill-registry-sync` does this.

## HOOK

The SessionStart hook branches on `CLAUDE_PLUGIN_ROOT` being set without
`COPILOT_CLI`. Smoke test it from the repo:

```bash
CLAUDE_PLUGIN_ROOT="$PWD" bash hooks/run-hook.cmd session-start | jq '{
  event: .hookSpecificOutput.hookEventName,
  oneEntryPoint: (.hookSpecificOutput.additionalContext | contains("using-as-usual")),
  isOneSentence: (.hookSpecificOutput.additionalContext | split(". ") | length <= 2),
  noRulePath: (.hookSpecificOutput.additionalContext | contains("as-usual-rules/") | not)
}'
```

Claude Code expects `hookSpecificOutput.additionalContext`; Codex expects plain
stdout. `hooks/session-start` emits both shapes from one script.

## SKILL INVOCATION

Runtime skills are namespaced `as-usual:<skill>` (e.g. `as-usual:using-as-usual`).
Maintainer skills in `.claude/skills/**` are project-local and unnamespaced.

## INSTALL AND RELOAD

```bash
claude plugin marketplace update harness-as-usual
claude plugin update as-usual@harness-as-usual
.agents/skills/turn-on-off-as-usual/scripts/as-usual-toggle.sh reload
```

Installed skills are served from
`~/.claude/plugins/cache/harness-as-usual/as-usual/<version>/`; the canonical
version is `.claude-plugin/plugin.json`, and publishing changes requires a bump.
A running session never reloads plugin state — start a new session.

Do not register both a GitHub source and a local-directory source under
different marketplace names; the same hook and skills load twice.
