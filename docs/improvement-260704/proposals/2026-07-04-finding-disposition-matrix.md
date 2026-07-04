# 개선 제안: 리뷰 finding disposition 심각도별 매트릭스 정의 (F9)

- **작성:** Fable / 2026-07-04
- **개선 축:** ② 워크플로우
- **규모:** Medium
- **상태:** 승인됨 (`02-DECISIONS.md` D3 — 매트릭스 안 사전 채택, 기록용 제안 후 바로 적용)

## 1. 문제 (근거 인용)

`templates/code-review-report.md`은 disposition 값 5개를 제공한다 (디스크 재확인, 현재 :36):

```
Disposition: fixed | blocked | rejected | user-accepted-risk | deferred
```

그러나 Critical/Important finding에 허용되는 경로는 규칙과 기계 검증 모두에서 3개뿐이다:

- `skills/review-execution/SKILL.md:22`: "Critical and Important findings must be fixed and re-reviewed to a passing result before `complete` or `follow-up-needed` finalization. If the user chooses not to fix a Critical or Important finding, record the decision and route finalization to `blocked` ..."
- `as-usual-rules/core-workflow.md:427`: "Critical and Important findings must be fixed and re-reviewed, rejected with technical reason and re-reviewed to passed, or route finalization to `blocked` under the current helper validation model." (동일 취지 :293)
- `scripts/topic-log.py:1182-1191`: `complete`/`follow-up-needed` finalize 시 최신 `review.completed` status가 `passed`이고 미해결 `critical`/`important`가 0임을 기계적으로 강제.

즉 `user-accepted-risk`, `deferred`는 Critical/Important에는 규칙상·기계상 절대 쓸 수 없는 값인데, 어느 심각도에서 허용되는지 정의한 곳이 없다.

**함정 시나리오:** agent가 Important finding에 `user-accepted-risk`를 기록하고 `follow-up-needed`로 finalize를 시도 → `validate`에서 실패. 규칙 위반이 finalize 시점에야 발견된다.

## 2. 변경 제안

**(a) 심각도별 허용 disposition 매트릭스를 `skills/review-execution/SKILL.md`의 Step 3(Handle Review Findings)에 추가한다.** 리뷰 기준의 단독 소유자는 review-execution 표면이므로 core-workflow에는 복제하지 않는다.

추가한 매트릭스(Step 3 heading 직후):

```markdown
Allowed dispositions by severity:

| Severity | Allowed dispositions |
| --- | --- |
| Critical | `fixed` (and re-reviewed to passed), `rejected` (with technical reason, re-reviewed to passed), `blocked` |
| Important | `fixed` (and re-reviewed to passed), `rejected` (with technical reason, re-reviewed to passed), `blocked` |
| Minor | `fixed`, `rejected`, `deferred` (non-blocking follow-up), `user-accepted-risk` (user explicitly accepts, recorded in `audit.jsonl`) |

`user-accepted-risk` and `deferred` are never valid for Critical or Important findings. If the user declines to fix a Critical or Important finding, the topic finalizes as `blocked`.
```

**(b) `templates/code-review-report.md`의 Dispositions 섹션에 소유자를 가리키는 한 줄 주석 추가:**

```markdown
<!-- Allowed dispositions per severity are owned by skills/review-execution/SKILL.md (Step 3). user-accepted-risk / deferred are Minor-only. -->
```

disposition 값 리스트(`fixed | blocked | rejected | user-accepted-risk | deferred`) 자체는 그대로 둔다 — Minor에서는 5개 값이 모두 합법이므로 값 목록은 유효하고, 심각도별 제약은 주석이 가리키는 소유자 표면에서 강제된다.

**(c) 정합 확인만 (변경 없음):** core-workflow.md §10(:293, :427), `skills/finalize/SKILL.md`의 상태 표(:109-111), `scripts/topic-log.py:1182-1191` — 모두 이미 매트릭스와 동일한 의미임을 확인. 3-경로 규칙을 어떤 문구로도 완화하지 않는다.

## 3. 함께 갱신할 대상 (정합성)

- `skills/review-execution/SKILL.md` (매트릭스 소유자) — 변경.
- `templates/code-review-report.md` (reviewer 산출물 템플릿) — 소유자 포인터 주석 추가.
- core-workflow ↔ finalize skill ↔ topic-log validate — 이미 정합, 확인만 (§2c).

### 대안 (반려)

매트릭스 대신 템플릿에서 `user-accepted-risk | deferred`를 **삭제**하는 최소안. 단점: Minor finding의 합법적 처분(다음 topic으로 이월 = deferred, 사용자 위험 수용 = user-accepted-risk)을 표현할 값이 사라져 agent가 `rejected`를 오남용할 수 있음. `02-DECISIONS.md` D3에 따라 매트릭스 안을 채택하고 최소안은 반려한다.

## 4. 가드레일 점검

- [x] 안전 게이트를 약화시키지 않는다 — C/I의 fixed/rejected/blocked 3-경로 규칙을 명시화만 하고 완화 문구를 넣지 않았다.
- [x] runtime ↔ maintainer 경계를 지킨다 — review-execution skill과 template은 runtime 표면이고, maintainer 규칙을 넣지 않았다.
- [x] 단일 원본 원칙 — 매트릭스는 review-execution에만 정의, core-workflow에 복제하지 않음. 템플릿은 소유자를 가리키기만 함.
- [x] machine-readable marker/status 값 보존 — disposition 값 이름과 status enum을 바꾸지 않음. `scripts/topic-log.py` 미변경.

## 5. 검증 계획

```bash
python3 -m unittest discover -s .agents/skills/sandbox-e2e-test/tests -p 'test_*.py'
grep -n "user-accepted-risk\|deferred" templates/code-review-report.md skills/review-execution/SKILL.md as-usual-rules/core-workflow.md
# 기대: 매트릭스/값은 template + review-execution에만, core-workflow에는 없음
```

추가로 `.agents/skills/verify-runtime-workflow-consistency/SKILL.md` 절차를 touched surface(review-execution, code-review-report 템플릿, core-workflow, finalize, topic-log)에 대해 수행.

## 6. 롤백

```bash
git checkout -- skills/review-execution/SKILL.md templates/code-review-report.md
```
