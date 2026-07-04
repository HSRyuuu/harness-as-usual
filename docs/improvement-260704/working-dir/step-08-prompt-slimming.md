# Step 08. 프롬프트 슬리밍: core §16 축소 + 반복 정리 (F12)

- **축:** ④ 프롬프트 (동작 보존 — 의미/게이트 변경 절대 금지)
- **규모:** Medium — 제안서 권장 (core-workflow 구조를 건드리므로 before/after를 제안서로 먼저 보이는 것이 안전)
- **대상 finding:** F12
- **선행 조건:** **step-04, 05, 06, 07이 모두 완료(또는 반려 확정)된 후.** 의미 변경 step들이 남아 있으면 슬리밍한 문장을 다시 고치게 된다.

## 문제 요약

1. core-workflow.md §16 Required Skills(:600-638)가 각 skill의 2-단락 요약을 담고 있다. 이는 각 `skills/*/SKILL.md` 서두 및 Responsibility Boundary와 실질 중복 (~40줄). §16의 고유 정보는 **트리거 조건(언제 어느 skill)** 뿐이다.
2. `skills/start-work/SKILL.md:29-34` Routing Principle bullet이 core §4(:179-186)와 준-verbatim 중복. (start-work는 Route Table을 "core §4 참조"로 처리하면서(:38) 원칙 bullet은 복제하고 있어 자기모순적.)
3. 같은 파일 내 반복: core-workflow에서 "Do not hand-edit" 계열이 3곳 (Inviolable :32, §2 :150, §13 :497).

## 변경 명세

### 8-A. §16을 트리거 라우팅 테이블로 축소

**원칙:** §16에서 각 skill의 "무엇을 하는지" 서술을 제거하고 "언제 부르는지"만 남긴다. 무엇을 하는지는 각 SKILL.md 소유.

**형태 (권고안 — 제안서에서 실제 내용으로 채운다):**

```markdown
## 16. Required Skills

When AsUsual is active, use `using-as-usual` first. The canonical runtime workflow is this `core-workflow.md`; each skill file owns its own detailed behavior.

| Skill | Invoke When |
| --- | --- |
| `using-as-usual` | AsUsual activates; owns activation confirmation and first reads |
| `start-work` | New topic or unclear next phase after first reads |
| `define-requirements` | Route is `requirements`, answered questions need validation, or the user asks to write/update requirements |
| `writing-plan` | User approves moving from completed requirements to plan, or asks to write/update `plan.md` |
| `executing-plan` | Requirements/plan current and the user explicitly approves or requests execution |
| `review-execution` | Execution completed, review follow-up needed, or the code cleanup decision is pending |
| `cleanup-code` | Review recorded and the user approves code cleanup |
| `finalize` | Review and cleanup decision recorded |
| `git-action` | Topic finalized and the user chooses `none` / `commit` / `commit + push` / `commit + push + PR` |
| `manage-self-improvement` | Triggered by `finalize` before topic closure |
| `search-long-term-memory` | Read-only recall from `.as-usual/memory/*`; typically as a subagent |
```

**동작 보존 체크 (핵심):** 현재 §16 산문에는 표로 옮기면 사라질 수 있는 **규범 문장**이 섞여 있다. 삭제 전에 §16 전문을 정독하고, 아래 유형의 문장이 다른 곳(해당 SKILL.md 또는 core의 해당 §)에 이미 존재하는지 문장 단위로 대조하라. 없으면 **삭제하지 말고 소유자 파일로 이동**한다:

- "`define-requirements` ... cannot be paused mid-synthesis" 계열 → §6(:314)에 이미 있음 → 확인 후 §16에서 제거 가능
- "`executing-plan` ... invokes `review-execution` after execution completion" → §9/§10 및 executing-plan skill에 있음 → 확인
- "`git-action` ... stages paths explicitly ..." → §12 및 git-action skill에 있음 → 확인
- 이 대조 결과(문장 → 이미 존재하는 위치 매핑 표)를 제안서에 포함하라. **하나라도 대응 위치가 없으면 그 문장은 이동 처리.**

### 8-B. start-work Routing Principle 중복 제거

`skills/start-work/SKILL.md` Routing Principle(:27-34)을 다음으로 교체:

```markdown
## Routing Principle

Use the canonical routing principle and Route table in `core-workflow.md` §4 (Start Work Gate Routing); do not maintain a second copy here. Treat the High-Risk Operation Gate as a hard gate, and when borderline, choose the heavier gate.
```

(High-Risk/heavier-gate 문장은 안전 중복으로 의도적으로 유지한다.) Route Table 섹션(:36-38)은 이미 참조형이므로 그대로.

### 8-C. core 내부 반복 정리 (보수적으로)

- "Do not hand-edit topic.md/audit.jsonl" 3곳 중: Inviolable(:32)과 §13(:497)은 **유지** (안전 중복 + 상세 규칙 위치). §2(:150)의 해당 문장은 §13을 가리키는 참조로 축약 가능한지 검토. **판단이 애매하면 유지한다 — 이 step에서 안전 중복 제거는 loss가 더 크다.**
- 각 skill의 "Follow Clarification Routing ..." 반복(9회)은 **모두 유지**. phase별 진입점마다 상기시키는 의도적 중복이다. (step-04가 이 문구들을 이미 정합화했음.)

## 가드레일

- [ ] **게이트/의미 문장은 한 글자도 삭제만으로 처리하지 않는다** — 삭제 전 "다른 곳에 존재" 증거를 문장 단위로 만든다 (8-A 대조 표).
- [ ] machine-readable 값(phase/next-action/status/이벤트 이름) 불변.
- [ ] reviewer 체크리스트를 core로 가져오거나 core 규칙을 reviewer로 내리는 이동 금지 (ownership 불변).
- [ ] step-04/05/06/07이 만든 새 문장을 훼손하지 않는다 — 슬리밍 대상에서 그 diff 영역을 제외하고, 겹치면 의미 유지 확인.

## 검증

```bash
python3 -m unittest discover -s .agents/skills/sandbox-e2e-test/tests -p 'test_*.py'
wc -l as-usual-rules/core-workflow.md    # 감소 확인 (기록용)
# verify-runtime-workflow-consistency (필수) + verify-runtime-surface 절차 수행
```

추가 탁상 검증: §16 표만 보고 "리뷰 완료 후 사용자가 cleanup을 승인" 상황에서 어느 skill을 불러야 하는지 판정 가능한지 확인 (기대: `cleanup-code`).

## 완료 기준 (DoD)

- [ ] 제안서(8-A 대조 표 포함) 승인 후 적용.
- [ ] §16이 트리거 테이블로 축소되었고, 유실된 규범 문장이 0건임이 대조 표로 입증된다.
- [ ] start-work 중복이 참조로 대체되었다.
- [ ] verify-runtime-workflow-consistency에서 새 불일치 없음.

## 롤백

`git checkout -- as-usual-rules/core-workflow.md skills/start-work/SKILL.md`
