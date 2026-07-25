# ③ 위임 프롬프트 7개 + quality reference 2개 리뷰

**이 층이 과잉의 잔존 질량이 집중된 곳이다.** v2 리팩터링이 규칙 층과 스킬 층은
재건했지만, 이 층의 일부 파일은 v1의 밀도와 v1의 어휘를 그대로 안고 넘어왔다.

잣대 보정: 서브에이전트 프롬프트는 메인 스킬과 델타 기준이 다르다. 자식은 대화
컨텍스트도 규칙 파일도 못 보므로 **자기완결적 재진술은 정당**하다(예: 트러스트
바운더리, 3건 캡의 6회 반복). 과잉 판정은 "자기완결에 필요한가"가 아니라 "프론티어
서브에이전트가 지시 없이도 할 판단인가"로 했다.

---

## plan-quality-reference.md (65줄) — 판정: **과잉 + v1 잔재. 이 리뷰의 최우선 개선 대상**

### F3-1. 자기모순: "reference"라 선언하고 게이트로 서술 `[줄여도 안전]`

헤더는 이렇게 선언한다:

> "This is a **reference, not a checklist to fill in**"

그런데 본문 첫 문단은:

> "Blocking checks (must cite concrete evidence — file/section/quote or concrete
> reason — **to pass**): Requirements coverage, … Policy restraint."

15개 항목을 "통과해야 하는 blocking check"로 지정하고, 개별 행에도 "A missing
`Decision Contracts` section … is a **blocking defect**" 같은 게이트 언어가 있다.
이는 합의된 설계(레코드 층 게이트는 스크립트가 소유, 품질 참조는 판단층)를
정면으로 위반한다 — **판단층 문서가 레코드 층 행세를 하는 사례.** write-plan
SKILL.md가 "Use it as a reference; there is no checklist to fill in"이라고 옳게
말하는 것과도 모순된다.

### F3-2. 템플릿에 존재하지 않는 구조를 요구 `[줄여도 안전 — 사실상 삭제 필수]`

다음 섹션/어휘를 blocking 조건으로 요구하지만 `templates/plan.md`에는 **어느 것도
정의되어 있지 않다**:

- `Decision Contracts` 섹션 (27행)
- `Dependency Analysis`, `Ordering Rationale` (28행)
- `Execution Design`과 `inline | subagent-driven | mixed` 모드 (32행)
- `Execution Surface` 섹션과 그 8개 하위 요건 (33행)
- `test-required` / `no-test` 태스크 어휘, `Test target` 필드 (35–36행)
- `Execution Task Index` (4태스크 이상 시, 40행)
- `Acceptance Criteria Coverage Matrix` (템플릿의 실제 명칭은
  `Acceptance Criteria Coverage`, 26행)
- 태스크 간 `Produces`/`Consumes` 명명 (31행)

v1 플랜 템플릿의 구조를 전제한 채 참조 문서만 살아남은 것이다. 이대로면 리뷰를
수행하는 모델이 (a) 존재하지 않는 섹션의 부재를 결함으로 오판하거나 (b) 템플릿에
없는 구조를 플랜에 역주입한다 — **참조 문서가 템플릿을 다시 비대하게 만드는
경로**다.

### F3-3. 사어휘(v1 이벤트 표기) `[삭제 필수 — 과잉 이전에 오류]`

> 36행: "record through `verification.recorded` or `task.completed` events"
> 38행: "record `approval.high_risk` events"

현행 스크립트 어휘는 평면형 12종(`verification`, `work`, `approval` +
`--action high-risk`)이다. 점 표기 이벤트는 존재하지 않는다. CLAUDE.md
ANTI-PATTERNS의 "제거된 표면 재도입 금지" 정신에 걸리는 잔재.

### F3-4. 프론티어 기본 판단과 고유 규약의 혼재 `[줄여도 안전(선별)]`

24개 카테고리 중 상당수는 "좋은 계획을 비판적으로 읽어라"만으로 프론티어 모델이
스스로 확인하는 것들이다: No placeholders, File surface, Consistency, YAGNI,
Human readability류. 반면 지시 없이는 복원되지 않는 고유 규약도 섞여 있다:

- Progress-ledger restraint (plan.md에 진행 상태 금지) `[유지]`
- Policy restraint (합의 안 된 commit/release 정책 결정 금지) `[유지]`
- Executor readiness (chat memory 없이 실행 가능해야) `[유지]`
- Source traceability (contexts.md로의 추적) `[유지]`
- Safety gate coverage의 과분류 방지 단서 `[유지]`
- User-language 규칙 — 유지하되 2개 항목(45–46행)이 사실상 같은 내용, 1개로 통합

**권고**: 이 파일을 requirements-quality-reference.md와 같은 형태(게이트 언어
없는 품질 서술, 현행 템플릿의 섹션만 언급)로 재작성. 고유 규약 6~8항목 중심으로
절반 이하 분량이 적정선이다.

---

## requirements-quality-reference.md (53줄) — 판정: **부분 과잉**

plan 참조와 달리 헤더-본문이 일관되고("reference, not a gate") 사어휘도 없다.
17개 카테고리 중:

- `[유지]`: Source traceability, Assumptions(무표기 가정 차단), None/N/A handling
  (없음을 지어내지 않기), Affected surface, 언어 규칙, "Do not write a review
  status block … Improving the document is the entire output."
- `[줄여도 안전]`: Completeness, Human readability, Consistency, Boundary
  clarity, YAGNI — "사용자와 플래너가 의지할 문서를 써라"는 목적만으로 프론티어
  모델이 도달하는 판단. 절반 축약 가능하나 plan 참조보다 우선순위 낮음.

---

## code-reviewer-prompt.md (99줄) — 판정: **부분 과잉 + 사어휘**

자기완결 정당성이 가장 큰 파일(별도 리뷰어에게 통째로 전달)이므로 밀도 자체는
수용 가능하다. 개별 판정:

- `[유지 — 암묵지]`: "blocker-finder, not a perfectionist" 정체성, adversarial
  falsification 프레임, Finding Quality Gate 4문항, 3건 블로킹 캡 + "Never hide a
  finding to satisfy this cap", speculative-noise 금지 4항목. 전부 리뷰 노이즈라는
  실제 실패 모드를 막는 규약이다.
- F3-5. 사어휘 `[삭제 필수]`: 41행 `verification.recorded` / `task.completed`,
  48행 `approval.high_risk` → 현행 어휘(`verification` verdict 이벤트, `approval
  --action high-risk`)로 교체.
- F3-6. 템플릿 미정의 구조 참조 `[줄여도 안전]`: 40행 "task-level Test Strategy",
  42행 "RED/GREEN … evidence" — F3-2와 같은 v1 전제. implementer 정책 결정(F3-8)과
  묶어 정리해야 한다.
- 소폭: 36행 고위험 목록이 safety-rules.md 목록의 전문 복제다. 자기완결상 목록이
  필요하다면 유지 가능하나, 컨트롤러가 디스패치 시 safety-rules.md 경로를 함께
  주는 방식이면 요약으로 줄일 수 있다. 선택 사항.

## task-reviewer-prompt.md (58줄) — 판정: **적정, 소폭**

구조가 간결하고 receipt 계약이 명확하다. 23행 "Required RED/GREEN … evidence"만
F3-6과 동일 계열 — implementer 정책 결정에 따라 함께 정리.

## implementer-prompt.md (40줄) — 판정: **부분 과잉 — 설계 결정 필요**

### F3-8. 테스트 기법 하드코딩 vs 판단층 선언의 충돌

> "If the task is a bug fix, first write a regression test that fails against
> the current code (report that RED evidence), then implement the fix…"
> "Use `no-test` only when the controller's task specifies it…"

CLAUDE.md와 core-rules §4는 "how tasks are tested"를 명시적으로 판단층에
두었는데, 이 프롬프트는 버그픽스에 TDD(RED→GREEN)를 기법 수준으로 지정하고
`test-required`/`no-test` 어휘(플랜 템플릿 미정의)를 계약으로 삼는다. **판단층
항목이 위임 프롬프트 안에서 레코드 층처럼 굳은 사례**다.

두 가지 정리 방향이 있고, 이는 개선 작업에서 결정할 사항이다:

1. **위임안(권고)**: 요구를 증거 수준으로 낮춘다 — "버그픽스는 수정 전 실패를
   보여주는 회귀 증거를 남겨라"(결과 요구)로 바꾸고 기법(테스트 먼저 작성)은
   서브에이전트 판단에 맡긴다. `no-test` 어휘는 "컨트롤러가 검증 방법을 지정하며,
   지정이 없으면 BLOCKED로 반환"으로 대체.
2. **정합안**: 어휘를 유지하려면 `templates/plan.md`에 Test Strategy 필드를
   정식으로 정의해 ③층과 ④층을 일치시킨다. (템플릿이 다시 무거워지는 방향이므로
   비권고.)

그 외 — `NEEDS_CONTEXT`/`BLOCKED` 반환 계약, "DONE is a claim", receipt-only
출력은 `[유지]`. 위임 계약의 핵심이다.

## cleanup 4종 (reuse/simplification/efficiency/abstraction, 각 ~30줄) — 판정: **적정**

각 프롬프트가 렌즈 경계(무엇을 보고 무엇을 보지 않는가)와 receipt만 담은 최소형.
3건 캡의 4회 반복은 자기완결상 정당하다. 한 가지 소폭: "If no safe X exists,
create the file with `verdict: passed`"는 review-execution SKILL의 "When there
are no findings, record that; do not create an empty review.md"와 미세하게
어긋난다(렌즈는 무발견도 파일 생성). 의도된 차이라면 무방하나 개선 작업 시 한번
확인할 것.

---

## 층 종합

| 파일 | 판정 | 조치 |
| --- | --- | --- |
| plan-quality-reference.md | **과잉 + v1 잔재** | 재작성: 게이트 언어 제거, 미정의 섹션 제거, 사어휘 교체, 고유 규약 중심 절반 이하로 |
| requirements-quality-reference.md | 부분 과잉 | 절반 축약(우선순위 낮음) |
| code-reviewer-prompt.md | 부분 과잉 | 사어휘 교체, Test Strategy 참조 정리 |
| task-reviewer-prompt.md | 적정 | RED/GREEN 참조만 F3-8과 연동 |
| implementer-prompt.md | 부분 과잉 | F3-8 설계 결정(위임안 권고) |
| cleanup 4종 | 적정 | 무발견 시 파일 생성 정책 확인만 |
