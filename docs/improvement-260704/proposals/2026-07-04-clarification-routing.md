# 개선 제안: Clarification Routing 재정의 (focused/broad 모델)

- **작성:** Fable / 2026-07-04
- **개선 축:** ② 워크플로우
- **규모:** Large
- **상태:** 승인됨 (사전 결정 `02-DECISIONS.md` D3 — 방향 사전 승인, 기록용 제안서 후 즉시 적용)
- **대상 finding:** F8

## 1. 문제 (근거 인용)

chat 질문 허용 기준이 두 모델로 갈라져 있고, 두 모델이 서로 모순한다.

**모델 A (material 기준)** — `as-usual-rules/core-workflow.md:200-206` (수정 전 디스크 확인):

```
## Clarification Routing

When a needed decision appears during requirements, plan, or execute writing or review, route it by impact:

- If the decision is non-material (see Key Terms) and resolvable in the current turn: ask a focused chat clarification, record the answer in `audit.jsonl` through `scripts/topic-log.py`, update the affected artifact, and rerun the relevant review.
- If the decision is material, becomes a broad multi-question cycle, or changes the topic boundary: route to `define-requirements` or `start-work` and stop. Record the routing through `scripts/topic-log.py`.
- If the decision involves a high-risk operation: use the High-Risk Operation Gate.
```

즉 이 섹션은 **material이면 무조건 파일 사이클로 route-out**하고, chat은 **non-material에만** 허용한다.

**모델 B (focused/broad 기준)** — 정체성 문서와 나머지 표면 다수:

- `PROJECT_IDENTITY.md:55`: "Focused clarifications may happen in chat only when the answer is recorded in `audit.jsonl` ...".
- `as-usual-rules/core-workflow.md:277` (§5 execute 분기): "ask a focused chat clarification if the gap is a single user decision" — plan을 바꾸는(정의상 material) 결정에 chat 허용.
- `as-usual-rules/core-workflow.md:399` (§9): "If implementation reveals a new user decision that could change requirements, plan, implementation, risk, or verification [= material 정의], ... follow Clarification Routing." → 모델 A라면 무조건 route-out인데,
- `skills/executing-plan/SKILL.md:226`: 같은 상황에서 "ask a focused chat clarification when it can be resolved in the current turn" — chat 허용.
- `skills/writing-plan/plan-document-reviewer-prompt.md:58`: "If the issue reveals a **material decision** ... ask a focused chat clarification when it can be resolved in the current turn" — material에 chat 명시 허용.
- `skills/define-requirements/requirements-document-reviewer-prompt.md:50-52`: focused는 chat, broad/경계 변경은 파일.
- `CLAUDE.md:132-133`, `AGENTS.md:146-147`: 동일한 focused/broad 이분법.

`material` 정의(`core-workflow.md:45`)가 "requirements/plan/구현/위험/검증을 바꿀 수 있음"이므로, 모델 A를 문자 그대로 따르면 모델 B가 허용하는 chat clarification이 **전부 금지**되고, 모델 B를 따르면 canonical Clarification Routing을 **위반**한다. agent가 어느 쪽을 따르든 다른 규칙을 위반하는 **진짜 지시 충돌**이다.

## 2. 변경 제안

정체성 문서(PROJECT_IDENTITY)와 표면 다수가 이미 모델 B이므로, **모델 A로 기술된 Clarification Routing 한 곳을 모델 B로 정정**한다. 방향: "chat을 더 넓게 허용"이 아니라 "이미 합의된 focused/broad 기준으로 한 곳을 정합화". 초기/broad 질문의 파일 사이클 의무는 그대로 유지한다.

### (a) Key Terms에 라우팅 축 용어 추가

`material` 정의는 "기록 의무" 판별에 계속 쓰이므로 유지. 라우팅 판별용 용어 2개 신설:

**before** (`core-workflow.md:43-46`):

```markdown
## Key Terms

- **material**: a decision or change is material if it could change any of requirements, plan, implementation approach, risk, or verification. Wording, comments, path/typo corrections, and behavior-preserving step reordering are non-material.
- **non-trivial**: implementation is non-trivial if it fails any `direct-execute` allow condition (clear, trivial, low-risk, reversible).
```

**after**:

```markdown
## Key Terms

- **material**: a decision or change is material if it could change any of requirements, plan, implementation approach, risk, or verification. Wording, comments, path/typo corrections, and behavior-preserving step reordering are non-material.
- **non-trivial**: implementation is non-trivial if it fails any `direct-execute` allow condition (clear, trivial, low-risk, reversible).
- **focused clarification**: a single user decision that can be resolved in the current turn. It may be material; if so, the answer must be recorded in `audit.jsonl` through `scripts/topic-log.py`, the affected artifact must be updated, and the relevant review rerun.
- **broad ambiguity**: multiple interdependent decisions, a decision requiring a durable multi-option review, or a topic-boundary change. Broad ambiguity must go through the file-backed `define-requirements` question cycle (or `start-work` re-routing), never chat alone.
```

### (b) Clarification Routing 섹션 교체

**before** (`core-workflow.md:200-206`, §1 인용과 동일):

```markdown
## Clarification Routing

When a needed decision appears during requirements, plan, or execute writing or review, route it by impact:

- If the decision is non-material (see Key Terms) and resolvable in the current turn: ask a focused chat clarification, record the answer in `audit.jsonl` through `scripts/topic-log.py`, update the affected artifact, and rerun the relevant review.
- If the decision is material, becomes a broad multi-question cycle, or changes the topic boundary: route to `define-requirements` or `start-work` and stop. Record the routing through `scripts/topic-log.py`.
- If the decision involves a high-risk operation: use the High-Risk Operation Gate.
```

**after**:

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

순서를 High-Risk → broad → focused로 정렬하여 High-Risk Gate 우선순위를 명시적으로 최상단에 둔다.

### (c) 파급 확인만 하고 표현 유지하는 곳

아래 표면은 이미 모델 B이므로 의미 변경 없음. 재확인 결과 정합함:

| 파일 | 확인 결과 |
| --- | --- |
| `core-workflow.md` §5 (`:253-258`, `:266-271`) | "non-material → absorb / material → Follow Clarification Routing" 구조. (b) 교체 후 material 분기가 새 라우팅으로 자연스럽게 연결됨. 변경 불필요 |
| `core-workflow.md` §9 (`:399`) | "material 정의 그대로 → follow Clarification Routing" — 새 규칙에서 focused면 chat 허용되어 `executing-plan:226`과 일치 (목표 달성). 변경 불필요 |
| `core-workflow.md` §7 (`:340`) | "material ambiguity ... follow Clarification Routing" — 정합. 변경 불필요 |
| `skills/define-requirements/SKILL.md:23,243,251,277` | "Follow Clarification Routing" 참조 — 정합. 변경 불필요 |
| `skills/writing-plan/SKILL.md:28,101,249,257,287` | 동일 — 정합. 변경 불필요 |
| `skills/executing-plan/SKILL.md:92,226` | 이미 focused/broad 이분법. 정합. 변경 불필요 |
| `skills/writing-plan/plan-document-reviewer-prompt.md:58` | "material decision ... focused chat clarification / broad → define-requirements" — (a) 정의와 충돌 없음. 변경 불필요 |
| `skills/define-requirements/requirements-document-reviewer-prompt.md:50-52` | focused=chat, broad=파일 — 정합. 변경 불필요 |
| `CLAUDE.md:132-133`, `AGENTS.md:146-147`, `PROJECT_IDENTITY.md:28,55` | 이미 focused/broad — (a) 정의와 일치. 변경 불필요 |

**모델 A 잔재 표현 정정 (2곳):** 예시 라벨 `Example — material (route out)`은 "material = route out"이라는 모델 A 프레이밍이다 (예시 본문은 이미 "ask focused clarification" 이중 경로를 제시). 라벨을 `material (route via Clarification Routing)`로 교체하여 (b)와 정합화:

- `skills/define-requirements/SKILL.md:281`
- `skills/writing-plan/SKILL.md:291`

### (d) Anti-Patterns 확인

`core-workflow.md:578` "Asking initial or broad define-requirements workflow questions only in chat", `:579` "Hiding material ambiguity ... instead of resolving it through focused chat clarification or a `define-requirements` cycle" — 새 모델과 이미 일치. 유지.

### Inviolable ALWAYS 문구 결정

**before** (`core-workflow.md:38`):

```
- ask broad/material decisions via file-backed question cycles, not chat-only
```

**after**:

```
- ask broad-ambiguity decisions via file-backed question cycles, not chat-only
```

**결정 근거:** 새 focused/broad 모델에서 **material이지만 focused한 단일 결정은 (기록을 전제로) chat으로 해결 가능**하다. "broad/material"을 그대로 두면 Inviolable ALWAYS가 "material은 무조건 파일"이라는 모델 A를 다시 주입하여 새 Clarification Routing과 정면 충돌한다. 따라서 "material"을 제거하고 "broad-ambiguity"로 다듬는다. **의미는 동일하게 유지된다: broad → 파일 사이클.** material 결정의 안전장치(기록 의무)는 약화되지 않는다 — Clarification Routing의 "IF material: record ... update artifact ... rerun review"와 PROJECT_IDENTITY 실패모드 1("Material ... decisions must be recorded")이 그대로 보존한다. 초기 requirements 질문 사이클의 파일 의무는 (b) 마지막 문단 + §6 + 이 ALWAYS 문구가 함께 보장한다.

### non-material 처리 델타 (의도적 변경 — 침묵 변경 아님)

**현행** (`core-workflow.md:204`): non-material chat 답변에도 "update the affected artifact, and rerun the relevant review"를 요구.

**신규** (b): non-material이면 "record it and continue"로 종료 (artifact 갱신/재리뷰 없음).

**근거:** non-material은 정의상(`core-workflow.md:45`) requirements/plan/구현/위험/검증을 **바꿀 수 없다**. 따라서 갱신할 artifact도, 다시 돌릴 review도 없다. 현행 문구는 "non-material인데 artifact를 갱신하라"는 자기모순이었다. 신규 규칙은 이 모순을 제거한 **정합 정리**이며, 게이트 약화가 아니다 (material 답변은 여전히 artifact 갱신 + 재리뷰 강제). audit 기록 의무는 non-material에도 유지된다.

## 3. 함께 갱신할 대상 (정합성)

| 대상 | 조치 |
| --- | --- |
| `as-usual-rules/core-workflow.md` Key Terms | (a) 용어 2개 추가 |
| `as-usual-rules/core-workflow.md` Clarification Routing | (b) 섹션 교체 |
| `as-usual-rules/core-workflow.md` Inviolable ALWAYS | "broad/material" → "broad-ambiguity" |
| `skills/define-requirements/SKILL.md:281` | 예시 라벨 정정 |
| `skills/writing-plan/SKILL.md:291` | 예시 라벨 정정 |
| 그 외 §2(c) 표면 | 이미 모델 B — 변경 없음 (재확인 완료) |
| reviewer prompt 체크리스트 | 소유 규칙 유지 — reviewer prompt는 reviewer prompt에 (core로 이동 금지) |
| tests / manifests | 의미 마커·상태값 불변 — 변경 없음 |

## 4. 가드레일 점검

- [x] 안전 게이트를 약화시키지 않는다 (`PROJECT_IDENTITY.md`) — 초기/broad 파일 사이클 의무 유지, material 기록·재리뷰 의무 유지, High-Risk 우선순위 유지.
- [x] 초기/broad 질문의 파일 사이클 의무 불변 — (b) 마지막 문단 + §6 + Inviolable ALWAYS("broad-ambiguity → 파일")로 보장. ALWAYS 문구 조정은 "material" 제거뿐, "broad → 파일" 의미 동일.
- [x] chat 답변의 audit 기록 의무 유지 (material·non-material 모두 record).
- [x] material 답변 후 artifact 갱신 + 재리뷰 의무 유지.
- [x] High-Risk Gate 우선순위 유지 — (b)에서 최상단 분기.
- [x] non-material 처리 델타를 근거와 함께 명시 (위 델타 절).
- [x] runtime ↔ maintainer 경계 준수 — runtime 표면만 수정, maintainer 규칙 유입 없음.
- [x] 단일 원본 원칙 준수 — reviewer 체크리스트를 core로 복제하지 않음.
- [x] machine-readable marker/status 값 보존 — 변경 없음.

## 5. 검증 계획

```bash
python3 -m unittest discover -s .agents/skills/sandbox-e2e-test/tests -p 'test_*.py'
grep -rn "Clarification Routing" as-usual-rules/ skills/
```

- `verify-runtime-workflow-consistency` (필수) — core ↔ skill ↔ template ↔ reviewer prompt 정합.
- `verify-runtime-surface` — runtime 표면에 maintainer 규칙 유입 없음.
- `verify-as-usual-harness` — 워크플로우/hook/manifest smoke.

**탁상 검증 (새 규칙 텍스트만으로 판정):**

1. plan 리뷰 중 "재시도 3 vs 5" 단일 결정 → focused/material → chat 허용 + audit 기록 + plan 갱신 + 재리뷰.
2. 실행 중 "admin 전용으로 바꿀까?" (경계 변경 가능성) → broad → define-requirements 라우팅.
3. 실행 중 `npm install` 필요 → High-Risk Gate 우선.
4. requirements 초입 다중 옵션 3개 → broad/초기 → question-cN.md 파일 사이클.

예상 결과: 4개 모두 기대대로 판정됨.

## 6. 롤백

`git checkout -- as-usual-rules/core-workflow.md skills/define-requirements/SKILL.md skills/writing-plan/SKILL.md` (수정한 파일 한정). 제안서는 기록으로 유지.
