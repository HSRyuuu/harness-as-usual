# ② skills/ — 런타임 스킬 15개 리뷰

잣대와 표기는 [01-rules.md](01-rules.md)와 동일. 파일 순서는 진입 → 오너 → 스텝 →
유틸.

---

## 공통 발견 — 전 스킬 관통

### F2-0. Anti-Patterns 목록의 재진술 비중 `[줄여도 안전(선별)]`

15개 스킬 중 11개가 7~9항목의 Anti-Patterns로 끝난다(합계 ~100줄). 항목의
대부분은 본문 규칙의 부정형 재진술이다. 예로 `gathering-context`의 9항목은
전부 본문에 이미 있는 문장의 반전이다.

**단, 전량 삭제는 권고하지 않는다.** 파일 끝의 부정형 요약은 프론티어 모델에도
작동하는 salience 장치이고, 일부 항목은 본문에 없는 고유 정보를 담는다(예:
`review-execution`의 "Forcing fixes for Minor findings", `git-action`의
"Reporting success for a step that did not run"). 권고: 스킬당 3~5개로 선별 —
**본문 문장의 단순 반전은 삭제, 교차 파일 규칙이나 관찰된 실패 모드를 담은 것만
유지.** 예상 절감 ~50줄.

### F2-0b. 하드코딩된 한국어 문자열 3곳 `[줄여도 안전]`

`write-plan:96`("인라인으로 실행합니다"), `review-execution:92`,
`finalize:92-99`에 사용자 발화 예시가 한국어 리터럴로 박혀 있다. core-rules §3은
"사용자의 대화 언어로 쓰라"고 명시하므로 비한국어 사용자에게는 모순 신호다.
내용 요소만 지시하고("in the user's language") 리터럴은 제거하거나 예시임을
표시하라. finalize의 git 4선택지 목록 자체는 core rule 4의 표면이므로
`[유지 — 암묵지]` — 열린 "다음은요?" 질문으로 대체되면 안 된다.

---

## using-as-usual (150줄) — 판정: **적정**

진입 스킬로서 분류·재개·활성화 판정을 소유하며, 절차 대부분이 레코드 층이다.

- "Verify before trusting"(다른 세션의 기록은 claim) — `[유지 — 암묵지]`. 지시가
  없으면 모델은 기록을 사실로 읽는다. 이 시스템에서 가장 가치 있는 문단 중 하나.
- pre-v2 레코드 식별 목록(`topic.md`, `journal.jsonl`…) — 유지. 모델이 알 수 없는
  역사적 사실.
- Activation 4조건 — 훅이 한 문장만 주입하는 설계상 이 스킬이 소유하는 게 맞다. 적정.
- 소폭: "Three Ways In"의 세 줄과 Resuming §1의 분기 서술이 일부 겹친다. 통합하면
  ~5줄 절감되나 우선순위 낮음.

## run-topic (69줄) — 판정: **모범적**

선언 매트릭스 + 게이트 + 라우팅 예외 3개만 있고 절차가 없다. 이 리팩터링이 의도한
"오너는 선언, 스텝은 공유"가 가장 잘 구현된 파일. **다른 파일을 다이어트할 때의
기준점으로 삼을 것.**

## run-direct-work (80줄) — 판정: **적정**

- "zero questions is normal", "This is the closest thing AsUsual has to plain
  plan-mode: you are trusted with most of the decisions" — 판단층 위임의 명문화.
  `[유지]`.
- 재분류 신호 4개(계약/제품 표면 목록 포함) — `[유지 — 암묵지]`. direct-work가
  topic을 잠식하는 것을 막는 실질 경계.
- 부수 발견(과잉 아님): 파이프라인 다이어그램에는 `cleanup-code`가 없는데 표에는
  optional 행이 있다. 개선 작업 시 다이어그램에 `cleanup-code?`를 추가해 일치시킬 것.

## run-issue (119줄) — 판정: **적정**

세 오너 중 유일하게 절차(조사 루프)를 소유하는데, 그 절차의 골격이 사실상 레코드
층이다 — hypothesis 이벤트, evidence 없는 confirm 거부, retraction 절차, "Record
before the turn ends". 모두 스크립트 어휘와 1:1이거나 세션 생존성을 지키는 규칙.

- "Retract promptly — a confirmed item that turns out wrong must be cancelled" —
  `[유지 — 암묵지]`. 모델은 지시 없이는 뒤집힌 결론을 조용히 덮어쓴다.
- "Do not ask the git-action question by default" — `[유지]`. finalize 기본
  동작에 대한 이슈 고유의 오버라이드.
- Anti-Patterns 8개 중 "Writing conclusion.md after recording closure" 정도만
  고유 정보, 나머지는 F2-0 대상.

## gathering-context (105줄) — 판정: **부분 과잉**

인터뷰 스타일(질문마다 추천안, 판단 질문은 하나씩, 의존성 순서)은 이 제품의 정체성
결정이므로 `[유지]`. 그러나:

### F2-1. 숫자 미세관리 `[줄여도 안전]`

> "**Batch independent facts** — 1 to 5 at a time is fine"

몇 개를 묶을지는 프론티어 판단이다. "Batch independent facts; ask judgment calls
one at a time"이면 충분하고 숫자는 델타가 없다.

> "If a question keeps failing to converge after about three rounds…"

수렴 실패 시 탈출 규칙 **자체는** `[유지 — 암묵지]` — 없으면 무한 인터뷰나 무단
진행 양극단으로 간다. 숫자만 부드럽게 두거나 빼도 된다(현재도 "about"이라 소프트).

### F2-2. Anti-Patterns 9개 전원 본문 재진술 — F2-0의 최다 사례

## write-requirements (95줄) — 판정: **적정, 소폭 중복**

- "Do not guess and do not invent a placeholder. Call gathering-context with just
  that item." — `[유지]`. 공백을 만나면 채워버리는 것이 모델 기본 행동이다.
- quality reference를 "reference, not a gate"로 선언한 문단 — `[유지]`. ③층
  리뷰에서 보듯 이 선언이 없으면 참조 문서가 게이트로 오독된다.

### F2-3. 섹션 표가 템플릿 주석과 이중 기술 `[줄여도 안전]`

Writing 절의 6행 표(Goal/Scope/…)는 `templates/requirements.md`의 섹션별 주석과
같은 내용이다. 소유를 템플릿에 두고(작성 시점에 보이는 위치) 스킬에서는 "follow
the template" 한 줄로 참조하라. `write-plan`의 5행 표도 동일(→ F2-5).

## write-plan (121줄) — 판정: **적정, 소폭 과잉**

- "A plan written without looking at the files it names is a guess." — `[유지 —
  암묵지]`. 한 문장으로 최대 델타를 내는 좋은 예.
- Review 절 3단계는 core rule 7의 실행 절차 — 레코드 층, 유지.
- "Treating the review as a formality — reading the plan and finding nothing
  every time" — `[유지]`. 게이트 형해화라는 실제 실패 모드.
- F2-5: 섹션 표 이중 기술 (F2-3과 동일 패턴).
- F2-0b: 한국어 리터럴.
- "How the work gets executed … is your call. Do not ask the user to choose." —
  판단층 위임 명문 `[유지]`.

## execute-plan (106줄) — 판정: **적정**

- "The plan arrives already reviewed … Do not re-review it here." — `[유지]`.
  단계 경계를 지키는 고유 규칙.
- "When The Plan Is Wrong" 3분기(경미 적응/접근 변경 중단/3회 실패) — 유용한
  경계 지식이나, 3회 실패 규칙은 core-rules §6과 이중 소유(F1-2). 이쪽을 소유로.
- 태스크당 record 커맨드 예시 2개 — 적정. 어휘 관례를 보여주는 최소량.

## review-execution (110줄) — 판정: **적정**

- Severity 표와 Dispositions 3종(fixed/rejected/accepted-by-user) — 레코드 층.
  `[유지]`. 특히 "accepted by the user — the user was told the risk in plain
  terms"는 삭제 시 복원 불가능한 규약.
- "The implementer does not clear their own work." — `[유지 — 암묵지]`.
- "Do not call a host slash command such as `/simplify`" — 호스트 구체 언급이지만
  실제 혼동 지점을 막는 저비용 한 줄. 유지 무방.
- F2-0b: 한국어 리터럴.

## cleanup-code (92줄) — 판정: **적정**

적용 기준 5개(behavior-preserving, 표면 내부, 합의 일치, 저위험, 검증 가능)와
"No safe cleanup found is a perfectly good outcome"은 정리가 스코프 크리프로
번지는 것을 막는 준레코드 층. "Run them as parallel subagents when the host
supports it … How you run them is your call"로 실행 방식은 위임 — 균형이 좋다.

## finalize (114줄) — 판정: **적정**

- Cancelled 문단 전체 — `[유지 — 암묵지]`. "Cancelling is not a way past a
  gate", 남은 변경 revert/keep 질문, 취소여도 메모리 패스 실행("An abandoned
  unit often carries the most useful lesson") 모두 지시 없이는 복원 안 되는 결정.
- Record Check 5항목 — "기록이 낯선 세션을 실어 나를 수 있는가"라는 목적 기준이
  분명해 체크리스트여도 과잉이 아니다.
- F2-0b: git 4선택지 한국어 리터럴(선택지 구조 자체는 유지).

## git-action (112줄) — 판정: **부분 과잉**

레코드 층 골격(사용자 선택 없이 실행 금지, `git add .` 금지, main 푸시 확인,
force-push 금지, sealed record 분기)은 전부 `[유지]`. sealed/open 분기 설명은
"This is by design, not a gap" 문장 덕에 게이트 우회 시도를 막는다 — 유지.

### F2-4. 커밋 분할 숫자 가이드 `[줄여도 안전]`

> "As a rough guide, 3+ changed files usually means at least 2 commits, 10+
> usually means several."

원자적 커밋 분할("Split by what can be reverted independently")은 원칙만으로
프론티어 모델이 판단한다. 숫자 휴리스틱은 델타가 없고, 오히려 3파일 1관심사
변경을 기계적으로 쪼개는 역효과 여지가 있다. 원칙 문장만 남겨라.

"the last ~30 commits, for message style" — 숫자는 예시로 무해하나 "메시지 스타일과
언어를 저장소에서 배워라"는 원칙만으로 충분. `[줄여도 안전]`.

Inspect 6항목 중 델타가 있는 것은 `.as-usual/` 처리와 무관 변경 감지 2개다.
나머지(브랜치, staged 확인)는 기본 행동. 절반으로 `[줄여도 안전(선별)]`.

## explore-codebase (95줄) — 판정: **부분 과잉**

디스패치 프로토콜은 자기완결 서브에이전트 프롬프트이므로 상세 자체는 정당하다
(자식은 대화를 못 본다). 유지 핵심: READ-ONLY 제약, UNTRUSTED 래핑, THOROUGHNESS
계약, `<results>` 출력 형태(컨트롤러 파싱용).

### F2-6. `<analysis>` 블록과 PROCEDURE 1단계 `[줄여도 안전]`

> "1. Restate the literal request, actual need, and success condition." +
> 출력에 `<analysis>` 3필드 강제

요청 재진술은 약한 모델용 사고 스캐폴드다. 프론티어 서브에이전트에는 델타가 없고
출력만 늘린다. PROCEDURE 2~5단계(최소 탐색 선택, 2웨이브 중단)도 "Stop when the
question is concretely answered; report the best answer if new waves stop
helping" 수준으로 압축 가능. `<results>` 블록만 남기는 것을 권고.

## search-long-term-memory (49줄) — 판정: **적정**

트러스트 바운더리가 safety-rules.md와 이중 진술이지만, 이 스킬은 규칙 파일을 읽지
않은 서브에이전트로 실행되는 것이 기본이므로 자기완결 재진술이 정당하다. 49줄로
이미 최소형. 유지.

## manage-self-improvement (101줄) — 판정: **적정**

two-pass 구조(제안 read-only → 사용자 항목별 승인 → 적용)는 "승인 없이 메모리
금지"라는 레코드 층의 절차적 표현이다. "Look at the gap: what was intended, what
was planned, what actually happened" — 반성의 방향을 주는 고밀도 한 문장,
`[유지]`. Timing 절(sealed 이후 요청 처리)도 스크립트 게이트와 정합. 축약 불필요.

---

## 층 종합

| 스킬 | 판정 | 주요 조치 |
| --- | --- | --- |
| using-as-usual | 적정 | — |
| run-topic | 모범적 | (기준점) |
| run-direct-work | 적정 | 다이어그램-표 일치(부수) |
| run-issue | 적정 | AP 선별 |
| gathering-context | 부분 과잉 | F2-1 숫자 제거, AP 축약 |
| write-requirements | 적정 | F2-3 표 이중 기술 해소 |
| write-plan | 적정 | F2-5 표 이중 기술, F2-0b |
| execute-plan | 적정 | F1-2 3회 규칙 소유 정리 |
| review-execution | 적정 | F2-0b |
| cleanup-code | 적정 | — |
| finalize | 적정 | F2-0b |
| git-action | 부분 과잉 | F2-4 숫자 가이드 제거 |
| explore-codebase | 부분 과잉 | F2-6 analysis 블록 제거 |
| search-long-term-memory | 적정 | — |
| manage-self-improvement | 적정 | — |

스킬 층은 리팩터링이 의도한 "선언형 + 판단 위임"이 대체로 달성됐다. 걷어낼 총량은
AP 선별 ~50줄 + 개별 finding ~30줄 수준이며, **삭제보다 중요한 것은 이중 소유
해소(F2-3/F2-5, F1-2)다.**
