# ① as-usual-rules — 규칙 3파일 리뷰

리뷰 잣대: **Opus 5 / GPT 5.6급 프론티어 모델이 이 지시 없이도 같은 판단에 도달하는가의 델타.**
델타가 없는 문장은 과잉, 델타가 있는 문장은 유지. 각 finding에 삭제 위험을 표시한다:
`[줄여도 안전]` / `[유지 — 암묵지]`.

---

## core-rules.md (243줄) — 판정: **대체로 적정, 부분 과잉**

이 파일의 대부분은 레코드 층 규약 — 유닛 정의, 분류 트리, 7대 규칙, 아티팩트 계약,
전환 규칙 — 으로, 모델이 스스로 도달할 수 없는 이 시스템 고유의 약속이다. 이 부분의
밀도는 적절하고, "What is deliberately left to you" 절(§4)로 판단층 위임을 명문화한
것은 프론티어 모델 튜닝으로서 모범적이다.

### F1-1. §3 "Writing artifacts" 불릿 — 부분 과잉 `[줄여도 안전(선별)]`

> "Optimize for the user's reading, not for trace dumping. Short paragraphs,
> grouped lists, compact traces."

짧은 문단, 묶인 목록, 흔적 덤프 금지는 프론티어 모델의 기본 작문 행동이다. 델타 없음.

> "When asking for approval or a material decision, use a compact block with one
> item per line: requested action, reason, scope/files, risk, rollback, and the
> exact choice needed."

승인 요청의 **내용 요소**(risk, rollback, 정확한 선택지)는 유지 가치가 있지만,
"one item per line" 같은 **형식 지정**은 판단층이다. 요소 목록만 남기고 형식 지시는
삭제 가능.

단, 같은 절의 사용자 언어 규칙(비영어 사용자 보호, 식별자 비번역)은
`[유지 — 암묵지]` — 모델이 지시 없이는 영어 아티팩트로 회귀하는 실패 모드가 실재한다.

### F1-2. §6 Completion — `execute-plan`과 이중 소유 `[줄여도 안전]`

"same action fails three times → stop, record, reassess" 규칙이 §6과
`skills/execute-plan/SKILL.md`("Same failure three times")에 **양쪽 다 조건까지
서술**되어 있다. CONVENTIONS의 "A rule has one owner; other files may reference
it but must not restate its conditions" 위반. 소유는 §6에 두고 execute-plan은
참조만 하거나, 실행 중 규칙이므로 execute-plan에 두고 §6에서 빼는 것이 맞다.
(권고: execute-plan 소유 — 발동 시점이 실행 중이다.)

그 외 §6의 evidence-surface 매칭, `INCONCLUSIVE ≠ PASS`, "subagent DONE is a
claim"은 레코드 층 핵심 — `[유지 — 암묵지]`. 특히 "tests alone never prove done"은
프론티어 모델도 지시 없이는 반대로 행동하는 대표적 지점이다.

### F1-3. §8 Instruction Priority 테이블 — 과잉 `[줄여도 안전]`

5행 테이블이지만 1행(현재 턴의 사용자 지시 최우선)과 5행(기본 행동 최하위)은 모든
프론티어 모델의 기본 우선순위와 동일하다. 델타가 있는 것은 3행 하나 — "현재 유닛의
`contexts.md`/아티팩트가 이 규칙 파일보다 위"라는 시스템 고유 결정. 테이블을 그
한 문장으로 대체할 수 있다.

### F1-4. §9 Skills 테이블 — 적정 (경계 사례)

각 스킬의 frontmatter description과 내용이 중복되지만, 컨트롤러가 파일을 열지 않고
라우팅하는 인덱스로서의 가치가 있고 행당 비용이 낮다. 유지 무방.

### 유지 확인 (삭제하면 안 되는 암묵지)

- §1 "if the user knows and you can just ask, that is requirements. If it has to
  be found in code, that is an issue." — 분류 경계의 핵심 암묵지. 이 한 문장이
  요구사항/이슈 오분류를 막는다.
- §2 "Size is not a criterion." — 프론티어 모델도 규모를 위험으로 오독한다.
- §2 "Present once; do not re-pitch." — 지시 없으면 모델은 재설득하는 경향이 있다.
- §7 이동/링크 규칙 전체 — 스크립트 게이트와 1:1 대응하는 레코드 층.

---

## safety-rules.md (75줄) — 판정: **적정**

전체가 레코드 층이다. 트러스트 바운더리, 고위험 게이트 목록, 이슈 read-only 기본값
모두 유지.

### 주목: H2/JPA 예시 문단 — `[유지 — 암묵지]`, 일반화만 고려

> "A local, test-only, reversible schema-like change — adding a JPA field for an
> in-memory H2 sandbox … is usually medium-risk"

특정 스택(JPA/H2) 예시가 범용 규칙 파일에 있는 것은 어색하지만, 이 문단이 담은
"schema라는 단어만 보고 전부 고위험으로 승격하지 말라"는 **과분류 방지 경계는
지시를 지우면 프론티어 모델이 안전 편향으로 복원해버리는(=전부 고위험 취급)
종류의 암묵지**다. 문단은 유지하되 예시를 스택 중립으로 바꾸는 것만 고려.

---

## record-commands.md (140줄) — 판정: **적정**

CLI 레퍼런스는 지시가 아니라 사실이다. 커맨드·플래그·거부 메시지 표는 스크립트
구현과 1:1이며, 예시 6개는 kind별 관례를 보여주는 최소량이다. Refusals 표는
스크립트가 거부했을 때 모델이 우회 대신 올바른 복구를 하게 하는 장치로 델타가
크다. 축약 불필요.

---

## 층 종합

| 파일 | 판정 | 조치 |
| --- | --- | --- |
| core-rules.md | 부분 과잉 | F1-1 형식 지시 삭제, F1-2 이중 소유 해소, F1-3 테이블→1문장 |
| safety-rules.md | 적정 | 예시 일반화만 선택적 |
| record-commands.md | 적정 | 없음 |

이 층에서 걷어낼 수 있는 양은 ~15줄 수준이다. 규칙 층은 리팩터링이 이미 잘 조여져
있다.
