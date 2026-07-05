# harness-as-usual 개선 항목 최종 문서 (improvement-plan)

작성일: 2026-07-05
입력: claude 제안 + codex 제안 (둘 다 [README.md](README.md), [baseline-analysis.md](baseline-analysis.md), [gajae-code-analysis.md](gajae-code-analysis.md), [lazycodex-analysis.md](lazycodex-analysis.md) 기반)
출처 표기: `G-a#` = gajae-code-analysis 아이디어 (a) 번호, `L-a#` = lazycodex-analysis 아이디어 (a) 번호.

---

## 0. 종합 판단

두 제안은 상위 우선순위에서 사실상 합의한다. **receipt-only 반환 + 폐쇄 어휘 판정**과 **DoneClaim/AdversarialVerify + INCONCLUSIVE ≠ PASS**를 1순위로 꼽은 것이 동일하며, 이는 baseline 최대 공백(#1 검증 자동화, #2 병렬 실행 전제, #5 observation 스키마)을 직접 해소하면서 AsUsual의 "파일이 진실, 채팅은 보조" 철학과 충돌하지 않는다.

두 제안의 차이와 최종 결정:

| 쟁점 | claude | codex | 최종 판단 |
|---|---|---|---|
| 승인 원자화 + 승인 대기 내구화 | 1순위 | 2순위 | **P1로 승격.** core-workflow.md 한 단락 + 기존 audit/status 파생 활용이라 비용이 거의 없고, 컴팩션/세션 재개 안전성에 직결됨 |
| Explorer agent 신설 | 언급 없음 | 1순위 (import-plan 문서 인용) | **백로그 제외.** codex가 인용한 `explorer-agent-import-plan.md`는 리서치 디렉토리에 존재하지 않고, `skills/explore-codebase/SKILL.md`가 이미 저장소에 구현되어 있음(미커밋). 남은 작업은 "커밋 + 서브에이전트 위임 메시지 계약(P2-7) 반영"뿐 |
| Suitability Gate | 1순위 | 2순위 | **P1 유지.** direct-execute 라우팅이 에이전트 1회성 판단에 의존하는 공백(#7)의 직접 해법이고, 시그널 표만 이식하면 되는 저비용 항목. 단 lazycodex의 LIGHT/HEAVY 단방향 래칫(L-a5)을 세트로 포함 |
| Stop 훅 자동 계속 | 3순위 + 안전장치 필수 | 주의 항목 | **P3 유지, 안전장치 없이는 도입 금지** (컨텍스트 압박 감지 무장해제 + 동일 실패 제한) |

공통 원칙(codex의 결론을 채택): **절차를 늘리는 것이 아니라, 에이전트의 자기 보고를 파일·증거·폐쇄 어휘로 낮춰 검증 가능한 계약으로 만드는 것**이 이번 개선의 축이다. gajae/lazycodex의 플러그인 아키텍처·훅 시스템 전체를 복사하지 않고, "완료 판정 계약"과 "서브에이전트 I/O 계약"만 얇게 이식한다.

---

## P1 — 즉시 도입 (설계 충돌 없음 · 효과 큼 · 저비용)

### P1-1. Receipt-only 서브에이전트 반환 계약 [G-a2]

서브에이전트가 산출물 전문을 응답으로 돌려주지 않고, **파일에 쓴 뒤 `경로 + 판정(+해시)`만** 반환한다. 리뷰어는 부모가 붙여넣어준 본문이 아니라 파일을 직접 읽는다.

- **효과**: 리뷰 루프가 여러 번 돌아도 컨트롤러 컨텍스트에 산출물 사본이 쌓이지 않음. task 병렬 실행(공백 #2)의 전제 조건.
- **적용 위치**: `skills/executing-plan/implementer-prompt.md`, `task-quality-reviewer-prompt.md`, `task-requirements-reviewer-prompt.md`, `skills/review-execution/SKILL.md`, `skills/cleanup-code/SKILL.md`의 서브에이전트 계약 절.
- **작업량**: 프롬프트 문구 수준 (각 파일 1~3문장).

### P1-2. 폐쇄 어휘 판정(closed-vocabulary verdict) [G-a3]

리뷰/검증 출력의 판정을 자유 서술이 아니라 고정 어휘로 강제: 예) 리뷰 `OKAY | ITERATE | REJECT`, 검증 `PASS | FAIL | INCONCLUSIVE`, 완료 확인 `CONFIRMED | NEEDS_FIX | NEEDS_HUMAN_REVIEW`.

- **효과**: "OKAY 나올 때까지 최대 N회" 같은 루프 종료 조건을 기계적으로 판정 가능. audit.jsonl 파생 계산(status.py)과도 궁합이 좋음.
- **적용 위치**: P1-1과 동일한 리뷰어 프롬프트들 + `scripts/topic-log.py`의 record-task-review 계열 이벤트 필드.
- **작업량**: 프롬프트 + topic-log.py 이벤트 스키마 소폭 수정.
- **비고**: P1-1과 한 몸으로 진행 (receipt = 경로 + 이 어휘).

### P1-3. DoneClaim → AdversarialVerify 분리 + INCONCLUSIVE ≠ PASS + 증거 타입 [L-a4, L-a8, G-a6]

실행자의 완료 보고는 구조화된 **주장(DoneClaim)** 일 뿐이며, 독립 컨텍스트의 검증자가 반증을 시도해 `confirmed`만 통과시킨다. 세 가지 규칙을 세트로:

1. `TESTS ALONE NEVER PROVE DONE` — 표면 종류별 증거 타입 요구 (CLI=재실행 명령+출력, UI=스크린샷, API=실제 호출 기록).
2. **INCONCLUSIVE ≠ PASS** — 서브에이전트 타임아웃, 무응답, 검증 불가, 애매한 결과는 제3의 상태이며 게이트 실패로 취급.
3. 리뷰어는 실행자와 독립 컨텍스트 — "본인이 본인 검사" 구조 차단 (review-execution의 기존 "separate code-review agent 선호"를 계약으로 승격).

- **효과**: baseline 최대 공백(#1 검증 자동화) 직접 해소. "Evidence over optimism" 정체성에 증거의 *형식*을 부여.
- **적용 위치**: `skills/executing-plan/SKILL.md`(task 완료 보고 형식), `skills/review-execution/SKILL.md`, finalize의 completion validation, audit.jsonl verification 이벤트에 증거 타입 필드 추가.
- **작업량**: 스킬 2~3개 + topic-log.py verification 이벤트 확장.

### P1-4. 승인 원자화 + 승인 대기의 내구 상태화 [L-a10, L-a1]

"Approval authorizes exactly one thing" — 단계 전환마다 이 승인이 정확히 무엇을 허가하는지 한 문장으로 명시한다(계획 승인 ≠ 구현 허가). 승인 대기 상태는 대화 기억이 아니라 audit.jsonl에서 파생되는 명시 상태로 두고, 사용자의 다음 답변은 approve / scope-change / still-unclear 3분류로만 해석한다.

- **효과**: "계획 승인했으니 구현 시작" 오해 차단. 컴팩션·세션 재개(hand-off) 시 게이트 통과 여부를 파일에서 판정. 기존 fresh approval 게이트와 정신이 같아 이식 마찰이 없음.
- **적용 위치**: `as-usual-rules/core-workflow.md` 승인 게이트 절 한 단락, `scripts/as_usual_topic_log/status.py`의 approvals 파생에 awaiting 상태 명시, `skills/hand-off/SKILL.md` 재개 판정.
- **작업량**: 문서 한 단락 + status 파생 로직 확인/보강.

### P1-5. 양방향 게이트 — Suitability Gate 시그널 표 [G-a1, L-a5, L-a13]

모호한 요청을 requirements로 올리는 기존 게이트에 반대 방향을 추가: **명확한 소규모 요청은 측정 가능한 시그널로 즉시 direct-execute로 튕겨낸다.** 파일 경로/이슈 번호/심볼/수용 기준 중 하나라도 있으면 직행 후보, "유효 단어 ≤15 + 구체 앵커 0개"면 requirements행. `force:` 접두사 우회 허용. lazycodex의 LIGHT/HEAVY 티어 + **단방향 래칫**(진행 중 HEAVY 사실 발견 시 승급만 허용, 강등 금지)을 함께 이식.

- **효과**: direct-execute 라우팅의 1회성 자율 판단(공백 #7)을 기계적 판정으로 대체. "하네스가 무거워서 안 쓰게 되는" 문제의 직접 해법.
- **적용 위치**: `skills/start-work/SKILL.md` 라우팅 절, `as-usual-rules/core-workflow.md` direct-execute 조건.
- **작업량**: 시그널 표 이식 + 라우팅 문구 수정.

---

## P2 — 구조 개선 (가치 확실 · 약간의 설계 작업 필요)

### P2-1. 블로커 2분류 (resolvable / human_blocked) [G-a7]

`resolvable`(조사·하위목표 분할·재시도·위임으로 에이전트가 풀 수 있는 모든 것)이면 **절대 멈추지 않고**, `human_blocked`(자격증명·외부 승인·물리 단계)만 사용자에게 온다. 기존 3회 실패 circuit breaker와 결합: 멈춘 뒤 "무엇을 스스로 진단할지"는 agent-toolkit의 `agent-introspection-debugging` 4-Phase 루프를 executing-plan Failure Handling에 참조로 통합(공백 #3, 현재 두 저장소 간 상호 참조 전무).

- **적용 위치**: `skills/executing-plan/SKILL.md` Failure Handling, blocker 기록 이벤트에 분류 필드.

### P2-2. 리뷰어 발산 방지 캘리브레이션 [L-a12]

리뷰 프롬프트에 3단 판정(P1-2의 폐쇄 어휘) + **이슈 상한(high-confidence 최대 3개)** + "blocker-finder, not a perfectionist" + "무엇을 검사하지 않는가" 섹션. 리뷰→수정→리뷰 루프가 스타일 지적으로 무한 발산하는 것을 막는다.

- **적용 위치**: `skills/review-execution/SKILL.md`, `skills/cleanup-code/SKILL.md`, executing-plan의 task 리뷰어 프롬프트 2종.

### P2-3. decision-complete 기준 명문화 [L-a2]

plan.md 합격 기준을 "실행자가 인터뷰 컨텍스트 없이 **판단 0회**로 실행 가능"으로 정의. 각 task에 References + 에이전트 실행형 Acceptance + happy/failure 시나리오를 요구. 기존 Consumes/Produces·No Placeholders 규칙의 자연스러운 확장.

- **적용 위치**: `skills/writing-plan/SKILL.md` 출력 품질 체크리스트, `templates/plan.md`.

### P2-4. 컴팩션 복구 표준 문구 [L-b11]

"컨텍스트 상실 징후 감지 시: topic 아티팩트 전체 재독(`status --json` 포함) → 현재 지점에서 재개. **재계획 금지, 완료 단계 재실행 금지**." audit.jsonl + status.py가 이미 있어 문구 한 단락이면 됨(공백 #4 보완).

- **적용 위치**: `as-usual-rules/core-workflow.md` 공통 규칙 절, `skills/hand-off/SKILL.md`.

### P2-5. Persisted Planner / Fresh Reviewer 비대칭 [G-a5]

수정 루프에서 계획자는 같은 세션을 재사용(맥락 누적 = 자산), 리뷰어는 매번 새로 스폰(이전 판정 앵커링 제거). "기억이 자산인가 편향인가"를 역할별로 구분.

- **적용 위치**: `skills/writing-plan/SKILL.md` 리뷰 루프, `skills/executing-plan/SKILL.md` subagent-driven 모드. 호스트가 세션 지속을 지원하지 않으면 순차 fallback 기록.

### P2-6. Intent Reconciliation 게이트 [G-a8]

계획 승인 직전, 루프가 "가정으로 해소한 항목"을 약한 것부터 사용자와 확인하고 결과를 plan.md의 `## Intent Reconciliation` 섹션에 기록. "그거 그런 뜻 아니었는데" 사고를 승인 전에 포착. 기존 assumption escalation(question 3사이클 상한)과 접점이 있으니 중복 설계 주의.

- **적용 위치**: `skills/writing-plan/SKILL.md` 승인 직전 단계, `templates/plan.md`.

### P2-7. 서브에이전트 위임 메시지 계약 표준화 [L-b5]

Task/서브에이전트 위임 메시지에 `TASK / DELIVERABLE / SCOPE / VERIFY` 필수 필드 + "자기완결 메시지, 부모 대화 이력 의존 금지" + "자식 출력은 검증 전까지 주장(CLAIM)" 원칙을 공통 조항으로. 이미 `explore-codebase`와 `implementer-prompt.md`가 이 방향이므로 공통 골격으로 추출.

- **적용 위치**: `as-usual-rules/core-workflow.md` 서브에이전트 공통 절 또는 공유 프롬프트 조각.

### P2-8. 상태머신 체인 가드 [G-a4]

단계 전환은 이전 phase가 완료/핸드오프 상태일 때만 허용. 각 phase 스킬 진입 시 `status --json`의 phase를 검사하고 불일치 시 진행 대신 라우팅 정정. corrupt-state 복구 절차(어떤 이벤트를 다시 기록해 복구하는지)를 표준 섹션으로.

- **적용 위치**: 각 phase 스킬의 진입 절차, `scripts/as_usual_topic_log/status.py`.
- **비고**: AsUsual은 gajae처럼 런타임 강제가 불가능(프롬프트 계약)하므로, topic-log.py 레벨에서 이벤트 순서 검증을 넣는 것까지가 현실적 상한.

---

## P3 — 선택 도입 (비용/복잡도 있음 · 조건부)

### P3-1. 스캐폴드 스크립트 + append 전용 편집 [L-a3]

requirements.md/plan.md/review report 골격을 멱등 스크립트(재실행 no-op 보장)가 생성하고, 에이전트는 지정 영역에만 append. topic-log.py가 이미 이 철학("프롬프트=비결정론, 지속화=결정론")이므로 템플릿 생성까지 확장하는 방향. 구조 드리프트와 "파일 절반만 다시 쓰는" 사고 차단.

- **적용 위치**: `scripts/topic-log.py` init 확장 또는 신규 scaffold 커맨드 + `templates/*`.

### P3-2. 적대 QA 트리거 매핑 [L-a9]

검증 클래스를 전수 실행하지 않고 "트리거 사실이 있을 때만 적용 + 미적용은 사유 1줄 기록". 검증 비용-엄격성 균형 장치. P1-3 증거 타입 시스템이 자리잡은 뒤 도입.

### P3-3. cross-topic 대시보드 [L-a6, 공백 #8]

`.as-usual/topic/*`를 스캔해 topic 목록 / phase 분포 / 승인 대기 / blocker를 보여주는 `topic-log.py list` / `status-all` 계열 커맨드.

### P3-4. agent-toolkit 자체 자산 상호 참조

외부 도입과 별개로, 이미 보유한 `agent-introspection-debugging`(P2-1에서 통합)과 `sub-agent-orchestration`의 3-tier 모델 라우팅(공백 #6)을 dispatch 시 모델 선택 기준으로 참조. 새로 만들 것 없이 연결만 하면 되는 항목.

### P3-5. Stop 훅 자동 계속 [L-a7] — ⚠️ 안전장치 없이는 도입 금지

plan.md 미완료 체크박스가 남아 있으면 Stop 훅이 턴을 강제 연장하는 메커니즘. 사람 없는 장기 실행이 가능해지지만 폭주 위험이 있다. 도입 시 다음 두 가지를 반드시 세트로:

1. **컨텍스트 압박 마커 감지 시 무장해제** (lazycodex는 "context compacted" 등 마커가 보이면 디렉티브 주입을 포기).
2. **동일 실패 반복 제한** (기존 3회 circuit breaker와 연동).

Claude Code 훅에서만 가능하고 Codex 호스트에서는 미지원이므로, 도입해도 호스트 의존 기능으로 명시해야 한다.

---

## 횡단 원칙 (모든 항목에 적용)

1. **자기강화 루프 차단** — `manage-self-improvement`에 "회상된 기억을 근거로 새 기억을 쓰지 않는다" 규칙 추가. gajae는 저장 직전 회상 태그를 무조건 스트리핑해 되먹임 왜곡을 막는다. (기존 UNTRUSTED RECALLED CONTEXT 경계의 쓰기 방향 확장 — 소규모이므로 P1 작업과 함께 처리 가능.)
2. **프롬프트만으로는 계약이 아니다** — gajae의 4층위 강제가 시사하듯, 핵심 게이트(판정 어휘, 이벤트 순서, 증거 필드)는 가능하면 topic-log.py 스크립트 레벨 검증으로 받친다.
3. **일관성 검사(반면교사: gajae `<soul>`)** — 기존 계약과 모순되는 텍스트가 프롬프트 말미에 붙으면 전체 계약 신뢰도가 무너진다. 스킬 수정 시 기존 섹션과의 일관성 검사를 리뷰 단계에 포함 — 기존 `verify-runtime-workflow-consistency` 스킬의 검사 항목으로 추가하면 됨.

## 제외 / 이미 완료 항목

| 항목 | 판단 |
|---|---|
| Explorer agent 신설 (codex 1순위 #5) | **이미 구현됨** — `skills/explore-codebase/SKILL.md`가 저장소에 존재(미커밋). codex가 인용한 `explorer-agent-import-plan.md`는 리서치 디렉토리에 없음. 남은 일: 커밋 + P2-7 위임 계약 정합성 확인 |
| gajae/lazycodex 플러그인 아키텍처·훅 시스템 전체 이식 | **제외** — AsUsual은 프롬프트 계약 기반 하네스. 완료 판정 계약과 서브에이전트 I/O 계약만 얇게 이식 (양 제안 합의) |
| TTSR(스트림 룰 강제), IRC 피어 메시징, BM25 툴 지연 로딩 | **제외** — 런타임 코드가 필요한 기능으로 AsUsual 구조상 구현 불가 |
| agent-toolkit 스킬 개선 (README 목표 2) | **본 문서 범위 밖** — harness-as-usual 강화와 별도 트랙으로 진행 |

## 권장 진행 순서

```
1차: P1-1 + P1-2 (receipt-only + 폐쇄 어휘 — 한 몸)
2차: P1-3 (DoneClaim/AdversarialVerify + INCONCLUSIVE + 증거 타입)
3차: P1-4 + P1-5 (승인 원자화 + Suitability Gate) + 횡단 원칙 1(자기강화 루프 차단)
4차: P2-1, P2-2, P2-4 (블로커 2분류 · 리뷰어 캘리브레이션 · 컴팩션 문구)
5차: P2-3, P2-5 ~ P2-8
6차: P3 항목은 각각 필요가 확인될 때 개별 결정
```

각 차수 완료 시 `verify-runtime-workflow-consistency` + `verify-project-identity`로 문서 정합성 검증을 돌린다.
