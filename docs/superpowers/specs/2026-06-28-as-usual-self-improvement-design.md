# AsUsual Self-Improvement 설계

- 날짜: 2026-06-28
- 대상: AsUsual harness (plugin development)
- 상태: 설계 확정, 구현 계획 대기

## 1. 목적과 범위

AsUsual에 Hermes식 **장기기억(memory) + skill 개선** 자기개선 루프를 추가한다. 무거운 `docs/lessons/*_LESSONS.md` 체계는 도입하지 않는다.

분류 원칙:

- 짧은 사실, 지속 규칙, 사용자 선호, 프로젝트 판단 기준 → 장기기억(`MEMORY.md`)
- 반복 가능한 비자명 절차 → skill (승인 후 직접 생성 또는 기존 skill patch)
- 단순 topic 기록, 일회성 대화, 미검증 추측 → 저장하지 않음 (audit/topic 아티팩트가 이미 history 역할)

핵심: `manage-self-improvement`는 한 self-improvement 턴 안에서 memory와 skill 후보를 분석해 **실제로 추가할 항목**을 찾고, "이런 memory를 추가하고 xx skill을 만들겠습니다"를 사용자에게 제시한 뒤, **승인받으면 memory 기록과 skill 생성을 직접 수행**한다.

### 비범위 (이번에 하지 않음)

- AsUsual memory를 사용자의 전역 KnowledgeBase, host 네이티브 memory, agentmemory MCP와 자동 동기화/통합하지 않는다. AsUsual memory는 host-agnostic 자립 시스템으로 유지한다.
- 사용자 선호의 전역화(`~/.as-usual/`, USER.md 전역 파일)는 범위 밖. `MEMORY.md` 안의 사용자 선호 섹션 + 향후 전역화 여지 주석만 남긴다.

## 2. 폴더 / 문서 구조

`.as-usual/`를 의도적으로 두 갈래로 확장한다. 이는 현재의 "타깃 프로젝트는 `.as-usual/topic/...`만 가진다" 하드 룰을 명시적으로 갱신하는 것이다.

```text
<project-root>/.as-usual/
├── topic/yyyy-MM-dd-<topic>/    # 기존: 작업 단위 기록
└── memory/                       # 신규: topic을 가로지르는 지속 지식
    ├── MEMORY.md                 # 1차 집계 파일 (사용자 선호 섹션 포함)
    └── <domain>_MEMORY.md        # 선택적 분리 (예: BACKEND_MEMORY.md) — consolidation 실패 시에만
```

### MEMORY.md 규칙 (Hermes 차용)

- **curated + size-bounded**. append-only가 아니다.
- **저장형 = 주입형**: 저장 텍스트가 곧 프롬프트에 들어갈 압축 다이제스트 형태여야 한다.
- **budget = 3000자 고정**.
- 새 항목 반영 시 단순 append 금지. 항상 다음을 먼저 시도한다: **축약(simplify) · 병합(consolidate) · 중복 제거(dedup)**.
- 사용자 선호는 `MEMORY.md` 안의 별도 섹션에 둔다(USER.md 분리하지 않음).

### overflow / 도메인 분리 규칙 (consolidation-first)

```text
새 항목 반영 시도
  ↓
3000자 초과?
  ↓ yes
기존 항목 축약·병합·중복 제거로 최대한 줄이기
  ↓
그래도 3000자 초과?
  ↓ yes
도메인 집중 항목을 <domain>_MEMORY.md로 분리
```

- 분리는 자동 기본값이 아니라 **축약으로도 budget을 못 지킬 때의 최후 수단**이다.
- 분리 후 기록 라우팅: 새 항목이 도메인에 매칭되면 해당 `*_MEMORY.md`, 아니면 `MEMORY.md`.
- `MEMORY.md` 상단에 분리된 도메인 파일 인덱스를 한 줄씩 유지한다.

### MEMORY.md few-shot (관리 예시)

좋은 항목(압축된 지속 지식):

```text
User is a Java/Spring Boot backend developer; prefers practical, polite Korean explanations.
Project uses Java 21, Spring Boot 3.1, JPA, MyBatis, Vue3/Nuxt3, TypeScript.
When reviewing this project, check DTO naming, API response standardization, transaction boundaries, and QueryDSL N+1 risks.
User prefers review comments that include: issue, reason, risk, suggested fix, and example code.
For Kafka local dev, host apps connect to localhost:9092, containers use event-kafka:9092.
```

병합(consolidate) — before → after:

```text
# before
User uses Java.
User uses Spring Boot.
User prefers Korean polite style.

# after
User is a Java/Spring Boot backend developer and prefers polite Korean technical explanations.
```

저장하지 않는 나쁜 항목(일회성 로그):

```text
2026-06-28에 사용자가 Kafka 네트워크 설정을 물었고 localhost:9092와 event-kafka:9092 차이를 설명했다.
오늘 RoleUserId 기본 생성자 오류를 해결했다.
```

dedup: 새 항목이 기존 항목과 의미가 겹치면 새 줄을 추가하지 말고 기존 줄에 병합한다.

### commit 정책

`.as-usual/` 아티팩트는 기본적으로 커밋하지 않지만(현 [docs/ARCHITECTURE-WORKFLOW.md](../../ARCHITECTURE-WORKFLOW.md), core-workflow §12 git-action), **`.as-usual/memory/*`는 명시적 커밋 대상**이다. 프로젝트 지속 지식이므로 팀/세션 간 공유되어야 한다. 이 예외를 다음에 반영한다:

- core-workflow §12 git-action invariant("`.as-usual/` 아티팩트는 명시 없이 커밋 금지")에 memory 디렉토리 예외 명시
- `git-action` 스킬: memory 파일을 커밋 대상으로 stage 허용(단, topic 아티팩트는 기존대로 제외)
- `.gitignore`: 현재 `.as-usual/` 전체 ignore이므로 `.as-usual/*` + `!.as-usual/memory/**` 패턴으로 memory만 추적 가능하게 예외 추가
- ARCHITECTURE-WORKFLOW 문서의 commit 정책 설명 갱신

## 3. 쓰기 시점 (2단계)

### (a) 즉시 포착 — 작업 흐름을 깨지 않음

requirements/plan/execute 도중 사용자가 명시적 장기 규칙("앞으로도 X로 해줘", "이 프로젝트에선 항상 Y")을 말하면, 작업을 멈추지 않고 `scripts/topic-log.py`로 `audit.jsonl`에 `memory.candidate` 이벤트 한 줄만 기록한다. 이 시점엔 `MEMORY.md`를 건드리지 않고 승인도 받지 않는다. "즉시"는 *포착*이 즉시라는 뜻이고, *쓰기+승인*은 finalize로 모은다.

### (b) finalize 시점 일괄 분석·승인·반영

finalize가 닫기 전에 `manage-self-improvement` 스킬을 로드한 서브에이전트를 호출하여, audit 기준으로 여러 아티팩트를 읽고 자기개선 후보를 처리한다. 항상 사용자 승인 후에만 저장/생성한다.

입력으로 읽는 자료:

```text
topic.md, audit.jsonl, question-cN.md, requirements.md, plan.md,
code-review-report.md, report.md(있으면; 이 패스는 report.md 작성 전에 돌므로
최초 finalize에선 실행/리뷰 증거와 draft summary로 대체), current diff summary,
기존 .as-usual/memory/*, 기존 project-local skills
```

특히 `question-cN.md → requirements.md → plan.md → 실제 결과(diff/report)`의 차이("초기 의도 → 승인 요구사항 → 계획 → 실제 결과")에서 후보를 발견한다.

### 후보 재검증 (중요)

포착 시점(2-a)에 `memory.candidate`로 잡힌 후보가 작업이 진행되면서 **무효화·번복**될 수 있다(예: "항상 X로" 했다가 나중에 다른 방식으로 바뀜). 따라서 finalize 분석은 단순히 후보를 그대로 옮기지 않는다. `references/memory-update.md`에 **"이 후보가 최종 결과 기준으로 여전히 참이고, 다음 작업에 재사용할 가치가 있는가?"**를 판단하는 프롬프트를 둔다. 무효·중복·저가치 후보는 드롭하고 그 사유를 기록한다.

## 4. 실행 모델: finalize 내 서브에이전트 (독립 phase 아님)

자기개선은 audit 기준으로 여러 문서를 읽는 read-heavy 분석 패스이며, finalize의 "기록 닫고 git action 묻기"와 성격이 다르다. 따라서 **새 workflow phase로 만들지 않고**, finalize 내부에서 서브에이전트로 수행한다. phase router/state machine과 `topic-log.py` 상태 도출은 변경하지 않는다.

### 경계: 서브에이전트와 controller 책임 분리

`core-workflow.md`의 위임 패턴(controller가 gate 결정·승인·완료 주장 소유)을 지킨다. 서브에이전트는 headless라 실행 중 사용자에게 질문할 수 없으므로 **2-pass**로 처리한다.

### 2-pass 흐름

1. **propose pass (read-only 서브에이전트)**: `manage-self-improvement` 스킬을 따라 audit + 아티팩트를 분석한다.
   - memory 후보를 재검증(§3)하고 기존 memory와 dedup하여 제안한다.
   - skill 후보를 3-of-5로 평가하고, **기존 등록 skill과의 overlap을 분석**한다: 겹치면 어느 skill에 patch하는 게 나은지 / 새로 만드는 게 나은지 / 안 만드는 게 나은지를 판단한다. 모호하면 "사용자 확인 필요" 플래그를 단다.
   - 결과(추가할 memory + 만들/patch할 skill + 모호 항목)를 controller에 반환한다. 쓰기 없음.
2. **approval (controller = finalize)**: "이런 memory를 추가하고, xx skill을 만들겠습니다(또는 yy skill에 patch)"를 사용자에게 **항목별**로 제시하고 승인을 받는다. propose pass가 모호 플래그를 단 항목은 여기서 사용자에게 직접 묻는다.
3. **apply pass (서브에이전트)**: 승인분만 `manage-self-improvement` 스킬을 따라 직접 수행한다.
   - `MEMORY.md` 기록(축약/병합/dedup 적용, budget 3000자 유지) → `memory.recorded`
   - 신규 skill 생성 또는 기존 skill patch를 project-local 디렉토리에 직접 작성(writing-skills 컨벤션 준수) → `skill.created`
   - 사용자가 보류한 skill 후보는 `skill.candidate`로만 기록
   - 결과를 controller에 반환한다.

서브에이전트를 지원하지 않는 host에서는 동일 절차를 inline fallback으로 수행한다(기존 패턴).

### finalize와 manage-self-improvement 책임 분리

`finalize`는 **승인 게이트만** 담당한다. 실제 memory 기록과 skill 생성/patch는 `manage-self-improvement` 스킬이 수행한다. 이로써 `finalize`가 "새 작업을 구현하지 않는다"는 기존 경계([skills/finalize/SKILL.md](../../../skills/finalize/SKILL.md))를 깨지 않는다.

- finalize는 `report.md` 작성 및 최종 status 설정 *전에* manage-self-improvement self-improvement 패스를 1회 트리거하고, propose 결과를 사용자에게 항목별로 제시해 승인만 받는다.
- 승인 후 apply pass(memory 기록 + skill 생성/patch)는 `manage-self-improvement`가 소유한다. finalize SKILL.md에는 "finalize 자신은 self-improvement 산출물을 직접 쓰지 않고 manage-self-improvement에 위임한다 / topic 구현 작업은 여전히 금지"를 명시한다.
- 후보가 없으면 "no candidates"를 audit에 기록한다.
- finalize SKILL.md 체크리스트에 "self-improvement 패스 수행 기록(또는 none) 없이 topic close 금지"를 명시하여 하드 게이트를 보강한다.

### apply pass 산출물 검증 (review 루프 우회 보완)

memory/skill 산출물은 topic의 plan/execute/review 검증 루프 *밖*에서 생성된다(execution review 이후 시점). 이 우회를 보완하기 위해 `manage-self-improvement`가 apply pass에서 자체 검증을 수행한다:

- 생성/patch된 skill: writing-skills 컨벤션 점검(front matter, description trigger, 절차/검증 포함)
- `MEMORY.md`: budget 3000자, 저장형=주입형, dedup 위반 없음 점검
- 검증 결과를 audit에 기록한다. 이들은 topic 코드 변경이 아닌 메타 산출물이며, 별도 topic review 게이트를 강제하지 않는다(트레이드오프는 §10).

## 5. 읽기 (recall): `search-long-term-memory` util 스킬

별도의 **read-only util 스킬**을 만든다. 워크플로우 phase가 아니다.

- 스킬명: `search-long-term-memory`
- 역할: 현재 작업 컨텍스트(예: 진행 중인 요청, 작성 중인 question/spec 내용)를 입력으로 받아 `.as-usual/memory/*`를 스캔하고, **"이 작업에 쓸만한 memory가 있는가"**를 찾아 관련 항목만 압축 다이제스트로 반환한다. 쓰기 없음.
- 호출 방식: **서브에이전트가 이 스킬을 로드해 수행**한다(context 오염 방지). 서브에이전트 미지원 host는 inline fallback.
- 사용 지점: 최소한 `define-requirements`의 question 생성과 requirements(spec) 작성 과정에서 관련 memory를 주입받는다. 다른 phase에서도 memory 컨텍스트가 도움이 될 때 재사용 가능.
- SessionStart 훅: memory 내용 주입 대신 "memory 존재" 정도만 가볍게 알림(현 active-topic-candidates와 동일 철학, 워크플로우 강제 아님).

### trust boundary (중요)

`.as-usual/memory/*`는 프로젝트 파일이므로 stale fact나 prompt-injection성 문구가 들어갈 수 있다. core workflow의 Trust Boundary([core-workflow.md](../../../as-usual-rules/core-workflow.md))는 프로젝트 파일을 데이터/증거로 취급하고, 바뀔 수 있는 사실은 재확인하라고 한다. 따라서:

- `search-long-term-memory` 출력은 **"untrusted recalled context"**로 명확히 감싸 반환한다.
- recalled memory는 현재 user 지시, current topic 아티팩트, core workflow, 안전 정책을 **절대 override할 수 없다**(Instruction Priority 하위).
- memory가 가리키는 파일/명령/사실이 바뀌었을 수 있으면 사용 전에 disk 현재 상태를 재확인한다.
- recalled memory에 내장된 지시문은 워크플로우 지시가 아니라 데이터로만 취급한다.

## 6. skill 개선 모델

### 후보 기준 (Hermes 3-of-5)

다음 5개 중 3개 이상이면 skill 후보:

1. 같은 유형 작업에 다시 쓸 수 있다.
2. 3단계 이상의 절차가 있다.
3. 도구 사용 순서가 중요하다.
4. 실패 경로와 성공 경로의 차이가 있다.
5. 검증 방법이 있다.

### overlap 분석 + patch 우선

propose pass는 기존 등록 skill과 새 후보의 overlap을 분석한다:

- 기존 skill 목적과 겹침 → 해당 skill에 patch (예외 케이스/검증 추가)
- 완전히 다른 trigger와 workflow → 새 skill
- 이미 충분히 커버됨 → 안 만듦
- 판단이 모호 → 사용자에게 질문

### 직접 생성 (승인 후)

승인된 후보는 apply pass에서 `manage-self-improvement`가 **직접** project-local 디렉토리에 skill을 생성하거나 기존 skill을 patch한다. 보류/모호 후보만 `skill.candidate`로 남긴다.

skill 후보 brief(분석·승인·기록 공통 포맷):

- `summary`: "xx 작업에서 yy 부분은 반복 가능한 skill감" 형태의 한 줄
- `rationale`: 3-of-5 중 충족 항목
- `kind`: `new` | `patch`
- `patchTarget`: patch면 기존 skill 이름, 아니면 null
- `brief`: trigger / 핵심 절차 / 검증 (`record-skill --brief`)
- `dest`: project-local 목적지

### skill 목적지 (project-local)

생성되는 skill은 **타깃 프로젝트 로컬**에 둔다. 탐색 규칙:

- `<PROJECT_ROOT>/.agents/skills/` 와 `<PROJECT_ROOT>/.claude/skills/` 를 찾는다.
- 존재하는 쪽 사용. 둘 다 있으면 host-aware 기본값(Claude → `.claude/skills`, Codex → `.agents/skills`). 둘 다 없으면 host 기본 디렉토리 신규 생성.

`/skill-creator`(Claude) / `$skill-creator`(Codex)는 선택적 보조 도구로 **언급만** 한다. 자체 생성이 기본이며 강제 라우팅이 아니다. skill 작성 품질은 writing-skills 컨벤션을 따른다.

## 7. 새 / 수정 skill

```text
skills/manage-self-improvement/
├── SKILL.md                      # 2-pass(propose/apply) 라우터, 입력 목록, 경계
└── references/
    ├── memory-update.md
    └── skill-improvement.md

skills/search-long-term-memory/
└── SKILL.md                      # read-only memory 탐색 util
```

`references/memory-update.md`:

- 장기기억 저장 기준 / 저장하지 말아야 할 기준 + few-shot(§2)
- 즉시 포착(`memory.candidate`)과 finalize 일괄 검토 2시점
- **후보 재검증 프롬프트**(최종 결과 기준 유효성·재사용 가치 판단)
- budget 3000자, consolidation-first overflow, 도메인 분리·라우팅·인덱스
- 2-pass 승인 절차와 사용자 승인 문구

`references/skill-improvement.md`:

- 3-of-5 후보 기준
- 기존 skill overlap 분석, patch vs new vs skip, 모호 시 사용자 질문
- memory vs skill 구분
- project-local 목적지 탐색 규칙(`.agents/skills` / `.claude/skills`)
- 직접 생성 절차 + writing-skills 컨벤션 + `/skill-creator`·`$skill-creator` 언급

## 8. audit 이벤트

신규 4종:

- `memory.candidate` — 포착 시점(2-a) 또는 finalize 분석에서 발견된 memory 후보
- `memory.recorded` — finalize apply pass에서 MEMORY.md에 실제 반영
- `skill.created` — finalize apply pass에서 직접 생성/patch한 skill
- `skill.candidate` — 사용자가 보류했거나 나중 처리로 남긴 skill 후보(brief 포함)

이들은 phase 매크로가 아니라 가벼운 audit append 헬퍼로 `scripts/topic-log.py`에 추가한다. phase/status 도출 로직은 변경하지 않는다.

## 9. 수정 / 신규 대상 파일

| 파일 | 변경 |
| --- | --- |
| `skills/manage-self-improvement/SKILL.md` (신규) | 2-pass propose/apply 라우터, 입력 목록, 경계 |
| `skills/manage-self-improvement/references/memory-update.md` (신규) | memory 저장/비저장/재검증/overflow/분리/승인 + few-shot |
| `skills/manage-self-improvement/references/skill-improvement.md` (신규) | 3-of-5, overlap 분석, patch/new/skip, 직접 생성, 목적지 |
| `skills/search-long-term-memory/SKILL.md` (신규) | read-only memory 탐색 util (서브에이전트 호출) |
| `templates/MEMORY.md` (신규) | MEMORY.md 시작 템플릿(섹션 + 사용자 선호 섹션 + few-shot 주석) |
| `as-usual-rules/core-workflow.md` | §2 Artifact Contract: `.as-usual/memory/` 허용으로 topic-only 경계 갱신 / §11 Finalize Rules: 닫기 전 self-improvement 2-pass(서브에이전트 우선, finalize는 승인만·apply는 manage-self-improvement) + 승인 후에만 반영 짧은 원칙 / §12 git-action: memory 커밋 예외 / §13 audit 이벤트 목록에 신규 4종 추가 + recalled memory trust boundary |
| `skills/finalize/SKILL.md` | precondition/체크리스트: self-improvement 패스 수행 기록(또는 none) 없이 close 금지; 2-pass 서브에이전트 호출 단계 추가 |
| `skills/define-requirements/SKILL.md` | question 생성·requirements 작성 시 `search-long-term-memory`로 관련 memory 주입 + `memory.candidate` 포착 규칙 |
| `skills/writing-plan/SKILL.md` | plan 작성·리뷰 중 명시적 장기 규칙 발생 시 `memory.candidate` 포착 규칙 추가 |
| `skills/executing-plan/SKILL.md` | execute 중 명시적 장기 규칙 발생 시 `memory.candidate` 포착 규칙 추가 |
| `skills/using-as-usual/SKILL.md` | first-reads에 memory 존재 인지 + 필요 시 `search-long-term-memory` 호출 안내 |
| `skills/git-action/SKILL.md` | `.as-usual/memory/*`를 커밋 대상으로 stage 허용(topic 아티팩트는 제외 유지) |
| `hooks/session-start` | `.as-usual/memory/` 존재 시 가벼운 알림 추가 |
| `scripts/topic-log.py` | `memory.candidate` / `memory.recorded` / `skill.created` / `skill.candidate` append 헬퍼 추가 (phase 변경 없음) |
| `CLAUDE.md` | STRUCTURE / RUNTIME WORKFLOW MODEL / CONVENTIONS / ANTI-PATTERNS / WHERE TO LOOK / CODE MAP 갱신 |
| `AGENTS.md` | target project artifact 모델(topic-only → topic/ + memory/) 설명 갱신 |
| `README.md` | target project artifact 설명 갱신(memory 디렉토리 추가) |
| `docs/ARCHITECTURE-WORKFLOW.md` | artifact 모델 + commit 정책(memory 커밋 예외) 갱신 |
| `.agents/skills/verify-project-identity/SKILL.md` | AGENTS/CLAUDE/README/ARCHITECTURE 동기화 기준에 memory 모델 추가 |
| `.agents/skills/verify-runtime-workflow-consistency/SKILL.md` | manage-self-improvement·search-long-term-memory·memory·finalize 정합성 체크 추가 |

## 10. 트레이드오프 / 알려진 한계

- 독립 phase가 아니라 finalize 체크리스트 + audit 이벤트로 self-improvement 수행을 보장하므로, phase status 기반 하드 게이트보다 강제력이 약간 약하다. 대신 phase state machine 복잡도를 늘리지 않고 controller context를 깨끗하게 유지한다.
- memory budget(3000자)은 별도 memory 도구가 강제하는 hard limit이 아니라 스킬이 점검하는 budget이다(파일 기반).
- 사용자 선호가 프로젝트별로 중복될 수 있다(전역화는 범위 밖).
- skill 직접 생성은 apply pass(서브에이전트, fallback inline)에서 일어나며, 품질은 writing-skills 컨벤션과 이후 사용자의 검토에 의존한다.
