# 프롬프트 전수 리뷰 — 종합 보고서

작업일: 2026-07-25
대상: 런타임 프롬프트 표면 전체 4개 층, 약 4,200줄
잣대: **Opus 5 / GPT 5.6급 프론티어 모델이 이 지시 없이도 같은 판단에 도달하는가의
델타.** 레코드 층(7대 규칙, 스크립트 게이트)은 게이트 자체가 아닌 표현만 심사하되,
판단층이 레코드 층으로 위장한 문장은 적발. 각 finding에 삭제 위험
(`[줄여도 안전]` / `[유지 — 암묵지]`)을 표시.

층별 상세: [01-rules.md](01-rules.md) · [02-skills.md](02-skills.md) ·
[03-delegation-prompts.md](03-delegation-prompts.md) · [04-templates.md](04-templates.md)

---

## 한 줄 결론

**리팩터링은 성공했다 — 규칙 층과 스킬 층은 프론티어 모델 기준으로 이미 잘 조여져
있다. 과잉의 잔존 질량은 ③ 위임 프롬프트 층, 특히 `plan-quality-reference.md`
한 파일에 집중되어 있으며, 그 파일은 과잉이기 이전에 v1 잔재(사어휘, 폐기된 플랜
구조 전제)라서 이번 개선 작업의 최우선 대상이다.**

## 판정 분포

| 층 | 파일 수 | 적정 | 부분 과잉 | 과잉 |
| --- | --- | --- | --- | --- |
| ① as-usual-rules | 3 | 2 | 1 (core-rules) | 0 |
| ② skills | 15 | 12 | 3 (gathering-context, git-action, explore-codebase) | 0 |
| ③ 위임 프롬프트·참조 | 9 | 5 | 3 | **1 (plan-quality-reference)** |
| ④ templates | 7 | 7 | 0 | 0 |

## 개선 후보 — 우선순위 순

### P1. plan-quality-reference.md 재작성 (F3-1~F3-4)

과잉·자기모순·사어휘·템플릿 불일치가 한 파일에 겹친다. "reference, not a
checklist"라 선언한 뒤 15개 "blocking check"를 지정하고, `templates/plan.md`에
존재하지 않는 8종 섹션/어휘(`Decision Contracts`, `Execution Design`,
`Execution Task Index`, `test-required`/`no-test` 등)를 통과 조건으로 걸며,
폐기된 v1 이벤트 표기(`verification.recorded`, `task.completed`,
`approval.high_risk`)를 참조한다. 게이트 언어 없는 품질 서술로, 현행 템플릿
기준으로, 고유 규약(Progress-ledger/Policy restraint, Executor readiness,
Source traceability, 과분류 방지) 중심 절반 이하 분량으로 재작성.

### P2. 사어휘 일소 (F3-3, F3-5)

`code-reviewer-prompt.md` 41·48행의 점 표기 이벤트를 현행 어휘로 교체. 기계적
수정이며, `verify-as-usual-harness`의 removed-surfaces 검사에 이 패턴을 추가하면
재발이 막힌다.

### P3. implementer-prompt의 테스트 정책 — 설계 결정 필요 (F3-8)

CLAUDE.md가 판단층으로 선언한 "how tasks are tested"를 이 프롬프트가 TDD 기법
수준으로 하드코딩하고, 템플릿에 없는 `Test Strategy`/`test-required` 어휘를
계약으로 쓴다(task-reviewer·code-reviewer의 RED/GREEN 참조도 동일 계열).
권고는 **위임안**: 증거 요구(버그픽스는 수정 전 실패 증거)만 남기고 기법은
서브에이전트 판단에 맡긴다. 대안은 템플릿에 어휘를 정식 정의하는 정합안이나,
템플릿이 되비대해지므로 비권고.

### P4. 하드코딩 한국어 리터럴 3곳 (F2-0b)

`write-plan`, `review-execution`, `finalize`의 사용자 발화 예시를 "in the user's
language" 지시로 교체. 비한국어 사용자에게 언어 규칙과 모순 신호를 준다.

### P5. Anti-Patterns 목록 선별 축약 (F2-0)

11개 스킬 ~100줄 중 본문 단순 반전은 삭제, 교차 파일 규칙·관찰된 실패 모드만
스킬당 3~5개 유지. 예상 절감 ~50줄. 전량 삭제는 비권고(말미 부정형 요약의
salience 가치).

### P6. 이중 소유 해소 (F1-2, F2-3, F2-5)

- 3회 실패 규칙: core-rules §6과 execute-plan 양쪽 서술 → execute-plan 소유로.
- requirements/plan 섹션 표: 스킬과 템플릿 주석 양쪽 서술 → 템플릿 소유로.
- contexts.md 3밴드 규칙 3중 진술 → core-rules 소유, gathering-context 축약.

### P7. 숫자 미세관리·기본 행동 명문화 제거 (F1-1, F1-3, F2-1, F2-4, F2-6)

- gathering-context "1 to 5 at a time" → 원칙만.
- git-action "3+ files → 2 commits" 휴리스틱 → 원칙만.
- core-rules §8 우선순위 테이블 → 델타 있는 1문장으로.
- core-rules §3 작문 형식 지시 → 요소 목록만.
- explore-codebase `<analysis>` 재진술 블록 → `<results>`만.

### P8. requirements-quality-reference 축약 (낮음)

프론티어 기본 판단 항목(Completeness, Consistency, YAGNI류) 정리. P1과 같은
문제의식이나 게이트 언어·사어휘가 없어 급하지 않다.

## 교차 패스에서 확인한 공통 패턴

1. **과잉은 층이 아니라 세대의 문제였다.** v2에서 재건된 파일(오너 스킬, 템플릿,
   규칙)은 거의 전부 적정 판정이고, v1에서 이월된 파일(quality reference, 실행기
   프롬프트)에 과잉이 몰려 있다. run-topic(69줄)이 도달점의 기준이다.
2. **자기완결 재진술은 정당, 이중 소유는 부당.** 서브에이전트 프롬프트의 반복
   (3건 캡 ×6, 트러스트 바운더리)은 자식이 규칙을 못 읽으므로 유지했고, 같은
   컨트롤러가 읽는 두 파일의 조건 재진술(F1-2, F2-3)만 위반으로 판정했다.
3. **지우면 안 되는 것들은 대부분 한 문장이다.** "tests alone never prove done",
   "Size is not a criterion", "Naming it here does not grant permission",
   "Retract promptly", 과분류 방지 단서 — 개선 작업에서 문단을 걷어낼 때 이
   문장들이 함께 쓸려나가지 않도록 층별 보고서의 `[유지 — 암묵지]` 표시를 확인할 것.

## 부수 발견 (과잉 아님, 개선 작업 시 함께)

- `run-direct-work` 파이프라인 다이어그램에 `cleanup-code?` 누락(표에는 있음).
- cleanup 4종 프롬프트의 "무발견 시에도 review.md 생성"이 review-execution
  SKILL·review 템플릿의 "무발견은 이벤트만, 빈 파일 금지"와 미세 충돌.
- P2 수용 시 removed-surfaces 검사에 점 표기 이벤트 패턴 추가.

## 예상 효과

P1~P7 적용 시 표면 전체에서 약 250~350줄(~7%)이 줄지만, 줄 수보다 중요한 효과는
(a) 참조 문서가 템플릿에 폐기 구조를 역주입하는 경로 차단, (b) 판단층 선언과 위임
프롬프트의 실제 요구 일치, (c) 단일 소유 관례의 회복이다.
