# Topic 실행 순서 (total-improvement-plan 분할)

원본: [total-improvement-plan-claude-fable.md](total-improvement-plan-claude-fable.md)

각 topic은 AsUsual 워크플로우로 순서대로 하나씩 실행한다. 하나가 끝나면(finalize + 검증 통과) 다음 topic을 시작한다.

---

## Phase 1

| 순서 | Topic | 원본 항목 | 요약 |
|---|---|---|---|
| 1 | receipt-verdict-contract | P1-1 + P1-2 + 횡단 3 | 서브에이전트는 파일에 쓰고 `경로 + 폐쇄 어휘 판정`만 반환. 판정 어휘(OKAY/ITERATE/REJECT, PASS/FAIL/INCONCLUSIVE 등)를 리뷰어 프롬프트와 topic-log.py 이벤트에 강제. 일관성 검사 항목을 verify-runtime-workflow-consistency에 추가 |
| 2 | approval-durability | P1-4 + P2-4 | 승인은 정확히 한 가지만 허가(계획 승인 ≠ 구현 허가). 승인 대기 상태를 audit.jsonl 파생 상태로 내구화. 컴팩션 복구 표준 문구(전체 재독 후 재개, 재계획 금지)를 core-workflow와 hand-off에 추가 |
| 3 | suitability-gate | P1-5 | 명확한 소규모 요청은 시그널 표(파일 경로/이슈 번호/심볼/수용 기준)로 direct-execute 직행. LIGHT/HEAVY 단방향 래칫(승급만 허용) 포함 |
| 4 | memory-write-guard | 횡단 1 | manage-self-improvement에 "회상된 기억을 근거로 새 기억을 쓰지 않는다" 규칙 추가 (자기강화 루프 차단) |

## Phase 2

| 순서 | Topic | 원본 항목 | 요약 |
|---|---|---|---|
| 5 | done-claim-adversarial-verify | P1-3 | 실행자의 완료 보고는 주장(DoneClaim)일 뿐. 독립 컨텍스트 검증자가 반증 시도, INCONCLUSIVE ≠ PASS, 표면 종류별 증거 타입(CLI 출력/스크린샷/호출 기록) 요구 |
| 6 | reviewer-calibration | P2-2 | 리뷰어 발산 방지: 이슈 상한(high-confidence 최대 3개) + "blocker-finder, not a perfectionist" + "무엇을 검사하지 않는가" 섹션 |
| 7 | subagent-delegation-contract | P2-7 | 위임 메시지에 TASK/DELIVERABLE/SCOPE/VERIFY 필수 필드 + 자기완결 메시지 + "자식 출력은 검증 전까지 CLAIM" 공통 조항. explore-codebase·implementer-prompt와 정합성 확인 |

## Phase 3

| 순서 | Topic | 원본 항목 | 요약 |
|---|---|---|---|
| 8 | blocker-classification | P2-1 | 블로커를 resolvable(에이전트가 풀 수 있음 — 멈추지 않음) / human_blocked(자격증명·외부 승인만 사용자행)로 2분류. agent-introspection-debugging 4-Phase 루프를 Failure Handling에 참조 통합 |
| 9 | plan-quality-gates | P2-3 + P2-6 | plan.md 합격 기준 = "판단 0회로 실행 가능"(References + 실행형 Acceptance + happy/failure 시나리오). 승인 직전 Intent Reconciliation 게이트로 가정 해소 항목을 사용자와 확인 |
| 10 | planner-reviewer-asymmetry | P2-5 | 수정 루프에서 계획자는 세션 재사용(맥락 = 자산), 리뷰어는 매번 새로 스폰(앵커링 제거). 호스트 미지원 시 순차 fallback |
| 11 | state-chain-guard | P2-8 | phase 전환은 이전 phase 완료 시에만 허용. 각 phase 스킬 진입 시 `status --json` 검사, corrupt-state 복구 절차 표준화. 이벤트 스키마가 안정된 마지막에 수행 |

## 제외

- P3-1 ~ P3-5: 필요가 확인될 때 개별 topic으로 결정 (P3-2는 topic 5 이후, P3-5는 안전장치 설계 선행 필수)
- Explorer agent: 이미 구현·커밋됨(`f8daa10`). topic 7에서 위임 계약 정합성만 확인

## 공통 규칙

- 각 topic 완료 시 `verify-runtime-workflow-consistency` + `verify-project-identity` 실행
- 핵심 게이트(판정 어휘, 이벤트 순서, 증거 필드)는 가능하면 topic-log.py 스크립트 레벨 검증으로 받친다 (횡단 2)
