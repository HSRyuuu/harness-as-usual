# Step 04. Clarification Routing 재정의 (F8) ★ 최중요

- **축:** ② 워크플로우
- **규모:** **Large — 제안서 필수.**
- **대상 finding:** F8
- **선행 조건:** step-01~03 완료

> **[2026-07-04 사전 결정 — `02-DECISIONS.md` D3]** focused/broad 모델 방향이 사전 승인되었다. 제안서는 기록용으로 작성 후 바로 적용한다. 단, 권고 설계에서 벗어나는 변경이 필요해지면 적용을 멈추고 사용자에게 보고한다.

## 문제 요약 (상세 근거는 01-DIAGNOSIS.md F8)

chat 질문 허용 기준이 두 모델로 갈라져 있다:

| 모델 | 기준 | 위치 |
| --- | --- | --- |
| A. material 기준 | material이면 무조건 파일 사이클로 route-out | core-workflow.md:199-205 (Clarification Routing 섹션) |
| B. focused/broad 기준 | 단일 결정·현재 턴 해결 가능·기록 필수면 chat 허용, 다중 결정/경계 변경이면 파일 사이클 | PROJECT_IDENTITY.md:55, CLAUDE.md CONVENTIONS, core §5(:276-277), core §9(:398 문맥), executing-plan:226, writing-plan reviewer prompt:58, requirements reviewer prompt:50 |

material의 정의(core:43-45)가 "requirements/plan/구현/위험/검증을 바꿀 수 있음"이므로, 모델 A를 문자 그대로 따르면 모델 B가 허용하는 chat clarification이 전부 금지된다. **agent가 어느 쪽을 따르든 다른 규칙을 위반한다.**

정체성 문서(PROJECT_IDENTITY)와 표면 다수가 모델 B이므로, **모델 A로 기술된 Clarification Routing 한 곳을 모델 B로 정정**하는 것이 이 step의 방향이다.

## 절차

### 1. 제안서 작성 (원본 수정 전)

`docs/improvement-260704/proposals/<실행일>-clarification-routing.md`를 `_TEMPLATE.md` 형식으로 작성한다. 아래 "권고 설계"를 제안 내용으로 쓰되, 실행 시점의 원본을 다시 읽고 인용을 갱신하라.

### 2. 권고 설계

**(a) Key Terms에 라우팅 축 용어를 추가한다** (core-workflow.md Key Terms 섹션). `material`은 "기록 의무" 판별에 계속 쓰이므로 정의 유지. 라우팅 판별용 용어를 신설:

```markdown
- **focused clarification**: a single user decision that can be resolved in the current turn. It may be material; if so, the answer must be recorded in `audit.jsonl` through `scripts/topic-log.py`, the affected artifact must be updated, and the relevant review rerun.
- **broad ambiguity**: multiple interdependent decisions, a decision requiring a durable multi-option review, or a topic-boundary change. Broad ambiguity must go through the file-backed `define-requirements` question cycle (or `start-work` re-routing), never chat alone.
```

**(b) Clarification Routing 섹션을 다음 결정 규칙으로 교체한다:**

```markdown
## Clarification Routing

When a needed decision appears during requirements, plan, or execute writing or review, route it by shape:

- IF the decision involves a high-risk operation: use the High-Risk Operation Gate.
- ELSE IF it is broad ambiguity (multiple interdependent decisions, durable multi-option review, or topic-boundary change): route to `define-requirements` or `start-work`, record the routing through `scripts/topic-log.py`, and stop.
- ELSE (focused clarification, single decision resolvable in the current turn): ask in chat.
    - IF the answer is material: record it in `audit.jsonl` through `scripts/topic-log.py`, update the affected artifact (`requirements.md`/`plan.md`), and rerun the relevant review before continuing.
    - IF the answer is non-material: record it and continue.

The initial requirements question cycle is not clarification. Broad or initial define-requirements decisions always use file-backed `question-cN.md` cycles (see §6 and Inviolable Rules).
```

**(c) 파급 확인만 하고 표현은 유지하는 곳:** 아래 표면들은 이미 모델 B이므로 의미 변경 없음. 단, "material decision → route out" 같은 모델 A 잔재 표현이 있으면 (b)의 용어(focused/broad)로 맞춘다:

| 파일 | 확인 포인트 |
| --- | --- |
| core-workflow.md §5 Phase Router | requirements/plan 변경 분기의 "ELSE: Follow Clarification Routing and STOP" — 새 규칙과 모순 없는지. 특히 `:252-257`, `:265-270`의 "material" 분기가 (b) 이후에도 자연스럽게 읽히는지 |
| core-workflow.md §9 (:398) | "If implementation reveals a new user decision that could change ... follow Clarification Routing" — 새 규칙에서 focused면 chat이 허용되므로 executing-plan:226과 일치하게 됨 (목표 달성 확인) |
| skills/define-requirements/SKILL.md:23, 243, 251 | "Follow Clarification Routing" 참조가 새 규칙과 정합한지 |
| skills/writing-plan/SKILL.md:28, 101, 228, 235, 249, 257, 287 | 동일 |
| skills/executing-plan/SKILL.md:26, 92, 226 | 동일 |
| skills/writing-plan/plan-document-reviewer-prompt.md:58 | "material decision ... ask a focused chat clarification" — (a)의 용어 정의와 충돌하지 않게 문구 확인 |
| skills/define-requirements/requirements-document-reviewer-prompt.md:50-52 | 동일 |
| CLAUDE.md / AGENTS.md CONVENTIONS | "Broad ambiguity involving multiple decisions..." 문구와 (a) 정의가 일치하는지 |

**(d) Anti-Patterns 확인:** core §15의 "Hiding material ambiguity in requirements.md Open Questions instead of resolving it through focused chat clarification or a define-requirements cycle"(:578) 및 "Asking initial or broad define-requirements workflow questions only in chat"(:576)은 새 모델과 이미 일치 — 유지.

### 3. 가드레일 (제안서 체크리스트에 포함)

- [ ] **초기/broad 질문의 파일 사이클 의무는 절대 약화되지 않는다** (Inviolable ALWAYS "ask broad/material decisions via file-backed question cycles" — 이 문구도 (a) 용어에 맞춰 "broad decisions"로 다듬을지 제안서에서 명시적으로 다룬다. 다듬는 경우에도 의미는 "broad는 파일"로 동일해야 한다).
- [ ] chat 답변의 audit 기록 의무 유지 (기록 없는 chat 결정 금지).
- [ ] material 답변 후 영향받는 artifact 갱신 + 재리뷰 의무 유지.
- [ ] High-Risk Gate 우선순위 유지.
- [ ] **non-material 처리의 의도적 변화를 제안서에 델타로 명시한다:** 현행 Clarification Routing(:203)은 non-material chat 답변에도 "update the affected artifact, and rerun the relevant review"를 요구하지만, (b)의 새 규칙은 non-material이면 "record it and continue"로 끝난다. non-material은 정의상(core:43-45) artifact를 바꿀 수 없으므로 정합한 정리이지만, 침묵 변경이 아니라 제안서에 근거와 함께 기록한다.

### 4. 승인 후 적용 → 검증

## 검증

```bash
python3 -m unittest discover -s .agents/skills/sandbox-e2e-test/tests -p 'test_*.py'
grep -rn "Clarification Routing" as-usual-rules/ skills/ | wc -l   # 참조 지점 전수 재확인용
# verify-runtime-workflow-consistency (필수) + verify-runtime-surface + verify-as-usual-harness 절차 수행
```

추가로, 다음 시나리오를 새 규칙 텍스트만으로 판정해보는 탁상 검증(desk check)을 수행하고 결과를 보고에 포함하라:

1. plan 리뷰 중 "재시도 횟수 3 vs 5" 단일 결정 발견 → 기대: chat 허용 + audit 기록 + plan 갱신 + 재리뷰.
2. 실행 중 "이 기능을 admin 전용으로 바꿀까?" (경계 변경 가능성) → 기대: broad로 판정, define-requirements 라우팅.
3. 실행 중 `npm install` 필요 발견 → 기대: High-Risk Gate 우선.
4. requirements 작성 초입의 다중 옵션 결정 3개 → 기대: question-cN.md 파일 사이클.

## 완료 기준 (DoD)

- [ ] 제안서가 승인되었다 (승인 전 원본 무수정).
- [ ] Clarification Routing이 focused/broad 모델로 교체되고, Key Terms에 용어가 정의되었다.
- [ ] (c)의 모든 참조 지점이 새 규칙과 정합한다 (모델 A 잔재 없음).
- [ ] 탁상 검증 4개 시나리오가 기대대로 판정된다.
- [ ] 유닛 테스트 + verify-runtime-workflow-consistency 통과.

## 롤백

`git checkout -- as-usual-rules/core-workflow.md skills/` (수정한 파일 한정). 제안서는 반려 기록으로 유지.
