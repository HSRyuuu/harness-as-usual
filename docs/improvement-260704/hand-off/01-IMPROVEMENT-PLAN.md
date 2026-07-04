# 01. AsUsual 개선 작업 계획서 (Fable 위임용)

이 문서는 Fable이 수행할 개선 작업의 **범위, 접근 방식, 가드레일, 검증 게이트, 산출물**을 정의한다.
개선은 4개 축으로 나뉜다: **① 단일 작업 개선 ② 워크플로우 개선 ③ 아키텍처 개선 ④ 프롬프트 개선.**

먼저 `00-ORIENTATION.md`를 읽었다고 가정한다. (구조·파일 위치·불변 규칙·검증 표면은 거기 있음.)

---

## 0. 모든 개선에 공통으로 적용되는 작업 프로토콜

Fable은 어떤 축이든 아래 루프를 따른다.

```
1. SCOPE   개선 대상을 한 문장으로 확정한다. (예: "define-requirements의 answer validation 규칙 강화")
2. READ    해당 축의 "최소 읽기 세트"만 연다. 원본 파일이 최종 진실.
3. DIAGNOSE 현재 동작/규칙의 문제를 근거와 함께 적는다. (추측 금지, 파일 인용)
4. PROPOSE  변경이 크면 docs/improvement-260704/proposals/<date>-<slug>.md 에 제안서 작성 후 승인 대기.
            작으면(문구/오타/명백한 정합성 수정) 바로 진행하되 근거를 커밋 메시지/PR에 남긴다.
5. CHANGE   원본 파일을 최소 변경으로 수정한다. 미러/manifest 동기화 규칙 준수(00-ORIENTATION §5).
6. VERIFY   아래 "검증 게이트" 통과. 통과 못 하면 완료라고 하지 않는다.
7. REPORT   무엇을 왜 바꿨고 무엇을 검증했는지 요약.
```

### 변경 규모 판단 (제안서 필요 여부)

| 규모 | 예시 | 절차 |
| --- | --- | --- |
| **Small** | 오타, 문구 다듬기, 명백한 skill↔core 정합성 수정, 링크 수정 | 바로 변경 + 검증 |
| **Medium** | 한 skill의 규칙 추가/조정, reviewer prompt 항목 추가, template 필드 변경 | 제안서 권장 → 승인 후 변경 |
| **Large** | phase 순서/게이트 변경, artifact 계약 변경, 아키텍처 계층 변경, core-workflow 구조 변경 | 제안서 필수 → 승인 후 변경 |

### 공통 가드레일 (위반 금지)

1. **gate를 약화시키지 마라.** `PROJECT_IDENTITY.md`의 실패 모드 예방 우선순위(요구사항 오해 → DB/API 영향 누락 → 미승인 위험작업)를 무너뜨리는 변경은 Large이며 제안 필수.
2. **runtime ↔ maintainer 경계를 지켜라.** runtime 표면(`as-usual-rules/`, `skills/`, `templates/`)에 plugin 개발/설치/미러 규칙을 넣지 마라. 그건 `CLAUDE.md`/`.agents/skills/`의 몫.
3. **단일 원본 원칙.** requirements/plan은 각각 파일 하나. workflow prompt는 `core-workflow.md` 하나. 표를 두 곳에 복제하지 마라(예: reviewer 체크리스트는 reviewer prompt에만).
4. **정합성 우선.** core-workflow에서 규칙을 바꾸면 대응 skill/template/reviewer prompt를 함께 맞춰라. 반대도 마찬가지.
5. **legacy 금지.** `.as-usual/topics/`(복수형), `yyyyMMdd` 압축 날짜, 제거된 JSON state artifact를 되살리지 마라.

---

## ① 단일 작업 개선 (Single-task Improvement)

**정의:** 하나의 skill 또는 하나의 prompt/script의 국소적 품질 개선. 워크플로우 순서는 건드리지 않음.

**대상 후보:**
- 특정 `skills/<phase>/SKILL.md`의 지시 명확화
- 특정 reviewer prompt의 체크 항목 강화/오탐 감소
- `scripts/topic-log.py`의 단일 서브커맨드 동작 개선/버그 수정
- template 한 개의 필드/섹션 개선

**최소 읽기 세트:** 대상 파일 + (skill이면) 그 skill의 reviewer prompt + `core-workflow.md`에서 해당 phase 섹션만.

**가드레일:**
- 그 skill이 담당한다고 선언된 책임(ownership) 밖으로 규칙을 확장하지 마라. core-workflow는 gate를, reviewer prompt는 review 기준을 소유한다.
- script 변경 시 `test_state_machine.py` 등 관련 테스트를 먼저 확인하고, 변경 후 통과시켜라. 필요하면 테스트도 추가.

**검증 게이트:** 관련 unittest 통과 + (해당되면) `verify-runtime-workflow-consistency` 절차.

---

## ② 워크플로우 개선 (Workflow Improvement)

**정의:** phase 순서, gate 조건, 라우팅, artifact 계약, 실행/리뷰/종료 흐름 자체의 개선.

**대상 후보:**
- `start-work`의 라우팅 조건(가장 가벼운 충분한 gate 판단)
- direct-execute 허용/거부 경계
- clarification routing(chat vs question cycle) 규칙
- review-execution → cleanup → finalize 전이 조건
- audit event 종류/파생 status 규칙

**최소 읽기 세트:** `core-workflow.md` §4–§13 + 대상 phase의 skill + (파생 로직이면) `topic-log.py`의 `status` 관련 부분.

**가드레일:**
- **Large 취급이 기본.** 순서/게이트 변경은 거의 항상 제안서 필수.
- core-workflow와 skill이 **양쪽 다** 바뀌어야 정합성이 맞는 경우가 대부분. 한쪽만 바꾸지 마라.
- machine-readable phase/nextAction 값을 바꾸면 `topic-log.py`와 테스트를 함께 갱신.
- 절대 불변 규칙(00-ORIENTATION §6)을 우회하는 지름길을 만들지 마라.

**검증 게이트:** unittest 전체 + `verify-runtime-workflow-consistency` + `verify-as-usual-harness` + (경계 이동 시) `verify-runtime-surface`.

---

## ③ 아키텍처 개선 (Architecture Improvement)

**정의:** 3계층 구조, 호스트 추상화(Claude/Codex), artifact/memory 모델, 미러/manifest 구조 등 구조적 변경.

**대상 후보:**
- runtime contract ↔ skills ↔ topic artifacts 경계 재정의
- `.as-usual/topic/` vs `.as-usual/memory/` 모델 조정
- maintainer skill 미러(`.agents/skills/` ↔ `.claude/skills/`) 구조/동기화 방식
- plugin manifest 구조, hook 주입 모델(SessionStart 한 문장 원칙)

**최소 읽기 세트:** `PROJECT_IDENTITY.md` + `docs/ARCHITECTURE-WORKFLOW.md` + `CLAUDE.md`/`AGENTS.md`의 STRUCTURE·CONVENTIONS·ANTI-PATTERNS + 관련 manifest.

**가드레일:**
- **항상 Large. 제안서 필수.** 아키텍처 변경은 정체성 문서와 충돌 여부를 먼저 검토.
- 이중 표면(호스트 2개, 미러, manifest 2벌)의 일관성을 깨지 마라. 한 곳을 바꾸면 대응 표면 전부 갱신.
- hook은 "capability 한 문장 + entrypoint"만 주입한다는 원칙을 지켜라. full workflow/후보/memory를 주입하지 마라.
- 새 project-global artifact를 만들지 마라(`.as-usual/memory/`만 예외).

**검증 게이트:** unittest 전체 + manifest jq + hook smoke + `verify-project-identity` + `verify-implementation`(aggregate).

---

## ④ 프롬프트 개선 (Prompt Improvement)

**정의:** LLM에게 주는 지시문 자체의 품질 개선 — 명확성, 모호성 제거, 지시 충돌 해소, 토큰 효율, 오탐/과잉게이트 감소.

**대상:** `as-usual-rules/core-workflow.md`, 각 `skills/*/SKILL.md`, 모든 `*-reviewer-prompt.md`, `implementer-prompt.md`, `manage-self-improvement/references/*.md`.

**접근 방식:**
- 지시가 **중복**되는지 확인(예: 같은 규칙이 core-workflow와 skill 양쪽에 서술). ownership 원칙에 따라 한 곳으로 모으고 다른 곳은 참조만.
- **모호/충돌** 지시를 찾아 결정 규칙으로 바꾼다(우선순위표, IF/ELSE 형태 선호 — core-workflow가 이미 그 스타일).
- **과잉 게이트/과잉 마찰**을 줄이되 안전 게이트는 유지(PROJECT_IDENTITY의 "friction은 유지, ceremony는 최소" 원칙).
- 토큰 낭비 문구(장황한 반복, 채우기용 문장)를 제거하되 machine-readable marker(`[Answer]:`, status 값, 섹션 순서)는 절대 보존.

**최소 읽기 세트:** 대상 prompt 파일 + `core-workflow.md`의 관련 섹션만 + 그 prompt의 짝(skill↔reviewer).

**가드레일:**
- prompt 문구를 바꿔 **의미(게이트/계약)**가 바뀌면 그것은 ②/③ 축이다. 순수 프롬프트 개선은 동작을 보존해야 한다.
- 사용자-facing artifact 언어 규칙(사용자 대화 언어로 작성)과 marker 보존 규칙을 깨지 마라.
- reviewer prompt의 체크리스트는 core-workflow로 복제하지 마라(반대도 금지).

**검증 게이트:** `verify-runtime-workflow-consistency` + `verify-runtime-surface` + (core-workflow 변경 시) hook smoke는 영향 없지만 skill 정합성 재확인.

---

## 검증 게이트 (완료 선언 전 필수)

변경 범위에 따라 아래를 실행하고 결과를 보고한다. **하나라도 실패하면 완료가 아니다.**

```bash
# (A) Python 테스트 — script/상태머신 변경 시 필수, 그 외 권장
python3 -m unittest discover -s .agents/skills/sandbox-e2e-test/tests -p 'test_*.py'

# (B) manifest / hook — manifest·hook·skill 목록 변경 시 필수
jq empty .claude-plugin/plugin.json .claude-plugin/marketplace.json
jq empty .codex-plugin/plugin.json .agents/plugins/marketplace.json
jq empty hooks/hooks.json hooks/hooks-codex.json
CLAUDE_PLUGIN_ROOT="$PWD" bash hooks/run-hook.cmd session-start | jq .

# (C) 의미 정합성 — 해당 검증 skill 절차 수행 (00-ORIENTATION §7.3)
#     verify-runtime-workflow-consistency / verify-runtime-surface /
#     verify-project-identity / verify-as-usual-harness / verify-implementation
```

미러 동기화가 필요한 변경(maintainer skill 수정)이면 `skill-registry-sync` 절차로 `.agents/skills/`와
`.claude/skills/`가 일치하는지 확인한다.

---

## 우선순위 제안 (사용자 조정 가능)

Fable이 어디부터 손댈지 정해지지 않았다면 아래 순서를 기본값으로 제안한다.

1. **④ 프롬프트 개선(동작 보존)** — 위험 낮고 즉시 가치. core-workflow/skill 중복·모호 문구 정리.
2. **① 단일 작업 개선** — 국소적, 테스트로 검증 가능.
3. **② 워크플로우 개선** — 제안서 기반. 게이트/라우팅 정교화.
4. **③ 아키텍처 개선** — 가장 신중. 정체성 검토 후.

각 축의 구체 대상 파일과 "무엇을 건드리고 무엇을 건드리면 안 되는가"는 `02-FILE-STRUCTURE.md`를 본다.
