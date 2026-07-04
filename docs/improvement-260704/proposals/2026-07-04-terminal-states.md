# 개선 제안: 종단 상태 경로 — topic cancel + direct-execute 이후 (F10)

- **작성:** Fable / 2026-07-04
- **개선 축:** ② 워크플로우 (+ script/tests 동시 수정)
- **규모:** Large
- **상태:** 승인됨 (사전 결정 `02-DECISIONS.md` D3/D5 — 기록용 작성 후 바로 적용)

## 1. 사전 조사 결과 (원본 무수정, 근거 인용)

step-06 §1 절차대로 read-only 조사를 수행했다. 라인 번호는 steps 01–05 적용 후의 현재 디스크 상태 기준이다.

### 1.1 cancelled / direct-execute 관련 전이 표

| 표면 | 위치(현재) | 현행 동작 |
| --- | --- | --- |
| `STATUSES` | `scripts/topic-log.py:26` | `{"active","blocked","complete","follow-up-needed","cancelled"}` — `cancelled`가 이미 enum에 존재 |
| `finalize-topic --status` choices | `scripts/topic-log.py:1415` | `sorted(STATUSES - {"active"})` = `blocked, cancelled, complete, follow-up-needed` → CLI상 `cancelled` 선택 가능 |
| `derive_status` 종단 status 파생 | `scripts/topic-log.py:365-366` | `topic.finalized` 시 `status["status"] = data.get("status","complete")` → `cancelled`가 `status --json`에 그대로 노출됨 (3번째 표면 = script status는 **이미 동작**) |
| `PHASES` | `scripts/topic-log.py:44` | `direct-execute-complete` phase가 enum에 존재하나 **이를 emit하는 전용 command는 없음** |
| `ROUTE_NEXT_ACTIONS["direct-execute"]` | `scripts/topic-log.py:102` | `"execute"` — 이는 routing 직후 "실행하라"는 next action이지 종단값이 아님 |
| direct-execute 완료 기록 경로 | core-workflow §5(:234-238), start-work(:76) | 범용 `audit` command로 `--phase direct-execute-complete --next-action <종단값>` 기록. `audit`은 `--phase`를 `PHASES`(:568), `--next-action`을 `NEXT_ACTIONS`(:572)로 검증 |
| 종단 next action canonical 값 | `NEXT_ACTIONS`(:69) | `none` (enum에 존재). direct-execute 종단 = phase `direct-execute-complete` + nextAction `none` |
| runtime 표면 status 노출 | core §11 finalize invariants, `skills/finalize/SKILL.md` Step 2 표 | `complete | follow-up-needed | blocked` 3개만 — `cancelled` 누락 (F10 핵심 불일치) |

결론: `cancelled`는 **script는 절반 구현(enum+CLI+status 파생) / prompt 표면은 0**. direct-execute 종단은 phase enum만 있고 canonical next action 문자열이 prompt에 미명시.

### 1.2 validate finalize 불변식 목록 (`validate_topic_invariants`, `scripts/topic-log.py:1151-1191`)

`finalized_events`가 비어있지 않으면(어떤 status든) 아래를 요구한다:

1. `report.md` artifact 기록됨 (:1170)
2. `review.completed` 이벤트 존재 (:1171-1175)
3. code cleanup decision 이벤트 존재 (`CODE_CLEANUP_DECISION_EVENTS`) (:1176-1179)

그리고 **`finalized_status in {"complete","follow-up-needed"}`일 때만** 추가로:

4. 최신 `review.completed` status == `passed` (:1182-1187)
5. 미해결 critical/important 리뷰 findings == 0 (:1188-1190)

### 1.3 blocked 면제 여부 — 재검증 결과

**`blocked`는 면제가 아니다.** 조사에서 재확인: `blocked`는 `{"complete","follow-up-needed"}` 조건(4·5)에는 해당되지 않아 review-passed/finding-zero 검사는 피하지만, **불변식 1·2·3(report + review.completed + cleanup decision)은 그대로 요구받는다**(:1169-1179의 `if finalized_events:` 블록이 status 무관하게 실행됨). 따라서 `finalize-topic --status blocked`는 **실행-후(post-execution) 전용**이다 — 실행/리뷰 증거 없이는 validate가 실패한다. 이는 orchestrator의 사전 검증 결과와 일치한다.

### 1.4 테스트 커버리지 (`test_state_machine.py`)

| 테스트 | 고정하는 계약 |
| --- | --- |
| `test_validate_requires_review_code_cleanup_decision_and_report_for_finalized_topic` (:534) | complete finalize에 review 증거 없으면 validate 실패(`review.completed`) |
| `test_validate_rejects_complete_finalization_after_latest_review_findings` (:556) | 나중 리뷰 findings 후 complete finalize → "latest review status must be passed" 실패 |
| `test_validate_rejects_complete_finalization_with_unresolved_important_findings` (:712) | important 미해결 시 complete finalize → "no unresolved critical or important" 실패 |
| `test_validate_accepts_legacy_simplify_decision_event` (:660) | legacy simplify decision 이벤트로도 complete finalize validate 통과 |
| `test_blocker_sets_blocked_status_and_none_next_action` (:756) | `blocker` 이벤트 → status/phase `blocked`, nextAction `none`, 재개 가능 상태 |
| `test_resolved_blocker_returns_status_to_active` (:779) | `blocker.resolved` → status `active` 복귀 |

`cancelled` / `direct-execute-complete`를 고정하는 테스트는 **없다**. 신규 필요.

**조사 결론: 사전 승인 설계(D3/D5)와 충돌 없음. 적용 진행.**

## 2. 변경 제안 (before / after)

### (A) cancel 경로

#### A-1. `scripts/topic-log.py` validate 불변식을 status 조건부로 수정

취소 사유(reason)를 finalize 이벤트 `data.cancellationReason`에 명시적으로 저장하고(사유 미제공 시 빈 문자열), validate에서 cancelled는 report/review/cleanup 면제 + 사유 필수로 검사한다.

`cmd_finalize_topic` (before):
```python
data={"status": args.status, "report": args.report},
```
(after):
```python
data = {"status": args.status, "report": args.report}
if args.status == "cancelled":
    data["cancellationReason"] = args.summary
...
data=data,
```

`validate_topic_invariants` (before):
```python
if finalized_events:
    require_invariant(status["artifacts"].get("report"), "finalized topic requires report.md artifact")
    review_events = [...]
    require_invariant(review_events, "finalized topic requires review.completed audit event")
    require_invariant(any(... CODE_CLEANUP_DECISION_EVENTS ...), "finalized topic requires code cleanup decision audit event")
    finalized_data = finalized_events[-1].get("data") or {}
    finalized_status = finalized_data.get("status")
    if finalized_status in {"complete", "follow-up-needed"}:
        ...passed / critical-important checks...
```
(after):
```python
if finalized_events:
    finalized_data = finalized_events[-1].get("data") or {}
    finalized_status = finalized_data.get("status")
    if finalized_status == "cancelled":
        require_invariant(
            (finalized_data.get("cancellationReason") or "").strip(),
            "finalized cancelled topic requires a cancellation reason summary",
        )
    else:
        require_invariant(status["artifacts"].get("report"), "finalized topic requires report.md artifact")
        review_events = [...]
        require_invariant(review_events, "finalized topic requires review.completed audit event")
        require_invariant(any(... CODE_CLEANUP_DECISION_EVENTS ...), "finalized topic requires code cleanup decision audit event")
        if finalized_status in {"complete", "follow-up-needed"}:
            ...passed / critical-important checks (문자 그대로 불변)...
```

- `complete`/`follow-up-needed` 불변식(1.2의 1–5)은 `else` 분기 안에서 **한 글자도 바뀌지 않고** 그대로 적용된다.
- `blocked`는 `cancelled`가 아니므로 `else`로 들어가 report/review/cleanup을 **현행대로** 요구받는다 → blocked finalize는 실행-후 전용 유지 (변경 없음).
- `cancelled`만 report/review/cleanup 면제, 그리고 취소 사유 필수.

#### A-2. core-workflow.md §11 — 최종 상태에 `cancelled` 추가 + 진입 규칙

(before) `- Set final topic status to `complete`, `follow-up-needed`, or `blocked`.`
(after) `- Set final topic status to `complete`, `follow-up-needed`, `blocked`, or `cancelled`.` + 진입 규칙 1줄: 사용자가 topic 포기를 명시하면 어느 phase에서든 `finalize-topic --status cancelled --summary "<취소 사유>"`로 종료 가능하며, cancelled finalize는 execution/review 전제조건을 요구하지 않는다(단, 사용자의 명시적 취소 의사와 사유 기록은 필수).

#### A-3. `skills/finalize/SKILL.md` — status 표 + 전제조건 예외 + Step 0 노트

- Step 2 status 표에 `cancelled` 행 추가: "사용자가 topic 중단을 명시적으로 선택; 남은 작업과 사유를 summary에 기록. execution/review 전제조건 면제."
- Preconditions 섹션에 cancel 예외 명시: cancelled 종료 시 execution/review 전제조건 미적용, 단 명시적 취소 의사·사유 기록 필수.
- Step 0(self-improvement)에 cancelled 노트: cancelled에도 self-improvement pass를 실행하되 "no candidates"를 허용한다(실패한 topic에서도 교훈이 나온다).

#### A-4. self-improvement pass on cancelled

**결정: 실행하되 "no candidates" 허용** (권고안 채택). core §11의 "Do not close the topic without a recorded self-improvement result (applied, skipped, or 'no candidates')" 문구는 cancelled에도 그대로 적용되며, cancelled는 "no candidates"가 정상 결과다.

#### A-5. git-action 관계 + 작업 트리 잔여 변경 질문

**결정(권고안 채택):** cancelled finalize 후에도 finalize skill Step 3의 git action 질문(`none|commit|commit + push|commit + push + PR`)은 동일하게 제공한다. 단, cancelled의 경우 이 topic의 미완 변경이 작업 트리에 남아 있으면 git action을 묻기 **전에** 사용자에게 "남은 변경을 되돌릴지/유지할지"를 먼저 묻고 그 응답을 요약에 남긴다. (finalize skill Step 2/Step 3에 반영.)

#### A-6. 테스트 (`test_state_machine.py`)

§3(A)5의 시나리오 i–iii:
- (i) requirements 단계에서 `finalize-topic --status cancelled --summary "..."` → validate **통과** (report/review/cleanup 면제).
- (ii) `finalize-topic --status cancelled`에 사유 없음(`--summary` 미제공) → validate **실패** ("cancellation reason summary").
- (iii) complete finalize 불변식 회귀 없음 — 기존 complete 경로 정상 통과(회귀 가드) 신규 케이스 추가.

### (B) direct-execute 종단

#### B-1. core-workflow.md §5 DIRECT_EXECUTE 말미 1줄

direct-execute 완료 후 사용자가 commit 등 git action을 원하면 일반 대화로 처리하며, AsUsual `git-action` skill은 finalized topic 전용임을 명시. direct-execute 종단은 finalize/git-action 경로에 합류하지 않는 경량 종단이다(정의상 trivial/reversible → "lightest sufficient gate" 원칙과 일치).

#### B-2. Inviolable NEVER 범위 명확화 (D5, 사전 승인)

Inviolable NEVER의 git action 문구를 게이트 대상(non-direct-execute) topic 한정으로 명확화.

(before, core-workflow.md `<NEVER>` 블록):
```
- run a git action before finalize + explicit user selection
```
(after):
```
- run a git action on a gated (non-direct-execute) topic before finalize + explicit user selection; on any path, never run a git action without explicit user request
```

- **게이트 의미 불변:** "사용자 명시 요청 없는 자동 git action 금지"는 direct-execute를 포함한 **모든 경로**에서 유지된다. 문구는 direct-execute topic이 finalize에 도달하지 않는다는 사실과 B-1을 정합시키되, 자동 git action 금지 자체는 강화되어 재진술된다(어느 경로에서도 금지).

#### B-3. `skills/start-work/SKILL.md` — terminal next action canonical 값 명시

Required Record의 "for direct-execute completion, the result, verification outcome, and terminal next action" 줄에 script 실제값을 명시: phase `direct-execute-complete`, terminal next action `none` (범용 `audit` command로 `--phase direct-execute-complete --next-action none` 기록). script와 prompt가 다른 값을 말하지 않게 한다.

### (C) blocked 실행-전 공백 결정 (§4 마지막 가드레일)

**결정: 재개 가능한 blocked 상태(active 계열)로 남긴다. blocked finalize는 실행-후 전용 유지(현행 불변).**

- 실행-전 단계에서 외부 입력 대기로 멈춘 topic의 canonical 경로: `scripts/topic-log.py blocker`로 blocker 이벤트를 기록한다 → `derive_status`가 status/phase `blocked`, nextAction `none`으로 파생하며(:437-438, `test_blocker_sets_blocked_status_and_none_next_action`), 이는 **finalized가 아니라 재개 대상**이다. 외부 입력이 오면 `blocker.resolved`로 active 복귀(`test_resolved_blocker_returns_status_to_active`).
- 사용자가 포기를 명시하면 그때 `finalize-topic --status cancelled`로 종료한다.
- `finalize-topic --status blocked`(종단 closure)는 실행-후 전용을 유지한다(validate 불변식 1·2·3 요구, 변경 없음). 현행 설계를 바꾸지 않으므로 사용자 보고 불필요.

### 대안 (기각) — direct-execute mini-finalize

direct-execute도 mini-finalize를 요구하는 무거운 안. **기각.** ceremony 증가가 정체성("not so much ceremony that ordinary safe work becomes impossible", `PROJECT_IDENTITY.md:47`)과 충돌한다. 병기용 기록.

## 3. 함께 갱신할 대상 (정합성)

- `scripts/topic-log.py` (`cmd_finalize_topic`, `validate_topic_invariants`) ↔ `.agents/skills/sandbox-e2e-test/tests/test_state_machine.py` — 같은 커밋(step §5 적용 순서 1).
- `as-usual-rules/core-workflow.md` §5, §11, Inviolable NEVER.
- `skills/finalize/SKILL.md` (status 표, 전제조건, Step 0, Step 2/3), `skills/start-work/SKILL.md` (Required Record).
- `docs/ARCHITECTURE-WORKFLOW.md` (finalize status 목록 stale → cancelled 추가, direct-execute 경량 종단 명시).
- `PROJECT_IDENTITY.md`: 변경 불필요(최종 arbiter). 아래 §4 참조.

## 4. 가드레일 점검

- [x] cancel이 게이트 우회 수단이 되지 않게: cancelled의 미완 변경이 작업 트리에 남아 있으면 그 사실을 summary와 사용자 응답에 명시(A-5). "cancel 후 조용히 이어서 구현"은 새 topic 또는 기존 topic 재개로만 가능함을 finalize skill에 명시.
- [x] complete/follow-up-needed 기존 기계 불변식은 한 글자도 완화하지 않는다 — `else` 분기로 이동하되 로직 문자 불변, 회귀 테스트(iii) 추가.
- [x] direct-execute allow/deny 조건(start-work 소유)은 변경하지 않는다 — B-3은 "terminal next action 값 명시"만 추가.
- [x] `topic.md`/`audit.jsonl` 수동 편집 금지 유지 — cancel도 `finalize-topic` helper 경유.
- [x] Inviolable NEVER 명확화(D5)는 게이트 자체를 완화하지 않는다 — "사용자 명시 요청 없는 자동 git action 금지"를 모든 경로에서 유지·강화 재진술(B-2).
- [x] blocked 실행-전 공백을 명시적으로 결정·기록(C): 재개 가능한 blocked 상태로 남김, blocked finalize는 실행-후 전용 유지.
- [x] runtime ↔ maintainer 경계 유지 — runtime 표면(core/skills)에는 workflow 규칙만, maintainer 규칙 없음.
- [x] machine-readable marker 보존 — 새로 노출하는 status 값 `cancelled`는 이미 `STATUSES` enum에 존재. 새 phase/nextAction 문자열 추가 없음(기존 `direct-execute-complete`/`none` 재사용). data 키 `cancellationReason` 추가(신규 마커 아님, validate 내부용).

### PROJECT_IDENTITY 정합
`PROJECT_IDENTITY.md:64` "Post-finalize git action selection is explicit; commit, push, PR, release, and deploy actions require user selection or approval." — 본 변경은 이를 강화하는 방향(모든 경로에서 자동 git action 금지)이며 충돌 없음. 편집 불필요.

## 5. 검증 계획

```bash
python3 -m unittest discover -s .agents/skills/sandbox-e2e-test/tests -p 'test_*.py'   # 신규 cancel 케이스 포함 전체 통과 기대

# 수동 cancel 스모크 (저장소 루트)
TMP=$(mktemp -d)/2026-07-04-cancel-smoke && mkdir -p "$TMP"
python3 scripts/topic-log.py init --topic-dir "$TMP" --topic 2026-07-04-cancel-smoke --initial-request "smoke" --summary "smoke" --actor claude
python3 scripts/topic-log.py finalize-topic --topic-dir "$TMP" --status cancelled --summary "user cancelled during requirements"
python3 scripts/topic-log.py validate --topic-dir "$TMP"        # 기대: OK
python3 scripts/topic-log.py status --topic-dir "$TMP" --json   # 기대: status=cancelled
```

의미 정합: `verify-runtime-workflow-consistency` + `verify-as-usual-harness` + `verify-project-identity` 절차 수행.

## 6. 적용 기록 (2026-07-04 적용 완료)

§2 제안대로 적용했고, 적용 중 발견한 정합 항목 3건을 추가로 반영했다 (모두 표면 정합 정정, 게이트 의미 불변):

1. **core-workflow §16 finalize 요약 줄**: "sets final status to `complete`, `follow-up-needed`, or `blocked`" → `cancelled` 포함으로 갱신 (§11과 동일 목록 유지). 같은 줄 앞의 "Use the `finalize` skill after ..." 문장에 cancelled 예외 추가.
2. **`docs/ARCHITECTURE-WORKFLOW.md`**: canonical flow 아래에 종단 경로 2종(gated / direct-execute) 설명 추가, finalize 섹션 status 목록에 `cancelled` 추가.
3. **maintainer skill 미러 동기화**: `test_state_machine.py` 변경을 `rsync -a --delete --exclude '__pycache__' .agents/skills/ .claude/skills/`로 `.claude/skills/` 미러에 반영.

경미한 참고 사항 (변경하지 않음, 후속 판단용): `finalize-topic`의 `--report` 기본값이 `report.md`라서 cancelled finalize에서도 이벤트 artifacts에 `report.md` 문자열이 기록된다. validate는 cancelled에서 report artifact를 검사하지 않으므로 게이트 영향은 없으나, cancelled 이벤트 메타데이터를 더 깨끗하게 하려면 `--report ""` 명시 또는 cancelled 시 기본값 무시를 후속 개선으로 검토할 수 있다 (사전 승인 범위 밖이라 이번에는 적용하지 않음).

검증 결과: unittest 55건 전체 통과(신규 3건 포함), cancel 스모크 통과(positive: validate OK + status cancelled/finalized/git-action-decision, negative: 사유 없는 cancelled → validate 실패 "cancellation reason summary"), manifest jq/hook smoke 통과, verify-runtime-workflow-consistency·verify-as-usual-harness·verify-project-identity 절차 통과. `PROJECT_IDENTITY.md`는 검토 후 무변경(충돌 없음, 본 변경이 identity를 강화하는 방향).

## 7. 롤백

`scripts/topic-log.py`, `.agents/skills/sandbox-e2e-test/tests/test_state_machine.py`, `.claude/skills/sandbox-e2e-test/tests/test_state_machine.py`(미러), `as-usual-rules/core-workflow.md`, `skills/finalize/SKILL.md`, `skills/start-work/SKILL.md`, `docs/ARCHITECTURE-WORKFLOW.md`를 파일 단위 `git checkout`. 스모크 스크래치 디렉터리는 mktemp 하위라 정리 불필요.
