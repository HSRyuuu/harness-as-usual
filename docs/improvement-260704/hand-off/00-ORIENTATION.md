# 00. AsUsual Orientation Map (탐색 토큰 절약용)

이 문서 하나로 AsUsual의 **전체 구조, 워크플로우, 파일 위치, 명령 표면, 불변 규칙**을 파악한다.
Fable은 이 문서를 읽은 뒤 저장소를 무작정 훑지 말고, 필요한 원본 파일만 골라서 열어라.

> 규모 감각: runtime prompt/skill/script 합계 약 4,600 라인.
> 가장 큰 파일은 `scripts/topic-log.py`(1,524줄)와 `as-usual-rules/core-workflow.md`(638줄)다.
> 이 둘을 무작정 통독하면 토큰이 크게 든다. 아래 요약과 명령 표면으로 대체하라.

---

## 1. AsUsual이 무엇인가 (한 문단)

AsUsual은 Claude Code와 Codex에서 함께 쓰는 **agent harness**다. agent가 사용자의 의도를
추측해서 곧장 구현하지 않도록, **하나의 작업 topic**을 파일 기반 사이클로 통과시킨다:
질문 → requirements → plan → execute → review → (optional cleanup) → finalize → git action.
모든 결정·승인·검증 증거는 target project의 `.as-usual/` 파일에 남아 세션 간 재개된다.
정체성/설계 원칙의 최종 기준은 `PROJECT_IDENTITY.md`.

---

## 2. 3계층 아키텍처

| 계층 | 위치 | 역할 | 개선 시 주의 |
| --- | --- | --- | --- |
| **Runtime contract** | `as-usual-rules/core-workflow.md` | canonical workflow prompt. phase routing, hard gate, artifact contract, trust boundary | 파급 최대. 여기 규칙과 skill prompt가 어긋나면 워크플로우가 깨짐 |
| **Runtime skills** | `skills/<phase>/` | 각 phase에서 agent가 따르는 실제 prompt + reviewer prompt | core-workflow와 의미 정합성 유지 필수 |
| **Topic artifacts** | target project의 `.as-usual/topic/...` | topic별 source of truth (질문/req/plan/audit/report) | 이 저장소엔 없음. runtime 결과물임 |

핵심: **chat memory는 보조**, **topic 파일이 source of truth**. 이 원칙이 전체 설계를 관통한다.

---

## 3. 전체 워크플로우 (phase 순서)

```
SessionStart hook
  → using-as-usual      (활성화 판단 + 첫 읽기)
  → start-work          (가장 가벼운 충분한 gate로 라우팅)
  → define-requirements | writing-plan | executing-plan | direct-execute
  → review-execution    (실행 후 필수 리뷰)
  → cleanup-code        (선택, 사용자 승인 시만)
  → finalize            (topic 종료 + self-improvement + git action 질문)
  → git-action          (사용자가 고른 git action만 수행)
```

- `direct-execute`: clear/trivial/low-risk/reversible 작업 전용 shortcut. 그 외 non-trivial은 반드시 requirements+plan gate 통과.
- phase의 machine-readable 값은 `audit.jsonl`에서 `scripts/topic-log.py status --json`로 파생.

### phase ↔ skill ↔ prompt/template 매핑

| Phase | Skill (`skills/`) | 딸린 reviewer/prompt | 관련 template |
| --- | --- | --- | --- |
| 활성화·첫읽기 | `using-as-usual/SKILL.md` | — | — |
| gate 라우팅 | `start-work/SKILL.md` | — | — |
| 요구사항 | `define-requirements/SKILL.md` | `requirements-document-reviewer-prompt.md` | `question.md`, `requirements.md` |
| 계획 | `writing-plan/SKILL.md` | `plan-document-reviewer-prompt.md` | `plan.md` |
| 실행 | `executing-plan/SKILL.md` | `implementer-prompt.md`, `task-quality-reviewer-prompt.md`, `task-requirements-reviewer-prompt.md` | — |
| 실행 리뷰 | `review-execution/SKILL.md` | `code-reviewer-prompt.md` | `code-review-report.md` |
| 코드 정리 | `cleanup-code/SKILL.md` | `reuse-` / `simplification-` / `efficiency-` / `abstraction-reviewer-prompt.md` | — |
| 종료 | `finalize/SKILL.md` | — | `report.md` |
| git 액션 | `git-action/SKILL.md` | — | — |
| 자기개선 | `manage-self-improvement/SKILL.md` | `references/memory-update.md`, `references/skill-improvement.md` | `MEMORY.md` |
| 메모리 회상 | `search-long-term-memory/SKILL.md` | — | — |

전체 phase별 상세 규칙과 prompt/template 위치는 **`docs/ARCHITECTURE-WORKFLOW.md`에 이미 완성도 높게 정리되어 있다.**
Fable은 특정 phase를 깊게 고칠 때 그 문서의 해당 섹션만 열어라(통독 불필요).

---

## 4. `scripts/topic-log.py` 명령 표면 (1,524줄 통독 금지)

`topic.md`/`audit.jsonl`은 손으로 편집하지 않고 이 스크립트로만 갱신한다.
서브커맨드 전체 목록(이것만 알면 스크립트 내부를 읽을 필요가 거의 없다):

```
init  status  validate  audit  note  decision  blocker  artifact  verification
route-start-work
complete-requirements  complete-plan  complete-task  complete-execution
approve-execution  approve-high-risk
dispatch-task  record-task-review  record-task-fix  record-task-commit  record-sweep
record-review  skip-code-cleanup  skip-simplify
finalize-topic  select-git-action
record-memory  record-memory-candidate  record-skill
```

- 상태 조회: `python3 scripts/topic-log.py status --topic-dir <dir> --json`
- 구조 검증: `python3 scripts/topic-log.py validate --topic-dir <dir>`
- 스크립트를 고칠 때만 원본을 열어라. 명령을 "쓰기"만 할 거면 위 목록으로 충분.

---

## 5. 이중 호스트 · 이중 표면 (중요한 함정)

AsUsual은 **Claude Code + Codex** 두 호스트를 지원한다. 그래서 표면이 중복 존재한다.

| 무엇 | Claude 쪽 | Codex 쪽 |
| --- | --- | --- |
| Plugin manifest | `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | `.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json` |
| Hook config | `hooks/hooks.json` | `hooks/hooks-codex.json` |
| Maintainer skills 미러 | `.claude/skills/<name>/` | `.agents/skills/<name>/` |

**함정 1 — maintainer skill 미러링:** `.agents/skills/`와 `.claude/skills/`는 동일 skill의 미러다.
한쪽만 고치면 동기화가 깨진다. 동기화는 `skill-registry-sync` skill이 담당.
**함정 2 — manifest 이중화:** hook/skill 목록을 바꾸면 Claude·Codex 양쪽 manifest를 함께 갱신해야 한다.
**함정 3 — public runtime skills(`skills/`)는 미러가 아니다.** 여긴 target project에 배포되는 stable 표면, 단일 원본.

---

## 6. 절대 불변 규칙 (core-workflow §Inviolable, 요약)

개선하더라도 아래를 약화시키면 안 된다. 약화가 필요하면 **먼저 제안서로 근거를 남겨라.**

- requirements.md + 승인된 plan.md 없이 non-trivial 구현 금지 (direct-execute 제외)
- high-risk 작업은 plan에 있어도 **실행 직전 fresh 승인** 필요 (파일삭제/일괄포맷/의존성설치/DB마이그레이션/env·secret변경/CI변경/deploy/git push 등)
- 검증 증거(또는 "왜 검증 못 했는지") 없이 완료 주장 금지
- secret 값 출력/복사/커밋/영속화 금지
- `topic.md`/`audit.jsonl`은 `topic-log.py`로만 갱신
- finalize + 사용자 명시 선택 전에는 git action 금지
- 실행 후 `review-execution`은 필수 (건너뛰기 금지)
- runtime 표면에 maintainer/plugin-development 규칙 유입 금지

---

## 7. 검증·테스트 표면 (개선 후 반드시 통과)

### 7.1 Python 테스트 (unittest)
위치: `.agents/skills/sandbox-e2e-test/tests/`
```
test_state_machine.py            # topic-log.py 상태머신
test_e2e_report_linter.py
test_fill_question_answers.py
test_run_sandbox_e2e_script.py
test_runtime_surface_manifest.py
```
실행(저장소 루트에서):
```
python3 -m unittest discover -s .agents/skills/sandbox-e2e-test/tests -p 'test_*.py'
```

### 7.2 Manifest / hook smoke (CLAUDE.md의 COMMANDS 섹션)
```
jq empty .claude-plugin/plugin.json .claude-plugin/marketplace.json
jq empty .codex-plugin/plugin.json .agents/plugins/marketplace.json
jq empty hooks/hooks.json hooks/hooks-codex.json
CLAUDE_PLUGIN_ROOT="$PWD" bash hooks/run-hook.cmd session-start | jq .
```

### 7.3 maintainer 검증 skill (의미 정합성)
`.agents/skills/` 아래에 검증 절차가 skill로 존재한다. 개선 범위에 맞게 해당 절차를 따른다.

| 검증 skill | 언제 |
| --- | --- |
| `verify-runtime-surface` | runtime 표면에 maintainer 규칙이 샜는지 |
| `verify-as-usual-harness` | 워크플로우/hook 주입/manifest smoke |
| `verify-runtime-workflow-consistency` | core-workflow ↔ skill ↔ template ↔ reviewer prompt 정합성 |
| `verify-project-identity` | 정체성/maintainer 문서 반영 여부 |
| `verify-implementation` | 위 검증들을 순차 실행하는 aggregate |

---

## 8. 어디부터 읽을지 (개선 축별 최소 읽기 세트)

토큰 절약의 핵심: **작업 축에 필요한 파일만** 연다. 상세는 `01-IMPROVEMENT-PLAN.md` 참조.

| 개선 축 | 최소로 열 파일 | 열지 않아도 되는 것 |
| --- | --- | --- |
| 단일 작업(한 skill/prompt) | 해당 `skills/<x>/SKILL.md` + 그 reviewer prompt | 다른 phase skill들 |
| 워크플로우(순서/게이트) | `core-workflow.md` §4–§13 + 관련 skill | topic-log 내부 구현 |
| 아키텍처 | `PROJECT_IDENTITY.md` + `docs/ARCHITECTURE-WORKFLOW.md` + manifest들 | 개별 reviewer prompt |
| 프롬프트 | 대상 prompt 파일 + `core-workflow.md`의 관련 §only | 무관한 skill들 |
