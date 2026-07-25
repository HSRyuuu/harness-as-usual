# 프롬프트 개선 — 최종 실행 계획 (Phase 0 완료 후 개정)

작성일: 2026-07-25 · 개정: Phase 0 감사 결과 반영
선행 문서: [summary.md](summary.md)(P1~P8) · [05-audit.md](05-audit.md)(감사 결과)

---

## 확정된 설계 결정 (인터뷰 결과)

1. **메타 주석 전면 제거 (N1).** "your call", "your judgment", "deliberately
   left to you", "you are trusted" 등 **재량·자유도를 언급하는 모든 표현**을
   런타임 표면에서 제거하거나 지시형 문장으로 대체한다. 자유도는 제약의
   **부재**로 구현한다 — 표면에 자유도라는 개념 자체가 등장하지 않는다.
2. **과완화 점검은 양방향 감사 (N2).** → **완료.** [05-audit.md](05-audit.md)
3. **감사 선행 통합안.** → 감사가 계획을 크게 바꿨다. 아래 참조.
4. **P3는 위임안.** → **이미 완료**되었고, 그 과정에서 R-06을 낳았다.
5. 계획서는 이 파일에 남긴다.

## 지도 원칙

- **설계 의도는 유지보수 표면에만 산다.** "판단층을 모델에 위임한다"는 의도는
  `CLAUDE.md`, `PROJECT_IDENTITY.md`, `docs/`에 기록한다. 런타임 표면
  (`as-usual-rules/`, `skills/`, `templates/`)에는 **지시와 사실만** 남는다.
  실행 에이전트는 무엇이 의도적으로 비워졌는지 몰라야 한다.
- **제거와 보존의 경계.** 재량 *선언*은 제거하되, 같은 문장에 실려 있던 실제
  *지시*는 보존한다.
- **복원은 최소 문장으로.** R-항목 복원이 문단 재도입이 되면 이번 리팩터링의
  성과를 되돌린다. 대부분 한 줄이면 충분하다.

---

## Phase 0 — 감사 (완료)

`.claude/before-refactor/`(HEAD `2f5ba31`)를 기준으로 7개 그룹 전수 대조.
약 230건의 record/safety 항목 중 **생존 214건, 유실 16건**(high 4 · medium 6 ·
low 6). 상세는 [05-audit.md](05-audit.md).

### 감사가 계획을 바꾼 세 가지

**① P1·P2·P3·P7 일부는 이미 완료되었다.** 커밋 `b1df7d1`(07-25 17:46)이
`plan-quality-reference.md` 재작성, 사어휘 일소, implementer-prompt 테스트 정책
위임을 모두 수행했다. 리뷰 문서는 그 커밋 **이전** 상태를 기술한다.
→ 기존 Phase 2·3·4는 **삭제**.

**② 유실 16건이 새 작업으로 들어온다.** 특히 high 4건은 게이트·권한 경계가
실제로 사라진 것이라 N1보다 우선한다.

**③ 유실의 최소 5건이 `b1df7d1`에서 나왔다** (R-03·R-06·R-08·R-10·R-15).
이번 개선 작업도 같은 실수를 반복할 수 있으므로, 삭제 계열 Phase에서는 각
삭제마다 "이 문장이 record/safety 층인가"를 먼저 묻는다.

### 스냅샷

`.claude/before-refactor/` 유지. 복원 작업에서 BEFORE 원문을 계속 참조한다.
전체 완료 시 `rm -rf .claude/before-refactor` (`.gitignore` 항목은 존치).

---

## ⚠️ 실행 전 사용자 결정 대기 — 승인 경계 완화

R-항목이 아니다. 조용한 삭제가 아니라 **명시적으로 다시 쓰인 정책 변경**이지만,
이번 리뷰의 렌즈에 가장 정확히 걸리는 지점이다.

- **BEFORE** (`review-execution/SKILL.md:114-122`): "`user-accepted-risk` and
  `deferred` are **never valid** for Critical or Important findings. If the user
  declines to fix a Critical or Important finding, the topic finalizes as
  `blocked`."
- **AFTER** (`review-execution/SKILL.md:64-71`): Critical/Important도
  "**accepted by the user** — the user was told the risk in plain terms and
  chose to ship anyway"로 종료 가능.

즉 Critical 발견에 **이전에 없던 통과 경로가 생겼다.** 이전 리뷰(02-skills.md)는
이 문장을 `[유지 — 삭제 시 복원 불가능한 규약]`으로 평했으나, 이것이 **새로
완화된 조항**이라는 사실은 BEFORE 대조 없이는 보이지 않았다.

**선택지**: ⓐ 의도한 완화로 두기 · ⓑ Critical만 `blocked` 경로 복원 ·
ⓒ 양쪽 다 복원. 결정 전까지 Phase 1에서 이 파일은 건드리지 않는다.

---

## Phase 1 — High 유실 복원 ✅ 완료

게이트와 권한 경계가 실제로 사라진 4건 + 같은 문단을 만지는 R-09. 전부 원문
검증 후 복원. 총 +79/−11줄, 9개 파일.

| # | 조치 | 결과 |
| --- | --- | --- |
| R-01 | 고위험 게이트 범위를 "every request AsUsual touches … equally to work carried out with no record at all"로 확장 + "The gate does not depend on a work folder existing … no user confirmation waives it" | `safety-rules.md:3-6,50-51` |
| R-01 | 4번 옵션에 "Option 4 is not always on the menu. Withhold it when the work is built around a high-risk operation" | `core-rules.md:69-72` |
| R-09 | 같은 문단에 "…and when the request falls inside the scope of a work folder that is still open" | `core-rules.md:70-72` |
| R-02 | "When it is unclear which of the two a target is … treat it as high-risk until that is settled" | `safety-rules.md:60-61` |
| R-03 | 위임 계약에 `SAFETY:` 항목 + 미승인 고위험 조작 조우 시 `BLOCKED` 반환 규칙 | `implementer-prompt.md:13,19`, `execute-plan/SKILL.md:57-59` |
| R-04 | `_check_finalize`에 확정 항목 요구 게이트. **탈출구는 신규 플래그 없이 해결** — `_check_status_change`의 기존 에러 메시지가 이미 "could not reproduce because …"를 증거 텍스트로 인정하므로 그 경로를 재사용 | `gates.py:161-178` + 테스트 2건 |
| R-04 | 거부 메시지를 문서화된 표와 오너 스킬에 반영 | `record-commands.md:138`, `run-issue/SKILL.md:100-103` |

**검증 (실제 출력 확인):**

- `pytest scripts/tests/ -q` → **55 passed** (기존 54 + 신규 1).
- 게이트 E2E 3단계: ①`conclusion.md` 없음 → 거부 ②`conclusion.md` 있고 확정
  없음 → **신규 게이트 거부** ③"could not reproduce because …" 증거로 확정 후
  → `seq 4 lifecycle done`, exit 0.
- hook smoke → `oneEntryPoint:true, isOneSentence:true, noRulePath:true`.
- 제거된 표면·사어휘 재유입 검사 → 각 0건.

### Phase 1 보강 — 사용자 결정 2건 반영 ✅ 완료

**결정 1 — Critical만 복원.** Critical의 정의("the work cannot honestly be
called done with this outstanding")와 처분 목록이 모순이었다. `accepted by the
user`를 `Important` 전용으로 좁히고 Critical에는 "consent decides whether to
ship, not whether the work is done"를 명시. 미해결 Critical은 `blocked`로 종료.
→ `review-execution/SKILL.md:68-74,109`, `templates/review.md:22-27`

**결정 2 — 규칙 3 집행 공백에 게이트 추가.** `topic`/`direct-work`의 finalize에
verification 이벤트 최소 1건을 요구. `VERIFICATION_UNITS` 상수 신설.
→ `constants.py:116-118`, `gates.py:162-170`

게이트가 막는 것은 **검증하지 않은 완료 주장**이지 정직하게 검증 불가능한
작업이 아니다 — `INCONCLUSIVE`를 기록하면 통과하고, `cancelled`는 영향 없다.

**부수 발견 — 무의미해진 기존 테스트 1건.** R-04 게이트 추가로
`test_link_is_still_allowed_after_closure`의 finalize가 조용히 실패하게 되었고,
봉인이 일어나지 않은 채 link를 검사해 **통과하지만 아무것도 증명하지 않는**
상태가 되었다. 확정 이벤트를 추가해 실제로 봉인되게 고치고, finalize에 명시적
`assert`를 걸어 재발을 막았다. 나머지 4건은 후속 단언이 봉인에 의존하므로
자체 검출된다.

**집행 주장 정정.** `core-rules.md:144`를 실측에 맞췄다 — "The script enforces
**3 and 7** mechanically, plus **the closed vocabulary**, the record's
append-only sealing, and the move restriction." 규칙 6은 `init --unit` 필수라는
간접 형태뿐이라 목록에서 뺐다. (N1의 "The rest you enforce" 삭제는 Phase 2.)

**최종 검증:** pytest **59 passed** (54 → 59). 게이트 E2E 3단계 — ①검증 0건
거부 ②`INCONCLUSIVE` 기록 후 `seq 3 lifecycle done` ③검증 없는 유닛의
`cancelled` 정상. hook smoke·manifest·사어휘 검사 전부 통과.
총 16개 파일, +269/−28줄.

## Phase 2 — 메타 주석 전면 제거 (N1) + core-rules 묶음 ✅ 완료

인벤토리 8건 전부 처리, 재량 선언 grep 히트 0. core-rules 묶음(F1-1·F1-2·F1-3)
동시 처리. 10개 파일 +78/−50줄.

의도한 오탐 `plan-quality-reference.md:4`("not a checklist **to fill in**")는
검사에 예외로 명문화하고 유지했다 — 산출물 제약이지 재량 부여가 아니다.

`verify-runtime-surface`에 §5 검사를 추가하고 `.claude/skills/` 미러 동기화 완료
(`sync-maintainer-skills.py --apply`).

**부수 처리:** Phase 1이 만든 `docs/ARCHITECTURE-WORKFLOW.md`의 낡음 2곳 —
거부 목록에 신규 게이트 2건 누락, disposition 문장이 Critical의 사용자 수용을
여전히 허용 — 을 함께 고쳤다.

**검증:** 재량 선언 0건 · pytest 59 passed · hook smoke · manifest · 미러 일치.

**미해결 (기존 상태, 이번 작업 무관):** `verify-runtime-surface` §4(사설 경로)가
`docs/superpowers/plans/**` 아카이브 계획 문서에서 실패한다. `main`에도 동일하게
존재하므로 별도 판단이 필요하다 — 아카이브를 검사 대상에서 제외하거나 경로를
치환.

---

### (원 계획) Phase 2 상세

같은 파일들을 만지므로 한 묶음.

### N1 제거 인벤토리 (전수, 7건)

| # | 위치 | 조치 |
| --- | --- | --- |
| 1 | `core-rules.md` §4 "What is deliberately left to you" (147–152) | **섹션 전체 삭제.** 내부 실규칙은 §8 우선순위가 커버 |
| 2 | `core-rules.md:124` "Everything else in AsUsual is your judgment. These seven are not." | 절대성만 남긴다 — "These seven rules are absolute." |
| 3 | `core-rules.md:144-145` "The script enforces 3, 6, and 7 mechanically … The rest you enforce." | "The rest you enforce" 삭제 + **집행 목록을 실측에 맞게 정정** (아래 참조) |
| 4 | `write-plan/SKILL.md:60` "…is your call. Do not ask the user to choose." | 지시만 — "Choose the format yourself; do not ask the user to choose." |
| 5 | `execute-plan/SKILL.md:55` "**Delegation is your call.**" | 선언부 삭제, 요구사항 문단만 |
| 6 | `cleanup-code/SKILL.md:31` "How you run them is your call; what matters is…" | 요구 중심으로 — "Apply all four lenses; any arrangement that does so is acceptable." |
| 7 | `run-direct-work/SKILL.md:12` "…you are trusted with most of the decisions" | 삭제 또는 유닛 동작 기술로 대체 |
| 8 | `requirements-quality-reference.md:3-6` + `write-requirements/SKILL.md:54-57` "This is a **reference, not a gate** — there is no checklist to pass … **Read it when** the work is unfamiliar or the document feels thin" | 집행 강도 선언과 조건부 읽기 지시 삭제. 참조 문서는 필요할 때 읽는 것이 기본 행동이므로 명시 불필요. **이중 진술도 함께 해소** — 소유는 quality reference에 두고 SKILL은 한 줄 참조 |

**제외(오탐) 2건:**

- `templates/contexts.md:26` "(What it deliberately does not cover.)" —
  에이전트 재량이 아니라 작업 범위 문구.
- `plan-quality-reference.md:4` "reference, **not a checklist to fill in**" —
  자유도 선언이 아니라 **산출물 형태 지시**다. 뒤의 절이 "the review is
  required (core rule 7), but its output is a better plan plus one `review`
  event, never a review section inside `plan.md`"로 강제성을 재확인하며,
  핵심은 `fill in`("문서에 채워 넣지 마라")이다. v1 `templates/plan.md:197-202`
  의 Review Status 블록 부활을 막는 문장이고, 같은 지시가 파일 끝에 다시 나온다.
  #8과 표현이 비슷하나 성격이 반대이므로 함께 지우지 않도록 주의.

**#1·#7·#8은 이전 리뷰가 `[유지]`로 판정한 항목이다.** N1이 그 판정을 뒤집는다.
특히 #8의 유지 근거였던 "이 선언이 없으면 참조 문서가 게이트로 오독된다"는
`plan-quality-reference`의 자기모순(reference 선언 + 15개 blocking check)을
전제로 했는데, 그 파일이 `b1df7d1`에서 재작성되어 **전제가 소멸했다.**

### 같은 묶음의 core-rules 조치

- **집행 주장 정정 (감사 신규).** `core-rules.md:144-145`의 주장이 실측과
  어긋난다 — 규칙 3은 verdict enum만 강제하고 완료 전 verification 존재는
  검사하지 않으며(절반), 규칙 6은 간접 집행이다. 반대로 주장에 없는 게이트
  (어휘 폐쇄, phase 부분집합, `confirmed`의 `--evidence`, `cancelled`의
  `--reason`, `issue`의 `conclusion.md`)는 실제로 집행된다. 문장을 실측에
  맞춘다.
- F1-3: §8 우선순위 5행 테이블 → 델타 있는 1문장.
- F1-1: §3 승인 요청 **형식** 지시 삭제, 내용 요소 목록만 유지.
- F1-2: 3회 실패 규칙 이중 소유 해소 → `execute-plan` 소유.

### 재발 방지

`.agents/skills/verify-runtime-surface`에 검사 추가:

```bash
rg -n -i "your call|your judgment|deliberately left|you are trusted|up to you|your discretion" as-usual-rules/ skills/ templates/
```

히트 0이어야 통과. 변경 후 `.claude/skills/` 미러 동기화(`skill-registry-sync`).

## Phase 3 — Medium 유실 복원

| # | 조치 | 대상 |
| --- | --- | --- |
| R-05 | 빈 승인 표현(`ㄱㄱ`/`go`/`ok`)을 material question의 답으로 기록 금지 | `gathering-context/SKILL.md` How To Ask |
| R-06 | 버그 수정은 수정-전 실패 재현이 증거의 조건 — **기법이 아닌 증거만** | `core-rules.md` §6 + `implementer-prompt.md` VERIFY |
| R-07 | 리뷰 수행 주체를 기록 (독립/인라인) + self-review 위장 금지 | `review-execution/SKILL.md` Recording 또는 `templates/review.md` |
| R-08 | 리뷰어 프롬프트에 high-risk 축약 목록 + 과잉분류 금지 인라인 | `review-execution/code-reviewer-prompt.md` |
| R-09 | 열린 유닛의 범위 안에 있으면 "just do it"을 제시하지 않는다 | `core-rules.md` §2, `using-as-usual/SKILL.md` |
| R-10 | 시크릿 금지 한 줄 (자식은 규칙 파일을 못 읽음) | `explore-codebase/SKILL.md` Hard Limits |

R-06은 P3(위임안)의 결정과 **모순되지 않는다** — 기법과 어휘는 제거된 채로
두고, 증거 요구만 복원한다.

R-01·R-09는 같은 문단(§2 4번 옵션)을 만지므로 Phase 1과 병합 가능.

## Phase 4 — Low 유실 + 잔여 P 항목 + 부수 발견

**Low 복원 (6건, 선택적):** R-11(`--actor user` 귀속) · R-12(리뷰 verdict 일치)
· R-13(diff 불가 시 한계 기록) · R-14(git action을 typed approval로) ·
R-15(explore 출력 `UNTRUSTED` 라벨) · R-16(AC별 증거 매핑 한 구절).

R-11·R-14는 어휘 정합 문제이기도 하다 — 복원하지 않을 거라면 반대로
`constants.py`에서 고아 어휘를 제거해 정합을 맞춘다.

**댕글링 참조 6곳 (감사 신규).** 전부 `write-requirements/
requirements-quality-reference.md`. D-1·D-3·D-5는 현행 섹션명으로 재작성,
D-4는 `Constraints & Assumptions`로 정정, D-6은 템플릿 정책("빈 섹션은 삭제")에
맞춰 수정. **D-2(`Affected Surface`)만 판단 필요** — 참조 재작성으로 끝낼지,
코드 대면 작업의 영향 파일 명시 강제력을 복원할지.

**잔여 P 항목:**
- **P4** 한국어 리터럴 3곳(`write-plan:96`, `review-execution:92`,
  `finalize:92-99`) → "in the user's language" 지시로. finalize의 git 4선택지
  **구조**는 유지.
- **P5** Anti-Patterns 선별 — 본문 단순 반전 삭제, 교차 파일 규칙·관찰된 실패
  모드만 스킬당 3~5개 (~50줄). **삭제 전 record/safety 층 여부를 먼저 묻는다.**
- **P6** 이중 소유 해소 — requirements/plan 섹션 표는 템플릿 소유,
  contexts.md 3밴드는 core-rules 소유.
- **P7 잔여** gathering-context "1 to 5 at a time" → 원칙만.
  (git-action·explore-codebase는 완료됨)
- **P8** requirements-quality-reference 축약 — 댕글링 수정과 함께 처리.

**기타 부수 발견:**
- `cleanup-code/SKILL.md:69-70`에 "적용한 변경이 있을 때만" 조건 추가 (빈
  `review.md` 생성 충돌 해소).
- `manage-self-improvement/references/{memory-update,skill-improvement}.md`의
  사어휘 `record-memory-candidate`·`record-skill --state`·`--brief` 교체
  — **P2의 유일한 잔여물.**
- `write-requirements/SKILL.md:73-74`의 "the Decisions section" 지시 정정.
- `run-direct-work` 파이프라인 다이어그램에 `cleanup-code?` 추가.

---

## 검증

```bash
# 재량 선언 부재 (N1)
rg -n -i "your call|your judgment|deliberately left|you are trusted|up to you|your discretion" as-usual-rules/ skills/ templates/

# 사어휘 부재 (P2 완료 상태 유지)
rg -n -i "Decision Contract|Execution Design|Execution Task Index|test-required|no-test|verification\.recorded|task\.completed|approval\.high_risk" as-usual-rules/ skills/ templates/ scripts/

# 하네스
python3 -m pytest scripts/tests/ -q
CLAUDE_PLUGIN_ROOT="$PWD" bash hooks/run-hook.cmd session-start | jq .
```

검증 스킬: `verify-runtime-workflow-consistency` → `verify-runtime-surface` →
`verify-as-usual-harness` → `verify-project-identity` (또는
`verify-implementation` 일괄). `.agents/skills/**` 변경 시 `.claude/skills/**`
미러 동기화.

## 커밋 전략

Phase 단위, 경로 명시 스테이징(`git add .` 금지).

0. `chore: ignore the local pre-refactor snapshot workspace` (`.gitignore`, 완료)
1. `docs: record the over-loosening audit and the revised plan` (Phase 0)
2. `fix: restore the safety gates the refactoring dropped` (Phase 1)
3. `refactor: remove discretion meta-commentary from the runtime surface` (Phase 2)
4. `fix: restore the record-integrity rules the refactoring dropped` (Phase 3)
5. 이후 Phase 4 항목별.

## 완료 기준

- **R-01~R-04 복원 완료** (+ R-04는 `scripts/tests/` 케이스 추가).
- R-05~R-10 복원 완료. R-11~R-16은 복원했거나 "복원 불요" 사유를 기록.
- 승인 경계 완화(Critical/Important disposition)에 대한 사용자 결정 반영.
- N1 인벤토리 7건 처리 + 재량 선언 grep 히트 0.
- `core-rules.md`의 스크립트 집행 주장이 실측과 일치.
- 댕글링 참조 6곳 해소.
- 검증 스킬 4종 통과, pytest 통과, hook smoke 통과.
- 런타임 표면 어디에도 "무엇이 왜 비워졌는지"가 설명되지 않는다.
- 스냅샷 정리: `rm -rf .claude/before-refactor`.
