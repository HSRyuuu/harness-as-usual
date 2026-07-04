# 01. AsUsual 하네스 문제점 진단 (근거 기반)

- **작성:** Fable / 2026-07-04
- **진단 방법:** `as-usual-rules/core-workflow.md` 전문, `skills/*` 12개 skill + reviewer/implementer prompt 전부, `templates/*` 전부, `hooks/session-start`, `scripts/topic-log.py`의 상태머신 표면(grep)을 직접 읽고 대조.
- **분류:** ① 단일 작업 / ② 워크플로우 / ③ 아키텍처 / ④ 프롬프트. 각 finding은 `F<N>`으로 참조하며, 실행 문서는 `step-XX-*.md`가 소유한다.

> 이 문서는 "왜 고치는가"의 근거 원장이다. "무엇을 어떻게 고치는가"는 각 step 파일에 있다.
> 인용한 라인 번호는 2026-07-04 기준이다. 실행 시점에 파일이 바뀌었을 수 있으므로, **수정 전 반드시 원본에서 인용문을 다시 찾아 확인하라.**

---

## 심각도 요약

| ID | 축 | 규모 | 한 줄 요약 | Step |
| --- | --- | --- | --- | --- |
| F1 | ①/④ | Small | `writing-plan` Complete Plan 목록 번호 오류 (1,2,3,5,6) | step-01 |
| F2 | ① | Small | `templates/report.md`에 legacy 명칭 `## Simplify Decision` 잔존 | step-01 |
| F3 | ④ | Small | controller 위임 문단이 core §3와 `using-as-usual`에 verbatim 중복 | step-01 |
| F4 | ④ | Small | `finalize` 전제조건이 자기 자신(Step 0)이 수행할 일을 요구 | step-01 |
| F5 | ① | Small | `finalize`가 core §13의 `validate` 요구를 수행하지 않음 | step-01 |
| F6 | ④ | Medium | `topic-log.py` 경로 표기 3종 혼용 (21:3:1) — target project에서 오동작 유발 | step-02 |
| F7 | ② | Medium | 활성화 신호 4개 vs 3개 — core §1이 feature-development 신호 누락 | step-03 |
| F8 | ② | **Large** | Clarification Routing의 `material` 기준이 나머지 전체 표면과 모순 | step-04 |
| F9 | ② | Medium | 리뷰 finding disposition 값 집합이 템플릿 ↔ 규칙 간 불일치 | step-05 |
| F10 | ② | **Large** | `cancelled` 상태 미노출 + 중도 포기/direct-execute 종단 경로 부재 | step-06 |
| F11 | ③/④ | Medium | 질문 파일 한국어 canonical heading이 언어 중립 정체성과 충돌 | step-07 |
| F12 | ④ | Medium | core §16 Required Skills가 각 SKILL.md 요약을 중복 (~40줄) + 반복 문구 | step-08 |
| F13 | ③ | Small | hook이 Cursor/Copilot 분기를 지원하지만 문서는 dual-host만 기술 | step-09 |

---

## F1. `writing-plan` Complete Plan 번호 오류

- **축/규모:** ① 단일 작업 (④ 겸) / Small — 바로 수정
- **근거:** `skills/writing-plan/SKILL.md:263-267`

```
1. Fill `plan.md` `Review Status`: ...
2. Run `scripts/topic-log.py complete-plan` to record `plan.completed`.
3. Confirm derived status now routes to execution approval.
5. Tell the user the plan is ready ...
6. Stop.
```

4번이 없다. 단순 번호 오타이며 의미 변화 없음.

## F2. `templates/report.md`의 legacy `Simplify` 명칭

- **축/규모:** ① / Small
- **근거:** `templates/report.md:34` — `## Simplify Decision`
- 프로젝트 전체가 "simplify"를 "code cleanup"으로 개명 완료한 상태다: core-workflow.md:597 anti-pattern "Calling a host `/simplify` command instead of `cleanup-code`", `scripts/topic-log.py:1406`은 `skip-simplify`를 "Deprecated alias for skip-code-cleanup"으로 명시. 그런데 최종 사용자-facing 리포트 템플릿에만 옛 이름이 남았다.
- `finalize/SKILL.md:113`은 report에 "code cleanup decision and result"를 담으라고 지시하므로 템플릿과 지시가 어긋난다.

## F3. controller 위임 문단 verbatim 중복

- **축/규모:** ④ / Small
- **근거:** `as-usual-rules/core-workflow.md:168`과 `skills/using-as-usual/SKILL.md:48`에 동일 문단이 글자 단위로 중복:

> "For topics with many or large artifacts, you may delegate artifact inventory and status summarization to a subagent ... does not delegate those."

- hand-off 가드레일 "단일 원본 원칙(01-IMPROVEMENT-PLAN §0 공통 가드레일 3)" 위반. 규칙 개정 시 한쪽만 고쳐져 어긋날 위험. first-read 상세 행동은 `using-as-usual` 소유, core §3는 gate 원칙 한 문장 + 참조로 축소하는 것이 ownership 원칙에 맞는다.

## F4. `finalize` 전제조건의 자기참조

- **축/규모:** ④ / Small
- **근거:** `skills/finalize/SKILL.md:35` 전제조건:

> "The self-improvement pass has been run via `manage-self-improvement`, and its result is recorded (applied, skipped with reason, or "no candidates")."

그런데 그 pass를 수행하는 것이 finalize 자신의 `Step 0: Self-Improvement Pass`(`:52-66`)다. 전제조건은 "스킬 진입 전 충족되어야 할 것"인데 스킬이 첫 스텝에서 스스로 수행할 일을 전제조건에 두어, 진입 시점에 항상 위반 상태가 된다. 실행 agent가 "전제 미충족 → review-execution으로 복귀"로 오판할 수 있는 지시 충돌.

## F5. `finalize`가 `validate`를 실행하지 않음

- **축/규모:** ① / Small (skill ↔ core 정합 수정)
- **근거:** core-workflow.md:520:

> "Run `scripts/topic-log.py validate --topic-dir <topic-dir>` before claiming a topic is structurally complete."

그러나 `skills/finalize/SKILL.md`에는 `validate` 언급이 전혀 없다 (Step 1은 수동 체크리스트만 나열: `:68-92`). 스크립트에는 finalize 구조 불변식 검증이 이미 구현되어 있다(`scripts/topic-log.py:1168-1191`: report artifact, review.completed, cleanup decision, passed review 요구). skill이 이를 호출하도록 정렬하면 수동 체크 일부를 기계 검증으로 대체할 수 있다.

## F6. `topic-log.py` 경로 표기 3종 혼용

- **축/규모:** ④ / Medium (기계적 대량 수정)
- **근거:** `grep -o "python3 [^ ]*topic-log.py" skills/ | sort | uniq -c`:

```
 1 python3 <as-usual-plugin-root>/scripts/topic-log.py
 3 python3 <plugin-root>/scripts/topic-log.py
21 python3 scripts/topic-log.py
```

core-workflow.md:483은 `<as-usual-plugin-root>/scripts/topic-log.py`를 canonical로 제시한다. 하지만 skill 예시 21곳은 bare `scripts/topic-log.py`로 되어 있다. **AsUsual은 target project에서 실행되는 하네스이므로 target project 루트에는 `scripts/topic-log.py`가 없다.** bare 경로를 그대로 복사해 실행하면 실패한다. 실제 오동작을 유발하는 지시 결함.

## F7. 활성화 신호 3개 vs 4개 불일치

- **축/규모:** ② / Medium
- **근거 대조:**
  - `hooks/session-start:10`: "...or **feature-development work that should use the AsUsual workflow**, use the `using-as-usual` skill first"
  - `skills/using-as-usual/SKILL.md:28-33`: 활성화 조건 4개, 4번째가 "The user asks for feature-development work that should use the AsUsual workflow."
  - `CLAUDE.md` HOOK ACTIVATION MODEL: 신호 4개 (4번 동일)
  - **`as-usual-rules/core-workflow.md:97-104` Activation Signals 표: 신호 3개뿐.** feature-development 행이 없고, "Ordinary coding or question request with no AsUsual signal → Not active"만 있다.
- 결과: core-workflow만 읽은 agent는 feature-development 요청을 활성화 신호로 인지하지 못한다. hook/skill/CLAUDE.md와 canonical contract가 어긋난 상태.

## F8. Clarification Routing의 `material` 기준 모순 ★ 최중요

- **축/규모:** ② 워크플로우 / **Large — 제안서 필수**
- **문제:** chat 질문 허용 여부의 판별 기준이 표면마다 다르다.

core-workflow.md:199-205 (Clarification Routing):

> "If the decision is **non-material** ... ask a focused chat clarification ...
> If the decision is **material**, becomes a broad multi-question cycle, or changes the topic boundary: route to `define-requirements` or `start-work` and stop."

즉 이 섹션은 **material이면 무조건 파일 사이클로 라우팅**하라고 한다. 그런데:

- core-workflow.md:43-45 (Key Terms): "**material**: ... could change any of requirements, plan, implementation approach, risk, or verification."
- core-workflow.md:276-277 (§5 Phase Router, execute 분기): "IF plan is stale or internally inconsistent: **ask a focused chat clarification if the gap is a single user decision**" — plan을 바꾸는 결정은 정의상 material인데 chat을 허용.
- core-workflow.md:398 (§9): "If implementation reveals a new user decision **that could change requirements, plan, implementation, risk, or verification** [= material 정의 그대로], stop implementation and follow Clarification Routing." → Clarification Routing대로면 무조건 route-out인데,
- `skills/executing-plan/SKILL.md:226`: 같은 상황에서 "**ask a focused chat clarification when it can be resolved in the current turn**, record the answer ..." — chat 허용.
- `skills/writing-plan/plan-document-reviewer-prompt.md:58`: "If the issue reveals a **material decision** that could change scope, requirements, risk ... **ask a focused chat clarification** when it can be resolved in the current turn" — material에 chat을 명시적으로 허용.
- `PROJECT_IDENTITY.md:55` 및 CLAUDE.md CONVENTIONS: "In requirements/plan/execute phases, **focused clarifications may be asked in chat**. Record the answer in audit.jsonl ... **Broad ambiguity involving multiple decisions or a topic-boundary change** should route to define-requirements."

- **진단:** 프로젝트의 의도된 모델은 정체성 문서와 대다수 표면이 말하는 **focused(단일 결정, 현재 턴 해결 가능, 기록 필수) vs broad(다중 결정/경계 변경 → 파일 사이클)** 이분법이다. Clarification Routing 섹션만 이 축을 **material vs non-material**로 잘못 인코딩했다. material의 정의가 "requirements/plan/risk/verification을 바꿀 수 있음"이므로, 이 섹션을 문자 그대로 따르면 §5/§9/executing-plan/reviewer prompt가 허용하는 chat clarification이 전부 금지되고, 반대로 따르지 않으면 canonical contract 위반이 된다. agent가 어느 쪽을 따르든 다른 규칙을 위반하는 **진짜 지시 충돌**.
- **주의:** 수정 방향은 "chat을 더 넓게 허용"이 아니라 "이미 대다수 표면이 합의한 focused/broad 기준으로 한 곳(Clarification Routing)을 정정"이다. 안전 게이트 약화가 아님 — 초기 broad 질문의 파일 사이클 의무(§6, Inviolable ALWAYS)는 그대로 유지된다.

## F9. finding disposition 값 집합 불일치

- **축/규모:** ② / Medium — 제안서 권장
- **근거 대조:**
  - `templates/code-review-report.md:36`: `Disposition: fixed | blocked | rejected | user-accepted-risk | deferred` — 5개 값.
  - `skills/review-execution/SKILL.md:22`: "Critical and Important findings must be **fixed and re-reviewed** ... or **rejected with technical reason** and re-reviewed to passed, or ... route finalization to **blocked**" — C/I에는 3개 경로만 허용.
  - core-workflow.md:420 동일: "fixed and re-reviewed, rejected with technical reason and re-reviewed to passed, or route finalization to blocked".
  - `scripts/topic-log.py:1182-1190`: `complete`/`follow-up-needed` finalize는 최종 review passed + 미해결 C/I 0을 기계적으로 강제.
- **진단:** 템플릿이 제공하는 `user-accepted-risk`, `deferred`는 Critical/Important에는 규칙상·기계상 절대 쓸 수 없는 값인데, 어느 심각도에 허용되는지 아무 데도 정의되어 있지 않다. agent가 Important finding에 `user-accepted-risk`를 기록하고 `follow-up-needed`로 finalize를 시도하면 `validate`에서 실패하는 함정. Minor에는 합리적인 값이므로, **심각도별 허용 disposition 매트릭스**를 한 곳에 정의해야 한다. (게이트 약화 아님 — 현재 규칙을 명시화.)

## F10. 종단 상태 경로 부재 (`cancelled` 미노출, 중도 포기 불가) ★

- **축/규모:** ② / **Large — 제안서 필수, script+tests 동시 수정**
- **근거:**
  - `scripts/topic-log.py:26`: `STATUSES = {"active", "blocked", "complete", "follow-up-needed", "cancelled"}` — **`cancelled`가 이미 존재**.
  - `scripts/topic-log.py:1415`: `finalize-topic --status` choices = STATUSES - {active} → cancelled 선택 가능.
  - 그러나 runtime 표면 어디에도 `cancelled`가 없다: core-workflow.md:441 "Set final topic status to `complete`, `follow-up-needed`, or `blocked`", `skills/finalize/SKILL.md:98-103` 상태 표도 3개만.
  - `skills/finalize/SKILL.md:31-33` 전제조건: "Execution completion is recorded. Review result is recorded." → **실행에 도달하지 못한 topic(요구사항/plan 단계에서 사용자가 포기)은 finalize에 진입할 수 없다.** 종료 수단이 없어 영구 in-progress로 남는다.
  - `scripts/topic-log.py:1168-1178`: `validate`는 **모든** finalized topic에 review.completed + cleanup decision을 요구 → 설령 cancelled로 finalize해도 validate가 실패한다. 스크립트 내부에서도 cancelled는 반쪽 구현.
  - direct-execute: `scripts/topic-log.py:44`에 `direct-execute-complete` phase는 있으나, core-workflow.md:227-231 router는 "record ... and STOP"으로 끝난다. direct-execute로 완료된 topic이 이후 commit을 원할 때의 경로(§12 git-action은 phase `finalized`를 전제: core-workflow.md:455-456)가 미정의 — direct-execute 후 git-action은 규칙상 불가능한데 이를 명시한 곳도 없다.
- **진단:** 상태머신에 종단 경로 2개가 비어 있다: (a) 중도 포기(cancel) 경로, (b) direct-execute 후 git 액션 경로. (a)는 스크립트 절반 + 프롬프트 0으로 구현된 상태라 표면 간 불일치이기도 하다.

## F11. 질문 파일 한국어 canonical heading

- **축/규모:** ③/④ / Medium — 제안서 필수 (사용자 정책 결정 필요)
- **근거:**
  - `skills/define-requirements/SKILL.md:82`: "Each question must follow this order: `### 왜 중요한가요?`, `### Requirements 반영`, `### 선택`, options, `**추천**:`, `✅ 답변을 입력하세요.`, then `[Answer]:`." — **한국어 heading이 필수 형식**으로 하드코딩.
  - `templates/question.md:14-35`: 동일 한국어 구조.
  - 반면 core-workflow.md:139: "Write user-facing artifact prose **in the user's current or clearly preferred conversation language**" + `PROJECT_IDENTITY.md`: "AsUsual은 **언어 중립** runtime workflow를 지향한다."
  - `templates/requirements.md:27,49,57,67,71`과 `templates/plan.md:26-28,87,124`에도 한국어 helper 텍스트(`없음`, `사용자 언어로 ...`)가 섞여 있다.
- **진단:** 영어 사용자가 쓰면 질문 파일에 한국어 heading이 강제된다. "canonical marker는 보존, prose는 사용자 언어"(core-workflow.md:141) 원칙에 비추면 이 heading들이 marker인지 prose인지 정의가 없다. 정책 결정이 필요: (a) 한국어 heading을 canonical marker로 선언하거나, (b) 영어 canonical + 사용자 언어 번역 규칙으로 바꾸거나. 어느 쪽이든 heading 순서 검증 규칙과 함께 한 곳에 명문화해야 한다.

## F12. core §16 중복 + 반복 문구 (프롬프트 토큰 효율)

- **축/규모:** ④ / Medium (동작 보존 필수)
- **근거:**
  - core-workflow.md:600-638 (§16 Required Skills): 각 skill마다 2-단락 요약(언제 쓰고 무엇을 하는지)이 있는데, 이는 각 `skills/*/SKILL.md`의 Responsibility Boundary/서두와 실질 중복이다 (~40줄). §16의 고유 정보는 "어느 상황에서 어느 skill을 부르는가"뿐이다.
  - `skills/start-work/SKILL.md:29-34` Routing Principle이 core-workflow.md:179-186과 준-verbatim 중복 (start-work가 Route Table은 참조로 처리하면서 원칙 bullet은 복제).
  - 반복 문구: "Follow Clarification Routing in `core-workflow.md` for any decision discovered here."가 skill 표면에 9회, "Do not hand-edit"가 core에만 3회(Inviolable/§2/§13) + 각 skill마다 1회 이상. 안전 중복은 일부 의도적이나, 같은 파일 안 3회는 과잉.
- **주의:** 이 축은 **의미(게이트) 변경 금지**. F8 등 의미 변경 step이 모두 끝난 뒤 마지막에 수행해야 rebase 충돌이 없다.

## F13. hook 호스트 분기 미문서화

- **축/규모:** ③ / Small
- **근거:** `hooks/session-start:14-21`은 `CURSOR_PLUGIN_ROOT`(Cursor), `COPILOT_CLI`(Copilot 제외 분기), `PLUGIN_ROOT`(generic) 분기를 구현. 그러나 `CLAUDE.md`/`AGENTS.md`/`docs/ARCHITECTURE-WORKFLOW.md`는 Claude Code + Codex dual-host만 기술한다.
- **진단:** 코드가 문서보다 앞서 있다. 지원 의도가 있으면 문서화, 없으면 분기 제거 중 하나로 정합해야 한다. (제거는 동작 축소이므로 사용자 확인 필요 — step-09에서 질문으로 처리.)

---

## 진단했지만 제외한 항목 (참고)

- **subagent task 이중 리뷰(requirements review + quality review) 부담:** `executing-plan/SKILL.md:211` — 무거운 ceremony지만 PROJECT_IDENTITY의 실패 모드 1(요구사항 오해) 예방 장치로 의도된 설계. 게이트 약화 위험이 있어 이번 라운드에서 제외. 추후 E2E 테스트 증거가 쌓이면 재검토.
- **`scripts/topic-log.py` 1,524줄 단일 파일:** 분할은 테스트 전면 개편을 동반하는 대형 리팩터링. 이번 개선 목표(하네스 품질) 대비 이득이 불분명해 제외.
- **maintainer skill 미러 구조:** `02-FILE-STRUCTURE.md` §G가 이번 작업 범위 밖으로 명시.
