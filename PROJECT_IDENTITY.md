# AsUsual Project Identity

AsUsual은 단순한 바이브코딩 보조 도구가 아니다. AsUsual은 24시간 열려 있는 실제 프로덕션 웹사이트에 배포할 수 있는 수준의 작업을, 사용자가 통제 가능한 방식으로 agent와 함께 진행하기 위한 개발 하네스다.

처음에는 개인 작업 방식을 보존하기 위해 만든 하네스지만, 목표는 특정 개인이나 특정 기술 스택에 갇히지 않는다. AsUsual은 언어 중립 runtime workflow를 지향한다. 요청은 진입 시점에 세 작업 단위 중 하나로 분류된다: 요구사항 합의가 필요한 `topic`, 무엇을 할지 이미 정해진 `direct-work`, 코드를 고치지 않고 원인이나 방향을 확정하는 `issue`. 어떤 기술 스택이든 사용자가 중요하게 여기는 요구사항, 조사 근거, 승인, 위험, 검증, 리뷰 흐름을 파일로 남기고 재개할 수 있어야 한다.

## Identity Statement

AsUsual exists to keep AI-assisted development from becoming uncontrolled implementation.

AsUsual should help an agent:

- stop before guessing unclear requirements,
- preserve user decisions and investigation evidence as durable work-unit artifacts,
- expose likely DB/API and external behavior impact before implementation,
- require explicit approval before dangerous operations,
- record verification evidence instead of relying on optimistic summaries,
- review actual changes rather than the summary of them.

The harness is successful when the user can understand what was decided, why it was decided, what changed, what was verified, what risk remains, and what action is still waiting.

## Primary Failure Modes To Prevent

AsUsual prioritizes preventing these failures, in this order.

1. Requirements misunderstanding
   - The agent must not silently convert unclear intent into implementation.
   - Ambiguity should go through `gathering-context`, with every material answer recorded in `contexts.md` before anything is built on it.
   - Material requirements, plan, implementation, risk, or verification decisions must be recorded.

2. Missed DB/API or behavior impact
   - The agent must identify changes that affect persistence, public API contracts, data shape, compatibility, user-visible behavior, or downstream consumers.
   - Plans should make affected surfaces, execution surfaces, task dependencies, interfaces, rollback/recovery notes, and verification commands explicit.
   - Unknown production/shared data impact should be treated conservatively until clarified.

3. Unapproved risky work
   - High-risk operations must not run because they merely appear in an approved plan.
   - The agent must ask for fresh explicit approval immediately before high-risk execution.
   - Approval, target, reversibility, and rollback or recovery notes must be recorded in `audit.jsonl` through `scripts/as-usual-record.py`.

## Production Meaning

In AsUsual, "production level" does not mean a fixed inventory of enterprise technologies. It means the work may affect a real service that people can use at any time.

Therefore the workflow must treat uncertainty, hidden impact, and unverified claims as real risks. A small code change can still be production-significant when it changes data, API behavior, user-visible behavior, authentication, deployment, or operational reliability.

AsUsual should keep enough friction to prevent careless changes, but not so much ceremony that ordinary safe work becomes impossible.

AsUsual is tuned for frontier models, which draws a deliberate line. The record layer — script-managed audit history, fresh approval for high-risk operations, completion backed by evidence, a critical plan review before execution approval, explicit git-action selection, and the trust boundary — is non-negotiable regardless of model strength, because it governs permission and durable records, not agent capability. The judgment layer — whether a post-execution review is worth running, how work is tested, whether tasks are delegated, how deep verification goes, and how much document structure a piece of work needs — gives a capable model discretion instead of forcing process. Adapting AsUsual for weaker models means tightening the judgment layer back up; it never means loosening the record layer.

## Runtime Principles

- Work-unit artifacts are the source of truth; chat memory is supporting context. Every unit keeps `contexts.md` (the agreed decisions) and `audit.jsonl` (the append-only evidence trail).
- The unit is decided before any work folder exists, and it is the user's choice: the agent classifies and recommends, but presents the options and follows what the user picks — including the option to use no harness at all.
- An `issue` never modifies production code. Implementation starts as a separately linked work unit after the cause or solution direction is confirmed with evidence.
- Gated implementation — work that is ambiguous, risky, or hard to reverse — requires a completed `requirements.md` and approved `plan.md`. Size alone does not gate; ambiguity and risk do.
- `direct-work` is for clear, low-risk, reversible work, gated on ambiguity and risk rather than size. It skips the requirements agreement, not the record: it still keeps `contexts.md` and `audit.jsonl`, and it still needs a plan review before execution approval.
- Material decisions are clarified with the user and recorded before they are built on. Questions are asked in chat and their answers written down by the agent — the user is never made to open a file and fill in a field. Every agreed decision lands in one document, `contexts.md`, whenever in the work it was made.
- `requirements.md` should read like a human-friendly requirements definition document: domain-specific rules, constraints, invariants, side effects, and acceptance criteria should be explicit enough for both a human developer and an agent to plan from it.
- `contexts.md` is live: when a later decision reverses an earlier one, the earlier entry is edited so the document always reads as the current agreement. Nothing is lost — `audit.jsonl` is append-only and keeps the history.
- Plans are execution contracts, not progress ledgers.
- Plans identify execution surfaces when work changes entrypoints, external dependencies, time-based behavior, out-of-request state changes, or runtime metadata/resources.
- Execute may use inline, subagent-driven, or mixed task execution, but the main agent remains the controller for task order, evidence, review/fix loops, and completion claims.
- Execution progress and verification evidence live in `audit.jsonl`; current phase and next action are derived with `scripts/as-usual-record.py status --json`, never remembered.
- Completion needs verification evidence that matches the surface — a command with its real output, an actual request and response, a screenshot or a recorded manual check. Tests alone never prove done, and an unverifiable result is `INCONCLUSIVE`, which is not `PASS`. How work is tested is the agent's judgment; that it is evidenced is not.
- A plan is critically reviewed and improved before the user is asked to approve execution, so what they approve has already been checked.
- Post-execution review of the actual diff is proposed by default for gated work and offered otherwise; when it runs, its Critical and Important findings reach a recorded disposition before the work closes.
- Code cleanup is optional and user-approved.
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

This identity should guide changes to `as-usual-rules/core-rules.md`, `as-usual-rules/safety-rules.md`, public runtime skills, templates, hook output, documentation, and maintainer-only development skills.
