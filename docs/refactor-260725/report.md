# AsUsual v2 리팩터링 — 최종 보고서

작업일: 2026-07-25
브랜치: `refactor/v2-work-units` (main 미병합, 미배포)
문서 체계: [decisions.md](decisions.md) (왜) · [design.md](design.md) (무엇) · [work-plan.md](work-plan.md) (어떻게) · 본 문서 (결과)

---

## 1. 요약

최초 AsUsual은 core-workflow 하나만 강제하는 하네스였다. 이후 `direct-execute`와
`find-cause`가 **기존 파이프라인의 분기**로 추가되면서 판정이 4곳에 흩어지고,
라우터가 2겹이 되고, 같은 작업의 기록 규칙이 진입 경로에 따라 달라졌다.

v2는 이를 **동급 작업 단위 3개**로 재편했다: 요구사항 합의가 필요한 `topic`,
할 일이 정해진 `direct-work`, 코드를 고치지 않고 원인/방향을 확정하는 `issue`.
분류는 진입 시 한 번, 기록은 스키마 하나, 대화는 스킬 하나가 소유한다.

동시에 강제 범위를 **코어 규칙 7개**로 줄여 나머지 전부를 에이전트 재량으로
내렸다. 강제되는 것은 기록·안전·증적·권한의 성격뿐이고, 그중 3개(검증 verdict,
실행 전 계획 리뷰, 기록 봉인)와 move 제한은 문서가 아니라 **스크립트가 거부**하는
방식으로 강제된다.

하위호환은 의도적으로 끊었다. 구 포맷 폴더(`topic.md`/`journal.jsonl`/
`question-cN.md`)는 재개 대상이 아니다.

## 2. 변경 규모

| 영역 | 이전 | 이후 |
| --- | --- | --- |
| 기록 스크립트 | `topic-log.py` + `journal-log.py` (스키마 2개, 매크로 커맨드 20+) | `as-usual-record.py` 1개 (`as-usual.record.v1`, 커맨드 6개) |
| rules | 7개 파일 761줄 | 3개 파일 458줄 (`core-rules` / `safety-rules` / `record-commands`) |
| 스킬 | 15개 (라우팅 스킬 3개 중복) | 15개 (진입 1 · 오너 3 · 단계 8 · 유틸 3) |
| phase 어휘 | 18개 (+legacy alias, 스킬명과 불일치) | 11개 (= 소유 스킬 이름, 단위별 부분집합) |
| nextAction | 17개 | 3형 (`<phase>` / `awaiting-user` / `none`) |
| 이벤트 어휘 | 30여 개 | kind 12개 (게이트가 쓰는 것만) |
| requirements 템플릿 | 17섹션 | 6섹션 |
| plan 템플릿 | 25+섹션 | 5섹션 (direct-work는 2섹션) |
| 공통 문서 | `topic.md`+`problem.md`+`question-cN.md` | `contexts.md` 하나 (3밴드) |

커밋: `e29e117`(기록 레이어) → `3d8b244`(rules) → `f987233`(스킬) →
`4a4dfb2`(템플릿) → `61b481a`(훅·매니페스트·검증·문서) → `42ea29e`(최종 리뷰 수정)

## 3. 최종 리뷰 결과

리뷰 관점 3개(사용자 지정) + 전반 검토. 모든 확인은 실제 실행 기반.

### 3-1. 3개 워크플로우 각각의 정합성 — PASS

- **기계 대조**: 오너 스킬 3개가 선언한 phase가 `constants.py`의 `UNIT_PHASES`
  부분집합과 정확히 일치. 스킬/rules에 등장하는 모든 `--kind`, `--next-action`
  값이 스크립트 어휘에 존재.
- **E2E 3종 실행**:
  - issue: 가설 2개 → 1개 철회(reason 필수 확인) → 1개 확정(evidence 필수 확인)
    → conclusion 없이 종료 시도 → **스크립트 거부** → 작성 후 종료 → 봉인 후
    link만 허용 확인 → 후속 topic 링크.
  - topic: inbox 오분류 → move → requirements 생성 후 move **거부** → 리뷰 없이
    실행 승인 **거부** → 리뷰 → 승인 → 검증 PASS → 봉인 → `validate` 통과.
  - direct-work: 질문 0개 통과 → 체크리스트 → 리뷰(발견 0도 기록) → 승인 → 검증
    PASS → finalize 없이 종료(정상 terminal 확인).
- 단위 테스트 54개 통과.

### 3-2. 분기 처리의 깔끔함 — PASS

- 분류 판정은 `using-as-usual` 한 곳, 2단 결정트리(산출물 축 → 위험 축)로 축이
  섞이지 않음. 명시 진입은 질문 생략, 미확정만 inbox.
- 단위 간 전환은 규칙 하나: **본 작업 산출물
  (`requirements.md`/`plan.md`/`conclusion.md`) 이전이면 move, 이후면 새 폴더 +
  양방향 링크.** 판정 주체는 에이전트가 아니라 스크립트(차단 목록 방식).
- 구 설계의 이중 라우터(`routing-rules` §3 ↔ `start-work`), 진입 경로별 2갈래
  결론 처리, `routed-to-find-cause` 주차 상태는 모두 소멸 확인.
- 단계 스킬 8개 전수 검사: 호출 단위로 분기(`if unit == …`)하는 스킬 0개.
  강도 차이는 오너 매트릭스와 호출 인자로만 전달.

### 3-3. 프롬프트 중복 — PASS (수정 2건 반영)

단일 소유 구조 확인:

| 규칙 | 소유자 | 다른 곳 |
| --- | --- | --- |
| 코어 규칙 7개 | `core-rules.md` §4 | 번호/이름 참조만 |
| 고위험 목록 · 신뢰 경계 | `safety-rules.md` | 참조만 |
| 전환(move/link) 조건 | `core-rules.md` §7 + `gates.py` | 참조만 |
| 완료 증적 기준 | `core-rules.md` §6 | 참조만 (아래 수정 1) |
| 대화 규칙(추천 동반·배치·순차) | `gathering-context` | find-cause User Interview 절 등 구 중복 소멸 |
| 어휘·게이트 | `constants.py` / `gates.py` | rules/스킬은 서술만 |

발견·수정:
1. `execute-plan`이 core-rules §6의 증적-표면 목록을 재서술 → 참조로 교체.
2. 문서 리뷰 체크리스트 2종은 "품질 참조 자료"로 지위 변경이 이미 반영되어
   있고, 문서 내 Review Status 기입 요구 잔재 없음을 확인.

### 3-4. 전반 리뷰에서 발견된 문제 (모두 수정, 커밋 `42ea29e`)

| # | 심각도 | 내용 | 수정 |
| --- | --- | --- | --- |
| F1 | **중요** | `finalize`가 기록을 봉인한 **뒤** git 질문을 하는데, `git-action`은 선택을 무조건 이벤트로 기록하라고 지시 → 봉인 게이트에 걸려 실패하는 모순 | open/sealed 분기 명시. 봉인된 기록은 chat 보고 + git 커밋 자체가 증거라는 설계 의도를 문서화 |
| F2 | 사소 | `write-requirements`·`execute-plan`의 `--next-action` 예시가 사용자 승인 대기 지점인데 다음 phase명을 기록 → `awaiting-user` 의미론과 불일치 | 두 예시를 `awaiting-user`로 교체, 이유 병기 |
| F3 | 사소 | `GIT_ACTIONS` 상수가 어떤 게이트에서도 미사용 → "게이트가 쓰는 어휘만 존재" 원칙 위반 | 제거 |
| F4 | 사소 | `search-long-term-memory`에 구 어휘 잔재("question/spec", "core workflow") | 문구 갱신 |

수정 후 테스트 54개 재통과, 어휘 대조 재실행 PASS.

### 3-5. 알고 있는 한계 (의도된 수용)

- `run-issue`만 오너 3개 중 절차(조사 루프)를 직접 소유 — Q16에서 의도적으로
  보류. 다음 리팩터링 후보.
- `contexts.md` 3밴드 규칙이 core-rules(계약) · gathering-context(수행 절차) ·
  템플릿(주석) 3곳에 등장 — 계약/절차/현장 힌트로 층위가 달라 수용. 단 조건
  변경 시 3곳 동기화 필요.
- phase 어휘 중 `investigating`/`concluding`/`blocked`는 스킬명이 아닌 예외
  (전자 둘은 `run-issue` 소유, `blocked`는 상태). `constants.py`가 단일 권위라
  실해는 없음.

## 4. 폐지 총목록

스킬 `start-work` · `hand-off` | 파일 `topic.md` · `question-cN.md` ·
`problem.md` · `journal.jsonl` · `code-review-report.md` · `execute/` ·
`clean-up/` | 스크립트 `topic-log.py` · `journal-log.py` ·
`as-usual.journal.v1` · 매크로 커맨드 전부 | rules `core-workflow.md` ·
`find-cause-workflow.md` · `routing-rules.md` · `logging-rules.md` ·
`completion-rules.md` · `log-audit-commands.md` | 개념 `routed-to-find-cause` ·
`-complete` phase · 실행 모드 선택 · question 파일 사이클 · 문서 리뷰 체크리스트
게이트 · "사용자가 파일에 직접 답 쓰기"

## 5. 남은 작업

- **릴리스 (work-plan 6.4)**: 버전 lockstep 범프 + `publish-as-usual`.
  사용자 명시 승인 대기. **릴리스 시 다른 프로젝트의 구 포맷 `.as-usual/`
  폴더는 재개 불가** — 릴리스 노트에 clean-break 명시 필요.
- 보류 항목: `investigate`/`write-conclusion` 단계 스킬 추출,
  `artifact`/`memory` kind의 `note` 흡수 여부.
