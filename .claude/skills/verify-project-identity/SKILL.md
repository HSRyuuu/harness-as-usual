---
name: verify-project-identity
description: Verifies that durable AsUsual project identity and maintainer documents reflect workflow, artifact, and verification changes. Use after broad runtime, skill, template, hook, or documentation changes.
---

# Verify Project Identity

## Purpose

Verify that broad AsUsual changes are reflected in the durable project documents that future agents and maintainers rely on.

1. Confirm `PROJECT_IDENTITY.md` still states the enduring product intent and runtime principles.
2. Confirm `AGENTS.md`, `CLAUDE.md`, `README.md`, and `docs/ARCHITECTURE-WORKFLOW.md` describe the same current workflow, artifacts, and boundaries.
3. Confirm project-local verification skill registries include the checks needed for the changed surface.
4. Confirm stale workflow vocabulary from older designs does not re-enter active guidance.
5. Confirm maintainer-only and runtime-facing documentation boundaries remain clear.

## When To Run

- After changing `PROJECT_IDENTITY.md`, `AGENTS.md`, `CLAUDE.md`, `README.md`, or `docs/ARCHITECTURE-WORKFLOW.md`
- After changing `as-usual-rules/core-workflow.md`, public runtime `skills/**`, `templates/**`, `scripts/topic-log.py`, or `hooks/session-start`
- After creating, deleting, renaming, or substantially changing verification skills under `.agents/skills/**`
- After terminology or artifact-model changes such as question/spec/requirements/plan/topic/audit naming
- Before finishing a broad workflow refactor that should be understandable to future maintainer agents

## Related Files

| File | Purpose |
| --- | --- |
| `PROJECT_IDENTITY.md` | Source of long-lived AsUsual identity, failure modes, and runtime principles |
| `AGENTS.md` | Codex-facing project knowledge base and maintainer instructions |
| `CLAUDE.md` | Claude-facing project knowledge base and maintainer instructions |
| `README.md` | Public project overview and workflow summary |
| `docs/ARCHITECTURE-WORKFLOW.md` | Detailed architecture and workflow map |
| `as-usual-rules/core-workflow.md` | Canonical runtime workflow contract |
| `skills/using-as-usual/SKILL.md` | Public runtime activation skill |
| `skills/hand-off/SKILL.md` | Public runtime hand-off resume skill |
| `skills/start-work/SKILL.md` | Public runtime routing skill |
| `skills/define-requirements/SKILL.md` | Public runtime requirements definition skill |
| `skills/writing-plan/SKILL.md` | Public runtime planning skill |
| `skills/executing-plan/SKILL.md` | Public runtime execution skill |
| `skills/review-execution/SKILL.md` | Public runtime execution review skill |
| `skills/cleanup-code/SKILL.md` | Public runtime optional cleanup skill |
| `skills/finalize/SKILL.md` | Public runtime finalization skill |
| `skills/git-action/SKILL.md` | Public runtime post-finalize git action skill |
| `skills/manage-self-improvement/SKILL.md` | Public runtime self-improvement skill triggered during finalize |
| `skills/search-long-term-memory/SKILL.md` | Public runtime long-term memory recall utility |
| `templates/question.md` | Runtime question artifact template |
| `templates/requirements.md` | Runtime requirements artifact template |
| `templates/plan.md` | Runtime plan artifact template |
| `templates/topic.md` | Runtime topic resume artifact template |
| `templates/MEMORY.md` | Runtime long-term memory baseline template |
| `.agents/skills/manage-skills/SKILL.md` | Registered verification skill list |
| `.agents/skills/verify-implementation/SKILL.md` | Aggregate verification skill list |
| `.agents/skills/verify-project-identity/SKILL.md` | This verification skill |

## Always-Maintained File List

These files are the durable project identity surface. When broad workflow, artifact, terminology, verification, hook, or public plugin behavior changes, review this list first and update any affected files.

| Category | Files |
| --- | --- |
| Identity anchor | `PROJECT_IDENTITY.md` |
| Maintainer knowledge bases | `AGENTS.md`, `CLAUDE.md` |
| Public overview and architecture | `README.md`, `docs/ARCHITECTURE-WORKFLOW.md` |
| Runtime contract | `as-usual-rules/core-workflow.md` |
| Public runtime skills | `skills/using-as-usual/SKILL.md`, `skills/hand-off/SKILL.md`, `skills/start-work/SKILL.md`, `skills/define-requirements/SKILL.md`, `skills/writing-plan/SKILL.md`, `skills/executing-plan/SKILL.md`, `skills/review-execution/SKILL.md`, `skills/cleanup-code/SKILL.md`, `skills/finalize/SKILL.md`, `skills/git-action/SKILL.md`, `skills/manage-self-improvement/SKILL.md`, `skills/search-long-term-memory/SKILL.md` |
| Runtime templates | `templates/question.md`, `templates/requirements.md`, `templates/plan.md`, `templates/topic.md`, `templates/MEMORY.md` |
| Verification registries | `.agents/skills/manage-skills/SKILL.md`, `.agents/skills/verify-implementation/SKILL.md` |
| This skill and mirror | `.agents/skills/verify-project-identity/SKILL.md`, `.claude/skills/verify-project-identity/SKILL.md` |

If you discover another living document that future agents or maintainers would rely on for project identity, workflow, artifacts, or verification expectations:

1. Add it to `Related Files` if it should be actively checked by this skill.
2. Add it to `Always-Maintained File List` if it must stay updated across broad changes.
3. Update the relevant workflow checks below so the new file is actually verified.
4. Sync the mirror with `rsync -a --delete .agents/skills/ .claude/skills/`.

## Optional Mode: Missing Durable Docs Discovery

Use this mode when asked whether any documents are missing from this skill, or after a broad documentation/workflow refactor where the maintained surface may have expanded.

Run:

```bash
find . \
  -path './.git' -prune -o \
  -path './references' -prune -o \
  -path './docs/test' -prune -o \
  -path './.as-usual' -prune -o \
  -type f \( -name 'AGENTS.md' -o -name 'CLAUDE.md' -o -name 'README.md' -o -name '*.md' \) \
  -print | sort
```

Then inspect candidate living docs with:

```bash
rg -n 'AsUsual|runtime|workflow|identity|requirements|question|plan|state\.json|audit\.jsonl|hook|manifest|plugin|verification|skill|install|architecture|maintainer' \
  AGENTS.md CLAUDE.md README.md PROJECT_IDENTITY.md docs as-usual-rules skills .agents/skills .claude/skills templates
```

PASS:

- Every living document that defines current project identity, runtime behavior, artifact names, maintainer rules, or verification expectations is included in `Related Files` or explicitly classified as out of scope.
- Historical/reference/test-result documents are excluded only when they are clearly not active guidance.

FAIL:

- A living document contains current project identity, workflow, artifact, or verification guidance but is absent from this skill's file lists.
- A new verification or maintainer document exists but this skill does not mention or check it.

Fix:

- Update `Related Files`, `Always-Maintained File List`, and any affected workflow checks in this skill before reporting PASS.
- If the new document is a project-local skill, sync `.agents/skills` to `.claude/skills`.

## Workflow

### Step 1: Required Durable Documents Exist

**Tools:** Bash

Run:

```bash
for f in \
  PROJECT_IDENTITY.md \
  AGENTS.md \
  CLAUDE.md \
  README.md \
  docs/ARCHITECTURE-WORKFLOW.md \
  as-usual-rules/core-workflow.md \
  .agents/skills/manage-skills/SKILL.md \
  .agents/skills/verify-implementation/SKILL.md
do
  test -s "$f" || echo "MISSING_OR_EMPTY: $f"
done
```

PASS:

- No `MISSING_OR_EMPTY` lines.

FAIL:

- A required durable identity, architecture, or verification registry document is missing or empty.

Fix:

- Restore or update the missing document before claiming the project identity is represented.

### Step 2: Changed Surface Requires Durable Documentation Review

**Tools:** Bash, Read

Run:

```bash
git diff HEAD --name-only | rg '^(PROJECT_IDENTITY\.md|AGENTS\.md|CLAUDE\.md|README\.md|docs/ARCHITECTURE-WORKFLOW\.md|as-usual-rules/|skills/|templates/|scripts/topic-log\.py|hooks/session-start|\.agents/skills/|\.claude/skills/|\.codex-plugin/|\.claude-plugin/|\.agents/plugins/)'
```

PASS:

- If runtime contract, public skills, templates, topic-log helper, hooks, plugin metadata, or verification skills changed, at least one durable project document was reviewed or updated when the change affects project identity, workflow, artifact model, activation model, or verification coverage.
- If no durable doc needed updating, the final report explicitly explains why the change was local and did not affect long-lived project guidance.

FAIL:

- A workflow/artifact/verification concept changed but none of `PROJECT_IDENTITY.md`, `AGENTS.md`, `CLAUDE.md`, `README.md`, or `docs/ARCHITECTURE-WORKFLOW.md` was reviewed or updated.
- A verification skill was created/renamed/deleted but `AGENTS.md`, `.agents/skills/manage-skills/SKILL.md`, or `.agents/skills/verify-implementation/SKILL.md` was not reviewed.
- A newly discovered living document should be continuously maintained but this skill's `Related Files` and `Always-Maintained File List` were not updated.

Fix:

- Update the durable document that future agents will read first, then rerun this check.
- If a new durable document belongs to the maintained surface, update this skill's file lists in the same change.

### Step 3: Current Runtime Vocabulary Check

**Tools:** Bash, Read

Run:

```bash
rg -n -g '!**/verify-project-identity/SKILL.md' \
  'user-interview|writing-spec|questions-cN|questions\.md|spec-complete|write-spec|complete-spec|specWritten|specCompleted|userInterview|User interview|interview question|interview cycle|Background|commit decision' \
  PROJECT_IDENTITY.md \
  AGENTS.md \
  CLAUDE.md \
  README.md \
  docs/ARCHITECTURE-WORKFLOW.md \
  as-usual-rules/core-workflow.md \
  skills \
  templates \
  .agents/skills \
  .claude/skills
```

PASS:

- No stale active-guidance terms remain.
- `spec.md` may appear only as an explicit anti-pattern or guard that says not to create a separate spec artifact for a new topic.
- Historical reference, archived test, or generated evidence documents are not part of this check unless the current task explicitly edits them as living docs.

FAIL:

- Active instructions still describe the old `user-interview -> writing-spec -> spec.md` workflow.
- Active instructions require removed files such as `templates/questions.md`, `templates/spec.md`, or `questions-cN.md`.
- Active instructions call the finalization prompt a commit decision instead of a post-finalize git action selection.
- Active requirements rules mention a template section such as `Background` that does not exist in `templates/requirements.md`.

Fix:

- Update active guidance to the current workflow vocabulary and artifact names.

### Step 4: Identity Principles Coverage Check

**Tools:** Bash, Read

Run:

```bash
rg -n 'uncontrolled implementation|Requirements misunderstanding|DB/API|High-risk|requirements\.md|plan\.md|topic\.md|audit\.jsonl|topic-log\.py|inline|subagent-driven|mixed|controller|TDD|approved exception|throwaway-prototype|generated-code|configuration|Execution review|post-finalize|git action|human-friendly requirements|domain-specific rules' PROJECT_IDENTITY.md
```

PASS:

- `PROJECT_IDENTITY.md` covers:
  - preventing uncontrolled implementation,
  - requirements misunderstanding,
  - DB/API or behavior impact,
  - high-risk approval,
  - `requirements.md` and `plan.md` gates,
  - `topic.md`, `audit.jsonl`, and `topic-log.py status --json`,
  - inline/subagent-driven/mixed execution with the main agent as controller,
  - mandatory TDD evidence and human-approved exception categories for non-TDD tasks,
  - mandatory execution review,
  - post-finalize git action selection,
  - the human-readable/domain-specific role of `requirements.md`.

FAIL:

- A broad workflow change removes or contradicts one of the project identity principles.
- `PROJECT_IDENTITY.md` no longer explains why the harness exists or what failure modes it prevents.

Fix:

- Update `PROJECT_IDENTITY.md` first, then align `AGENTS.md`, `CLAUDE.md`, README, architecture docs, and runtime skills to that identity.

### Step 5: Durable Document Alignment Check

**Tools:** Bash, Read

Run:

```bash
rg -n 'hand-off|define-requirements|question-cN\.md|requirements\.md|plan\.md|review-execution|cleanup-code|finalize|git-action|post-finalize|\.as-usual/memory|memory/MEMORY\.md|manage-self-improvement|search-long-term-memory|memory commit exception' \
  AGENTS.md \
  CLAUDE.md \
  README.md \
  docs/ARCHITECTURE-WORKFLOW.md \
  as-usual-rules/core-workflow.md
```

PASS:

- Durable documents agree on the current topic artifact model: `question-cN.md`, `requirements.md`, `plan.md`, `topic.md`, `audit.jsonl`, and derived status through `scripts/topic-log.py`.
- Durable documents agree that `define-requirements` owns file-backed questions plus requirements writing/review.
- Durable documents agree that non-trivial implementation requires completed requirements and an approved plan.
- Durable documents agree that execution review is mandatory, code cleanup is optional/user-approved, and git actions happen only after finalization and explicit user selection.
- When the artifact model or self-improvement surface changes, durable documents agree that `.as-usual/` has both `topic/` and `memory/` branches; `manage-self-improvement` and `search-long-term-memory` are the self-improvement and recall skills; and `.as-usual/memory/*` is the memory commit exception while topic artifacts remain excluded by default.

FAIL:

- One durable document describes a different phase sequence, artifact name, or ownership boundary than another.
- A public overview promises behavior that the runtime workflow does not implement.
- `AGENTS.md` and `CLAUDE.md` drift in ways that would make Codex and Claude maintainers follow different project rules.

Fix:

- Pick `PROJECT_IDENTITY.md` for enduring intent and `as-usual-rules/core-workflow.md` for runtime contract, then update every durable doc to match those two anchors.

### Step 6: Verification Registry Coverage Check

**Tools:** Bash, Read

Run:

```bash
rg -n 'verify-project-identity|verify-runtime-surface|verify-as-usual-harness|verify-runtime-workflow-consistency' \
  AGENTS.md \
  CLAUDE.md \
  .agents/skills/manage-skills/SKILL.md \
  .agents/skills/verify-implementation/SKILL.md
```

PASS:

- The registered verification skills table in `manage-skills` includes `verify-project-identity`.
- The aggregate target skill table in `verify-implementation` includes `verify-project-identity`.
- `AGENTS.md` and `CLAUDE.md` list or point to the project identity verification skill where project-local verification skills are documented.
- `.agents/skills/**` and `.claude/skills/**` remain synchronized after registry edits.

FAIL:

- A new verification skill exists but is absent from `manage-skills`, `verify-implementation`, `AGENTS.md`, or `CLAUDE.md`.
- `.agents/skills` and `.claude/skills` disagree after project-local skill edits.

Fix:

- Update the registries and run `rsync -a --delete .agents/skills/ .claude/skills/`.

### Step 7: Maintainer/Runtime Boundary Check

**Tools:** Bash, Read

Run:

```bash
rg -n 'dev-as-usual|plugin development|install guide|reload|marketplace|AGENTS\.md' \
  as-usual-rules/core-workflow.md \
  skills \
  templates \
  hooks/session-start
```

PASS:

- Runtime-facing files do not instruct target-project users to follow maintainer-only plugin development rules.
- Maintainer-only project guidance stays in `AGENTS.md`, `CLAUDE.md`, `.agents/skills/**`, `.claude/skills/**`, and development docs.

FAIL:

- `core-workflow.md`, public runtime skills, templates, or hook payloads contain maintainer-only install/reload/plugin development instructions.

Fix:

- Move maintainer-only guidance to project-local documents or skills.

## Output Format

```markdown
## verify-project-identity Report

| Check | Status | Evidence |
| --- | --- | --- |
| Required documents | PASS/FAIL | ... |
| Durable doc review coverage | PASS/FAIL | ... |
| Runtime vocabulary | PASS/FAIL | ... |
| Identity principles | PASS/FAIL | ... |
| Durable doc alignment | PASS/FAIL | ... |
| Verification registry | PASS/FAIL | ... |
| Maintainer/runtime boundary | PASS/FAIL | ... |
| Missing durable docs discovery | PASS/FAIL/N/A | ... |

### Findings

| File | Line | Problem | Fix |
| --- | --- | --- | --- |
| `path/to/file` | 12 | Durable doc still describes old workflow | Align with `PROJECT_IDENTITY.md` and `core-workflow.md` |
```

## Exceptions

1. Historical evidence under `docs/test/**` and archived handoff notes may contain old terminology when clearly historical.
2. `spec.md` may appear in active guidance only as an anti-pattern guard that forbids creating a separate spec artifact for new runtime topics.
3. Public install docs may mention plugin install/reload commands when explaining setup; those commands must not become runtime workflow instructions.
4. A tiny local fix may not require `PROJECT_IDENTITY.md` or architecture docs to change, but the verification report should state why the durable docs were reviewed and left unchanged.
5. Verification skills may include stale terms inside grep patterns that explicitly detect removed vocabulary; those detection commands should exclude their own skill file to avoid self-matches.
6. Install guides and generated reports do not automatically become always-maintained identity docs; include them only when they define current workflow, artifact, maintainer, or verification expectations.
