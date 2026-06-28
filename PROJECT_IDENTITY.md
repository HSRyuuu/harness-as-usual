# AsUsual Project Identity

AsUsual은 단순한 바이브코딩 보조 도구가 아니다. AsUsual은 24시간 열려 있는 실제 프로덕션 웹사이트에 배포할 수 있는 수준의 작업을, 사용자가 통제 가능한 방식으로 agent와 함께 진행하기 위한 개발 하네스다.

처음에는 개인 작업 방식을 보존하기 위해 만든 하네스지만, 목표는 특정 개인이나 특정 기술 스택에 갇히지 않는다. AsUsual은 언어 중립 runtime workflow를 지향한다. 어떤 기술 스택이든 사용자가 중요하게 여기는 요구사항, 승인, 위험, 검증, 리뷰 흐름을 파일로 남기고 재개할 수 있어야 한다.

## Identity Statement

AsUsual exists to keep AI-assisted development from becoming uncontrolled implementation.

AsUsual should help an agent:

- stop before guessing unclear requirements,
- preserve user decisions as durable topic artifacts,
- expose likely DB/API and external behavior impact before implementation,
- require explicit approval before dangerous operations,
- record verification evidence instead of relying on optimistic summaries,
- review actual changes before finalizing a topic.

The harness is successful when the user can understand what was decided, why it was decided, what changed, what was verified, what risk remains, and what action is still waiting.

## Primary Failure Modes To Prevent

AsUsual prioritizes preventing these failures, in this order.

1. Requirements misunderstanding
   - The agent must not silently convert unclear intent into implementation.
   - Broad ambiguity should go through file-backed `define-requirements` questions.
   - Material requirements, plan, implementation, risk, or verification decisions must be recorded.

2. Missed DB/API or behavior impact
   - The agent must identify changes that affect persistence, public API contracts, data shape, compatibility, user-visible behavior, or downstream consumers.
   - Plans should make affected surfaces, execution surfaces, task dependencies, interfaces, rollback/recovery notes, and verification commands explicit.
   - Unknown production/shared data impact should be treated conservatively until clarified.

3. Unapproved risky work
   - High-risk operations must not run because they merely appear in an approved plan.
   - The agent must ask for fresh explicit approval immediately before high-risk execution.
   - Approval, target, reversibility, and rollback or recovery notes must be recorded in `audit.jsonl` through `scripts/topic-log.py`.

## Production Meaning

In AsUsual, "production level" does not mean a fixed inventory of enterprise technologies. It means the work may affect a real service that people can use at any time.

Therefore the workflow must treat uncertainty, hidden impact, and unverified claims as real risks. A small code change can still be production-significant when it changes data, API behavior, user-visible behavior, authentication, deployment, or operational reliability.

AsUsual should keep enough friction to prevent careless changes, but not so much ceremony that ordinary safe work becomes impossible.

## Runtime Principles

- Topic artifacts are the source of truth; chat memory is supporting context.
- Non-trivial implementation requires a completed `requirements.md` and approved `plan.md`.
- Requirements questions are file-backed when the answer can materially change the work.
- `requirements.md` should read like a human-friendly requirements definition document: domain-specific rules, constraints, invariants, side effects, and acceptance criteria should be explicit enough for both a human developer and an agent to plan from it.
- Focused clarifications may happen in chat only when the answer is recorded in `audit.jsonl` through `scripts/topic-log.py`; add a durable note to `topic.md` only when the clarification changes lasting topic context.
- Plans are execution contracts, not progress ledgers.
- Plans identify execution surfaces when work changes entrypoints, external dependencies, time-based behavior, out-of-request state changes, or runtime metadata/resources.
- Execute may use inline, subagent-driven, or mixed task execution, but the main agent remains the controller for task order, evidence, review/fix loops, and completion claims.
- Execution progress and verification evidence live in canonical `audit.jsonl`; current phase and next action are derived with `scripts/topic-log.py status --json`.
- Behavior/API/domain logic, bug fixes, and refactors require TDD evidence: test target, RED before implementation, GREEN after implementation, and refactor check. Non-TDD execution is allowed only as a human-approved exception for `throwaway-prototype`, `generated-code`, or `configuration`.
- `topic.md` is agent-first, human-readable, and low-churn: it carries initial request, boundary, durable notes, and artifact orientation, not a constantly maintained snapshot.
- Execution review is mandatory before finalization.
- Simplify cleanup is optional and user-approved.
- Post-finalize git action selection is explicit; commit, push, PR, release, and deploy actions require user selection or approval.

## Non-Goals

- AsUsual is not optimized for the fastest possible first implementation.
- AsUsual is not a replacement for the user's engineering judgment.
- AsUsual is not tied to any one language, framework, architecture, or stack.
- AsUsual does not make every request use the workflow just because the plugin is installed.
- AsUsual should not hide maintainer/plugin-development rules inside target-project runtime prompts.

## Design Bias

When tradeoffs are unclear, AsUsual should prefer:

- explicit decision records over implicit assumptions,
- heavier gates over unsafe shortcuts for material ambiguity,
- current disk state over memory,
- narrow scoped plans over broad implementation drift,
- concrete verification evidence over "looks done",
- user approval over inferred consent for risky operations.

This identity should guide changes to `as-usual-rules/core-workflow.md`, public runtime skills, templates, hook output, documentation, and maintainer-only development skills.
