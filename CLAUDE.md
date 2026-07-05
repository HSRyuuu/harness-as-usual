# PROJECT KNOWLEDGE BASE

## OVERVIEW

AsUsual is an agent harness for use with both Claude Code and Codex. It provides a work-unit workflow for starting one topic inside one project, moving through file-backed requirements definition, written plan, execute, execution review, optional code cleanup, finalize, and post-finalize git action selection.

The core idea of AsUsual is to keep topic-level decision records in files so the agent does not guess the user's existing work style.

The canonical file for the current runtime contract is `as-usual-rules/core-workflow.md`.

## STRUCTURE

```text
as-usual/
├── .claude-plugin/       # Claude plugin and local marketplace manifest
├── .codex-plugin/        # Codex plugin manifest
├── .agents/plugins/      # Codex local marketplace manifest
├── .agents/skills/       # AsUsual maintainer-only project-local skills
├── as-usual-rules/       # runtime workflow rules; core-workflow.md is canonical
├── commands/             # local command experiments; not public runtime surface
├── docs/                 # Claude/Codex clone, install, and development guide
├── hooks/                # SessionStart hook config and shared hook runner
├── plugins/              # local marketplace source symlink workspace
├── templates/            # topic artifact templates
└── skills/               # stable skills only; do not commit draft/probe skills
    ├── hand-off/  # resume entrypoint for continuing an existing topic path from another session
    ├── explore-codebase/  # read-only codebase discovery util; repository facts before requirements/plan
    ├── manage-self-improvement/  # triggered at finalize; records cross-topic lessons into memory
    └── search-long-term-memory/  # read-only recall util; queries .as-usual/memory/ for past decisions
```

## RUNTIME WORKFLOW MODEL

The runtime workflow applies to only one topic in a target project. The canonical topic folder has this shape:

```text
.as-usual/
├── topic/
│   └── yyyy-MM-dd-<topic>/
│       ├── question-c1.md
│       ├── question-c2.md
│       ├── requirements.md
│       ├── plan.md
│       ├── execute/
│       │   ├── task-<N>-requirements-review.md
│       │   └── task-<N>-quality-review.md
│       ├── clean-up/
│       │   └── review-result-<type>.md
│       ├── topic.md
│       └── audit.jsonl
└── memory/
    ├── MEMORY.md           # curated cross-topic knowledge; 3000-char budget; commit target
    └── *_MEMORY.md         # optional domain-specific memory files
```

Basic cycle:

1. `define-requirements`: create `question-cN.md` files only when material ambiguity exists, validate answered files, then synthesize a single `requirements.md`. Focused clarifications during requirements writing/review may happen in chat only when recorded in `audit.jsonl` through `scripts/topic-log.py`.
2. `plan`: write a single `plan.md` based on the approved `requirements.md`. Focused clarifications that appear during plan writing or review may be asked in chat, and the answer must be recorded in `audit.jsonl` through `scripts/topic-log.py`.
3. `execute`: perform the work based on the plan using `inline`, `subagent-driven`, or `mixed` mode. The main agent stays controller for task order, audit events, verification, and completion claims. If a single user decision is needed during execution, pause implementation, ask in chat, record the answer in `audit.jsonl` through `scripts/topic-log.py`, and route back to requirements/plan when artifacts must change.
4. `review-execution`: mandatory post-execution review of actual changes and recorded evidence.
5. `cleanup-code`: optional code cleanup after review, only when the user approves.
6. `finalize`: close the topic record, trigger `manage-self-improvement` to update `.as-usual/memory/MEMORY.md` with cross-topic lessons, and ask which post-finalize git action to run.

## RUNTIME CONTRACT BOUNDARY

- `as-usual-rules/core-workflow.md` contains only AsUsual runtime usage rules.
- Rules for developing the AsUsual plugin itself, including hooks, manifests, docs, skills, install, and reload, belong in `CLAUDE.md` and `.agents/skills/dev-as-usual/SKILL.md`.
- Do not mix plugin development goals, packaging details, or install guides into `core-workflow.md`.
- Do not copy the runtime workflow prompt into target projects. Target projects contain `.as-usual/topic/...` work-unit artifacts and, once seeded, `.as-usual/memory/...` durable knowledge artifacts.
- Requests that modify the AsUsual repository are plugin development work. Do not force the `.as-usual/topic/` workflow unless the user explicitly asks to run the plugin development itself as an AsUsual topic.

## HOOK ACTIVATION MODEL

The SessionStart hook announces only the AsUsual capability and the `using-as-usual` entrypoint in one sentence. It does not inject the full core workflow, topic candidates, or memory content; when AsUsual activates, `using-as-usual` finds and reads files from disk. The fact that this hook injected context does not force every request into the workflow.

The hook output includes host-specific format branches: Claude Code (`CLAUDE_PLUGIN_ROOT` without `COPILOT_CLI`), Codex (`PLUGIN_ROOT`), Cursor (`CURSOR_PLUGIN_ROOT`, experimental), otherwise a fallback that emits both formats. Officially supported hosts are Claude Code and Codex; the Cursor branch is best-effort.

Signals that count as AsUsual work:

1. The user explicitly says `as-usual` or `AsUsual`.
2. The user mentions `.as-usual/`, question/requirements/plan/topic.md/audit.jsonl, or a specific topic artifact.
3. The user asks to resume an active topic with phrasing like "I answered", "write the requirements", "write the plan", or "continue", and there are in-progress topic artifacts and derived status under `.as-usual/topic/`.
4. The user asks for feature-development work that should use the AsUsual workflow.

Plugin development requests are classified as plugin development even when they include the signals above. Apply the runtime workflow only if the user explicitly says to run plugin development itself as an AsUsual topic.

## WHERE TO LOOK

| Task | Location | Notes |
| --- | --- | --- |
| Runtime workflow rules | `as-usual-rules/core-workflow.md` | canonical AsUsual workflow read when AsUsual activates |
| Hook context injection | `hooks/session-start`, `hooks/run-hook.cmd`, `hooks/hooks.json`, `hooks/hooks-codex.json` | injects a one-sentence capability summary and entrypoint skill |
| Artifact templates | `templates/question.md`, `templates/requirements.md`, `templates/plan.md`, `templates/topic.md`, `templates/MEMORY.md` | file shapes created under `.as-usual/topic/yyyy-MM-dd-<topic>/`; `topic.md` and `audit.jsonl` are initialized by `scripts/topic-log.py init`; `MEMORY.md` is the template for `.as-usual/memory/MEMORY.md` |
| Runtime activation skill | `skills/using-as-usual/SKILL.md` | reads core workflow and topic artifacts when AsUsual signals are detected |
| Hand-off resume skill | `skills/hand-off/SKILL.md` | routes `/as-usual:hand-off path` or cross-session topic resume requests back to the current phase owner skill |
| Requirements definition skill | `skills/define-requirements/SKILL.md` | handles question files and `requirements.md` synthesis/review |
| Self-improvement skill | `skills/manage-self-improvement/SKILL.md` | triggered at finalize; distills cross-topic lessons into `.as-usual/memory/MEMORY.md` |
| Long-term memory recall skill | `skills/search-long-term-memory/SKILL.md` | read-only recall util; queries `.as-usual/memory/` for past decisions and patterns |
| Codebase exploration skill | `skills/explore-codebase/SKILL.md` | read-only discovery util for repository-discoverable facts before requirements or plan writing |
| Plugin development guide | `.agents/skills/dev-as-usual/SKILL.md` | explains runtime usage vs plugin development boundary |
| Harness smoke verification | `.agents/skills/verify-as-usual-harness/SKILL.md` | verifies runtime workflow, hook injection, and manifest smoke tests |
| Runtime surface verification | `.agents/skills/verify-runtime-surface/SKILL.md` | verifies that maintainer guidance has not leaked into runtime-facing surface |
| Runtime workflow consistency verification | `.agents/skills/verify-runtime-workflow-consistency/SKILL.md` | verifies runtime workflow, public runtime skills, requirements/plan templates, and reviewer prompts stay aligned |
| Project identity verification | `.agents/skills/verify-project-identity/SKILL.md` | verifies durable identity and maintainer docs reflect broad workflow/artifact/verification changes |
| Aggregate verification | `.agents/skills/verify-implementation/SKILL.md` | runs registered verification skills in sequence |
| Skill registry maintenance | `.agents/skills/manage-skills/SKILL.md` | synchronizes verification skill coverage and AGENTS.md registration lists |
| Local plugin toggle guide | `.agents/skills/turn-on-off-as-usual/SKILL.md` | handles local Claude/Codex plugin on/off while developing |
| Claude install docs | `docs/CLAUDE-PLUGIN-SETTING.md`, `.claude-plugin/` | public install flow; do not include private absolute paths |
| Codex install/reload docs | `docs/CODEX-PLUGIN-SETTING.md`, `.codex-plugin/`, `.agents/plugins/` | Codex local marketplace and snapshot reload flow |

## CODE MAP

| Surface | Type | Location | Role |
| --- | --- | --- | --- |
| Core workflow | Markdown prompt | `as-usual-rules/core-workflow.md` | runtime contract the agent follows while working in a target project |
| SessionStart hook | shell + JSON | `hooks/session-start` | injects one-sentence lightweight bootstrap context for `using-as-usual` |
| Hook config | JSON | `hooks/hooks.json`, `hooks/hooks-codex.json` | runs the hook runner on Claude/Codex SessionStart |
| Topic log helper | Python | `scripts/topic-log.py` | initializes `topic.md`/`audit.jsonl`, appends audit events, and derives current status |
| Activation skill | Skill | `skills/using-as-usual/SKILL.md` | AsUsual work classification, first reads, artifact gate progress |
| Hand-off resume skill | Skill | `skills/hand-off/SKILL.md` | rehydrates an existing `.as-usual/topic/...` path and routes to the current phase owner skill |
| Requirements definition skill | Skill | `skills/define-requirements/SKILL.md` | `question-cN.md` creation/validation and `requirements.md` synthesis/review |
| Self-improvement skill | Skill | `skills/manage-self-improvement/SKILL.md` | finalize trigger; distills cross-topic lessons into `.as-usual/memory/MEMORY.md` |
| Long-term memory recall skill | Skill | `skills/search-long-term-memory/SKILL.md` | read-only recall util for `.as-usual/memory/` |
| Codebase exploration skill | Skill | `skills/explore-codebase/SKILL.md` | read-only repository surface discovery before requirements or plan writing |
| Memory template | Markdown | `templates/MEMORY.md` | baseline shape for `.as-usual/memory/MEMORY.md` in target projects |
| Maintainer development skill | Project-local Skill | `.agents/skills/dev-as-usual/SKILL.md` | classifies AsUsual repository changes as plugin development |
| Harness smoke skill | Project-local Skill | `.agents/skills/verify-as-usual-harness/SKILL.md` | harness smoke verification procedure |
| Workflow consistency skill | Project-local Skill | `.agents/skills/verify-runtime-workflow-consistency/SKILL.md` | semantic consistency checks across runtime workflow files |
| Project identity verification skill | Project-local Skill | `.agents/skills/verify-project-identity/SKILL.md` | durable project identity and maintainer docs alignment checks |
| Verification registry | Project-local Skill | `.agents/skills/verify-implementation/SKILL.md`, `.agents/skills/manage-skills/SKILL.md` | aggregate verification and verification skill registry management |
| Local admin skills | Project-local Skill | `.agents/skills/turn-on-off-as-usual/SKILL.md` | local plugin on/off |
| Templates | Markdown | `templates/*.md` | topic artifact creation baseline |
| Codex plugin | JSON | `.codex-plugin/plugin.json` | Codex plugin metadata, skills, hooks |
| Claude marketplace | JSON | `.claude-plugin/`, `.agents/plugins/` | local marketplace registration |

## CONVENTIONS

- Keep the runtime workflow in the single file `as-usual-rules/core-workflow.md`.
- The canonical topic path is `.as-usual/topic/yyyy-MM-dd-<topic>/`.
- `topics/` and the `yyyyMMdd` format are legacy designs. Do not use them for new runtime artifacts.
- `question-cN.md` and `[Answer]:` fields are for the `define-requirements` question cycle only.
- The agent stops after creating or updating a requirements question file.
- When the user says they answered, reread the question file from disk.
- In requirements/plan/execute phases, focused clarifications may be asked in chat. Record the answer in `audit.jsonl` through `scripts/topic-log.py`, and rerun the affected requirements or plan review when artifacts change.
- Broad ambiguity involving multiple decisions or a topic-boundary change should route to `define-requirements` or `start-work` instead of being compressed into one chat question.
- Before writing requirements, read the same topic's `question-cN.md` files in order.
- The requirements document is a single `requirements.md`; the plan is a single `plan.md`.
- Non-trivial implementation goes through `requirements.md` and `plan.md` gates inside the topic folder.
- `topic.md` is an agent-first, human-readable, low-churn resume document for initial request, topic boundary, durable notes, and artifact orientation. Do not maintain it as a current snapshot or task list.
- `audit.jsonl` is the canonical append-only event log. Current phase, next action, blockers, approvals, and verification are derived with `scripts/topic-log.py status --json`.
- Review verdicts use `passed | findings | blocked`, verification verdicts use `PASS | FAIL | INCONCLUSIVE`, and implementer completion uses `DONE | NEEDS_CONTEXT | BLOCKED`; subagent receipt responses return only verdict plus artifact path while detailed review files keep YAML frontmatter `verdict`.
- Task review detail paths are `execute/task-<N>-requirements-review.md` and `execute/task-<N>-quality-review.md`; cleanup review detail paths are `clean-up/review-result-<type>.md`.
- Public docs use `https://github.com/HSRyuuu/harness-as-usual.git` and `AS_USUAL_REPO`. Do not put private absolute paths such as `/Users/...` in public install docs.
- `.as-usual/memory/` holds curated cross-topic knowledge. `MEMORY.md` is limited to a 3000-character budget; additional domain-specific files use the `*_MEMORY.md` naming convention. Unlike `topic/` artifacts, `.as-usual/memory/*` is a commit target — stage it explicitly when updating.
- Do not commit draft/probe skills. Keep only stable skills in `skills/`.
- When committing, stage paths explicitly. Avoid broad `git add .`.

## ANTI-PATTERNS

- Creating project-global artifacts such as `.as-usual/state.md` or `.as-usual/audit.md` (`.as-usual/memory/` is the sole allowed exception — it is intentional, curated, and a commit target).
- Creating the removed legacy JSON state artifact for a new runtime topic or treating it as an operational source of truth.
- Creating new artifacts under legacy paths such as `.as-usual/topics/yyyyMMdd-<topic>/`.
- Forcing AsUsual workflow onto ordinary requests only because a hook injected context.
- Creating both `spec.md` and `requirements.md` for one topic.
- Quietly weakening question/requirements/plan gates for fast implementation.
- Mixing plugin development guidance into `core-workflow.md`.
- Changing repo-relative install examples into machine-specific personal paths.
- Using the default `personal` marketplace for Codex local plugin setup.
- Committing `.codegraph/`, `.as-usual/topic/`, installed plugin cache output, or local probe output. (`.as-usual/memory/` is an allowed commit target.)

## COMMANDS

```bash
# Manifest validation
jq empty .claude-plugin/plugin.json .claude-plugin/marketplace.json
jq empty .codex-plugin/plugin.json .agents/plugins/marketplace.json
jq empty hooks/hooks.json hooks/hooks-codex.json
jq '.skills,.hooks' .codex-plugin/plugin.json

# Hook smoke verification
CLAUDE_PLUGIN_ROOT="$PWD" bash hooks/run-hook.cmd session-start \
  | jq '{event: .hookSpecificOutput.hookEventName, hasUsingSkill: (.hookSpecificOutput.additionalContext | contains("using-as-usual")), isOneSentence: (.hookSpecificOutput.additionalContext | split(".") | length <= 2), hasNoRuleSource: (.hookSpecificOutput.additionalContext | contains("Harness rule source:") | not), hasNoActiveCandidates: (.hookSpecificOutput.additionalContext | contains("Active topic candidates:") | not), hasNoFullCore: (.hookSpecificOutput.additionalContext | contains("## 8. Plan Rules") | not)}'

# Check that public surface does not include draft/cache content
git ls-tree -r --name-only HEAD | rg '^(commands/|skills/as-usual-(interview|execute|test)/)' || true
git grep -n 'private absolute path' HEAD || true

# Codex plugin snapshot reload
codex plugin remove as-usual@as-usual-local --json
codex plugin add as-usual@as-usual-local --json
```

## PROJECT-LOCAL VERIFICATION SKILLS

| Skill | Purpose |
| --- | --- |
| verify-runtime-surface | Verifies that runtime-facing surfaces do not contain maintainer/plugin-development guidance. |
| verify-as-usual-harness | Verifies runtime workflow, hook injection, and plugin manifest smoke tests. |
| verify-runtime-workflow-consistency | Verifies runtime workflow, public runtime skills, requirements/plan templates, and reviewer prompts stay aligned. |
| verify-project-identity | Verifies that durable identity and maintainer docs reflect broad workflow/artifact/verification changes. |

## NOTES

- `as-usual-rules/core-workflow.md` is the only runtime workflow prompt.
- Runtime workflow skills in `skills/` are stable public plugin surface.
- Post-execute policy is: task-level verification inside `executing-plan`, mandatory `review-execution`, optional `cleanup-code`, and `finalize` asking for post-finalize git action selection.
