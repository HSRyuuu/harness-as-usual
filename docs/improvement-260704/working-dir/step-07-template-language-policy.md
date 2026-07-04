# Step 07. 템플릿 언어 정책 결정 (F11)

- **축:** ③ 아키텍처(artifact 계약) + ④ 프롬프트
- **규모:** Medium — **제안서 필수. 사용자 정책 결정이 핵심인 step.**
- **대상 finding:** F11
- **선행 조건:** step-01 완료

> **[2026-07-04 사전 결정 — `02-DECISIONS.md` D1]** **안 1 (영어 canonical + 사용자 언어 번역 허용)이 채택되었다.** §1의 사용자 결정 요청은 완료된 것으로 간주하고, 제안서는 기록용으로 작성 후 §2 (안 1 기준)를 바로 적용한다.

## 문제 요약

- `skills/define-requirements/SKILL.md:82`가 질문 파일의 필수 구조를 **한국어 heading**으로 하드코딩: "`### 왜 중요한가요?`, `### Requirements 반영`, `### 선택`, options, `**추천**:`, `✅ 답변을 입력하세요.`, then `[Answer]:`".
- `templates/question.md`도 동일 한국어 구조. `templates/requirements.md`(:27,49,57,67,71)와 `templates/plan.md`(:26-28,87,124)에도 한국어 helper 텍스트(`없음`, `사용자 언어로 ...`) 잔존.
- 충돌 상대: core-workflow.md:139 "Write user-facing artifact prose in the user's current or clearly preferred conversation language", :141 "Preserve canonical filenames, template section order, and machine-readable markers", PROJECT_IDENTITY "언어 중립 runtime workflow 지향".
- 결과: 영어(또는 일본어 등) 사용자의 topic에도 한국어 heading이 강제되며, 이 heading들이 "보존해야 할 canonical marker"인지 "번역해야 할 prose"인지 어디에도 정의가 없다.

## 절차

### 1. 제안서 작성 + 사용자 결정 요청

`docs/improvement-260704/proposals/<실행일>-template-language-policy.md`. **이 step의 본질은 정책 결정이므로, 제안서에 아래 두 안을 나란히 제시하고 사용자에게 선택을 요청한다.**

**안 1 — 영어 canonical + 사용자 언어 렌더링 (권고):**

- 템플릿의 구조 heading을 영어 canonical로 교체 (예: `### Why This Matters`, `### Requirements Impact`, `### Options`, `**Recommendation**:`, 답변 유도선). `[Answer]:`는 현행 유지.
- define-requirements 규칙을 "heading은 canonical 영어를 유지하거나 사용자 언어로 일관 번역하되, **순서와 개수는 canonical 구조를 따른다**. `[Answer]:`와 option letter는 항상 보존"으로 재정의.
- 장점: 언어 중립 정체성과 일치, 어느 언어 사용자든 동일 규칙. 단점: 기존 한국어 topic 아카이브와 형식이 달라짐 (신규 artifact에만 적용되므로 실해는 없음).

**안 2 — 한국어 heading을 canonical marker로 선언 (최소 변경):**

- core-workflow.md:141의 marker 목록에 질문 파일 heading들을 명시적으로 추가하고, "이 heading들은 언어와 무관하게 보존되는 canonical marker"라고 선언.
- 장점: 변경 최소. 단점: 언어 중립 정체성과 영구 충돌, 비한국어 사용자 경험 저하.

**공통 (어느 안이든):** `templates/requirements.md`/`templates/plan.md`의 한국어 helper 텍스트는 다음처럼 정리한다:
- `없음` placeholder → 영어 canonical `None` (또는 안 2 선택 시 현행 유지 결정을 명시).
- `사용자 언어로 성공 기준 작성` 같은 **agent 지시문**은 사용자-facing 본문이 아니라 지시이므로 HTML 주석(`<!-- ... -->`)으로 이동하거나 영어 지시로 통일 — 템플릿의 기존 주석 관례(requirements.md:84-91)와 일치시킨다.

### 2. 결정 반영 시 함께 갱신할 파일 (안 1 기준)

| 파일 | 변경 |
| --- | --- |
| `templates/question.md` | heading 교체, 구조 유지 |
| `skills/define-requirements/SKILL.md:82` 부근 | 필수 순서 규칙을 새 canonical 명칭으로 재기술 + 번역 허용 규칙 |
| `templates/requirements.md`, `templates/plan.md` | helper 텍스트 정리 (주석화/`None`) |
| `as-usual-rules/core-workflow.md:139-143` | marker 보존 규칙에 "구조 heading은 canonical 유지 또는 일관 번역, 순서/개수 보존" 명시 |
| reviewer prompts | `requirements-document-reviewer-prompt.md`의 "User-language consistency" 체크(:37)와 출력 예시의 `근거:` 라벨 — 출력 예시 라벨도 같은 정책을 따르게 확인 (예시 내 `근거:`는 localized 라벨의 예시임을 주석으로 명시하거나 canonical로 교체) |
| 테스트 | `grep -rn "왜 중요한가요\|Answer\]:" .agents/skills/sandbox-e2e-test/` — E2E 질문 자동응답 스크립트(`test_fill_question_answers.py` 등)가 한국어 heading이나 `[Answer]:` 파싱에 의존하면 **함께 갱신** (특히 `fill_question_answers` 관련) |

### 3. 가드레일

- [ ] `[Answer]:` marker와 option letter 형식은 어떤 안에서도 변경 금지 (E2E/검증 파이프라인 의존 가능성).
- [ ] 질문 파일 구조(질문 블록 구분 `---`, 질문당 1결정, 옵션 2-5 + `X) Other`)는 언어 정책과 무관하게 유지.
- [ ] 기존 `.as-usual/topic/` 아카이브 재작성 금지 — 신규 artifact부터 적용.

## 검증

```bash
python3 -m unittest discover -s .agents/skills/sandbox-e2e-test/tests -p 'test_*.py'
grep -rn "왜 중요한가요" skills/ templates/ as-usual-rules/   # 안 1 채택 시 기대: 없음
# verify-runtime-workflow-consistency 절차 수행
# 가능하면 sandbox-e2e-test 스킬로 질문 사이클 1회 스모크 (선택; 비용 큼 — 사용자에게 실행 여부 확인)
```

## 완료 기준 (DoD)

- [ ] 사용자가 안 1/안 2 중 하나를 명시적으로 선택했다.
- [ ] heading의 marker/prose 지위가 core-workflow 한 곳에 명문화되었다.
- [ ] `[Answer]:` 및 질문 구조 불변식이 유지되었다.
- [ ] 관련 테스트(질문 파싱)가 통과한다.

## 롤백

`git checkout -- templates/ skills/define-requirements/ as-usual-rules/core-workflow.md`
