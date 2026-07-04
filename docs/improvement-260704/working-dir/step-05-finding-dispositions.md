# Step 05. 리뷰 finding disposition 매트릭스 정의 (F9)

- **축:** ② 워크플로우
- **규모:** Medium — **제안서 권장** (게이트 명시화이지 완화가 아니지만, disposition 값 의미 확정은 사용자 확인이 안전)
- **대상 finding:** F9
- **선행 조건:** step-01 완료

> **[2026-07-04 사전 결정 — `02-DECISIONS.md` D3]** 심각도별 disposition 매트릭스 안이 채택되었다 (§3 대안 아님). 제안서는 기록용으로 작성 후 바로 적용한다.

## 문제 요약

`templates/code-review-report.md:36`은 disposition 값 5개를 제공한다:

```
Disposition: fixed | blocked | rejected | user-accepted-risk | deferred
```

그러나 Critical/Important finding에 허용되는 경로는 규칙(core §10:420, review-execution:22)과 기계 검증(`scripts/topic-log.py:1182-1190` — complete/follow-up-needed finalize 시 review passed + 미해결 C/I 0 강제) 모두에서 3개뿐이다: **fixed(+재리뷰) / rejected(+재리뷰 passed) / blocked**. `user-accepted-risk`와 `deferred`가 어느 심각도에 허용되는지 정의한 곳이 없다.

**함정 시나리오:** agent가 Important finding에 `user-accepted-risk`를 기록하고 `follow-up-needed`로 finalize → `validate` 실패. 규칙 위반이 finalize 시점에야 발견된다.

## 절차

### 1. 제안서 작성

`docs/improvement-260704/proposals/<실행일>-finding-disposition-matrix.md`. 아래 권고 설계를 담되 원본 재확인 후 인용 갱신.

### 2. 권고 설계

**(a) 심각도별 허용 disposition 매트릭스를 `skills/review-execution/SKILL.md`에 정의한다** (Step 3: Handle Review Findings 안). review 기준의 단독 소유자는 review-execution 표면이므로 core에는 복제하지 않는다:

```markdown
Allowed dispositions by severity:

| Severity | Allowed dispositions |
| --- | --- |
| Critical | `fixed` (and re-reviewed to passed), `rejected` (with technical reason, re-reviewed to passed), `blocked` |
| Important | `fixed` (and re-reviewed to passed), `rejected` (with technical reason, re-reviewed to passed), `blocked` |
| Minor | `fixed`, `rejected`, `deferred` (non-blocking follow-up), `user-accepted-risk` (user explicitly accepts, recorded in `audit.jsonl`) |

`user-accepted-risk` and `deferred` are never valid for Critical or Important findings. If the user declines to fix a Critical or Important finding, the topic finalizes as `blocked`.
```

**(b) `templates/code-review-report.md`의 Dispositions 섹션에 한 줄 주석을 추가**해 매트릭스 소유자를 가리킨다:

```markdown
<!-- Allowed dispositions per severity are owned by skills/review-execution/SKILL.md (Step 3). user-accepted-risk / deferred are Minor-only. -->
```

**(c) 정합 확인만:** core-workflow.md §10(:420), finalize 상태 표(`skills/finalize/SKILL.md:98-103`), `scripts/topic-log.py:1182-1190` — 모두 이미 매트릭스와 동일한 의미 → 변경 불필요, 어긋남 없는지 확인만.

### 3. 대안 (제안서에 병기)

매트릭스 대신 템플릿에서 `user-accepted-risk | deferred`를 **삭제**하는 최소안도 있다. 단점: Minor finding의 합법적 처분(다음 topic으로 이월, 사용자 위험 수용)을 표현할 값이 사라져 agent가 `rejected`를 오남용할 수 있음. **매트릭스 안을 기본 권고로 하되 사용자가 최소안을 선호하면 따른다.**

## 가드레일

- [ ] C/I finding의 fixed/rejected/blocked 3-경로 규칙이 어떤 문구로도 완화되지 않는다.
- [ ] `validate`의 기계 검증(`topic-log.py:1182-1190`)은 변경하지 않는다 (이 step은 프롬프트/템플릿 정합만).
- [ ] 체크리스트/기준을 core-workflow에 복제하지 않는다 (review-execution 표면 단독 소유).

## 검증

```bash
python3 -m unittest discover -s .agents/skills/sandbox-e2e-test/tests -p 'test_*.py'
grep -n "user-accepted-risk\|deferred" templates/code-review-report.md skills/review-execution/SKILL.md as-usual-rules/core-workflow.md
# 기대: 매트릭스는 review-execution에만, core에는 없음
# verify-runtime-workflow-consistency 절차 수행
```

## 완료 기준 (DoD)

- [ ] 제안서 승인 후 적용되었다.
- [ ] 모든 disposition 값이 정확히 한 곳(review-execution)에서 심각도별로 정의된다.
- [ ] 템플릿 주석이 소유자를 가리킨다.
- [ ] 유닛 테스트 + verify-runtime-workflow-consistency 통과.

## 롤백

`git checkout -- skills/review-execution/SKILL.md templates/code-review-report.md`
