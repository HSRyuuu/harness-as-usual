# Step 01. Small 일괄 수정 (F1~F5)

- **축:** ① 단일 작업 + ④ 프롬프트
- **규모:** Small — 제안서 불필요, 바로 변경 + 검증
- **대상 finding:** F1, F2, F3, F4, F5 (`01-DIAGNOSIS.md` 참조)
- **선행 조건:** 없음

5개의 독립적인 소형 수정이다. 각각 별도로 적용/검증 가능하며, 하나가 막혀도 나머지는 진행한다.

---

## 1-A. F1: `writing-plan` Complete Plan 번호 오류

**파일:** `skills/writing-plan/SKILL.md` (Complete Plan 섹션, 2026-07-04 기준 :263-267)

**현재:**

```markdown
1. Fill `plan.md` `Review Status`: ...
2. Run `scripts/topic-log.py complete-plan` to record `plan.completed`.
3. Confirm derived status now routes to execution approval.
5. Tell the user the plan is ready and ask them to review `plan.md` ...
6. Stop.
```

**변경:** `5.` → `4.`, `6.` → `5.` 로 번호만 수정. 내용 변경 금지.

---

## 1-B. F2: `templates/report.md` legacy `Simplify Decision` 개명

**파일:** `templates/report.md:34`

**현재:**

```markdown
## Simplify Decision
```

**변경:**

```markdown
## Code Cleanup Decision
```

**함께 갱신할 파일 (필수 확인):**

1. `grep -rn "Simplify Decision" .` 로 이 heading을 참조하는 모든 곳을 찾는다. 특히:
   - `skills/finalize/SKILL.md` — report 작성 지시가 섹션명을 직접 인용하는지 확인 (2026-07-04 기준 인용 없음, "code cleanup decision and result"라는 표현만 있음 → 이미 새 이름과 정합).
   - `.agents/skills/sandbox-e2e-test/tests/*.py` 와 `.agents/skills/analyze-e2e-results/` — 테스트/린터가 report 템플릿의 섹션명을 검사하는지 grep로 확인. 검사한다면 테스트도 함께 갱신.
   - `docs/ARCHITECTURE-WORKFLOW.md` — report 템플릿 섹션 목록을 기술하고 있으면 함께 갱신.
2. `scripts/topic-log.py`는 report의 섹션명을 파싱하지 않는지 확인: `grep -n "Simplify" scripts/topic-log.py` (기대: `skip-simplify` deprecated alias만 존재, report 섹션 파싱 없음).

**주의:** 템플릿 heading은 machine-readable marker일 수 있다. 위 grep에서 이 heading에 의존하는 코드가 발견되면, 코드와 템플릿을 **같은 커밋**에서 함께 바꾼다.

---

## 1-C. F3: controller 위임 문단 verbatim 중복 제거

**파일:** `as-usual-rules/core-workflow.md` §3 (:168)과 `skills/using-as-usual/SKILL.md` (:48)

두 파일에 동일 문단이 글자 단위로 중복되어 있다:

> "For topics with many or large artifacts, you may delegate artifact inventory and status summarization to a subagent to keep the controller's context clean when the host supports it. This does not replace controller first reads: ... The controller remains the owner of gate decisions, approvals, artifact edits, and completion claims, and does not delegate those."

**소유권 결정:** first-read의 상세 행동 절차는 `using-as-usual`이 소유한다 (core-workflow.md §16: "`using-as-usual` is the activation and first-read helper"). core §3는 gate 원칙만 유지한다.

**변경:**

- `skills/using-as-usual/SKILL.md`: 문단 **그대로 유지** (변경 없음).
- `as-usual-rules/core-workflow.md` §3: 해당 문단을 다음 한 문장으로 교체:

```markdown
Artifact inventory and status summarization may be delegated to a subagent per `using-as-usual`, but the controller must directly read the canonical artifact needed for any gate decision, approval request, artifact edit, or completion claim, and never delegates those decisions.
```

**가드레일:** "controller가 gate 결정/승인/완결 주장을 위임하지 않는다"는 안전 규칙이 core에서 사라지면 안 된다. 위 대체 문장에 그 규칙이 유지되는지 확인하라.

---

## 1-D. F4: `finalize` 전제조건 자기참조 해소

**파일:** `skills/finalize/SKILL.md` Preconditions (:35)

**현재 (Preconditions 목록의 마지막 항목):**

```markdown
- The self-improvement pass has been run via `manage-self-improvement`, and its result is recorded (applied, skipped with reason, or "no candidates").
```

**변경:** 이 항목을 Preconditions에서 **삭제**한다. 이 요구는 이미 두 곳에 올바르게 존재한다:

- `Step 0: Self-Improvement Pass` — finalize가 스스로 수행
- Anti-Patterns: "Closing the topic without running the self-improvement pass."

삭제 후, Step 0 서두에 다음 한 문장이 없다면 추가한다 (닫기 전 완료 보장을 workflow 쪽으로 이동):

```markdown
Do not proceed to Step 1 until this pass has a recorded result (applied, skipped with reason, or "no candidates").
```

**함께 확인:** core-workflow.md §11 Finalize Rules (:446)는 "Before writing `report.md` and setting final status, run one self-improvement pass"라고 되어 있어 이미 "finalize 내부 수행"으로 기술함 → core는 변경 불필요. 확인만 하라.

---

## 1-E. F5: `finalize`에 `validate` 실행 단계 추가

**파일:** `skills/finalize/SKILL.md` Step 1 (Final Record Check)

**근거:** core-workflow.md:520 "Run `scripts/topic-log.py validate --topic-dir <topic-dir>` before claiming a topic is structurally complete." — 그러나 finalize skill은 validate를 언급하지 않는다. 스크립트에는 finalize 불변식 검증이 이미 구현되어 있다 (`scripts/topic-log.py:1168-1191`).

**변경:** `skills/finalize/SKILL.md` Step 1의 수동 체크리스트 앞 또는 뒤에 다음을 추가:

```markdown
Run the structural validator and treat a failure as a blocker:

```bash
python3 <plugin-root>/scripts/topic-log.py validate --topic-dir <topic-dir>
```

If validation fails, route back to the owning phase or report the missing helper capability. Do not finalize while `validate` fails.
```

(경로 표기는 step-02 이후 규칙과 맞추기 위해 `<plugin-root>` placeholder를 사용한다. step-02가 다른 표기를 canonical로 정하면 그에 따른다.)

**주의 — 실행 순서 문제:** `validate`의 finalize 불변식(:1168)은 `topic.finalized` 이벤트가 **존재할 때** 검사된다. 즉 Step 1(finalize-topic 실행 전)에 돌리면 finalize 불변식은 건너뛰고 구조 검증만 수행된다. 따라서 **Step 2의 `finalize-topic` 실행 직후에도 validate를 한 번 더 실행**하도록 Step 2 말미에 동일 명령을 추가하라 ("Confirm `status --json` derives phase `finalized`" 항목 옆).

---

## 검증 (이 step 전체)

```bash
# 1. 유닛 테스트 (템플릿/heading 참조 테스트 회귀 확인)
python3 -m unittest discover -s .agents/skills/sandbox-e2e-test/tests -p 'test_*.py'

# 2. 잔존 확인
grep -rn "Simplify Decision" . --include='*.md' | grep -v docs/improvement-260704   # 기대: 없음
grep -c "does not delegate those" as-usual-rules/core-workflow.md                    # 기대: 0
grep -c "does not delegate those" skills/using-as-usual/SKILL.md                     # 기대: 1

# 3. 의미 정합
# .agents/skills/verify-runtime-workflow-consistency/SKILL.md 절차 수행
```

## 완료 기준 (DoD)

- [ ] 5개 수정이 각각 적용되었거나, 적용 불가 사유가 보고되었다.
- [ ] `Simplify Decision`을 참조하던 코드/테스트/문서가 함께 갱신되었다.
- [ ] core §3에 controller 비위임 안전 규칙이 유지되어 있다.
- [ ] 유닛 테스트 전체 통과.
- [ ] `verify-runtime-workflow-consistency` 절차에서 새 불일치가 없다.

## 롤백

파일 단위 `git checkout -- <file>`. 수정 파일: `skills/writing-plan/SKILL.md`, `templates/report.md`, `as-usual-rules/core-workflow.md`, `skills/finalize/SKILL.md` (+ 1-B에서 발견된 참조 파일).
