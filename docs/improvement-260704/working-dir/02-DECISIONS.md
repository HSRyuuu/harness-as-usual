# 02. 사용자 사전 결정 사항 (2026-07-04 확정)

실행 시작 전 사용자에게 확인받은 결정들이다. **이 결정들은 각 step 문서의 "제안서 승인 대기" 절차를 대체한다.**
실행 에이전트는 이 문서의 결정 범위 안에서는 승인 대기 없이 적용하고, **결정 범위를 벗어나는 상황이 나오면 멈추고 사용자에게 보고**한다.

## D1. 템플릿 언어 정책 (step-07)

**결정: 안 1 — 영어 canonical + 사용자 언어 번역 허용.**

- 질문 파일 heading을 영어 canonical로 교체. 사용자 언어로 일관 번역 허용하되 **순서/개수는 canonical 구조 고정**.
- `[Answer]:` 마커와 option letter 형식은 불변.
- requirements/plan 템플릿의 한국어 helper 텍스트는 step-07 명세대로 정리 (`None` / 주석화).

## D2. hook 호스트 분기 (step-09)

**결정: (a) 실험적 지원으로 문서화.** 동작 보존. Cursor/Copilot 분기를 CLAUDE.md/AGENTS.md에 "실험적 best-effort, 공식 지원은 Claude Code + Codex"로 문서화. 코드 변경 없음.

## D3. Large/Medium step 승인 방식 (step-04, 05, 06)

**결정: 권고안 방향 사전 승인.**

- step-04: focused/broad 모델로 Clarification Routing 재정의 — 방향 승인됨.
- step-05: 심각도별 disposition 매트릭스 안 채택 (최소안 아님).
- step-06: 권고 설계 채택 — `cancelled` 상태 3표면 노출 + validate의 cancelled 면제(사유 summary는 필수), direct-execute는 경량 종단(finalize/git-action 비합류 명시), self-improvement pass는 cancelled에도 실행하되 "no candidates" 허용, cancel 시 작업 트리 잔여 변경은 사용자에게 되돌림/유지 질문.
- 제안서는 **기록용으로 작성 후 바로 적용**한다 (`docs/improvement-260704/proposals/`). 승인 대기 없음.
- **단, 사전 조사(step-06 §1) 결과가 권고 설계와 충돌하거나, 적용 중 권고안에서 벗어나는 설계 변경이 필요해지면 적용을 멈추고 사용자에게 보고한다.** 가드레일(게이트 약화 금지, complete/follow-up-needed 불변식 유지 등)은 사전 승인과 무관하게 절대 준수.

## D4. 커밋 정책

**결정: step마다 커밋.**

- 각 step 완료 + 검증 통과 후, **실행 에이전트가** 경로 명시 스테이징으로 step 단위 커밋을 수행한다. (이 하네스에는 별도 컨트롤러/오케스트레이터가 없다. 이 작업은 plugin development이므로 AsUsual runtime의 finalize/git-action 게이트 대상도 아니다.)
- 작업 일부를 서브에이전트에 위임한 경우에도 **커밋은 메인 에이전트가 수행한다** — 서브에이전트는 변경과 검증 결과 보고까지만.
- push는 하지 않는다. 커밋 메시지는 저장소 최근 스타일(`fix:`, `docs:` 등)을 따른다.

## D5. direct-execute 커밋 경로와 Inviolable 문구 (step-06 추가 결정, 2026-07-04 최종 검토에서 확정)

**결정: Inviolable NEVER의 git action 문구를 게이트 대상 topic으로 한정하는 범위 명확화를 step-06에 포함한다.**

- 배경: step-06(B)의 "direct-execute 완료 후 commit 등은 일반 대화로 처리" 문장은 core-workflow Inviolable NEVER(:35) "run a git action before finalize + explicit user selection"과 문자 그대로 충돌한다 (direct-execute topic은 finalize에 도달하지 않으므로).
- 적용: Inviolable NEVER 문구를 게이트 대상(non-direct-execute) topic 한정으로 명확화하고, direct-execute 완료 후 **사용자가 명시적으로 요청한** git 작업은 일반 대화로 처리 가능함을 함께 명시한다.
- 게이트 의미 불변: 사용자 명시 요청 없는 자동 git action 금지는 어떤 경로에서도 유지된다. 제안서에 Inviolable 문구의 before/after를 명시한다.
