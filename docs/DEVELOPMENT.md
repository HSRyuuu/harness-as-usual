# Development

Maintainer-facing reference for working on the AsUsual plugin itself. For the
runtime workflow and project identity, see [`../README.md`](../README.md) and
[`../PROJECT_IDENTITY.md`](../PROJECT_IDENTITY.md).

## Project Layout

```text
as-usual/
├── as-usual-rules/core-workflow.md   # canonical runtime workflow (read on disk)
├── .agents/                          # Codex marketplace + maintainer-only skills
├── .claude-plugin/                   # Claude plugin + marketplace manifest
├── .codex-plugin/                    # Codex plugin manifest
├── hooks/                            # SessionStart hook + shared runner
├── skills/                           # stable public runtime skills
├── docs/                             # install + architecture guides
└── templates/                        # topic artifact templates
```

## Smoke Test

```bash
claude plugin details as-usual@harness-as-usual
codex plugin list | grep -E 'as-usual|harness-as-usual'
CLAUDE_PLUGIN_ROOT="$PWD" hooks/run-hook.cmd session-start | jq .
```

See also [`../CLAUDE.md`](../CLAUDE.md), [`../AGENTS.md`](../AGENTS.md), and
[`ARCHITECTURE-WORKFLOW.md`](ARCHITECTURE-WORKFLOW.md).
