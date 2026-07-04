# AsUsual 개선 작업 실행 가이드 (working-dir)

이 폴더는 **실행 에이전트가 이 문서들만 읽고 AsUsual 하네스 개선을 수행**할 수 있게 만든 작업 패키지다.
진단(왜)은 `01-DIAGNOSIS.md`, 실행 명세(무엇을 어떻게)는 `step-01` ~ `step-10`에 있다.

## 읽기 순서

1. `../hand-off/00-ORIENTATION.md` — 저장소 구조/불변 규칙/검증 표면 (필수 1회)
2. `../hand-off/01-IMPROVEMENT-PLAN.md` — 공통 작업 프로토콜과 검증 게이트 (필수 1회)
3. 이 파일 — step 순서와 의존성
4. `01-DIAGNOSIS.md` — 전체 문제 목록 (F1~F13, 근거 인용)
5. `02-DECISIONS.md` — **사용자 사전 결정 (승인 절차 대체)** — 반드시 읽는다
6. 착수하는 `step-XX-*.md` — 해당 step의 실행 명세

`../hand-off/02-FILE-STRUCTURE.md`는 특정 파일을 고치기 직전에 그 파일의 등급(⚠️/⛔)과 함께-갱신 대상을 확인하는 용도로만 연다.

## 이 작업의 성격 (필수 이해)

- 이것은 **plugin development**다. `.as-usual/topic/` runtime workflow를 돌리지 않는다 (사용자가 명시적으로 요구할 때만 예외).
- **최종 진실은 디스크의 원본 파일이다.** step 문서의 인용은 2026-07-04 스냅샷이므로, 수정 전 반드시 원본에서 인용문을 다시 확인하라. 인용이 원본과 다르면 그 step을 멈추고 차이를 보고하라.
- **게이트를 약화시키지 마라.** 모든 step은 "정합성 정정"이지 "게이트 완화"가 아니다. 작업 중 게이트 완화로 해석될 여지가 생기면 멈추고 제안서로 근거를 남겨라 (`PROJECT_IDENTITY.md`가 최종 기준).

## Step 목록과 실행 순서

순서는 의존성을 고려해 설계했다. **step-01 → 02 → 03은 순서대로, 04/05/06/07은 `02-DECISIONS.md`의 사전 승인 범위 안에서 제안서(기록용) 작성 후 바로 적용, 08은 반드시 04~07 완료 후, 09는 독립, 10은 마지막.**

| Step | 제목 | 규모 | 제안서 | 선행 조건 |
| --- | --- | --- | --- | --- |
| step-01 | Small 일괄 수정 (F1~F5) | Small | 불필요 | 없음 |
| step-02 | topic-log.py 경로 표기 통일 (F6) | Medium | 불필요(기계적) | step-01 |
| step-03 | 활성화 신호 정합 (F7) | Medium | 불필요(정합 수정) | step-01 |
| step-04 | Clarification Routing 재정의 (F8) | **Large** | 기록용 (방향 사전 승인 — D3) | step-01~03 |
| step-05 | finding disposition 매트릭스 (F9) | Medium | 기록용 (매트릭스 안 채택 — D3) | step-01 |
| step-06 | 종단 상태 경로: cancel/direct-execute (F10) | **Large** | 기록용 (설계 사전 승인 — D3; 조사 충돌 시 중단) | step-01, step-05 |
| step-07 | 템플릿 언어 정책 (F11) | Medium | 기록용 (안 1 채택 — D1) | step-01 |
| step-08 | 프롬프트 슬리밍: §16 축소 + 반복 정리 (F12) | Medium | 권장 | **step-04~07 완료 후** |
| step-09 | hook 호스트 분기 문서화 (F13) | Small | 불필요 ((a) 문서화 채택 — D2) | 없음 |
| step-10 | 최종 검증 + maintainer 문서 동기화 | — | — | 모든 step 종료 후 |

의존성 이유:
- step-02(경로 표기)를 먼저 하면 이후 step들이 새 표기 규칙 위에서 작업한다.
- step-04/06은 core-workflow와 여러 skill의 **의미**를 바꾼다. step-08(문구 슬리밍)이 먼저 가면 의미 변경 step들이 슬리밍된 문장을 다시 고쳐야 하므로 반드시 뒤로 보낸다.
- step-06은 disposition 개념(step-05)을 참조하므로 step-05 뒤가 안전하다.

## 공통 작업 프로토콜 (모든 step에 적용)

`../hand-off/01-IMPROVEMENT-PLAN.md` §0의 SCOPE→READ→DIAGNOSE→PROPOSE→CHANGE→VERIFY→REPORT 루프를 따른다. 추가 규칙:

1. **step 1개 = 커밋 1개 이상.** step 간 변경을 한 커밋에 섞지 마라. 커밋은 `02-DECISIONS.md` D4를 따른다: 실행 에이전트가 step 완료 + 검증 통과 후 step 단위로 수행한다 (서브에이전트에 위임한 작업도 커밋은 메인 에이전트가 수행). 스테이징은 경로 명시(`git add <path>`), `git add .` 금지.
2. **제안서가 필요한 step**은 `docs/improvement-260704/proposals/<yyyy-MM-dd>-<slug>.md`에 작성한다 (템플릿: `../hand-off/proposals/_TEMPLATE.md`). 승인 절차는 `02-DECISIONS.md` D3가 대체한다: 권고안 방향은 사전 승인되었으므로 제안서를 기록용으로 작성 후 바로 적용하되, **권고안에서 벗어나면 멈추고 사용자에게 보고**한다.
3. **함께-갱신 쌍을 지켜라.** core-workflow ↔ skill ↔ template ↔ reviewer prompt는 의미가 함께 움직인다. 각 step 문서의 "함께 갱신할 파일" 목록이 계약이다.
4. **runtime 표면(`as-usual-rules/`, `skills/`, `templates/`, `hooks/`)에 maintainer 규칙을 넣지 마라.**
5. machine-readable marker(`[Answer]:`, status/phase/next-action 값, canonical heading, 이벤트 이름)는 해당 step이 명시적으로 변경 대상으로 선언한 경우 외에는 절대 바꾸지 마라.
6. 각 step의 "완료 기준(DoD)"을 전부 만족하기 전에는 완료라고 보고하지 마라.

## 검증 게이트 (각 step 종료 시)

각 step 문서에 명시된 검증을 실행한다. 최소 공통 게이트:

```bash
# 저장소 루트에서
python3 -m unittest discover -s .agents/skills/sandbox-e2e-test/tests -p 'test_*.py'
```

hook/manifest를 건드린 step은 추가로:

```bash
jq empty .claude-plugin/plugin.json .claude-plugin/marketplace.json
jq empty .codex-plugin/plugin.json .agents/plugins/marketplace.json
jq empty hooks/hooks.json hooks/hooks-codex.json
CLAUDE_PLUGIN_ROOT="$PWD" bash hooks/run-hook.cmd session-start | jq .
```

의미 정합 검증은 maintainer skill 절차를 따른다 (`.agents/skills/` 아래):
- core-workflow/skill/template/reviewer prompt를 바꾼 step → `verify-runtime-workflow-consistency`
- runtime 표면 경계가 움직인 step → `verify-runtime-surface`
- 워크플로우/hook/manifest smoke → `verify-as-usual-harness`
- 넓은 변경 후 정체성/문서 반영 → `verify-project-identity`
- step-10에서 aggregate → `verify-implementation`

## 보고 형식 (step 종료 시)

각 step 완료 시 다음을 요약해 보고한다:

- 무엇을 왜 바꿨는가 (F-ID 참조)
- 바꾼 파일 목록
- 실행한 검증 명령과 결과 (실패 포함, 숨기지 마라)
- 남은 이슈 / 후속 제안

## 산출물 위치

| 산출물 | 위치 |
| --- | --- |
| 개선 제안서 (승인 전) | `docs/improvement-260704/proposals/<yyyy-MM-dd>-<slug>.md` |
| 실제 변경 | 해당 원본 파일 직접 수정 |
| step별 작업 기록/메모 | 이 폴더에 `step-XX-notes.md`로 남겨도 됨 (선택) |
