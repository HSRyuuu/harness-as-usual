# Step 06. 종단 상태 경로 설계: topic cancel + direct-execute 이후 (F10)

- **축:** ② 워크플로우 (+ script/tests 동시 수정)
- **규모:** **Large — 제안서 필수.**
- **대상 finding:** F10
- **선행 조건:** step-01, step-05 완료 (disposition/finalize 의미가 확정된 뒤가 안전)

> **[2026-07-04 사전 결정 — `02-DECISIONS.md` D3]** 권고 설계가 사전 승인되었다: `cancelled` 3표면 노출 + validate의 cancelled 면제(취소 사유 summary 필수), direct-execute는 경량 종단, self-improvement pass는 cancelled에도 실행("no candidates" 허용), cancel 시 작업 트리 잔여 변경은 사용자에게 질문. 제안서는 기록용 작성 후 바로 적용. **단, §1 사전 조사 결과가 이 설계와 충돌하면 적용 전에 멈추고 사용자에게 보고한다.**

## 문제 요약 (근거는 01-DIAGNOSIS.md F10)

상태머신에 종단 경로 2개가 비어 있다:

**(A) 중도 포기(cancel) 경로 부재 — 스크립트 반쪽 구현**

- `scripts/topic-log.py:26`: `STATUSES`에 `cancelled`가 존재하고 `finalize-topic --status cancelled`도 CLI상 가능(:1415).
- 그러나 runtime 표면(core §11:441, finalize skill:98-103)은 `complete | follow-up-needed | blocked` 3개만 노출.
- finalize 전제조건(:31-33)이 "Execution completion is recorded / Review result is recorded"를 요구 → **실행 전 단계에서 포기한 topic은 finalize에 진입 자체가 불가**, 영구 in-progress로 남는다.
- `scripts/topic-log.py:1168-1178`: `validate`가 모든 finalized topic에 review.completed + cleanup decision을 요구 → cancelled로 finalize해도 validate 실패.

**(B) direct-execute 이후 git 액션 경로 미정의**

- `direct-execute-complete` phase는 존재(`topic-log.py:44`)하나, core §5 router(:227-231)는 "record ... STOP"으로 끝난다.
- git-action은 phase `finalized`를 전제(core §12:455-456) → direct-execute로 끝난 topic은 규칙상 commit 경로가 없고, 이 제약을 명시한 곳도 없다.

## 절차

### 1. 사전 조사 (제안서 근거 확보 — 원본 무수정)

```bash
# 상태머신 전이 파악: cancelled/direct-execute 관련 전이와 next-action 매핑
grep -n "cancelled\|direct-execute" scripts/topic-log.py
# validate의 finalize 불변식 블록 정독
sed -n '1160,1200p' scripts/topic-log.py
# 기존 테스트가 finalize/validate/direct-execute를 어떻게 고정하는지
grep -n "finalize\|cancelled\|direct" .agents/skills/sandbox-e2e-test/tests/test_state_machine.py | head -40
```

조사 결과(전이 표, validate 불변식 목록, 테스트 커버리지)를 제안서 §1에 기록한다.

### 2. 제안서 작성

`docs/improvement-260704/proposals/<실행일>-terminal-states.md`. 아래 권고 설계를 기본안으로, 조사 결과에 따라 조정.

### 3. 권고 설계

#### (A) cancel 경로

1. **`scripts/topic-log.py`**: `validate`의 finalize 불변식을 상태 조건부로 수정 — `topic.finalized`의 `status == "cancelled"`이면 review.completed / cleanup decision / report 요구를 **면제**하되, 취소 사유 summary는 요구한다. (기존 complete/follow-up-needed 불변식(:1182-1190)은 그대로.) `blocked`는 현행 유지 — 조사에서 blocked가 이미 면제인지 확인하고 제안서에 명시.
2. **core-workflow.md §11**: 최종 상태에 `cancelled` 추가 + 진입 규칙 1줄: 사용자가 topic 포기를 명시하면 어느 phase에서든 `finalize-topic --status cancelled --summary "<취소 사유>"`로 종료할 수 있다. cancelled finalize는 execution/review 전제조건을 요구하지 않는다.
3. **`skills/finalize/SKILL.md`**: 상태 표에 `cancelled` 행 추가 ("사용자가 topic 중단을 명시적으로 선택; 남은 작업과 사유를 summary에 기록"). 전제조건 섹션에 cancel 예외 명시: "cancelled 종료 시 execution/review 전제조건은 적용되지 않는다. 단, 사용자의 명시적 취소 의사와 사유 기록은 필수." Step 0(self-improvement)은 cancelled에도 실행할지 여부를 제안서에서 결정 (권고: 실행하되 "no candidates" 허용 — 실패한 topic에서도 교훈이 나온다).
4. **git-action 관계**: cancelled 후 git action 질문을 할지 결정 (권고: 작업 트리에 이 topic의 변경이 남아 있으면 "되돌릴지/남길지"를 묻고, git action 선택지는 동일하게 제공).
5. **테스트**: `test_state_machine.py`에 cancel 시나리오 추가 — (i) requirements 단계에서 cancelled finalize → validate 통과, (ii) cancelled인데 사유 없음 → validate 실패, (iii) complete finalize 불변식 회귀 없음.

#### (B) direct-execute 종단

최소 변경안(권고): **direct-execute는 finalize/git-action 경로에 합류하지 않는 경량 종단임을 명시**한다.

1. **core-workflow.md** §5 DIRECT_EXECUTE 분기 말미에 1줄 추가: direct-execute 완료 후 사용자가 commit 등 git action을 원하면 일반 대화로 처리하며, AsUsual git-action skill은 finalized topic 전용임을 명시. (직접-실행 작업은 정의상 trivial/reversible이므로 무거운 finalize 게이트에 합류시키지 않는 것이 "lightest sufficient gate" 원칙과 일치.)
2. **core-workflow.md Inviolable NEVER(:35) 범위 명확화 (`02-DECISIONS.md` D5, 사전 승인됨):** "run a git action before finalize + explicit user selection" 문구를 게이트 대상(non-direct-execute) topic 한정으로 명확화한다. 이렇게 하지 않으면 위 1번 문장이 Inviolable 규칙과 문자 그대로 충돌한다 (direct-execute topic은 finalize에 도달하지 않으므로). **게이트 의미 불변:** 사용자 명시 요청 없는 자동 git action 금지는 어떤 경로에서도 유지한다. 제안서에 Inviolable 문구 before/after를 명시한다.
3. **`skills/start-work/SKILL.md`** Required Record의 "terminal next action"에 canonical 값 명시 — 조사에서 확인한 `topic-log.py`의 실제 값(예: `direct-execute-complete` phase의 next action)을 그대로 쓴다. 스크립트와 프롬프트가 다른 값을 말하지 않게 한다.

대안(무거움): direct-execute도 mini-finalize를 요구. 권고하지 않음 — ceremony 증가가 정체성("not so much ceremony that ordinary safe work becomes impossible")과 충돌. 제안서에 대안으로만 병기.

### 4. 가드레일

- [ ] cancel이 **게이트 우회 수단이 되지 않게** 한다: cancelled topic의 미완 구현이 작업 트리에 남아 있으면 그 사실을 summary와 사용자 응답에 명시해야 한다. "cancel 후 조용히 이어서 구현"은 새 topic 또는 기존 topic 재개로만 가능함을 제안서에 명시.
- [ ] complete/follow-up-needed의 기존 기계 불변식(:1182-1190)은 한 글자도 완화하지 않는다.
- [ ] direct-execute allow/deny 조건(start-work 소유)은 변경하지 않는다.
- [ ] `topic.md`/`audit.jsonl` 수동 편집 금지 규칙 유지 — cancel도 반드시 helper 명령 경유.
- [ ] Inviolable NEVER 명확화(D5)는 문구 한정을 넘어 게이트 자체를 완화하지 않는다 — "사용자 명시 요청 없는 자동 git action 금지"는 direct-execute 경로에서도 유지.
- [ ] **blocked의 실행-전 공백을 제안서에 명시적으로 다룬다:** 조사 결과 `validate`는 blocked finalize에도 review.completed/cleanup decision/report를 요구한다(면제 아님, `topic-log.py:1169-1181`). 실행 전 단계에서 외부 입력 대기로 멈춘 topic은 (i) blocker 이벤트와 함께 active로 남겨 재개 대상으로 두거나 (ii) 사용자가 포기를 선택하면 cancelled로 종료하는 두 경로 중 무엇이 canonical인지 제안서에서 결정하고 기록한다. blocked finalize를 실행-후 전용으로 유지하는 현행 설계를 바꾸려면 사용자에게 보고 후 진행.

### 5. 승인 후 적용 순서

script + tests → core-workflow → finalize/start-work skill → 문서 확인. script와 테스트는 같은 커밋으로.

## 검증

```bash
python3 -m unittest discover -s .agents/skills/sandbox-e2e-test/tests -p 'test_*.py'   # 신규 케이스 포함 전체 통과

# 수동 스모크: 스크래치 topic으로 cancel 경로 실증
TMP=$(mktemp -d)/2026-07-04-cancel-smoke && mkdir -p "$TMP"
python3 scripts/topic-log.py init --topic-dir "$TMP" --topic 2026-07-04-cancel-smoke --initial-request "smoke" --summary "smoke" --actor claude
python3 scripts/topic-log.py finalize-topic --topic-dir "$TMP" --status cancelled --summary "user cancelled during requirements"
python3 scripts/topic-log.py validate --topic-dir "$TMP"    # 기대: 통과
python3 scripts/topic-log.py status --topic-dir "$TMP" --json

# verify-runtime-workflow-consistency + verify-as-usual-harness + verify-project-identity 절차 수행
```

## 완료 기준 (DoD)

- [ ] 제안서 승인 후 적용 (승인 전 무수정).
- [ ] cancelled가 script/core/finalize skill 세 표면에서 동일 의미로 정의된다.
- [ ] cancel 스모크가 통과하고, complete 경로 회귀 테스트가 전부 통과한다.
- [ ] direct-execute 이후 경로가 core와 start-work에 명시된다 (script 실제 값과 일치).
- [ ] `PROJECT_IDENTITY.md`/`docs/ARCHITECTURE-WORKFLOW.md`에 반영 필요 여부를 검토했고, 필요 시 갱신했다 (workflow 변경이므로 ARCHITECTURE-WORKFLOW 갱신 가능성 높음).

## 롤백

script/tests/core/skill 파일 단위 `git checkout`. 스모크 스크래치 디렉터리는 mktemp 하위라 정리 불필요.
