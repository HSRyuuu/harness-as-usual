# 02. 파일 구조 Hand-off (무엇을 건드리고, 무엇을 건드리면 안 되는가)

Fable이 특정 파일을 고치기 전에 여기서 **역할·개선 여지·수정 시 함께 갱신할 대상·금지 사항**을 확인한다.
`✅ 개선대상` = 개선 작업의 주 타깃 / `⚠️ 조심` = 파급 큼, 함께 갱신 필요 / `⛔ 손대지마` = 이 개선 작업 범위 밖.

전체 파일 목록과 라인 수는 `00-ORIENTATION.md` 참고. 여기서는 개선 관점의 주석을 단다.

---

## A. Runtime Contract (계층 1)

| 파일 | 라인 | 등급 | 역할 / 개선 노트 |
| --- | --- | --- | --- |
| `as-usual-rules/core-workflow.md` | 638 | ⚠️ 조심 | canonical workflow prompt. §0 우선순위 ~ §16 skill 목록. 여기 규칙 변경 시 대응 skill/template/reviewer prompt 동시 갱신 필수. 프롬프트 개선(④)의 핵심 타깃이지만 의미 변경은 ②/③. |

**core-workflow.md 섹션 지도** (필요한 섹션만 열기):
- §0 Instruction Priority / Trust Boundary / High-Risk Gate / Hard Gates
- §1 Scope & Activation, §2 Artifact Contract, §3 Required First Reads
- §4 Start Work Routing, Clarification Routing, §5 Phase Router (IF/ELSE)
- §6 Requirements Question, §7 Requirements, §8 Plan, §9 Execute
- §10 Review, §11 Finalize, §12 Git Action, §13 Topic Log
- §14 Failure Handling, §15 Anti-Patterns, §16 Required Skills

---

## B. Runtime Skills (계층 2) — target project에 배포되는 stable 표면, 단일 원본

| 경로 | 등급 | 역할 / 개선 노트 |
| --- | --- | --- |
| `skills/using-as-usual/SKILL.md` | ✅ | 활성화 판단 + 첫 읽기. core-workflow §1–§3와 정합. |
| `skills/start-work/SKILL.md` | ✅ | gate 라우팅. direct-execute allow/deny 소유. core-workflow §4와 정합. |
| `skills/define-requirements/SKILL.md` (305줄) | ✅ | 질문 사이클 + requirements 합성/리뷰 소유. §6–§7. |
| `skills/define-requirements/requirements-document-reviewer-prompt.md` | ✅ | requirements 리뷰 체크리스트 **단독 소유**(core에 복제 금지). |
| `skills/writing-plan/SKILL.md` (316줄) | ✅ | 의존성 분석 + plan 작성/리뷰. §8. |
| `skills/writing-plan/plan-document-reviewer-prompt.md` | ✅ | plan 리뷰 체크리스트 단독 소유. |
| `skills/executing-plan/SKILL.md` (319줄) | ✅ | 실행 컨트롤러. inline/subagent/mixed. §9. |
| `skills/executing-plan/implementer-prompt.md` | ✅ | subagent implementer용 bounded prompt. |
| `skills/executing-plan/task-quality-reviewer-prompt.md` | ✅ | task 품질 리뷰. |
| `skills/executing-plan/task-requirements-reviewer-prompt.md` | ✅ | task↔요구 정합 리뷰. |
| `skills/review-execution/SKILL.md` (214줄) | ✅ | 실행 후 필수 리뷰. §10. |
| `skills/review-execution/code-reviewer-prompt.md` | ✅ | 코드 리뷰 기준 단독 소유. |
| `skills/cleanup-code/SKILL.md` | ✅ | optional cleanup. 4개 reviewer 실행. |
| `skills/cleanup-code/{reuse,simplification,efficiency,abstraction}-reviewer-prompt.md` | ✅ | 각 cleanup 관점 prompt. |
| `skills/finalize/SKILL.md` | ✅ | topic 종료 + self-improvement 트리거 + git action 질문. §11. |
| `skills/git-action/SKILL.md` | ✅ | 선택된 git action만 수행. §12. |
| `skills/manage-self-improvement/SKILL.md` | ✅ | finalize 트리거. cross-topic 교훈 → memory. |
| `skills/manage-self-improvement/references/{memory-update,skill-improvement}.md` | ✅ | 참조 절차. |
| `skills/search-long-term-memory/SKILL.md` | ✅ | read-only 회상 util. |

**skill 개선 시 규칙:** 각 skill이 "소유"한다고 선언한 책임 밖으로 넘지 마라. reviewer prompt의
체크리스트를 SKILL.md나 core-workflow로 복제하지 마라. skill 규칙과 core-workflow phase 규칙은
의미가 어긋나면 안 된다(→ `verify-runtime-workflow-consistency`).

---

## C. Templates — artifact 형태의 source of truth

| 파일 | 등급 | 역할 |
| --- | --- | --- |
| `templates/question.md` | ✅ | 질문 파일 형태 + `[Answer]:` marker (보존 필수). |
| `templates/requirements.md` (92줄) | ✅ | requirements 섹션 목록/순서의 **단일 진실**. |
| `templates/plan.md` (158줄) | ✅ | plan 섹션 목록/순서의 단일 진실. |
| `templates/topic.md` | ⚠️ | low-churn resume doc 형태. `topic-log.py init`이 생성. script와 정합. |
| `templates/code-review-report.md` | ✅ | 리뷰 리포트 형태. |
| `templates/report.md` | ✅ | finalize handoff 요약 형태. |
| `templates/MEMORY.md` | ✅ | `.as-usual/memory/MEMORY.md` baseline (3000자 budget). |

**template 개선 시:** 섹션 순서/필드를 바꾸면 해당 skill의 작성 규칙과 reviewer prompt를 함께 갱신.
`topic.md`/`MEMORY.md`는 `topic-log.py`가 참조하므로 script와의 정합 확인.

---

## D. Scripts

| 파일 | 라인 | 등급 | 역할 |
| --- | --- | --- | --- |
| `scripts/topic-log.py` | 1524 | ⚠️ 조심 | topic.md/audit.jsonl 갱신 + status 파생. 서브커맨드 표면은 00-ORIENTATION §4. 변경 시 `test_state_machine.py` 등 동시 갱신 필수. **통독 금지, 대상 서브커맨드 함수만 열어라.** |
| `scripts/as-usual-record.py` | 14 | ✅ | 보조 기록 유틸(소형). |

---

## E. Hooks — SessionStart 부트스트랩 (한 문장 원칙)

| 파일 | 등급 | 역할 |
| --- | --- | --- |
| `hooks/session-start` | ⚠️ | capability 한 문장 + `using-as-usual` entrypoint만 주입. full workflow/후보/memory 주입 금지. |
| `hooks/run-hook.cmd` | ⚠️ | 공용 hook runner. |
| `hooks/hooks.json` | ⚠️ | Claude hook config. Codex 짝(`hooks-codex.json`)과 함께 갱신. |
| `hooks/hooks-codex.json` | ⚠️ | Codex hook config. |

**개선 시:** hook 출력 변경은 `CLAUDE_PLUGIN_ROOT="$PWD" bash hooks/run-hook.cmd session-start | jq .`로 smoke 확인.
"한 문장 + entrypoint" 원칙(00-ORIENTATION §6, CLAUDE.md HOOK ACTIVATION MODEL)을 깨지 마라.

---

## F. Manifests — 이중화 (Claude + Codex 동시 갱신)

| 파일 | 등급 | 역할 |
| --- | --- | --- |
| `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | ⚠️ | Claude plugin/marketplace. |
| `.codex-plugin/plugin.json` | ⚠️ | Codex plugin(skills/hooks 목록 포함). |
| `.agents/plugins/marketplace.json` | ⚠️ | Codex local marketplace. |

**개선 시:** skill/hook 목록을 바꾸면 Claude·Codex manifest를 **둘 다** 갱신 + `jq empty`로 검증.

---

## G. Maintainer 표면 — ⛔ 이 개선 작업의 타깃이 아님 (도구로만 사용)

이 개선 작업(runtime harness 개선)의 **대상이 아니다.** 다만 검증/미러 도구로 사용한다.

| 경로 | 역할 | 주의 |
| --- | --- | --- |
| `.agents/skills/<name>/` | maintainer 전용 skill 원본 | `.claude/skills/`와 **미러**. 둘이 동일해야 함 |
| `.claude/skills/<name>/` | 위의 Claude-facing 미러 | 한쪽만 고치면 동기화 깨짐 → `skill-registry-sync` |
| `.agents/skills/verify-*` | 검증 절차 skill | 개선 후 검증에 사용 |
| `.agents/skills/sandbox-e2e-test/tests/*.py` | Python 테스트 | 변경 검증에 사용; script 변경 시 함께 갱신 |
| `.agents/skills/dev-as-usual/SKILL.md` | runtime vs plugin-dev 분류 규칙 | 경계 판단 기준 |
| `.agents/skills/{skill-registry-sync,manage-skills}` | 미러/등록 동기화 | maintainer skill 편집 후 |

**규칙:** 여기 파일을 "개선 산출물"로 바꾸지 마라. maintainer skill을 수정할 일이 생기면
반드시 `.agents/skills/`와 `.claude/skills/` 양쪽을 동기화하고 `skill-registry-sync` 절차를 밟는다.

---

## H. 문서 — 참조 및 갱신 대상

| 파일 | 등급 | 역할 |
| --- | --- | --- |
| `PROJECT_IDENTITY.md` | ⚠️ | 정체성/설계 원칙의 **최종 기준**. 아키텍처 변경 시 여기와 충돌 검토. |
| `docs/ARCHITECTURE-WORKFLOW.md` | ⚠️ | 전체 아키텍처·워크플로우 상세(이미 고품질). 워크플로우/아키텍처 변경 시 갱신. |
| `CLAUDE.md`, `AGENTS.md` | ⚠️ | maintainer 지식베이스. 구조/규칙 변경 시 갱신(둘은 유사 내용, 정합 유지). |
| `README.md` | ✅ | 공개 소개. |
| `docs/{CLAUDE,CODEX}-PLUGIN-SETTING.md`, `docs/INSTALL*.md`, `docs/UNINSTALL.md`, `docs/DEVELOPMENT.md` | ✅ | 설치/개발 가이드. 사설 절대경로 금지, 공개 repo URL 사용. |
| `docs/design/*.md`, `docs/superpowers/*` | 참고 | 과거 설계 기록. 새 설계는 `docs/design/<date>-<slug>-design.md`. |

---

## 빠른 결정 규칙 (요약)

- **한 skill/prompt만** 다듬는다 → B 또는 C의 해당 파일 + core-workflow 관련 섹션.
- **순서/게이트**를 바꾼다 → A(core-workflow) + B(대응 skill) 동시, 제안서 필수.
- **구조/호스트/미러**를 바꾼다 → PROJECT_IDENTITY 검토 + F(manifest) + G(미러) 동기화, 제안서 필수.
- **script 동작**을 바꾼다 → D + G의 tests 동시.
- 무엇이든 **끝내기 전 `01-IMPROVEMENT-PLAN.md`의 검증 게이트** 통과.
