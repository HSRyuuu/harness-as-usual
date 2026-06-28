# AsUsual Test Result Improvement List

## Purpose

이 문서는 실제 사용 결과와 sandbox E2E 결과를 함께 검토해 AsUsual 하네스의 문제점과 개선 후보를 정리한다. 목표는 바로 작업 topic으로 쪼갤 수 있는 개선사항 목록을 만드는 것이다.

## Evidence Read

- 실제 사용 topic: `<target-project>/.as-usual/topic/2026-06-27-expire-booking-job`
  - `topic.md`
  - `question-c1.md`
  - `requirements.md`
  - `plan.md`
  - `audit.jsonl`
  - `report.md`
  - `scripts/topic-log.py status --json --topic-dir ...`
- E2E report: `docs/test/2026-06-27-priority-e2e-codex`
  - `report.md`
  - `evidence.md`
  - `logs/artifacts/e2e-lint-result.json`
  - copied topic artifacts under `logs/artifacts/copied-topic-files/`
  - terminal/codex/backend log inventory
- E2E summary report: `docs/test/2026-06-27-priority-subagent-tdd-e2e-codex-20260627-222544`
  - `report.md`
  - `evidence.md`

## Executive Summary

AsUsual의 큰 흐름은 의도대로 작동했다. 실제 topic과 최신 E2E 모두 question -> requirements -> plan -> execution approval -> execute -> review-execution -> cleanup decision -> finalize 흐름을 끝까지 기록했다. TDD RED/GREEN evidence, final sweep, mandatory review, git action handoff도 대체로 남아 있다.

개선이 필요한 지점은 구현 단계 자체보다 "상태/판정/증거의 해석 가능성"에 몰려 있다. 특히 E2E runner는 topic이 성공적으로 finalized 되었는데도, agent가 중간에 없는 파일을 한 번 읽으려 한 exploratory command failure 때문에 전체를 `FAIL`로 판정했다. 실제 사용 topic에서는 high-risk 승인 대기, cleanup 승인, cross-host 실행 같은 중요한 흐름이 audit에 더 구조적으로 남을 필요가 보였다.

## Findings

| Priority | Area | Evidence | Problem | Improvement |
| --- | --- | --- | --- | --- |
| P0 | E2E result classification | `docs/test/2026-06-27-priority-e2e-codex/report.md` says `Overall Result: FAIL`; final topic status is `complete/finalized`; only fatal command is `cat frontend/tsconfig.app.json` missing | E2E가 "작업 성공 여부"와 "agent가 한 command 중 실패가 있었는지"를 한 판정으로 섞는다. 성공적으로 복구되거나 최종 검증에 영향 없는 exploratory failure가 전체 workflow failure로 올라간다. | E2E lint result를 `workflowOutcome`, `agentCommandHealth`, `recoveryHealth`, `artifactIntegrity`로 분리한다. 전체 실패는 phase skip, missing final verification, unreviewed failure, artifact corruption 같은 contract violation에만 부여한다. |
| P0 | Approval state modeling | 실제 topic `audit.jsonl` seq 19 says "waiting for fresh high-risk approval"; `topic-log.py status` later records approval, but approval request itself is not a first-class state | high-risk 승인 대기 상태가 `task.started` notes에 묻힌다. 사용자가 재개할 때 "지금 승인해야 하는가, 실행 중인가"를 machine-readable하게 알기 어렵다. | `approval.high_risk_requested` event를 추가하고 derived status가 `phase=executing`, `nextAction=approve-high-risk`, blocker/approval request metadata를 노출하게 한다. |
| P0 | Cleanup approval traceability | 실제 topic `report.md` says code cleanup ran by user approval; `audit.jsonl` has `code_cleanup.completed` but no explicit `code_cleanup.approved` event | optional cleanup은 사용자 승인 후에만 실행되어야 하는데, 승인 근거가 append-only log에서 직접 추적되지 않는다. 나중에 audit만 보고는 승인 여부를 검증하기 어렵다. | `code_cleanup.approved`와 `code_cleanup.skipped`를 대칭 이벤트로 표준화한다. cleanup 실행 skill은 approval event가 없으면 실행하지 않도록 규칙/검증을 추가한다. |
| P1 | Final report timestamp quality | 실제 topic `report.md`: `Completed At: 2026-06-27T (finalize)` | final report에 placeholder성 timestamp가 남았다. topic은 complete지만 user-facing handoff 품질과 자동 파싱 신뢰도가 떨어진다. | finalize/report template이 `topic.finalized.timestamp`를 그대로 사용하게 한다. `report.md` lint에 malformed timestamp check를 추가한다. |
| P1 | Cross-host continuity | 실제 topic `audit.jsonl` seq 1-20 actor is mostly `codex`, seq 21-29 actor is `claude`; initial `topic.created.data.sessionId` is empty | AsUsual은 Codex/Claude 공용 하네스인데, host 전환이 명확한 handoff event로 남지 않는다. actor mix가 정상 resume인지 accidental mixed execution인지 구분하기 어렵다. | `runtime.host_changed` 또는 `session.resumed` event를 도입한다. `runtimeHost`, `actor`, `sessionId`, `thread/session source`를 status/report에 요약한다. |
| P1 | Session metadata | E2E report improvement idea mentions session metadata; actual `topic.created.data.sessionId` is empty | E2E와 실제 사용 결과를 비교할 때 어떤 Codex/Claude session이 어떤 artifact를 만들었는지 추적이 약하다. | hook 또는 topic init에서 가능한 host session id/thread id/run id를 채운다. 비어 있으면 `unknown`으로 명시하고 report-quality warning을 낸다. |
| P1 | Report evidence completeness | Older E2E directory has only `report.md` and `evidence.md`, while newer E2E includes raw `logs/` and copied artifacts | summary-only E2E는 나중에 재검토할 때 raw evidence reconstruction이 불가능하다. | sandbox E2E skill/report generator가 raw logs and copied topic artifacts를 필수 산출물로 요구하게 한다. summary-only reports는 `evidenceIntegrity=WARNING`으로 표시한다. |
| P1 | Command failure taxonomy | `e2e-lint-result.json` has `fatal` and `expected`; expected no-match `rg` failures are ignored, but missing file `cat` is fatal even though final verification passed | command failure 분류가 너무 command-exit 중심이다. "나쁜 실패", "탐색 실패", "RED evidence", "복구된 실패"가 더 세밀히 구분되어야 한다. | command events를 목적별로 분류한다: `exploration`, `assertion`, `test-red`, `verification`, `final-sweep`. `verification/final-sweep` failure만 기본 fatal로 본다. |
| P1 | Runtime report lint | Actual `report.md` has malformed timestamp; E2E linter focuses more on topic/audit and command logs | runtime topic의 final handoff report 품질을 자동으로 잡는 검증이 부족하다. | `topic-log.py validate` 또는 별도 report lint에 required sections, valid timestamp, status/phase/nextAction consistency, verification command/result presence를 추가한다. |
| P2 | Telemetry warning noise | Latest E2E report has 19 skill telemetry warnings: skill tag values like `as-usual:using-as-usual` contain invalid characters | AsUsual 자체 runtime failure는 아니지만 stderr summary가 noisy하다. 실제 문제를 찾을 때 unrelated host telemetry warning이 앞에 노출된다. | E2E report에서 known host telemetry warnings를 separate bucket으로 분리한다. 가능하면 Codex/tooling 쪽에는 skill tag sanitization issue로 별도 추적한다. |
| P2 | Unrelated plugin manifest noise | Latest E2E report counts 240 unrelated plugin manifest warnings | E2E stderr가 AsUsual 문제와 주변 plugin 문제를 섞어 보여준다. maintainer가 매번 필터링해야 한다. | stderr parser에서 AsUsual-owned warnings, host telemetry warnings, unrelated plugin warnings를 분리하고 result severity에 반영하지 않는다. |
| P2 | Decision event phase fields | 실제 topic `audit.jsonl` seq 6-10 `decision.recorded` events have `phase: null`, `nextAction: null` | 결정 event가 어떤 lifecycle 시점의 결정인지 파생하기 어렵다. | `topic-log.py decision` 또는 호출 규칙이 current phase/nextAction을 기본 주입하게 한다. |
| P2 | Question file answer UX | 실제 `question-c1.md`는 5개 질문으로 충분히 작동했지만 답변 문장에 오타/자연어가 섞여도 parser는 문제없이 넘어간다 | 유연성은 좋지만, requirements에 반영된 결정이 원문 answer와 어떻게 정규화되었는지 기계적으로 확인하기 어렵다. | `decision.recorded.data`에 `answerRaw`, `normalizedOption`, `normalizedDecision`을 넣어 question answer normalization을 추적한다. |
| P2 | Review report artifact optionality | Both runs have `review.completed` with `report: ""` and no `code-review-report.md` when findings are zero | finding 0일 때는 합리적이지만, 리뷰 범위/검토 파일을 나중에 더 자세히 보고 싶을 때 증거가 요약뿐이다. | findings가 0이어도 optional compact review evidence를 남기는 정책을 검토한다. 예: `review.completed.data.checkedSurfaces`, `commands`, `diffScope`. |

## Improvement Backlog

### 1. Split E2E Overall Result Into Contract Outcome And Diagnostic Health

- Problem: topic이 complete/finalized 되었는데 E2E `Overall Result`가 exploratory command failure 하나로 `FAIL`이 되었다.
- Change:
  - `overallResult`를 단일 PASS/FAIL로만 두지 말고 `contractResult`, `diagnosticResult`, `evidenceResult`를 분리한다.
  - final contract failure 조건을 명시한다: phase skip, missing approval, missing requirements/plan, missing final verification, failed final sweep without recovery, missing review-execution, invalid audit.
  - exploratory command failure는 `diagnosticResult=WARNING` 또는 `agentCommandHealth=WARNING`으로 내린다.
- Acceptance:
  - 최신 priority E2E와 같은 run은 contract가 성공이면 `contractResult=PASS`, `agentCommandHealth=WARNING`으로 표시된다.
  - 실제 final verification 실패는 여전히 `contractResult=FAIL`이다.

### 2. Add First-Class Approval Request Events

- Problem: high-risk approval request가 `task.started.notes`에만 들어가 있다.
- Change:
  - `approval.high_risk_requested` event를 추가한다.
  - event data에는 `operationId`, `description`, `reason`, `rollback`, `affectedFiles`, `requestedBy`, `sourcePlanTask`를 넣는다.
  - `topic-log.py status --json`은 pending approval request를 `blockers` 또는 `approvalRequests`로 노출한다.
- Acceptance:
  - approval request 후 status는 `nextAction=approve-high-risk`를 반환한다.
  - matching `approval.high_risk`가 기록되면 request가 resolved 처리된다.

### 3. Make Optional Cleanup Decisions Auditable

- Problem: cleanup 실행 승인과 skip은 정책상 중요하지만 실제 topic에는 approval event가 없다.
- Change:
  - cleanup 실행 전 `code_cleanup.approved`를 기록한다.
  - skip 시에는 기존처럼 `code_cleanup.skipped`를 유지하되 data shape을 `approved/skipped`와 맞춘다.
  - cleanup skill은 approval event 없이 cleanup을 수행하지 않는다고 명시한다.
- Acceptance:
  - cleanup completed topic에는 항상 직전 또는 최근 decision으로 `code_cleanup.approved`가 있다.
  - finalize validation은 cleanup approved/skipped/completed 상태를 구분해 검증한다.

### 4. Harden Final Report Generation And Linting

- Problem: 실제 report에 malformed `Completed At`이 남았다.
- Change:
  - finalize에서 `topic.finalized.timestamp` 또는 status output 기반 completedAt을 사용한다.
  - `report.md` lint를 추가한다: ISO timestamp, status/phase/nextAction consistency, verification section presence, cleanup decision trace, git action section.
  - malformed timestamp는 finalize 전 warning 또는 fail로 처리한다.
- Acceptance:
  - `Completed At: 2026-06-27T (finalize)` 같은 값이 검증에서 잡힌다.
  - report와 `topic-log.py status --json`의 status/phase/nextAction이 일치한다.

### 5. Record Cross-Host Resume Metadata

- Problem: 실제 topic은 Codex에서 시작해 Claude가 이어서 실행했지만 handoff가 구조화되어 있지 않다.
- Change:
  - topic init/resume 시 `session.resumed` 또는 `runtime.host_changed` event를 기록한다.
  - event data에는 previous actor, current actor, runtime host, session/thread id, resume reason을 넣는다.
  - status/report에 host transitions summary를 표시한다.
- Acceptance:
  - actor가 바뀐 topic은 "normal cross-host resume"인지 "unexpected actor mix"인지 분석 가능하다.
  - empty session id는 report-quality warning으로 표시된다.

### 6. Require Raw Evidence For Maintainer E2E Reports

- Problem: older E2E result는 summary만 있어 raw transcript 재검토가 어렵다.
- Change:
  - `sandbox-e2e-test` result contract에 `logs/`, host transcript logs, terminal logs, copied topic files, lint JSON을 필수로 둔다.
  - summary-only result는 보존 가능하지만 `evidenceIntegrity=WARNING`으로 명시한다.
- Acceptance:
  - 새 E2E report는 raw artifact가 없으면 PASS가 될 수 없다.
  - `analyze-e2e-results` skill이 raw evidence absence를 report-quality finding으로 낸다.

### 7. Add Command Purpose Classification To Transcript Lint

- Problem: 모든 non-zero command가 같은 의미의 실패가 아니다.
- Change:
  - agent command event를 목적별로 분류한다: exploration, expected-no-match, tdd-red, verification, final-sweep, mutation, unknown.
  - `tdd-red`와 `expected-no-match`는 expected failure로 보고, `exploration`은 recovered 여부를 본다.
  - `verification`과 `final-sweep` failure만 기본 fatal로 둔다.
- Acceptance:
  - 없는 파일을 읽은 exploration command는 final verification이 통과하면 warning으로 남는다.
  - final sweep command 실패는 topic이 finalized되어도 E2E failure로 남는다.

### 8. Reduce Non-AsUsual Stderr Noise In Reports

- Problem: Codex telemetry warning과 unrelated plugin manifest warning이 report noise를 만든다.
- Change:
  - stderr parser에 bucket을 둔다: AsUsual-owned, host telemetry, unrelated plugin manifest, unknown.
  - unrelated bucket은 report에는 count만 표시하고 details는 collapsible/raw evidence로 보낸다.
  - skill telemetry warning은 AsUsual action item이 아니라 host/tooling compatibility item으로 분류한다.
- Acceptance:
  - report summary에서 AsUsual maintainers가 직접 조치할 stderr issue와 환경 noise가 분리된다.

### 9. Normalize Decision Evidence From Question Answers

- Problem: question answer 원문과 normalized decision 사이 연결은 summary prose로만 남는다.
- Change:
  - `decision.recorded.data`에 `answerRaw`, `option`, `normalizedDecision`, `constraints`를 추가한다.
  - requirements source trace가 이 normalized data를 참조할 수 있게 한다.
- Acceptance:
  - 질문 답변이 "B로 할게"처럼 자연어여도 audit에서 선택지와 normalized decision을 확인할 수 있다.

### 10. Enrich Review Evidence Without Always Writing A Full Review Report

- Problem: finding 0인 review는 `review.completed.reason`만 남아 있어 검토 범위가 짧게만 보인다.
- Change:
  - `review.completed.data`에 `checkedArtifacts`, `checkedDiffs`, `checkedCommands`, `findingIds`, `residualRisk`를 넣는다.
  - finding이 있을 때만 `code-review-report.md`를 만들되, finding 0이어도 structured compact evidence는 남긴다.
- Acceptance:
  - review report file 없이도 어떤 파일/명령/요구사항을 검토했는지 status JSON에서 확인 가능하다.

## Suggested Work Order

1. P0 approval/reporting correctness:
   - `approval.high_risk_requested`
   - `code_cleanup.approved`
   - final report timestamp lint
2. P0/P1 E2E result quality:
   - split E2E result segments
   - command purpose taxonomy
   - raw evidence contract
3. P1 traceability:
   - session/runtime host metadata
   - cross-host resume event
4. P2 maintainability:
   - stderr noise buckets
   - decision normalization
   - compact review evidence

## Non-Issues Observed

- File-backed question cycle worked: actual topic created `question-c1.md`, stopped before requirements, then reread filled answers before requirements synthesis.
- Requirements and plan gates worked: both actual and E2E topics wrote single `requirements.md` and `plan.md` before execution.
- Execution approval was recorded before implementation in both examined complete runs.
- Mandatory `review-execution` ran before finalize.
- Optional cleanup was skipped in E2E and executed in actual use according to user decision; the missing piece is audit trace shape for the approval path.
- Git action was not performed automatically; final state correctly handed off to git action decision/none.

## Candidate Next Topics

- "AsUsual approval request state and cleanup approval audit"
- "AsUsual E2E result classification and command failure taxonomy"
- "AsUsual final report lint and timestamp generation"
- "AsUsual cross-host session metadata and resume events"
