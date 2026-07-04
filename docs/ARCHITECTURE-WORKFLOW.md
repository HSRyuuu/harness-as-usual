# AsUsual Architecture And Full Workflow

이 문서는 AsUsual의 아키텍처, runtime full workflow, 그리고 각 단계에서 사용되는 prompt와 template 위치를 한눈에 보기 위해 정리한 문서다.

AsUsual은 Claude Code와 Codex에서 함께 쓰기 위한 agent harness다. 핵심 목표는 agent가 사용자의 기존 작업 방식을 추측해서 바로 구현하지 않도록, 하나의 작업 topic마다 질문, 결정, requirements, plan, 실행 기록, 검증 증거를 파일로 남기는 것이다. 프로젝트 정체성과 설계 원칙은 `PROJECT_IDENTITY.md`를 기준으로 한다.

## Core Architecture

AsUsual은 세 계층으로 동작한다.

| 계층 | 위치 | 역할 |
| --- | --- | --- |
| Runtime contract | `as-usual-rules/core-workflow.md` | AsUsual runtime의 canonical workflow prompt. phase routing, hard gate, artifact contract, topic/audit 규칙을 정의한다. |
| Runtime skills | `skills/` | 각 workflow 단계에서 agent가 실제로 따라야 하는 phase별 prompt. |
| Topic artifacts | target project의 `.as-usual/topic/yyyy-MM-dd-<topic>/` | topic별 source of truth. 질문, requirements, plan, low-churn topic context, audit events, review report, final report를 저장한다. |

AsUsual에서 chat memory는 보조 맥락이다. Runtime 중에는 topic artifact가 source of truth다.

```text
as-usual/
├── PROJECT_IDENTITY.md
├── as-usual-rules/
│   └── core-workflow.md
├── hooks/
│   ├── session-start
│   ├── hooks.json
│   └── hooks-codex.json
├── skills/
│   ├── using-as-usual/
│   ├── start-work/
│   ├── define-requirements/
│   ├── writing-plan/
│   ├── executing-plan/
│   ├── review-execution/
│   ├── cleanup-code/
│   ├── finalize/
│   ├── git-action/
│   ├── manage-self-improvement/   # finalize 트리거; cross-topic 교훈을 memory에 기록
│   └── search-long-term-memory/   # read-only recall util; .as-usual/memory/ 조회
├── templates/
│   ├── question.md
│   ├── requirements.md
│   ├── plan.md
│   ├── topic.md
│   ├── code-review-report.md
│   ├── report.md
│   └── MEMORY.md                  # .as-usual/memory/MEMORY.md baseline shape
└── scripts/
    └── topic-log.py
```

## Runtime Artifact Model

Target project에는 runtime prompt를 복사하지 않는다. AsUsual이 활성화되면 target project의 `.as-usual/`은 두 갈래로 나뉜다: `topic/`(작업 단위)과 `memory/`(topic을 가로지르는 지속 지식).

```text
<target-project>/
└── .as-usual/
    ├── topic/
    │   └── yyyy-MM-dd-<topic>/
    │       ├── topic.md
    │       ├── audit.jsonl
    │       ├── question-c1.md
    │       ├── question-c2.md
    │       ├── requirements.md
    │       ├── plan.md
    │       ├── code-review-report.md
    │       └── report.md
    └── memory/
        ├── MEMORY.md           # curated cross-topic 지식; 3000자 budget; 커밋 대상
        └── *_MEMORY.md         # 선택적 도메인별 memory 파일
```

| Artifact | 역할 |
| --- | --- |
| `topic.md` | initial request, topic boundary, durable notes, artifact orientation을 담는 agent-first low-churn resume document. 사람도 읽기 좋게 쓰되, current snapshot이나 progress ledger로 계속 갱신하지 않는다. |
| `audit.jsonl` | canonical append-only event log. topic created, route, answer validation, requirements/plan completion, execution, review, finalize, git action 등을 기록한다. 현재 phase, next action, blockers, approvals, verification은 여기서 파생한다. |
| `question-cN.md` | define-requirements cycle별 질문 파일. 사용자가 `[Answer]:` field에 직접 답한다. Topic/cycle/input provenance는 YAML front matter에 두고, 본문은 사용자 결정 질문에 집중한다. |
| `requirements.md` | answered question files와 initial request를 합성한 단일 requirements document. |
| `plan.md` | 승인된 requirements을 기반으로 만든 단일 execution contract. 실행 progress ledger가 아니다. Input provenance는 YAML front matter에 둔다. |
| `code-review-report.md` | execution review에서 finding이 있을 때만 생성하는 review report. Review input provenance는 YAML front matter에 둔다. |
| `report.md` | finalize 시 생성하는 user-facing handoff summary. |

`topic.md`와 `audit.jsonl`은 직접 수정하지 않고 `scripts/topic-log.py`로 갱신한다. 일반 진행 상태는 `scripts/topic-log.py status --json`으로 조회한다.

## Full Workflow

Canonical flow는 다음과 같다.

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

`direct-execute`는 clear, trivial, low-risk, reversible 작업에만 허용되는 좁은 shortcut이다. 일반적인 non-trivial implementation은 `requirements.md`와 승인된 `plan.md` gate를 지나야 한다.

종단 경로는 두 가지다.

- **Gated topic**: review-execution → (optional cleanup) → finalize → optional git-action. finalize의 최종 status는 `complete`, `follow-up-needed`, `blocked`, `cancelled` 중 하나다. 사용자가 topic 포기를 명시하면 어느 phase에서든 `finalize-topic --status cancelled --summary "<취소 사유>"`로 종료할 수 있다(cancelled는 execution/review 전제조건과 `report.md` 요구에서 면제되고, 취소 사유 summary는 필수).
- **Direct-execute topic**: phase `direct-execute-complete` + next action `none`으로 끝나는 경량 종단이다. finalize/git-action 경로에 합류하지 않으며, 이후 commit 등 git 작업은 사용자가 명시적으로 요청할 때 일반 대화로 처리한다. 어떤 경로에서도 사용자 명시 요청 없는 자동 git action은 금지된다.

## Workflow Stage Details

### 1. Hook Bootstrap

SessionStart hook은 AsUsual capability와 `using-as-usual` entrypoint를 한 문장으로만 주입한다. Full workflow prompt, active topic 후보, memory 내용은 주입하지 않는다.

hook 출력은 호스트별 형식 분기를 포함한다: Claude Code(`CLAUDE_PLUGIN_ROOT`, `COPILOT_CLI` 아님), Codex(`PLUGIN_ROOT`), Cursor(`CURSOR_PLUGIN_ROOT`, 실험적), 그 외 fallback(두 형식 동시 출력). 공식 지원 호스트는 Claude Code와 Codex이며 Cursor 분기는 best-effort다.

| 항목 | 위치 |
| --- | --- |
| Hook runner | `hooks/session-start` |
| Claude hook config | `hooks/hooks.json` |
| Codex hook config | `hooks/hooks-codex.json` |

### 2. Activation: `using-as-usual`

사용자가 `as-usual`, `.as-usual/`, topic artifact, "답변했어", "requirements 작성해", "plan 작성해", "continue" 같은 activation signal을 주면 AsUsual이 활성화된다.

`using-as-usual`은 다음을 수행한다.

- full `as-usual-rules/core-workflow.md`를 읽는다.
- AsUsual이 활성화되면 `using-as-usual`이 `.as-usual/topic/` 아래 active topic 후보를 찾는다.
- 기존 topic이면 `topic.md`를 먼저 읽고 `audit.jsonl`, derived status, 연결된 artifact를 읽는다.
- 새 topic이면 `yyyy-MM-dd-<topic>` folder를 만들고 `scripts/topic-log.py init`으로 `topic.md`와 `audit.jsonl`을 초기화한다.

Prompt 위치:

- `skills/using-as-usual/SKILL.md`
- `as-usual-rules/core-workflow.md`

### 3. Gate Routing: `start-work`

`start-work`는 AsUsual activation을 결정하지 않는다. Activation과 first reads 이후, 현재 topic을 가장 가벼운 충분한 gate로 routing한다.

| Route | 사용 조건 |
| --- | --- |
| `requirements` | material ambiguity가 있거나 durable requirements review가 필요할 때 |
| `plan` | `requirements.md`가 완료됐고 사용자가 plan 작성으로 넘어가도록 승인했을 때 |
| `execute` | 완료된 `requirements.md`, 승인된 `plan.md`가 있고 사용자가 실행을 요청했을 때 |
| `direct-execute` | 명확하고 사소하며 low-risk이고 되돌리기 쉬운 작업일 때 |

Prompt 위치:

- `skills/start-work/SKILL.md`
- `as-usual-rules/core-workflow.md`

Topic log helper:

- `scripts/topic-log.py route-start-work`

### 4. Define Requirements: `define-requirements`

초기 broad ambiguity는 chat으로만 묻지 않는다. `question-cN.md`를 만들고 사용자가 `[Answer]:` field에 직접 답하게 한다.

주요 규칙:

- 한 cycle에는 보통 1-5개 질문만 둔다.
- 질문은 requirements, plan, implementation, risk, verification을 바꿀 수 있는 decision만 묻는다.
- repository에서 agent가 직접 확인 가능한 사실은 사용자에게 묻지 않는다.
- question cycle metadata는 front matter에 두고, agent-only 작성 규칙이나 내부 notes를 question file 본문에 남기지 않는다.
- 사용자가 돌아오면 question file을 disk에서 다시 읽는다.
- answer validation이 통과하면 같은 turn에서 `requirements.md`를 작성/리뷰한다.

Prompt/template 위치:

- `skills/define-requirements/SKILL.md`
- `templates/question.md`

Topic log helper:

- `scripts/topic-log.py`

### 5. Requirements Document: `requirements.md`

`define-requirements`는 initial request, answered question files, durable topic context, audit events를 하나의 `requirements.md`로 합성한다. Requirements은 user review document이자 planning input이다.

주요 규칙:

- Requirements은 단일 `requirements.md`만 사용한다.
- `templates/requirements.md`가 section list와 order의 source of truth다.
- `Source Inputs > Initial request`는 chat memory가 아니라 `topic.md#Initial Request`와 `topic.created` audit event에서 온다.
- `Requirements Review Checks`는 markdown checkbox list로 작성한다.
- material ambiguity를 `Open Questions`에 숨기지 않는다.
- self-review 후 local reviewer prompt를 적용한다.
- review가 통과하면 `scripts/topic-log.py complete-requirements`로 기록하고, `status --json`에서 `requirements-complete`/`approve-plan`이 파생되는지 확인한 뒤 멈춘다.

Prompt/template 위치:

- `skills/define-requirements/SKILL.md`
- `skills/define-requirements/requirements-document-reviewer-prompt.md`
- `templates/requirements.md`

Topic log helper:

- `scripts/topic-log.py complete-requirements`

### 6. Writing Plan: `writing-plan`

`writing-plan`은 승인된 requirements을 실행 가능한 단일 `plan.md`로 변환한다. Plan은 execution contract이지 progress ledger가 아니다.

주요 규칙:

- Plan은 단일 `plan.md`만 사용한다.
- plan input provenance는 YAML front matter(`topic`, `requirements`, `topicFile`, `audit`, `statusCommand`, `questionFiles`)에 두고, 본문은 execution contract에 집중한다.
- Task는 `## Task N: <name>` 단위로 dependency-ordered되어야 한다.
- 새 실행 진입점, 외부 의존성, 시간 기준 동작, request/response 밖의 상태 변경, runtime metadata/resource 의존이 있으면 `Execution Surface`에 invocation, 설정/입력, test environment, 성공/실패 신호, 재실행/재시도 기준을 명시한다.
- 각 task는 files/areas, interfaces, safety, test strategy, steps, verification command와 expected result를 포함한다.
- high-risk operation은 별도 approval 필요 여부와 rollback/recovery note를 명시한다.
- self-review 후 local reviewer prompt를 적용한다.
- `Plan Review Checks`는 markdown checkbox list로 작성한다.
- review가 통과하면 `scripts/topic-log.py complete-plan`으로 기록하고, `status --json`에서 `plan-review`/`approve-execute`가 파생되는지 확인한 뒤 멈춘다.

Prompt/template 위치:

- `skills/writing-plan/SKILL.md`
- `skills/writing-plan/plan-document-reviewer-prompt.md`
- `templates/plan.md`

Topic log helper:

- `scripts/topic-log.py complete-plan`

### 7. Executing Plan: `executing-plan`

사용자가 execution을 명시적으로 승인하면 `executing-plan`이 실행된다. 이 phase의 machine-readable phase value는 `executing`이다.

주요 규칙:

- 실행 전에 `topic.md`, `audit.jsonl`, derived status, `requirements.md`, `plan.md`를 다시 읽는다.
- Plan을 비판적으로 검토한 뒤 task 순서대로 실행한다. 실행 모드는 `inline`, `subagent-driven`, `mixed` 중 plan에서 승인된 값을 따른다.
- subagent-driven task에서도 main agent가 controller로 남아 task 순서, audit event, verification, completion claim을 책임진다.
- Plan에 없는 scope를 즉흥적으로 추가하지 않는다.
- `plan.md`를 progress ledger로 수정하지 않는다.
- task progress, dispatch, task review/fix loop, verification command, result, final sweep, blocker는 `scripts/topic-log.py`로 `audit.jsonl`에 기록한다.
- `tdd` task는 test target, RED-before-implementation, GREEN-after-implementation evidence를 기록해야 한다. Non-TDD task는 `approved-tdd-exception`으로만 기록할 수 있고, category는 `throwaway-prototype`, `generated-code`, `configuration` 중 하나여야 하며 human approval source가 필요하다.
- high-risk operation은 실행 직전에 fresh user approval을 다시 받아야 한다.
- execution completion 후 같은 turn에서 `review-execution`을 호출한다.

Prompt 위치:

- `skills/executing-plan/SKILL.md`

Topic log helpers:

- `scripts/topic-log.py approve-execution`
- `scripts/topic-log.py approve-high-risk`
- `scripts/topic-log.py dispatch-task`
- `scripts/topic-log.py record-task-review`
- `scripts/topic-log.py record-task-fix`
- `scripts/topic-log.py record-task-commit`
- `scripts/topic-log.py record-sweep`
- `scripts/topic-log.py complete-task`
- `scripts/topic-log.py complete-execution`

### 8. Review Execution: `review-execution`

Execution 후 finalize 전에 mandatory review를 수행한다. 이 단계는 task-level verification을 대체하지 않고, 실제 변경 코드와 기록된 evidence를 다시 검토한다.

주요 검토 기준:

- requirements/plan alignment
- correctness and regression risk
- verification quality
- high-risk approval evidence
- secret leakage
- prompt-injection trust boundary
- code quality and production readiness

Finding이 있으면 `code-review-report.md`를 생성하거나 갱신한다. Critical finding은 fix, block, user-accepted risk 같은 disposition 없이 finalize로 갈 수 없다.

Review 완료 후 optional code cleanup을 실행할지 사용자에게 묻는다.

Prompt/template 위치:

- `skills/review-execution/SKILL.md`
- `skills/review-execution/code-reviewer-prompt.md`
- `templates/code-review-report.md`

Topic log helpers:

- `scripts/topic-log.py record-review`
- `scripts/topic-log.py skip-code-cleanup`

### 9. Optional Code Cleanup: `cleanup-code`

Code cleanup은 correctness review가 아니라 optional cleanup review다. 사용자가 승인한 경우에만 실행한다.

네 가지 cleanup review를 수행한다.

| Review | Prompt 위치 |
| --- | --- |
| Reuse existing helpers | `skills/cleanup-code/reuse-reviewer-prompt.md` |
| Simplification | `skills/cleanup-code/simplification-reviewer-prompt.md` |
| Efficiency | `skills/cleanup-code/efficiency-reviewer-prompt.md` |
| Abstraction level | `skills/cleanup-code/abstraction-reviewer-prompt.md` |

Main prompt 위치:

- `skills/cleanup-code/SKILL.md`

규칙:

- behavior-preserving cleanup만 적용한다.
- approved change surface 밖으로 확장하지 않는다.
- 파일이 바뀌면 relevant verification을 다시 실행하거나 skip reason을 기록한다.
- 완료 후 finalize로 routing한다.

### 10. Finalize: `finalize`

Review와 code cleanup decision이 기록된 뒤 topic을 닫는다. 예외로, 사용자가 topic 포기를 명시하면 어느 phase에서든 `cancelled`로 닫을 수 있다.

주요 규칙:

- topic status를 `complete`, `follow-up-needed`, `blocked`, `cancelled` 중 하나로 정한다.
- `report.md`를 생성하거나 갱신한다. (`cancelled`는 `report.md` 면제, 취소 사유 summary 필수. 작업 트리에 이 topic의 잔여 변경이 있으면 되돌릴지/유지할지 사용자에게 먼저 묻는다.)
- self-improvement pass는 `cancelled`에도 실행하며 "no candidates"가 허용된다.
- `scripts/topic-log.py finalize-topic`으로 finalization을 기록하고, `status --json`에서 `finalized`/`git-action-decision`이 파생되는지 확인한다.
- git action을 사용자에게 묻고 멈춘다.
- commit, push, PR, release, deploy를 자동으로 실행하지 않는다.

Prompt/template 위치:

- `skills/finalize/SKILL.md`
- `templates/report.md`

Topic log helper:

- `scripts/topic-log.py finalize-topic`

### 11. Git Action: `git-action`

Finalize 후 사용자가 명시적으로 고른 git action만 수행한다.

지원 action:

- `none`
- `commit`
- `commit + push`
- `commit + push + PR`

주요 규칙:

- 사용자가 고르기 전에 git action을 선택하지 않는다.
- broad `git add .`를 피하고 path를 명시적으로 stage한다.
- unrelated changes를 stage하지 않는다.
- `.as-usual/topic/` artifact는 project policy나 사용자 명시 요청이 없으면 commit하지 않는다.
- `.as-usual/memory/`는 커밋 대상이다. `manage-self-improvement`가 `MEMORY.md`를 갱신하면 git action 시 명시적으로 stage한다.
- push, PR, release, deploy는 명시 승인 없이 하지 않는다.

Prompt 위치:

- `skills/git-action/SKILL.md`

Topic log helper:

- `scripts/topic-log.py select-git-action`

## Prompt And Template Map

| 목적 | Path |
| --- | --- |
| Canonical workflow prompt | `as-usual-rules/core-workflow.md` |
| Activation and first reads | `skills/using-as-usual/SKILL.md` |
| Gate routing | `skills/start-work/SKILL.md` |
| Requirements questions | `skills/define-requirements/SKILL.md` |
| Question template | `templates/question.md` |
| Requirements definition | `skills/define-requirements/SKILL.md` |
| Requirements reviewer prompt | `skills/define-requirements/requirements-document-reviewer-prompt.md` |
| Requirements template | `templates/requirements.md` |
| Plan writing | `skills/writing-plan/SKILL.md` |
| Plan reviewer prompt | `skills/writing-plan/plan-document-reviewer-prompt.md` |
| Plan template | `templates/plan.md` |
| Plan execution | `skills/executing-plan/SKILL.md` |
| Execution review | `skills/review-execution/SKILL.md` |
| Code reviewer prompt | `skills/review-execution/code-reviewer-prompt.md` |
| Code review report template | `templates/code-review-report.md` |
| Code cleanup | `skills/cleanup-code/SKILL.md` |
| Reuse reviewer prompt | `skills/cleanup-code/reuse-reviewer-prompt.md` |
| Simplification reviewer prompt | `skills/cleanup-code/simplification-reviewer-prompt.md` |
| Efficiency reviewer prompt | `skills/cleanup-code/efficiency-reviewer-prompt.md` |
| Abstraction reviewer prompt | `skills/cleanup-code/abstraction-reviewer-prompt.md` |
| Finalize | `skills/finalize/SKILL.md` |
| Final report template | `templates/report.md` |
| Git action | `skills/git-action/SKILL.md` |
| Self-improvement (finalize trigger) | `skills/manage-self-improvement/SKILL.md` |
| Long-term memory recall | `skills/search-long-term-memory/SKILL.md` |
| Memory template | `templates/MEMORY.md` |
| Topic context template | `templates/topic.md` |
| Topic/audit helper | `scripts/topic-log.py` |

## Key Design Boundaries

- `core-workflow.md`에는 runtime usage rule만 둔다.
- Plugin development guide와 install guide는 runtime prompt에 섞지 않는다.
- Target project에는 prompt를 복사하지 않고 `.as-usual/topic/...` artifact만 만든다.
- Non-trivial implementation은 `requirements.md`와 approved `plan.md`를 거친다.
- Execution 후에는 mandatory `review-execution`을 거친다.
- `cleanup-code`은 optional이며 사용자 승인 후에만 실행한다.
- `finalize`는 post-finalize git action 선택을 묻는 데서 멈춘다.
- Git action은 finalized topic에서 사용자가 명시적으로 선택한 action만 수행한다.
