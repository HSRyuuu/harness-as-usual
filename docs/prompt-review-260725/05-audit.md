# Phase 0 — 과완화 감사 결과

작업일: 2026-07-25
상태: **완료.** 7개 그룹 전수 대조 + high 등급 원문 검증 + 순방향 커버리지 완료.

기준: [final-plan.md](final-plan.md) Phase 0.
BEFORE 스냅샷: `.claude/before-refactor/` (HEAD = `2f5ba31`, v2 첫 커밋 직전).
BEFORE 인용의 파일 경로는 모두 이 스냅샷 기준이다.

---

## 세 줄 결론

1. **41% 축소의 절대다수는 의도대로 판단층을 걷어낸 것이다.** 약 230건의
   record/safety 항목을 추적해 생존 214건, 유실 16건. 게이트를 무너뜨리는 high는
   4건뿐이다.
2. **유실은 무작위가 아니라 한 패턴이다** — 짝을 이루던 두 문장 중 완화 방향만
   남고 보수 방향이 함께 삭제되었거나, 삭제된 경로에 걸려 있던 가드레일이 그
   경로의 후계자로 이사하지 못했다.
3. **이전 리뷰의 P1·P2·P3는 이미 완료되었다** (커밋 `b1df7d1`). 리뷰 문서는 그
   커밋 이전 상태를 기술하고 있어 해당 항목은 계획에서 제외해야 한다. → 아래
   "리뷰 문서의 시효" 참조.

---

## 진행 상황

| 그룹 | 범위 | BEFORE→AFTER | 유실 |
| --- | --- | --- | --- |
| A | templates 9종 | 562 → 305 | 1 (low) |
| B | define-requirements·writing-plan | 800 → 330 | 2 (high 1) |
| C | executing-plan | 416 → 153 | 3 (high 1) |
| D | 규칙 층 7파일→3 | 761 → 458 | 3 (high 1) |
| E | review-execution·cleanup-code | 568 → 263 | 3 |
| F | 진입점·유닛 오너 | 502 → 523 | 2 (high 1) |
| G | finalize·git-action·유틸 | 569 → 391 | 3 |

각 그룹은 BEFORE 전문을 읽고 record/safety 항목을 추출한 뒤, 현행 표면 전체
(`as-usual-rules/`, `skills/`, `templates/`, `scripts/as_usual_record/`)를 검색해
대응처 부재를 확인했다. high 4건과 medium 1건은 이후 원문 대조로 재검증했다.

---

## 리뷰 문서의 시효 — 계획 수정이 필요한 발견

`docs/prompt-review-260725/`의 리뷰는 커밋 `b1df7d1`(07-25 17:46,
"rewrite the skills and prompts the v2 pass left untouched") **이전** 상태를
대상으로 작성되었다. 그 커밋이 이미 수행한 것:

| 이전 계획 | 상태 | 근거 |
| --- | --- | --- |
| **P1** plan-quality-reference 재작성 | **완료** | 현재 61줄, "reference, not a checklist to fill in" 선언, 인용 섹션 전부 실재, blocking check 0개. 커밋 메시지 "plan-quality-reference realigns with the v2 plan template" |
| **P2** 사어휘 일소 | **완료** | `Decision Contracts`·`Execution Design`·`Execution Task Index`·`test-required`·`no-test`·`verification.recorded`·`task.completed`·`approval.high_risk` → 런타임 표면 히트 **0건** |
| **P3** implementer-prompt 테스트 정책 위임안 | **완료 (부작용 있음)** | 현재 프롬프트에 TDD/RED-GREEN·`test-required` 없음. 다만 기법과 함께 **증거 요구까지 제거**되어 R-06을 낳았다 |
| **P7** git-action 숫자 휴리스틱 | **완료** | 커밋 `11eb805` |

**남은 이전 계획은 P4·P5·P6·P8과 P7 잔여(gathering-context 숫자,
explore-codebase `<analysis>`)뿐이다.** 단 explore-codebase는 `b1df7d1`에서
109줄이 삭제되며 이미 정리되었고, 그 과정에서 R-10·R-15를 낳았다.

교훈: 이번 감사의 진짜 대상은 v2 리팩터링만이 아니라 **`b1df7d1`까지 포함한
전체 축소**였다. 이 커밋은 하루 전 리뷰가 "과잉"이라 지목한 파일들을 그대로
잘라냈고, 유실 16건 중 최소 5건(R-03·R-06·R-08·R-10·R-15)이 이 커밋에서 나왔다.

---

## 사용자 결정이 필요한 항목 — 승인 경계 완화

R-항목이 아니다. **조용한 삭제가 아니라 명시적으로 다시 쓰인 정책 변경**이므로
유실로 분류하지 않았으나, 이번 리뷰의 렌즈("제한을 너무 풀어둔 것이 아닌가")에
가장 정확히 걸리는 단 하나의 지점이다.

**BEFORE** (`skills/review-execution/SKILL.md:114-122`):

> | Critical | `fixed` (and re-reviewed to passed), `rejected` (with technical reason, re-reviewed to passed), `blocked` |
> | Important | (동일) |
> | Minor | `fixed`, `rejected`, `deferred`, `user-accepted-risk` |
>
> `user-accepted-risk` and `deferred` are never valid for Critical or Important
> findings. If the user declines to fix a Critical or Important finding, the
> topic finalizes as `blocked`.

**AFTER** (`skills/review-execution/SKILL.md:64-71`):

> Every Critical and Important finding reaches one of these before the work closes:
> - **fixed** … - **rejected** … - **accepted by the user** — the user was told
>   the risk in plain terms and chose to ship anyway.

즉 **Critical 발견에 대해 이전에는 존재하지 않던 통과 경로가 생겼다.** 이전에는
사용자가 수정을 거부하면 유닛이 `blocked`로 종료되는 것 외에 길이 없었다.

주의: 이전 리뷰(02-skills.md)는 이 문장을 `[유지]`로 판정하며 "삭제 시 복원
불가능한 규약"이라 평했는데, **이것이 새로 완화된 조항이라는 사실을 놓쳤다.**
BEFORE와 대조하지 않으면 보이지 않는 종류의 변화다.

판단이 필요하다 — 의도한 완화라면 그대로 두고, 아니라면 Critical만이라도
`blocked` 경로를 복원한다.

---

## R-항목 (16건)

### High — 게이트·권한 경계 유실 (4건, 전부 원문 검증 완료)

#### R-01. 무기록 경로("just do it")의 고위험 작업 절대 거부 ✅검증됨
- BEFORE: `skills/direct-execute/SKILL.md:95` — "**High-risk operation
  present**: refuse direct execution. … **Do not offer a confirmation that can
  override the refusal.**" / `:56` — "The high-risk operation definition in
  `as-usual-rules/safety-rules.md` is a hard gate. **High-risk work is never
  allowed through either entry path.**" / anti-pattern — "Allowing a high-risk
  operation after confirmation." / `as-usual-rules/core-workflow.md:25` — "**no
  confirmation may allow a high-risk operation**"
- 층: safety · 출처: 그룹 F·D 중복 지목 (교차 검증)
- **검증 결과**: 현행 `safety-rules.md:3-5`는 적용 범위를 "every AsUsual work
  unit shares — `topic`, `direct-work`, and `issue` alike"로 **명시 한정**하고,
  `core-rules.md` §2는 "4. just do it — no harness. No folder, no record."를
  제시하며 "If the user picks something other than your recommendation, follow
  it without arguing"라고만 한다. `core-rules.md`와 `using-as-usual/SKILL.md`의
  분류 트리 전체에서 `high-risk` 언급은 **rule 2 한 줄뿐**이며 4번 옵션에
  단서가 없다. 확인으로 뒤집을 수 없던 권한 경계가 통째로 사라졌다.
- 제안: `safety-rules.md` 게이트 도입부의 범위를 work unit에서 "AsUsual이
  관여하는 모든 요청"으로 확장 + `core-rules.md` §2 4번 옵션에 예외 한 줄.

#### R-02. 위험도 분류의 안전측 기본값 (unknown → high) ✅검증됨
- BEFORE: `skills/writing-plan/SKILL.md:154` — "If the task may run against
  persistent user data, shared environments, or an unknown database, classify
  it as high risk **until clarified**."
- 층: safety · 출처: 그룹 B
- **검증 결과**: BEFORE는 3단 보정이었다 — ①high 목록 ②로컬/테스트는 medium
  ③**불확실하면 high**. 현행 `safety-rules.md:34-54`는 ①과 ②만 옮겨왔다.
  `until clarified|unknown database|persistent user data|shared environment|
  when in doubt|if unsure` 전수 검색 **히트 0건**. 불확실할 때의 판정 방향을
  말하는 문장이 표면에 하나도 없고, 이 판정이 곧 core rule 2의 발동 여부다.
- 제안: `safety-rules.md` 하향 보정 문단(L49-54) 직후 한 문장.

#### R-03. 서브에이전트 위임 계약의 안전 정보 ✅검증됨
- BEFORE: `skills/executing-plan/implementer-prompt.md:14` — "- **Safety notes
  and high-risk approval status:**" (컨트롤러 필수 입력 필드) / 같은 파일 계약
  정의 — "SCOPE = relevant files/areas **and safety notes**"
- 층: safety · 출처: 그룹 C
- **검증 결과**: 현행 계약은 `TASK`/`SCOPE`/`VERIFY`/`CONTEXT` 4개이고 SCOPE는
  `{RELEVANT_FILES_AND_LIMITS}`로 안전 항목이 없다. 금지 목록은 "Do not commit,
  push, open a PR, release, or deploy" 한 줄로 **git 계열만** 덮는다. 파일
  삭제·의존성 변경·DB 마이그레이션·시크릿 변경·CI/CD 변경은 자식에게 전달되지
  않는다. 고위험 게이트는 컨트롤러 규칙인데 실제 조작 주체는 서브에이전트이므로,
  위임 지점에서 승인 경계가 무력화된다.
- 제안: `implementer-prompt.md`에 `SAFETY:` 항목 추가 + 미승인 고위험 조작
  조우 시 `BLOCKED` 반환 규칙. `execute-plan/SKILL.md:56-57` 나열에도 반영.

#### R-04. `issue` 종료의 "확정 항목 최소 1건" 게이트 ✅검증됨
- BEFORE: `as-usual-rules/find-cause-workflow.md:71-73` — "`journal-log.py
  conclude` **requires at least one confirmed entry**, and
  `--force-without-confirmed` requires a recorded `--reason`."
- 층: record · 출처: 그룹 D
- **검증 결과**: 현행 `gates.py:161-166` `_check_finalize`는 `unit == "issue"`일
  때 `conclusion.md`의 **존재만** 검사한다. 확정 항목 유무는 보지 않으므로,
  가설을 하나도 확정하지 않은 추측 결론으로 finalize가 통과한다. BEFORE에서
  `issue`의 core rule 3에 해당하던 유일한 기계 게이트였다. 재현 불가로 확정할
  수 없을 때 이유를 남기고 닫던 명시적 탈출구(`--force-without-confirmed
  --reason`)도 함께 사라져, 그 상황이 기록에 구분되지 않는다.
- 제안: `gates.py::_check_finalize`에 기계적 복원(최선). 산문이면
  `run-issue/SKILL.md` Concluding.

### Medium — 지속 증거·기록 무결성 (6건)

#### R-05. 빈 승인 표현을 material question의 답으로 기록 금지
- BEFORE: `skills/define-requirements/SKILL.md:73` — "Do not treat a bare
  approval phrase such as `ㄱㄱ`, `go`, `진행`, `ok`, or `yes` as an answer to a
  material question." (`:135`, `:146`, `:331` 반복)
- 층: record · 출처: 그룹 B
- 특기: **리팩터링이 이 위험을 키웠다.** `gathering-context/SKILL.md:35`가 모든
  질문에 추천안을 붙이도록 요구하므로 "ㄱㄱ"를 추천안 채택으로 읽을 여지가 상시
  존재한다. 남은 방어선(`:92` "Do not answer your own question")은 "질문 미해결"
  을 전제하므로 답으로 **오인한** 경우를 못 잡는다.
- 제안: `gathering-context/SKILL.md` How To Ask 또는 Stop Conditions.

#### R-06. 버그 수정의 수정-전 실패 재현 증거
- BEFORE: `skills/executing-plan/SKILL.md:56` — "For a bug fix, also require
  regression RED evidence (a failing test that reproduces the bug before the
  fix)." (`:203`, `:207`, `:213`, `implementer-prompt.md:21`,
  `task-reviewer-prompt.md:23`)
- 층: record (기법 아닌 **증거**) · 출처: 그룹 C
- 특기: **P3(`b1df7d1`)의 부작용이다.** 기법(TDD/RED-GREEN)을 걷어내면서 증거
  요구까지 함께 제거됐다. 현행 최근접은 `templates/plan.md:33-34` "must exercise
  the changed behavior"인데 시간 순서를 요구하지 않는다. `issue`는
  `gates.py:138-142`가 `confirmed`에 `--evidence`를 강제하는데 그 원인을 고치는
  실행 단위에는 수정-전 실패 증거 요구가 없는 **비대칭** 상태다.
- 제안: `core-rules.md` §6에 한 줄 + `implementer-prompt.md`의 VERIFY.

#### R-07. 리뷰 독립성의 기록과 self-review 위장 금지
- BEFORE: `skills/review-execution/SKILL.md:208-214` — 리뷰 모드
  (`independent`/`self`/`local-prompt`) + "**Use the actual mode. Do not imply
  independent review when the host only allowed self-review.**"
- 층: record · 출처: 그룹 E
- 왜: 행위 규칙("The implementer does not clear their own work", 현행 `:34`)은
  남았으나 **지켜졌는지가 기록에 남지 않는다.** 새 세션이 리뷰 강도를 판단할 수
  없고, 인라인 self-review를 독립 리뷰처럼 적어도 금지하는 문장이 없다.
- 제안: `review-execution/SKILL.md` Recording (`--data mode=…`) 또는
  `templates/review.md`에 "Reviewed by" 한 줄.

#### R-08. 리뷰어 서브에이전트의 high-risk 자기완결성
- BEFORE: `skills/review-execution/code-reviewer-prompt.md:36-37` — high-risk
  조작 열거 + "Do not over-classify local/test-only reversible schema-like code
  changes as high risk" / `:49` 승인 이벤트 필수 내용(operation, approver,
  rollback)
- 층: safety · 출처: 그룹 E
- 왜: 현행은 "each high-risk operation has a fresh `approval` event"만 지시하는데
  **서브에이전트는 `safety-rules.md`를 읽을 수 없다.** 판정 기준 없이 게이트를
  검증하라는 요구라 양방향 오류(누락 놓침 / 과잉분류로 잘못된 Critical)가 난다.
- 제안: `code-reviewer-prompt.md`에 high-risk 축약 목록 + 과잉분류 금지 인라인.

#### R-09. 무기록 경로가 활성 유닛의 범위를 침범하는 것 방지 ✅검증됨
- BEFORE: `skills/direct-execute/SKILL.md:96` — "Recordless direct entry **may
  not silently change files that an active topic's `audit.jsonl` makes claims
  about**, because that desyncs the topic record from the working tree and
  breaks later hand-off/resume. … **This is a hard route, not an ask-once
  confirmation.**"
- 층: record · 출처: 그룹 F
- 왜: AsUsual의 존재 이유("새 세션이 디스크에서 이어받는다")를 직접 깨뜨린다.
  열린 유닛이 주장하는 파일이 무기록으로 바뀌면 기록이 워킹 트리와 어긋난 채
  봉인된다. `using-as-usual`의 "verify before trusting"은 발견은 해도 발생을
  막지 못한다.
- 제안: `core-rules.md` §2 4번 옵션 + `using-as-usual/SKILL.md` 선택 제시부.

#### R-10. explore-codebase 서브에이전트의 시크릿 금지
- BEFORE: `skills/explore-codebase/SKILL.md:50-52` — "No internet. **No
  secrets**: if relevant, report only sanitized path-level findings."
- 층: safety · 출처: 그룹 G (`b1df7d1`에서 109줄 삭제 시 유실)
- 왜: 자식은 `safety-rules.md`를 읽을 수 없는데 현행 `Hard Limits`에 시크릿
  조항이 없다. `.env`·자격증명·토큰을 그대로 인용해 컨트롤러 컨텍스트로
  올려보내는 것을 막는 문구가 브리프에 없다.
- 제안: `explore-codebase/SKILL.md` `## Hard Limits` 한 줄.

### Low — 게이트 없는 유용한 제약 (6건)

- **R-11. 승인 이벤트의 `--actor user` 귀속** (그룹 C). `--actor` 기본값은
  `claude`(`cli.py:48`)인데 어떤 스킬도 승인에 `user`를 쓰라고 하지 않아
  `ACTORS`의 `user`가 고아 어휘가 되고, "사용자가 승인했다"가 구조화 필드로
  남지 않는다.
- **R-12. 리뷰 문서 verdict와 기록 이벤트의 일치 요구** (그룹 D,
  `logging-rules.md:26`). 파일이 `clean`인데 이벤트 요약은 findings인 상태가
  위반이 아니게 되었다.
- **R-13. diff 불가 시 대체 경로와 한계 기록** (그룹 E,
  `review-execution/SKILL.md:47`). 현행은 전제조건으로만 바뀌어, 전제가 깨졌을
  때의 지시도 기록 요구도 없다.
- **R-14. git action 선택의 typed approval 이벤트화** (그룹 G). 현행은
  `--kind decision`으로만 기록해 `status --json`의 `approvals`에 나타나지
  않는다. `APPROVAL_ACTIONS`의 `git-action`이 고아 어휘가 되었다.
- **R-15. explore-codebase 출력의 `UNTRUSTED` 자기 표기** (그룹 G).
  자매 스킬 `search-long-term-memory:22`는 래퍼를 유지하고 있어 비대칭.
- **R-16. AC별 증거/단언 매핑** (그룹 A). BEFORE `templates/plan.md:38-51`의
  표 컬럼 `Evidence` / `Assertion`이 사라지고 `Covered By`만 남았다. AC→Task→
  Task Verification의 이행적 연결이 상당 부분 커버하므로 low.

---

## 순방향 커버리지 — 7대 규칙의 소유자와 집행 수단

| # | 규칙 | 소유 | 집행 | 상태 |
| --- | --- | --- | --- | --- |
| 1 | 스크립트 전용 기록 | `core-rules.md:126` | 프롬프트 + `validation.py` 사후 감사 | 정상 |
| 2 | 고위험 즉시 승인 | `safety-rules.md:34` | 프롬프트 | **범위 결함 (R-01)** |
| 3 | 완료엔 검증 증거 | `core-rules.md:131`, §6 | verdict enum만 | **절반 (아래)** |
| 4 | git은 명시적 선택만 | `core-rules.md:134`, `git-action` | 프롬프트 | 정상 (R-14는 가시성) |
| 5 | 트러스트 바운더리 | `safety-rules.md:7` | 프롬프트 | 위임 시 누수 (R-08·R-10) |
| 6 | 유닛 결정 전 작업 금지 | `core-rules.md:138` | `init --unit` 필수 | **주장 과장** |
| 7 | 실행 승인 전 계획 리뷰 | `core-rules.md:140` | `gates.py:_check_approval` | **완전 집행** |

**규칙 3 — 절반만 기계화.** `gates.py`에서 `verification`은 verdict를 강제하고
enum 밖 값을 거부하므로 `INCONCLUSIVE`를 `PASS`로 위장할 수는 없다. 그러나
**완료 선언 전에 verification 이벤트가 존재하는지는 어디서도 검사하지 않는다**
(`_check_finalize`는 `issue`의 `conclusion.md`만 본다). `topic`/`direct-work`는
검증 0건으로 `finalized` 기록이 가능하다.

**규칙 6 — 간접 집행, 주장은 과장.** `init --unit`이 필수라 유닛 없는 기록은
못 만들지만 `inbox`도 유효값이고, 코드 수정 자체는 스크립트가 관측할 수 없다.

**주장 목록이 실제 게이트보다 좁다.** `core-rules.md:144-145`가 열거하지 않지만
실제로 집행되는 것: 어휘 폐쇄(unit/kind/actor/status/phase/nextAction), 유닛별
phase 부분집합, `confirmed`의 `--evidence` 필수, `cancelled`의 `--reason` 필수,
`issue`의 `conclusion.md` 필수.

`python3 -m pytest scripts/tests/ -q` → **54 passed.**

---

## 부수 발견

### 댕글링 참조 6곳 — 전부 `requirements-quality-reference.md`

현행 `templates/requirements.md`의 실재 섹션은 6개다: `Goal`:9 · `Scope`:13
(`In Scope`:15 / `Out Of Scope`:19) · `Requirements`:23 ·
`Constraints & Assumptions`:29 · `Risks`:38 · `Acceptance Criteria`:43.

| # | 참조 | 인용 대상 | 조치 |
| --- | --- | --- | --- |
| D-1 | `requirements-quality-reference.md:25` | `Domain Requirements` | 부재 → 참조를 `Requirements`로 재작성 |
| D-2 | `:31` | `Affected Surface` | 부재 → **판단 필요.** 내용은 `Out Of Scope`·`Constraints`에 산개 흡수됐으나 "코드 대면 작업에서 영향 파일·기존 동작을 명시하라"는 강제력은 사라짐 |
| D-3 | `:27` | "domain requirements, functional requirements" | 부재 → 재작성 |
| D-4 | `:30` | `Assumptions` | 이름 불일치 → `Constraints & Assumptions` |
| D-5 | `:34` | `NFRs`, "affected files" | 부재 → 재작성 |
| D-6 | `:20` | "no **empty required section** remains" | **정책 충돌** — `templates/requirements.md:4-6`과 `write-requirements/SKILL.md:41-43`은 빈 섹션을 **삭제하라**고 지시 |

`plan-quality-reference.md`는 **깨끗하다** (P1 완료 확인).

### 기타

1. **빈 `review.md` 충돌 잔존.** `cleanup-code/SKILL.md:69-70`이 조건 없이
   "Append the cleanup outcome as a section in `review.md`"라고 지시해,
   `review-execution/SKILL.md:62`·`templates/review.md:7,40`("do not create an
   empty `review.md`")과 어긋난다. `:69`에 "적용한 변경이 있을 때만" 한 구절이면
   해소.
2. **`manage-self-improvement/references/*`의 사어휘.** `memory-update.md:15`,
   `skill-improvement.md:28,47`이 제거된 `record-memory-candidate`,
   `record-skill --state`, `--brief`를 지시한다. 두 파일은 v2에서도 `b1df7d1`
   에서도 손대지 않아 46/48줄 그대로다 — **P2의 유일한 잔여물.**
3. **`write-requirements/SKILL.md:73-74`**가 "the Decisions section"을 가리키나
   `requirements.md` 템플릿에 없다. R-05의 보상 장치가 여기 걸려 있다.
4. **경계 항목(미보고).** `hand-off:84`의 "Only a `spec.md` … do not silently
   treat it as a completed AsUsual requirements artifact"는 대응물이 없으나,
   v2에서 `status`가 정식 파일명으로만 artifact를 도출하게 되어 통로가 좁아졌다는
   판단으로 제외했다. 재검토 여지 있음.

---

## 생존 확인 (재보고 방지)

- **`hand-off`의 resume discipline 전부 생존.** 최대 위험 파일이었으나 핵심
  4개가 `using-as-usual` Resuming에 안착: 이전 세션 챗 메모리 불신, "Anything
  another session recorded is a claim until you check it", 본인이 검증한 것만
  기록, pre-v2 폴더 거부.
- **`find-cause-workflow.md`의 record 층이 `run-issue`에 거의 온전히 이관.**
  턴 종료 전 기록, 즉시 철회, 원본 라인 불변, `conclusion.md`의 seq 인용, 종료
  전 메모리 패스 순서까지 확인.
- **`templates/plan.md`는 75% 축소에도 실질 손실 거의 없음.** 안전 블록(고위험
  열거·복구가능성·롤백·별도 승인)은 `safety-rules.md:34-58`에 온전하고, "계획에
  적었다고 허가가 아니다"는 오히려 템플릿에 새로 명시됐다. 잘린 것은 Execution
  Mode/Surface, Decision Contracts, Task Index 등 판단층이거나 이벤트·게이트로
  이관된 것들이다. 유일한 약화가 R-16.
- **core rule 7은 프롬프트에서 코드로 강화됨** (`gates.py:153-158`).
- **`search-long-term-memory`는 43% 축소에도 자기완결성 온전.**
- **`writing-plan` Hard Gates 3종, 승인 이벤트 필수 내용, severity 어휘,
  cleanup 적용 5개 기준, cancelled 3종 규칙, git 4대 규칙, 메모리 2패스 승인**
  모두 생존.
