# CRITIC-RESULT: 작업 계획 최종 검토 결과

- **검토자:** Claude (Fable 5) / 2026-07-04
- **검토 대상:** `docs/improvement-260704/working-dir/` 전체 (00-README, 01-DIAGNOSIS, 02-DECISIONS, step-01~10) + `hand-off/` 3종
- **검토 방법:** 계획 문서 전문 정독 + 모든 핵심 인용을 디스크 원본(`as-usual-rules/core-workflow.md`, `skills/*`, `templates/*`, `scripts/topic-log.py`, `hooks/session-start`, `PROJECT_IDENTITY.md`, `CLAUDE.md`, `AGENTS.md`)과 직접 대조
- **검토 우선순위:** 프로젝트 아이덴티티(`PROJECT_IDENTITY.md`) 정합성 최우선

## 종합 판정

**승인 — 실행 가능.** 계획의 방향은 프로젝트 아이덴티티와 강하게 정합하며, 진단(F1~F13)의 근거 인용은 검증 결과 정확했다. 검토 중 발견한 결함 6건은 사용자 결정(4건)을 받아 이 검토에서 계획 문서에 직접 반영 완료했다. 실행 에이전트는 정정된 현재 버전의 working-dir 문서를 기준으로 착수하면 된다.

---

## 1. 프로젝트 아이덴티티 정합성 평가 (최우선 검토)

| Step | 판정 | 근거 |
| --- | --- | --- |
| step-01 (F1~F5) | ✅ 정합 | 순수 정정. controller 비위임 안전 규칙 유지 가드레일 명시됨. finalize의 `validate` 추가는 identity의 "verification evidence over optimistic summaries" 강화. |
| step-02 (F6) | ✅ 정합 | 실제 오동작(target project에 없는 bare 경로) 제거. 동작 보존. |
| step-03 (F7) | ✅ 정합 | 이미 hook/skill/CLAUDE.md/AGENTS.md 4표면이 합의한 신호를 canonical contract에 반영하는 것. "Do not force AsUsual" 반대 신호 유지 확인 절차 포함 — identity Non-Goal("모든 요청에 workflow 강제 안 함")과 정합. |
| step-04 (F8) | ✅ 정합 | **identity가 기준점으로 올바르게 사용됨.** PROJECT_IDENTITY:55와 실패 모드 1이 말하는 focused/broad 모델로, 유일하게 어긋난 Clarification Routing 한 곳을 정정하는 방향. broad→파일 사이클 의무(Inviolable ALWAYS)와 audit 기록 의무는 유지. Inviolable ALWAYS 문구를 다듬는 경우도 제안서에서 명시적으로 다루도록 되어 있음. |
| step-05 (F9) | ✅ 정합 | 게이트 명시화(현행 규칙의 문서화)이지 완화가 아님. C/I 3-경로 규칙과 기계 불변식 불변 가드레일 확인. `user-accepted-risk`의 Minor 한정 + audit 기록 요구는 identity의 "explicit decision records" 편향과 일치. |
| step-06 (F10) | ✅ 정합 (D5 반영 후) | cancel 경로는 identity의 "durable topic artifacts"를 종단까지 완성. complete/follow-up-needed 기계 불변식 한 글자도 완화 금지 가드레일 있음. direct-execute 경량 종단은 "not so much ceremony" 원칙과 일치. **단, 검토에서 Inviolable NEVER 충돌을 발견 → D5로 해소 (아래 결함 C1).** |
| step-07 (F11) | ✅ 정합 | 안 1(영어 canonical + 사용자 언어 번역)은 identity의 "언어 중립 runtime workflow 지향"과 직접 일치. `[Answer]:` marker 불변 + E2E 테스트 동시 갱신 명시. |
| step-08 (F12) | ✅ 정합 | 동작 보존 원칙 + 문장 단위 "다른 곳에 존재" 증거표 요구 — 게이트 유실 방지 장치가 충분. 의미 변경 step 이후로 순서 고정한 것도 옳음. |
| step-09 (F13) | ✅ 정합 | 문서화(동작 보존) 채택. runtime 표면에 maintainer 지식을 넣지 않는다는 경계 명시 — identity Non-Goal과 일치. |
| step-10 | ✅ 정합 | "PROJECT_IDENTITY는 최종 기준이므로 개선 결과에 맞춰 고치는 대상이 아니다"라는 원칙이 명시됨 — 올바른 방향성. |

**아이덴티티 관점 총평:** 이 계획의 가장 큰 미덕은 F8 정정 방향을 "chat 확대"가 아니라 "identity 문서가 이미 선언한 모델로의 수렴"으로 잡은 것, 그리고 모든 Large step에 "게이트 약화 금지" 가드레일을 반복 배치한 것이다. 실패 모드 우선순위(요구사항 오해 → 영향 누락 → 미승인 위험작업)를 훼손하는 항목은 없다.

---

## 2. 원본 대조 검증 결과

step 문서의 인용(2026-07-04 스냅샷)을 디스크 원본과 대조했다.

**정확함 (검증 통과):**

- F1: `writing-plan/SKILL.md` Complete Plan 번호 오류(1,2,3,5,6) — 실재 확인
- F2: `templates/report.md:34` `## Simplify Decision` 잔존 — 실재 확인
- F3: controller 위임 문단이 core:168과 `using-as-usual:48`에 글자 단위 중복 — 실재 확인
- F4/F5: finalize 전제조건 자기참조, `validate` 미호출 — 실재 확인. `validate`의 finalize 불변식이 `topic.finalized` 존재 시에만 검사됨(:1169 `if finalized_events:`)도 확인 — step-01 1-E의 "Step 2 직후 재실행" 지시가 옳다.
- F7: core §1 표는 신호 3개, hook/using-as-usual/CLAUDE.md/AGENTS.md는 4개 — 실재 확인 (AGENTS.md:74-79도 4개 보유, step-03의 "변경 없음, 확인만" 판단이 옳다)
- F8: Clarification Routing(:199-205)의 material 기준 vs 나머지 표면의 focused/broad 기준 모순 — 전 인용 지점 실재 확인. **진짜 지시 충돌 맞음.**
- F9: disposition 5개 값 vs C/I 3-경로 규칙 vs 기계 불변식 — 실재 확인
- F10: `STATUSES`에 `cancelled` 존재(:26), CLI 선택 가능(:1415), runtime 표면 미노출, validate가 모든 finalized topic에 review/report/cleanup 요구 — 실재 확인
- F11: 한국어 heading 하드코딩(define-requirements:82, templates/question.md) — 실재 확인. `test_fill_question_answers.py`의 한국어 heading 의존도 확인 — step-07의 테스트 동시 갱신 지시가 필수적으로 옳다.
- F12: §16이 :600-638 (파일 끝)에 존재 — 확인
- F13: hook 4분기(:14-21) vs dual-host 문서 — 실재 확인

**스냅샷 드리프트 (경미, step-02 문서에 정정 반영 완료):**

- F6 경로 표기 개수: 진단은 21:3:**1**이라 했으나 실제는 21:3:**2** (`using-as-usual/SKILL.md:80`에도 `<as-usual-plugin-root>` 실행 예시 존재). 추가로 비명령 경로 1곳(`manage-self-improvement/SKILL.md:51`의 `<as-usual-plugin-root>/templates/MEMORY.md`)이 step-02의 원래 치환 규칙으로는 잡히지 않지만 잔존 검증 grep에는 걸려 DoD가 자기모순이었다.

---

## 3. 발견 결함과 조치 (전부 해소됨)

### C1. step-06(B) ↔ Inviolable NEVER 충돌 (Critical — 사용자 결정으로 해소)

step-06(B)이 core §5에 추가하려던 "direct-execute 완료 후 commit 등은 일반 대화로 처리" 문장은 Inviolable NEVER(:35) "run a git action before finalize + explicit user selection"과 문자 그대로 충돌한다. direct-execute topic은 finalize에 도달하지 않으므로, 이 문장을 그대로 추가하면 **F8과 같은 유형의 지시 충돌을 새로 만드는** 결과였다.

- **사용자 결정 (2026-07-04):** Inviolable NEVER 문구를 게이트 대상 topic 한정으로 명확화하는 것을 step-06 범위에 포함. 사용자 명시 요청 없는 자동 git action 금지는 유지.
- **조치:** `02-DECISIONS.md`에 D5 신설, `step-06-terminal-states.md` §3(B)에 항목 2로 반영, 가드레일 추가.

### C2. PROJECT_IDENTITY.md의 legacy 용어 (사용자 결정으로 해소)

F2의 전제("프로젝트 전체가 simplify→code cleanup 개명 완료")와 달리, 최종 기준 문서인 `PROJECT_IDENTITY.md:63`에 "Simplify cleanup is optional and user-approved"가 남아 있었다. step-10이 실행 에이전트의 PROJECT_IDENTITY 수정을 금지하므로 계획 안에서는 해소 불가능했다.

- **사용자 결정:** 용어만 즉시 개명.
- **조치:** 이 검토에서 `PROJECT_IDENTITY.md:63`을 "Code cleanup is optional and user-approved."로 직접 수정 완료. 원칙(optional + user-approved)은 불변. F2의 전제가 이제 성립한다.

### C3. 제안서 경로 불일치 (사용자 결정으로 해소)

계획 문서 9곳이 존재하지 않는 `docs/handoff/proposals/`를 지정했고, 템플릿이 있는 `hand-off/proposals/`는 step-10이 "갱신하지 않는 스냅샷"으로 선언해 어느 쪽도 그대로 쓸 수 없었다.

- **사용자 결정:** 경로 현행화.
- **조치:** working-dir + hand-off 문서의 참조 10곳을 전부 `docs/improvement-260704/proposals/`로 통일. 템플릿은 `hand-off/proposals/_TEMPLATE.md`를 읽기 전용으로 계속 사용. 실행 에이전트는 첫 제안서 작성 시 이 디렉토리를 생성하면 된다.

### C4. 커밋 주체 미정의 (사용자 결정으로 해소)

D4가 "컨트롤러(오케스트레이터)가 커밋, 실행 에이전트는 커밋 금지"라 했으나 이 하네스에는 그런 역할 분리가 없다 (subagent-driven은 runtime topic의 실행 모드일 뿐, 이 개선 작업 자체는 plugin development).

- **사용자 결정:** 컨트롤러/실행 에이전트 구분 제거. 단, "커밋은 finalize 전 금지" 규칙은 target project runtime 규칙이라 이 저장소 개선 커밋에 적용되지 않으므로, **step 단위 커밋 규칙 자체는 유지**한다 (D4 전체 삭제는 하지 않음).
- **조치:** D4를 "실행 에이전트가 step 완료 + 검증 통과 후 step 단위 커밋 (서브에이전트 위임 시에도 커밋은 메인 에이전트)"로 수정. `00-README.md` 프로토콜 규칙 1 동기화. "컨트롤러에 보고" 표현 5곳을 "사용자에게 보고"로 교체.

### I1. step-02 placeholder 치환 범위 누락 (Important — 직접 정정)

비명령 경로의 `<as-usual-plugin-root>`(`manage-self-improvement/SKILL.md:51`)가 치환 절차에서 빠졌으나 잔존 검증 grep에는 걸려 DoD가 충족 불가능했다. **조치:** step-02의 발생 수치를 실제(21:3:2 + 비명령 1곳)로 정정하고, 비명령 경로 사용도 전부 `<plugin-root>`로 통일하는 치환 규칙을 추가했다.

### I2. step-04 non-material 처리의 침묵 변경 (Important — 직접 정정)

현행 Clarification Routing은 non-material chat 답변에도 artifact 갱신 + 재리뷰를 요구하는데, step-04 (b)의 새 규칙은 "record it and continue"로 끝난다. non-material은 정의상 artifact를 바꿀 수 없으므로 정합한 정리이지만, 델타로 명시되지 않은 침묵 변경이었다. **조치:** step-04 가드레일에 "제안서에 델타로 명시" 항목을 추가했다.

### I3. blocked의 실행-전 공백 (Important — step-06에 지시 추가)

`validate`는 blocked finalize에도 review.completed/cleanup decision/report를 요구한다(면제 아님 — `topic-log.py:1169-1181`에서 직접 확인). 실행 전 단계에서 외부 입력 대기로 멈춘 topic은 cancelled 외에 종단 수단이 없다. step-06은 "blocked 현행 유지"만 말하고 이 공백의 처리 방침을 정하지 않았다. **조치:** step-06 가드레일에 "blocked 실행-전 공백을 제안서에서 명시적으로 결정·기록"하는 항목을 추가했다 (active+blocker로 재개 대기 vs cancelled 종료 중 canonical 경로 결정).

---

## 4. 실행 에이전트를 위한 잔여 주의사항

1. **인용 재확인 의무는 여전히 유효하다.** 이 검토는 2026-07-04 원본과 대조했지만, 00-README의 규칙대로 각 step 착수 시 원본에서 인용을 다시 확인하라. 특히 F6 수치는 이미 한 번 드리프트가 확인됐다.
2. **step-08의 8-A 대조표는 생략 불가.** §16 산문에는 표로 옮기면 사라질 규범 문장이 섞여 있다. "문장 → 기존 위치" 매핑 없이 삭제하지 마라.
3. **step-06 사전 조사(§1)에서 blocked 불변식을 반드시 확인하라.** 이 검토의 확인 결과(blocked 비면제)를 제안서 §1에 그대로 옮기지 말고 실행 시점에 재확인하라.
4. **proposals 디렉토리는 첫 제안서 작성 시 생성한다:** `docs/improvement-260704/proposals/`.
5. **PROJECT_IDENTITY.md:63은 이미 개명되었다.** step-01 실행 시 F2의 함께-갱신 grep(`grep -rn "Simplify Decision"`)에 PROJECT_IDENTITY가 잡히지 않는 것이 정상이다.

## 5. 후속 과제 (이번 라운드 범위 밖, 최종 보고서에서 재평가)

- 01-DIAGNOSIS "제외한 항목" 3건: subagent 이중 리뷰 부담, `topic-log.py` 1,524줄 분할, maintainer skill 미러 구조 — 제외 판단은 타당하다 (각각 게이트 약화 위험 / 이득 불분명한 대형 리팩터링 / 범위 밖 명시).
- CLAUDE.md 신호 3(topic artifacts + derived status 조건)과 `using-as-usual` 신호 3(조건 없음)의 미세한 문구 차이 — 이번 라운드 비대상이나, step-10 문서 동기화 시 눈에 띄면 함께 정리 가능.

---

## 검토에서 직접 수정한 파일 목록

| 파일 | 변경 |
| --- | --- |
| `PROJECT_IDENTITY.md` | :63 "Simplify cleanup" → "Code cleanup" (C2) |
| `working-dir/02-DECISIONS.md` | D4 커밋 주체 정리, D5 신설, "컨트롤러에 보고" → "사용자에게 보고", 제안서 경로 (C1/C3/C4) |
| `working-dir/00-README.md` | 프로토콜 규칙 1 커밋 주체, 제안서 경로 2곳, 보고 대상 (C3/C4) |
| `working-dir/step-02-path-consistency.md` | 발생 수치 정정 + 비명령 placeholder 치환 규칙 추가 (I1) |
| `working-dir/step-04-clarification-routing.md` | 제안서 경로, 보고 대상, non-material 델타 가드레일 (C3/C4/I2) |
| `working-dir/step-05-finding-dispositions.md` | 제안서 경로 (C3) |
| `working-dir/step-06-terminal-states.md` | 제안서 경로, 보고 대상, Inviolable 명확화 항목(D5), blocked 공백 가드레일 (C1/C3/C4/I3) |
| `working-dir/step-07-template-language-policy.md` | 제안서 경로 (C3) |
| `hand-off/01-IMPROVEMENT-PLAN.md`, `hand-off/README.md` | 제안서 경로만 현행화 (C3; 그 외 스냅샷 불변 유지) |
