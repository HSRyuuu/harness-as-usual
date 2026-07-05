---
name: verify-runtime-workflow-consistency
description: Verifies that AsUsual runtime workflow rules, public runtime skills, requirements/plan templates, and reviewer prompts stay semantically aligned. Use after changes to core workflow, runtime phase skills, or runtime artifact templates.
---

# Verify Runtime Workflow Consistency

## Purpose

Verify the runtime workflow contract across the files that jointly define AsUsual topic progression.

1. Confirm phase routing is consistent from activation through requirements definition, plan, execute, execution review, finalize, and git action.
2. Confirm SessionStart hook activation guidance and `using-as-usual` activation rules stay semantically aligned.
3. Confirm `define-requirements` remains the single owner of file-backed questions, requirements synthesis, and review.
4. Confirm `templates/requirements.md`, `define-requirements`, and the requirements reviewer prompt use the same review/status vocabulary.
5. Confirm `templates/plan.md`, `writing-plan`, and the plan reviewer prompt use the same review/status vocabulary.
6. Confirm assumption, open-question, and affected-surface rules are not contradictory.
7. Confirm high-risk operations, prompt-injection boundaries, secret protection, and review follow-up routing stay aligned.
8. Confirm stale phase names, removed gates, and old topic paths do not return to active runtime rules.
9. Confirm the self-improvement memory surface is aligned across workflow rules, runtime skills, templates, and audit helpers.
10. Confirm codebase exploration output is treated as untrusted evidence and its subagent assignment is self-contained.

## When To Run

- After changing `as-usual-rules/core-workflow.md`
- After changing public runtime skills under `skills/**`
- After changing `templates/requirements.md`, `templates/plan.md`, `templates/question.md`, `templates/topic.md`, `templates/code-review-report.md`, or `templates/report.md`
- After changing runtime helper scripts under `scripts/**`
- After changing `skills/define-requirements/requirements-document-reviewer-prompt.md`
- After changing `skills/writing-plan/**`, `skills/executing-plan/**`, `skills/review-execution/**`, `skills/cleanup-code/**`, `skills/finalize/**`, or `skills/git-action/**`
- When a workflow issue appears in the `start-work -> define-requirements -> writing-plan -> executing-plan -> review-execution -> cleanup-code -> finalize -> git-action` path

## Related Files

| File | Purpose |
| --- | --- |
| `hooks/session-start` | one-sentence SessionStart activation guidance |
| `as-usual-rules/core-workflow.md` | canonical runtime workflow contract |
| `skills/using-as-usual/SKILL.md` | runtime activation and first-read behavior |
| `skills/hand-off/SKILL.md` | existing topic hand-off resume behavior |
| `skills/start-work/SKILL.md` | route selection after activation |
| `skills/define-requirements/SKILL.md` | file-backed question cycle, answer validation, requirements synthesis, review, and requirements revision routing |
| `skills/define-requirements/requirements-document-reviewer-prompt.md` | local requirements reviewer criteria and output shape |
| `skills/writing-plan/SKILL.md` | plan synthesis, dependency analysis, review, and plan revision routing |
| `skills/writing-plan/plan-document-reviewer-prompt.md` | local plan reviewer criteria and output shape |
| `skills/executing-plan/SKILL.md` | inline/subagent-driven/mixed plan execution and progress/review/verification recording |
| `skills/review-execution/SKILL.md` | mandatory post-execution review and optional code cleanup decision |
| `skills/review-execution/code-reviewer-prompt.md` | execution reviewer prompt template |
| `skills/cleanup-code/SKILL.md` | optional code cleanup skill |
| `skills/cleanup-code/reuse-reviewer-prompt.md` | reuse cleanup reviewer prompt |
| `skills/cleanup-code/simplification-reviewer-prompt.md` | simplification cleanup reviewer prompt |
| `skills/cleanup-code/efficiency-reviewer-prompt.md` | efficiency cleanup reviewer prompt |
| `skills/cleanup-code/abstraction-reviewer-prompt.md` | abstraction cleanup reviewer prompt |
| `skills/finalize/SKILL.md` | topic finalization and git action decision prompt |
| `skills/git-action/SKILL.md` | selected post-finalize git action handling |
| `skills/manage-self-improvement/SKILL.md` | finalize-triggered self-improvement proposal/application skill |
| `skills/search-long-term-memory/SKILL.md` | read-only long-term memory recall utility |
| `skills/explore-codebase/SKILL.md` | read-only codebase exploration utility |
| `templates/question.md` | question artifact shape |
| `templates/requirements.md` | canonical requirements artifact shape |
| `templates/plan.md` | canonical plan artifact shape |
| `templates/topic.md` | low-churn topic resume artifact shape |
| `templates/code-review-report.md` | conditional code review findings report shape |
| `templates/report.md` | final topic handoff report shape |
| `templates/MEMORY.md` | baseline shape for `.as-usual/memory/MEMORY.md` |
| `scripts/topic-log.py init` | creates `topic.md`, creates the topic `audit.jsonl` stream, and records the initial request |
| `scripts/topic-log.py` | helper script referenced by runtime skills for routine topic/audit updates and derived status |

## Workflow

### Step 1: Required Runtime Files Exist

**Tool:** Bash

Run:

```bash
for f in \
  as-usual-rules/core-workflow.md \
  skills/using-as-usual/SKILL.md \
  skills/hand-off/SKILL.md \
  skills/start-work/SKILL.md \
  skills/define-requirements/SKILL.md \
  skills/define-requirements/requirements-document-reviewer-prompt.md \
  skills/writing-plan/SKILL.md \
  skills/writing-plan/plan-document-reviewer-prompt.md \
  skills/executing-plan/SKILL.md \
  skills/review-execution/SKILL.md \
  skills/review-execution/code-reviewer-prompt.md \
  skills/cleanup-code/SKILL.md \
  skills/cleanup-code/reuse-reviewer-prompt.md \
  skills/cleanup-code/simplification-reviewer-prompt.md \
  skills/cleanup-code/efficiency-reviewer-prompt.md \
  skills/cleanup-code/abstraction-reviewer-prompt.md \
  skills/finalize/SKILL.md \
  skills/git-action/SKILL.md \
  skills/manage-self-improvement/SKILL.md \
  skills/search-long-term-memory/SKILL.md \
  skills/explore-codebase/SKILL.md \
  templates/question.md \
  templates/requirements.md \
  templates/plan.md \
  templates/topic.md \
  templates/code-review-report.md \
  templates/report.md \
  templates/MEMORY.md \
  scripts/topic-log.py
do
  test -s "$f" || echo "MISSING_OR_EMPTY: $f"
done
removed_state_template="templates/state"".json"
test ! -e "$removed_state_template" || echo "REMOVED_FILE_PRESENT: $removed_state_template"
python3 scripts/topic-log.py --help >/dev/null || echo "HELP_FAILED: scripts/topic-log.py"
```

PASS: no `MISSING_OR_EMPTY` lines.
PASS: no `REMOVED_FILE_PRESENT` line and `topic-log.py --help` exits 0.

FAIL: any required runtime workflow file is missing or empty.
FAIL: the removed state template exists for the new runtime model, or `topic-log.py --help` fails.

Fix: restore the missing runtime file or update this skill only if the runtime contract intentionally moved.

### Step 2: Route And Skill Ownership Check

**Tools:** Read, Bash

Run:

```bash
rg -n 'hand-off|using-as-usual|start-work|define-requirements|writing-plan|executing-plan|review-execution|cleanup-code|finalize|git-action|direct-execute|requirements-complete|approve-plan|plan-review|approve-execute|execution-complete|decide-code-cleanup|git-action-decision' \
  as-usual-rules/core-workflow.md \
  skills/using-as-usual/SKILL.md \
  skills/hand-off/SKILL.md \
  skills/start-work/SKILL.md \
  skills/define-requirements/SKILL.md \
  skills/writing-plan/SKILL.md \
  skills/executing-plan/SKILL.md \
  skills/review-execution/SKILL.md \
  skills/review-execution/code-reviewer-prompt.md \
  skills/cleanup-code/SKILL.md \
  skills/cleanup-code/reuse-reviewer-prompt.md \
  skills/cleanup-code/simplification-reviewer-prompt.md \
  skills/cleanup-code/efficiency-reviewer-prompt.md \
  skills/cleanup-code/abstraction-reviewer-prompt.md \
  skills/finalize/SKILL.md \
  skills/git-action/SKILL.md
```

PASS:

- `using-as-usual` owns activation, first reads, and topic initialization.
- `hand-off` owns explicit hand-off resume from an existing topic path and routes to the existing phase owner without adding a workflow phase.
- `start-work` owns routing after first reads.
- `define-requirements` owns question creation, answer validation, and material ambiguity.
- `define-requirements` owns requirements writing, local review, `requirements-complete`, and asking for plan approval.
- `writing-plan` owns dependency analysis, plan writing, local plan review, `plan-review`, and asking for execution approval (`approve-execute`).
- `executing-plan` owns inline execution and progress/verification recording, then routes successful completion to `review-execution`.
- `review-execution` owns mandatory post-execution review and the optional code cleanup decision.
- `cleanup-code` owns approved cleanup reviews, behavior-preserving cleanup, and re-verification after cleanup changes.
- `finalize` owns topic closure and asking for the git action decision.
- `git-action` owns the selected post-finalize git action.
- No file says `define-requirements` writes `plan.md`, and no file says `writing-plan` executes work.
- Answer validation passes directly into `define-requirements` without an extra approval gate.

FAIL:

- Two skills claim the same phase owner in incompatible ways.
- A skill skips required handoff to another owner.
- Any runtime rule says `define-requirements` writes `plan.md`, `writing-plan` executes work, or `executing-plan` authors the plan.
- Any runtime rule allows `executing-plan` to bypass `review-execution` after successful execution completion.
- Any runtime rule runs code cleanup automatically without user approval.
- Any runtime rule calls a host `/simplify` command instead of the public `cleanup-code` skill.
- Any runtime rule runs a git action before `finalize` asks for a git action decision.
- Any runtime rule adds a user approval gate between validated answers and requirements synthesis.
- A next action that means approval to execute uses stale `execute-plan` wording instead of `approve-execute`.

Fix: keep phase ownership in `core-workflow.md` and mirror the same boundary in the responsible skill.

### Step 2a: Hook And Activation Alignment Check

**Tools:** Read, Bash

Run:

```bash
rg -n 'AsUsual is available|using-as-usual|explicit AsUsual work|topic/artifact resumes|feature-development work that should use the AsUsual workflow|otherwise handle the request normally|The user asks for feature-development work that should use the AsUsual workflow|Read the full `as-usual-rules/core-workflow.md`' \
  hooks/session-start \
  skills/using-as-usual/SKILL.md \
  AGENTS.md \
  CLAUDE.md \
  docs/ARCHITECTURE-WORKFLOW.md
```

PASS:

- `hooks/session-start` injects one concise activation sentence that points to `using-as-usual`.
- The hook sentence and `skills/using-as-usual/SKILL.md` agree on activation categories: explicit AsUsual work, topic/artifact references or resumes, and feature-development work that should use the AsUsual workflow.
- `skills/using-as-usual/SKILL.md` owns rule and topic discovery when the hook no longer announces the core workflow path or active topic candidates.
- Durable maintainer docs describe the same hook/activation boundary without reintroducing full workflow injection.

FAIL:

- The hook mentions an activation category that `using-as-usual` does not recognize.
- `using-as-usual` requires the hook to announce a core workflow path or active topic candidates before it can perform first reads.
- Durable docs still say the hook injects the full rule path, active topic candidates, memory content, or detailed workflow sections.

Fix: align `hooks/session-start`, `skills/using-as-usual/SKILL.md`, and durable docs so the hook remains a one-sentence entrypoint and `using-as-usual` owns file-backed discovery.

### Step 3: Requirements Template And Reviewer Vocabulary Check

**Tools:** Read, Bash

Run:

```bash
rg -n 'Status:|Reviewer Result:|Requirements Review Checks|Requirements Review Findings|Requirements Review Actions Taken|requirements-complete|issues-fixed|not-run|blocked' \
  templates/requirements.md \
  skills/define-requirements/SKILL.md \
  skills/define-requirements/requirements-document-reviewer-prompt.md \
  as-usual-rules/core-workflow.md
```

PASS:

- `templates/requirements.md` contains `Status: draft | requirements-complete | blocked`.
- `templates/requirements.md` contains `Reviewer Result: not-run | passed | issues-fixed | blocked`.
- `define-requirements` and the reviewer prompt write into the existing `Review Status` area rather than creating a separate review block.
- `passed` or `issues-fixed` maps to `Status: requirements-complete`; unresolved findings map to `Status: blocked`.

FAIL:

- Any file uses a stale requirements status vocabulary such as `pending-user-review`, `Passed`, or `Issues Fixed` as the canonical `requirements.md` template value.
- Reviewer instructions tell the agent to create a separate `## Requirements Review` block.
- `define-requirements` and the reviewer prompt disagree on result values.

Fix: make `templates/requirements.md` the vocabulary source of truth and update `define-requirements` plus the reviewer prompt to match it.

### Step 4: Clarification, Assumptions, And Open Questions Check

**Tools:** Read, Bash

Run:

```bash
rg -n 'Assumptions|Open Questions|Affected Surface|material ambiguity|chat clarification|focused chat|3-cycle|assumption-based|None identified|unlabeled assumption' \
  as-usual-rules/core-workflow.md \
  skills/define-requirements/SKILL.md \
  skills/writing-plan/SKILL.md \
  skills/executing-plan/SKILL.md \
  skills/review-execution/SKILL.md \
  skills/define-requirements/requirements-document-reviewer-prompt.md \
  skills/writing-plan/plan-document-reviewer-prompt.md \
  templates/requirements.md
```

PASS:

- Initial or broad material ambiguity routes through `define-requirements` unless the explicit 3-cycle escalation allows an assumption-based draft.
- Focused clarifications discovered during requirements, plan, or execute may be asked in chat only when the decision can be resolved in the current turn.
- Chat clarification answers are recorded in `audit.jsonl` through `scripts/topic-log.py` before affected artifacts are updated or execution continues; durable topic context is added to `topic.md` only when needed.
- Broad multi-question decision cycles and topic-boundary changes route to `define-requirements` or `start-work`, not a single chat answer.
- Assumptions are allowed only in `Assumptions` with source and risk.
- `Open Questions` is limited to non-blocking confirmations or `None`.
- `Affected Surface` is required when knowable, or explicitly none with a reason.
- Optional empty content uses explicit none rules instead of invented requirements, risks, assumptions, or files.

FAIL:

- Material ambiguity can be hidden in `Open Questions`.
- A runtime file says requirements/plan/execute must always return to `define-requirements` for a single focused clarification.
- A runtime file allows chat clarification without recording the answer in `audit.jsonl` through `scripts/topic-log.py`.
- Unlabeled assumptions are allowed.
- Any file says to invent non-functional requirements, risks, assumptions, or affected files to fill the template.
- The template contains placeholder examples that completed requirements are allowed to keep.

Fix: align all requirements-authoring rules with `define-requirements` and the reviewer prompt.

### Step 5: Safety Gate And Review Follow-Up Check

**Tools:** Read, Bash

Run:

```bash
rg -n 'High-Risk Operation Gate|high-risk operation|file deletion|bulk formatting|package installation|dependency changes|DB migration|schema changes|environment variable|\\.env|secret|credential|CI/CD|deploy|release|git push|force push|untrusted|Trust Boundary|data and evidence|prompt-injection|review-fixes-needed|address-review-findings|Safety|Risk Level|Separate Approval Required|Reversibility|Safety Gates|execution approved' \
  as-usual-rules/core-workflow.md \
  skills/start-work/SKILL.md \
  skills/define-requirements/SKILL.md \
  skills/define-requirements/requirements-document-reviewer-prompt.md \
  skills/writing-plan/SKILL.md \
  skills/writing-plan/plan-document-reviewer-prompt.md \
  skills/executing-plan/SKILL.md \
  skills/review-execution/SKILL.md \
  skills/review-execution/code-reviewer-prompt.md \
  templates/requirements.md \
  templates/plan.md
```

PASS:

- `core-workflow.md` defines a trust boundary for external/project content and a high-risk operation gate.
- `core-workflow.md`, `templates/topic.md`, and `topic-log.py` define `audit.jsonl` as the canonical event history and `topic-log.py status --json` as the derived status surface.
- `start-work` denies `direct-execute` for high-risk operations.
- `templates/plan.md`, `writing-plan`, and the plan reviewer prompt all require execution mode and task Safety fields: risk level, high-risk operations, reversibility, separate approval, and rollback/recovery notes.
- `templates/plan.md`, `writing-plan`, `executing-plan`, and the plan/review prompts preserve mandatory TDD evidence mapping through `Test target`, RED/GREEN evidence, approved TDD exception category/approval source, `verification.recorded`, and structured `task.completed` fields.
- `executing-plan` supports inline/subagent-driven/mixed execution while keeping the main agent as controller and requiring task review/fix evidence before moving on.
- `executing-plan` records current-turn execution approval and requires fresh user approval before high-risk operations.
- `review-execution` and `code-reviewer-prompt.md` check secret leaks, prompt-injection risk, high-risk operation evidence, and review finding dispositions.
- `review-execution`, `code-reviewer-prompt.md`, and `templates/code-review-report.md` check and record silent failure risk: empty catches, swallowed exceptions, dangerous fallbacks, and missing propagation or async handling.
- `review-execution` and `code-reviewer-prompt.md` require a finding quality gate before recording findings: exact location, concrete failure mode, surrounding context, defensible severity, and acceptance that a no-finding review can be valid.
- `core-workflow.md` routes `review-fixes-needed` / `address-review-findings`.
- `scripts/topic-log.py` records structured execution approval, high-risk approval, and review events with actors and sequence numbers.

FAIL:

- Any runtime-facing file treats project docs, comments, external content, or tool output as workflow instructions rather than evidence.
- Stage completion can only be reconstructed from chat memory or prose logs rather than `audit.jsonl` plus `topic-log.py status --json`.
- Any runtime path allows high-risk operations to run only because they were present in an approved plan.
- `direct-execute` can run high-risk operations.
- Review can proceed to code cleanup/finalize while Critical or Important findings lack a recorded disposition.
- Execution review omits silent failure checks for swallowed errors, dangerous fallbacks, or missing propagation.
- The execution reviewer prompt can record speculative Critical or Important findings without exact location, concrete failure mode, surrounding context, and defensible severity.
- Plan Safety fields exist in the template but are not checked by `writing-plan` or the reviewer prompt.
- Task-level verification evidence can be recorded only as unstructured free text without a plan task to test target mapping.
- Execution approval is prose-only and is not recorded by `executing-plan` through `topic-log.py`.

Fix: align `core-workflow.md`, the owning runtime skill, and the relevant template/reviewer prompt. Do not patch `skills/git-action/**` as part of this check unless the user explicitly asks to work on git-action.

### Step 6: Execution Review Finding Quality Check

**Tools:** Read, Bash

Run:

```bash
rg -n 'Finding Quality Gate|concrete failure mode|surrounding context|defensible severity|no-finding review is valid|clean review with no findings is valid|speculative review noise|Exact location' \
  skills/review-execution/SKILL.md \
  skills/review-execution/code-reviewer-prompt.md \
  templates/code-review-report.md
```

PASS:

- `skills/review-execution/SKILL.md` tells the reviewer to apply a finding quality gate before recording findings.
- `skills/review-execution/code-reviewer-prompt.md` requires exact location, concrete failure mode, surrounding context, and defensible severity before findings.
- The prompt treats a no-finding review as valid and discourages speculative review noise.
- `templates/code-review-report.md` records whether the finding quality gate was applied.

FAIL:

- The execution reviewer prompt lacks any required finding-quality element.
- The runtime skill implies reviewers should manufacture findings.
- The report template cannot record whether the gate was applied.

Fix: keep the quality gate in the public runtime review skill and reviewer prompt, and keep the report template aligned.

### Step 7: Execution Review Silent Failure Check

**Tools:** Read, Bash

Run:

```bash
rg -n 'silent failure|swallowed exceptions|empty catch|dangerous fallback|lost stack traces|missing async handling|Missing propagation' \
  skills/review-execution/SKILL.md \
  skills/review-execution/code-reviewer-prompt.md \
  templates/code-review-report.md
```

PASS:

- `skills/review-execution/SKILL.md` includes silent failure risk in mandatory execution review.
- `skills/review-execution/code-reviewer-prompt.md` asks the reviewer to hunt swallowed errors, dangerous fallbacks, and missing failure propagation.
- `templates/code-review-report.md` has a place to record silent failure assessment.

FAIL:

- Silent failures can pass review without being considered.
- Review output has no field for silent failure assessment.

Fix: keep silent failure checks inside the public execution review path.

### Step: Structured Approval And Review Evidence Check

Run:

```bash
rg -n 'approve-execution|approve-high-risk|dispatch-task|record-task-review|record-task-fix|record-task-commit|record-sweep|record-review|approval.execution|approval.high_risk|task.dispatched|task.review_completed|task.fix_completed|task.commit_recorded|sweep.completed|review.completed|seq|actor' \
  scripts/topic-log.py \
  skills/executing-plan/SKILL.md \
  skills/review-execution/SKILL.md \
  skills/finalize/SKILL.md
```

PASS:

- `topic-log.py` exposes `approve-execution`, `approve-high-risk`, `dispatch-task`, `record-task-review`, `record-task-fix`, `record-task-commit`, `record-sweep`, and `record-review`.
- `topic-log.py` emits structured `approval.execution`, `approval.high_risk`, `task.dispatched`, `task.review_completed`, `task.fix_requested`, `task.fix_completed`, `task.commit_recorded`, `sweep.completed`, and `review.completed` events.
- runtime skills instruct agents to use structured commands rather than free-text-only state updates.
- audit actor guidance uses host values such as `codex` and `claude`.

FAIL:

- high-risk approval can be recorded only in progress text.
- execution review mode is not machine-readable.
- runtime instructions allow generic `agent` actor for host audit events.

### Step 8: Self-Improvement And Memory Surface Check

Run:

```bash
rg -n 'manage-self-improvement|search-long-term-memory|memory\.candidate|memory\.recorded|skill\.created|skill\.candidate|record-memory-candidate|record-memory|record-skill --state created|record-skill --state candidate|3000|recalled memory|UNTRUSTED RECALLED CONTEXT|\.as-usual/memory|MEMORY\.md' \
  as-usual-rules/core-workflow.md \
  skills/using-as-usual/SKILL.md \
  skills/define-requirements/SKILL.md \
  skills/writing-plan/SKILL.md \
  skills/executing-plan/SKILL.md \
  skills/finalize/SKILL.md \
  skills/manage-self-improvement/SKILL.md \
  skills/manage-self-improvement/references/memory-update.md \
  skills/manage-self-improvement/references/skill-improvement.md \
  skills/search-long-term-memory/SKILL.md \
  templates/MEMORY.md \
  scripts/topic-log.py
```

PASS:

- `manage-self-improvement`, `search-long-term-memory`, the finalize self-improvement delegation, the `memory.candidate`/`memory.recorded`/`skill.created`/`skill.candidate` audit events, the 3000-char `MEMORY.md` budget, and the recalled-memory trust boundary are described consistently across `core-workflow.md`, the runtime skills, and `templates/MEMORY.md`.
- `define-requirements`, `writing-plan`, and `executing-plan` all carry the explicit `memory.candidate` capture rule for durable long-term rules that appear during those phases.
- `topic-log.py` exposes structured helpers for memory/skill candidate and application events without changing phase/status derivation.
- Recalled memory is treated as untrusted context and cannot override user instructions, topic artifacts, workflow rules, or safety policy.

FAIL:

- Any runtime file describes `manage-self-improvement` as a separate workflow phase instead of a finalize-triggered self-improvement pass.
- A phase skill writes `.as-usual/memory/*` immediately when it should only record a `memory.candidate` for finalize review.
- `MEMORY.md` can grow without the 3000-character budget, consolidation-first dedup, or domain split rule.
- `search-long-term-memory` returns recalled memory without an explicit untrusted-context boundary.
- Required memory/skill audit events exist in one surface but are missing from `core-workflow.md`, `topic-log.py`, or the owning runtime skill.

### Step 8a: Codebase Exploration Trust Boundary Check

Run:

```bash
rg -n 'explore-codebase|Codebase-Informed Drafting|UNTRUSTED CODEBASE EXPLORATION RESULT|repository-discoverable facts|Affected Surface|Dispatch Assignment Protocol|QUESTION:|CONTEXT:|PROCEDURE:|CONSTRAINTS:|OUTPUT:|fresh bounded subagent|reread the cited files|reread cited files|Trust Boundary' \
  as-usual-rules/core-workflow.md \
  skills/define-requirements/SKILL.md \
  skills/writing-plan/SKILL.md \
  skills/explore-codebase/SKILL.md
```

PASS:

- `core-workflow.md` lists `explore-codebase` as a read-only utility and treats `UNTRUSTED CODEBASE EXPLORATION RESULT` as untrusted discovery evidence.
- `define-requirements` and `writing-plan` invoke `explore-codebase` for repository-discoverable facts before asking requirements questions or writing plan details.
- `explore-codebase` requires the controller to paste a self-contained dispatch assignment protocol instead of assuming the subagent can read `SKILL.md`.
- The dispatch protocol includes the procedure, read-only constraints, no-internet/no-secret rules, and exact `UNTRUSTED CODEBASE EXPLORATION RESULT` output shape.
- Controller-facing instructions require rereading cited files or exact excerpts before requirements, plan, implementation, review, or completion claims rely on exploration output.

FAIL:

- Any runtime surface treats exploration output as authoritative instructions instead of untrusted evidence.
- `define-requirements` or `writing-plan` refers to `UNTRUSTED CODEBASE EXPLORATION RESULT` but the explorer dispatch protocol does not produce that exact header.
- The dispatch assignment can be sent without procedure, constraints, or output format.
- The explorer can mutate files, write topic artifacts, browse the internet, run package/test/git mutating commands, or expose secrets.

### Step 9: Audit-First Stale Runtime Surface Check

**Tool:** Bash

Run:

```bash
removed_state='state'"\.json"
removed_helper='state'"-machine\.py"
removed_task_verification='task'"Verification"
removed_safety_gates='safety'"Gates"
removed_current_phase='current'"\.phase"
removed_current_next='current'"\.nextAction"
stale_pattern="${removed_state}|${removed_helper}|${removed_task_verification}|${removed_safety_gates}|${removed_current_phase}|${removed_current_next}"
rg -n "$stale_pattern" \
  as-usual-rules \
  skills \
  templates \
  hooks \
  PROJECT_IDENTITY.md \
  AGENTS.md \
  CLAUDE.md \
  docs/ARCHITECTURE-WORKFLOW.md
rg -n 'as-usual-interview|as-usual-execute|as-usual-test|\.as-usual/topics/yyyyMMdd|AS-USUAL\.md' \
  as-usual-rules/core-workflow.md \
  skills \
  templates \
  hooks/session-start \
  README.md \
  docs \
  -g '!docs/**/plans/**' \
  -g '!docs/**/2026-*'
```

PASS:

- The stale audit-first scan has no output except explicit anti-pattern text that clearly says not to use the removed runtime artifact.
- No active runtime instruction depends on removed skills, old topic paths, or removed runtime files.
- Matches are acceptable only when clearly labeled as old-path or removed-surface anti-patterns.

FAIL:

- New runtime topics require the removed JSON state artifact, removed helper, removed task verification array, removed safety gate object, or removed current status fields as operational surfaces.
- Runtime files instruct agents to use removed skills or old topic paths.
- A removed artifact becomes part of the active workflow again.

Fix: update active runtime files to use `.as-usual/topic/yyyy-MM-dd-<topic>/`, `topic.md`, `audit.jsonl`, `scripts/topic-log.py`, and the current public runtime skills.

## Output Format

```markdown
## verify-runtime-workflow-consistency Report

| Check | Status | Evidence |
| --- | --- | --- |
| Required files | PASS/FAIL | ... |
| Route ownership | PASS/FAIL | ... |
| Hook/activation alignment | PASS/FAIL | ... |
| Requirements review vocabulary | PASS/FAIL | ... |
| Ambiguity and assumptions | PASS/FAIL | ... |
| Safety gates and review follow-up | PASS/FAIL | ... |
| Structured approval/review evidence | PASS/FAIL | ... |
| Self-improvement and memory surface | PASS/FAIL | ... |
| Codebase exploration trust boundary | PASS/FAIL | ... |
| Removed runtime surface | PASS/FAIL | ... |

### Findings

| File | Line | Problem | Fix |
| --- | --- | --- | --- |
| `path/to/file` | 12 | Inconsistent workflow rule | Align with the owning skill/template |
```

## Exceptions

1. `AGENTS.md` and `.agents/skills/**` may discuss maintainer workflow boundaries that are not runtime-facing.
3. Public docs may mention old paths or removed surfaces only as explicit anti-patterns or troubleshooting notes.
4. `templates/requirements.md` may include a single example trace only when `define-requirements` and the reviewer prompt require completed requirements to replace it.
5. Historical handoff docs under `docs/**` may contain implementation commands that search for old paths or removed surfaces.
