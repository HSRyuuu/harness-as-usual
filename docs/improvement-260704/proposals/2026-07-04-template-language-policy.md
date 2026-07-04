# 개선 제안: 템플릿 언어 정책 (질문 파일 canonical heading)

- **작성:** Fable / 2026-07-04
- **개선 축:** ③ 아키텍처(artifact 계약) + ④ 프롬프트
- **규모:** Medium
- **상태:** 승인됨 (`02-DECISIONS.md` D1 — 안 1 사전 선택). 기록용 제안서, 작성 후 바로 적용.
- **대상 finding:** F11

## 1. 문제 (근거 인용)

- `skills/define-requirements/SKILL.md:82`: "Each question must follow this order: `### 왜 중요한가요?`, `### Requirements 반영`, `### 선택`, options, `**추천**:`, `✅ 답변을 입력하세요.`, then `[Answer]:`." — 질문 파일의 필수 구조가 **한국어 heading으로 하드코딩**.
- `templates/question.md:16-34`: 동일한 한국어 구조(`### 왜 중요한가요?`, `### Requirements 반영`, `### 선택`, `**추천**:`, `✅ 답변을 입력하세요.`) + 한국어 placeholder.
- `templates/requirements.md:27,49,57,67,71`, `templates/plan.md:87,124`: 한국어 helper 텍스트(`없음`, `사용자 언어로 ...`) 잔존.
- 충돌 상대: `as-usual-rules/core-workflow.md:142` "Write user-facing artifact prose in the user's current or clearly preferred conversation language", `:144` "Preserve canonical filenames, template section order, and machine-readable markers", `PROJECT_IDENTITY.md`의 "언어 중립 runtime workflow" 정체성.
- 결과: 영어(또는 일본어 등) 사용자의 topic에도 한국어 heading이 강제되며, 이 heading들이 "보존해야 할 canonical marker"인지 "번역해야 할 prose"인지 정의가 없다.

## 2. 검토한 두 안

**안 1 — 영어 canonical + 사용자 언어 렌더링 (권고, 채택):**

- 템플릿의 구조 heading을 영어 canonical로 교체(`### Why This Matters`, `### Requirements Impact`, `### Options`, `**Recommendation**:`, `✅ Enter your answer.`). `[Answer]:`와 option letter 형식은 불변.
- define-requirements 규칙을 "heading은 canonical 영어를 유지하거나 사용자 언어로 일관 번역하되, **순서와 개수는 canonical 구조 고정**. `[Answer]:`와 option letter는 항상 보존"으로 재정의.
- 장점: 언어 중립 정체성과 일치, 어느 언어 사용자든 동일 규칙. 단점: 기존 한국어 topic 아카이브와 형식이 달라짐(신규 artifact에만 적용되므로 실해 없음).

**안 2 — 한국어 heading을 canonical marker로 선언 (최소 변경):**

- core-workflow marker 목록에 질문 파일 heading을 추가하고 "언어와 무관하게 보존되는 canonical marker"라고 선언.
- 장점: 변경 최소. 단점: 언어 중립 정체성과 영구 충돌, 비한국어 사용자 경험 저하.

**결정 (`02-DECISIONS.md` D1):** **안 1 채택.** §1의 사용자 정책 결정 요청은 D1로 완료됨. 아래 적용 설계는 안 1 기준이다.

## 3. 적용 설계 (안 1) — before/after

### 3.1 Canonical heading 매핑

| 위치 | Before (한국어) | After (canonical 영어) |
| --- | --- | --- |
| 왜 중요 | `### 왜 중요한가요?` | `### Why This Matters` |
| 요구 반영 | `### Requirements 반영` | `### Requirements Impact` |
| 선택 | `### 선택` | `### Options` |
| 추천 | `**추천**:` | `**Recommendation**:` |
| 답변 유도선 | `✅ 답변을 입력하세요.` | `✅ Enter your answer.` |

`[Answer]:` 마커, `X) Other` option letter 형식, `---` 질문 블록 구분, `## 💡 Question N:` 헤더는 불변.

### 3.2 함께 갱신할 파일

| 파일 | 변경 |
| --- | --- |
| `templates/question.md` | 구조 heading을 canonical 영어로 교체, placeholder 영어화, 순서/개수 유지 |
| `skills/define-requirements/SKILL.md` | 필수 순서 규칙(:82)을 새 canonical 명칭으로 재기술 + 번역 허용 규칙 추가 |
| `templates/requirements.md` | `없음` → `None`, agent 지시문(`사용자 언어로 ...`) → HTML 주석 |
| `templates/plan.md` | `없음` → `None`, agent 지시문(`사용자 언어로 성공 기준 작성`) → HTML 주석 |
| `as-usual-rules/core-workflow.md` | marker 보존 규칙(:144)에 "구조 heading은 canonical 유지 또는 일관 번역, 순서/개수 보존" 명시 |
| `skills/define-requirements/requirements-document-reviewer-prompt.md` | "User-language consistency" 체크 문구 정합, 출력 예시 `근거:` 라벨을 canonical `evidence:`로 교체 + 번역 허용 주석 |
| `skills/writing-plan/plan-document-reviewer-prompt.md` | 동일한 `근거:` → `evidence:` 정합 (자매 reviewer prompt, 동일 패턴 일관 유지) |
| `.agents/skills/sandbox-e2e-test/scripts/fill-question-answers.py` | 답변 유도선 regex를 새 canonical `✅ Enter your answer.`에 맞춤 |
| `.agents/skills/sandbox-e2e-test/tests/test_fill_question_answers.py` | 테스트 픽스처를 새 canonical heading으로 갱신 |
| `.claude/skills/sandbox-e2e-test/{scripts,tests}/...` | 위 두 파일 미러 동기화 (step-06 미러 관례) |

### 3.3 helper 텍스트 정리

- `templates/requirements.md`: `없음` placeholder → `None`. `없음 또는 해당 없음일 때도 사용자 언어로 이유를 짧게 작성` 지시문 → HTML 주석(`<!-- ... -->`), 템플릿 기존 주석 관례(:84-91)와 일치.
- `templates/plan.md`: `없음` → `None`. `Expected result: 사용자 언어로 성공 기준 작성` → HTML 주석 지시.

## 4. 가드레일 점검

- [x] 안전 게이트를 약화시키지 않는다 — heading 순서/개수 검증 규칙은 유지, 오직 언어 표기만 canonical화.
- [x] runtime ↔ maintainer 경계를 지킨다 — runtime 표면(templates/skills/core-workflow)에 maintainer 규칙 추가 없음.
- [x] 단일 원본 원칙 유지 — 필수 순서 규칙은 SKILL.md 한 곳, heading 정책은 core-workflow 한 곳.
- [x] machine-readable marker 보존 — `[Answer]:`, option letter(`A)`,`X) Other`), status 값, `---` 구분자 불변.
- [x] 기존 `.as-usual/topic/` 아카이브 재작성 없음 — 신규 artifact에만 적용.

## 5. 검증 계획

- `python3 -m unittest discover -s .agents/skills/sandbox-e2e-test/tests -p 'test_*.py'` → all pass.
- `grep -rn "왜 중요한가요" skills/ templates/ as-usual-rules/` → 없음.
- `.agents/skills/verify-runtime-workflow-consistency/SKILL.md` 절차 수행.
- (권장 후속) sandbox-e2e-test 스킬로 질문 사이클 1회 스모크 — 비용이 커서 이번 step에서는 실행하지 않고 후속 권장.

## 6. 롤백

`git checkout -- templates/ skills/define-requirements/ skills/writing-plan/ as-usual-rules/core-workflow.md .agents/skills/sandbox-e2e-test/ .claude/skills/sandbox-e2e-test/`
