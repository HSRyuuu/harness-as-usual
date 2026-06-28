# AsUsual

AsUsual is an agent harness that helps an AI coding agent run one work topic inside one project in the user's usual way.

AsUsual is designed for controlled AI-assisted development on work that may eventually affect real, always-on production services. It is intentionally not a pure vibe-coding harness. See `PROJECT_IDENTITY.md` for the project identity and design principles.

## Core Idea

- Runtime workflow rules live in `as-usual-rules/core-workflow.md`.
- Do not copy the workflow rule file into target projects.
- In target projects, create only topic artifacts under `.as-usual/topic/yyyy-MM-dd-<topic>/`.
- Initial `define-requirements` questions are written to `question-cN.md`.
- The user answers those requirements questions directly in `[Answer]:` fields.
- During requirements, plan, or execute, focused clarifications may be asked in chat when the answer is recorded in `audit.jsonl` through `scripts/topic-log.py`.
- The agent rereads answered question files and proceeds to `requirements.md`, `plan.md`, and execution.

## Workflow

```text
SessionStart hook
  -> using-as-usual
  -> start-work
  -> define-requirements | writing-plan | executing-plan | direct-execute
  -> review-execution
  -> optional cleanup-code
  -> finalize
  -> optional git-action
```

For the full architecture, workflow stages, and prompt/template path map, see `docs/ARCHITECTURE-WORKFLOW.md`.

Topic folder:

```text
.as-usual/
└── topic/
    └── yyyy-MM-dd-<topic>/
        ├── topic.md
        ├── audit.jsonl
        ├── question-c1.md
        ├── question-c2.md
        ├── requirements.md
        ├── plan.md
        ├── code-review-report.md
        └── report.md
```

## Mode Boundary

`as-usual-rules/core-workflow.md` defines target-project runtime usage rules.

## Layout

```text
as-usual/
├── as-usual-rules/core-workflow.md
├── .agents/
├── .claude-plugin/
├── .codex-plugin/
├── hooks/
├── skills/
├── docs/
└── templates/
```

For local Codex marketplace development, create `plugins/as-usual -> ..` as described in `docs/CODEX-PLUGIN-SETTING.md`.

## Install Guides

- Claude Code: `docs/CLAUDE-PLUGIN-SETTING.md`
- Codex: `docs/CODEX-PLUGIN-SETTING.md`

## Smoke Test

```bash
claude plugin details as-usual@as-usual-local
codex plugin list | grep -E 'as-usual|as-usual-local'
CLAUDE_PLUGIN_ROOT="$PWD" hooks/run-hook.cmd session-start | jq .
```
