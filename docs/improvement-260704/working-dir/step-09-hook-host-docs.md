# Step 09. hook 호스트 분기 문서화 (F13)

- **축:** ③ 아키텍처 (문서 정합)
- **규모:** Small — 제안서 불필요.
- **대상 finding:** F13
- **선행 조건:** 없음 (독립 실행 가능)

> **[2026-07-04 사전 결정 — `02-DECISIONS.md` D2]** **(a) 실험적 지원으로 문서화가 채택되었다.** §1의 사용자 질문은 완료된 것으로 간주하고 §2 문서화 경로만 수행한다. 코드 변경 없음.

## 문제 요약

`hooks/session-start:14-21`은 4가지 호스트 분기를 구현한다:

1. `CURSOR_PLUGIN_ROOT` → Cursor 형식 (`additional_context`)
2. `CLAUDE_PLUGIN_ROOT` (COPILOT_CLI 아님) → Claude Code 형식
3. `PLUGIN_ROOT` → generic (Codex 포함)
4. fallback → 두 형식 동시 출력

그러나 `CLAUDE.md`/`AGENTS.md`/`docs/ARCHITECTURE-WORKFLOW.md`/`PROJECT_IDENTITY.md`는 Claude Code + Codex dual-host만 기술한다. Cursor/Copilot 분기는 코드에만 존재하는 미문서 동작이다.

## 절차

### 1. 사용자에게 방향 질문 (필수)

> hooks/session-start가 Cursor(`CURSOR_PLUGIN_ROOT`)와 Copilot(`COPILOT_CLI`) 분기를 지원하는데 문서에는 없습니다. (a) 실험적 지원으로 문서화할까요, (b) dual-host 원칙에 맞게 분기를 제거할까요?

- **(a) 문서화 (기본 권고 — 동작 보존):** 아래 2번 수행.
- **(b) 제거:** 동작 축소이므로 사용자가 명시적으로 선택한 경우에만. 아래 3번 수행.

### 2. (a) 문서화 경로

- `CLAUDE.md`와 `AGENTS.md`의 hook 관련 서술(CODE MAP의 SessionStart hook 행 또는 HOOK ACTIVATION MODEL)에 1-2문장 추가: "hook 출력은 호스트별 형식 분기를 포함한다: Claude Code(`CLAUDE_PLUGIN_ROOT`), Codex(`PLUGIN_ROOT`), Cursor(`CURSOR_PLUGIN_ROOT`, 실험적), 그 외 fallback. 공식 지원 호스트는 Claude Code와 Codex이며 Cursor 분기는 best-effort다."
- `docs/ARCHITECTURE-WORKFLOW.md`에 hook 섹션이 있으면 동일 취지 반영.
- **runtime 표면에는 넣지 않는다** (maintainer 지식이다).

### 3. (b) 제거 경로 (사용자 선택 시에만)

- `hooks/session-start`에서 CURSOR 분기(:14-15)와 `COPILOT_CLI` 조건(:16)을 제거하고 Claude/Codex/fallback 3분기로 단순화.
- 제거 후 hook smoke 필수 (아래 검증).

## 검증

```bash
CLAUDE_PLUGIN_ROOT="$PWD" bash hooks/run-hook.cmd session-start | jq .
# CLAUDE.md COMMANDS 섹션의 hook smoke jq 필터도 그대로 실행해 전부 true인지 확인
jq empty hooks/hooks.json hooks/hooks-codex.json
# (b) 선택 시) PLUGIN_ROOT="$PWD" bash hooks/run-hook.cmd session-start | jq . 로 Codex 분기도 스모크
```

## 완료 기준 (DoD)

- [ ] 사용자가 (a)/(b)를 선택했다.
- [ ] 선택에 따라 문서 또는 코드가 갱신되었고 hook smoke가 통과한다.
- [ ] maintainer 문서(CLAUDE.md/AGENTS.md) 서술과 hook 코드가 일치한다.

## 롤백

`git checkout -- hooks/session-start CLAUDE.md AGENTS.md docs/ARCHITECTURE-WORKFLOW.md`
