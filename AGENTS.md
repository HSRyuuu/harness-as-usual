# PROJECT KNOWLEDGE BASE

## OVERVIEW

AsUsual은 Claude Code와 Codex에서 함께 쓰기 위한 agent harness다. 하나의 project 안에서 하나의 작업 topic을 시작하고, file-backed requirements question, written requirements, written plan, execute, execution review, optional code cleanup, finalize cycle을 거친 뒤 종료하는 작업 단위 workflow를 제공한다.

AsUsual의 핵심은 사용자의 기존 작업 방식을 agent가 추측하지 않도록 topic별 결정 기록을 파일에 남기는 것이다.

AsUsual은 단순 바이브코딩 보조 도구가 아니라, 실제 프로덕션 서비스에 배포될 수 있는 작업을 사용자가 통제 가능한 방식으로 진행하기 위한 개발 하네스다. 프로젝트 정체성과 설계 원칙은 `PROJECT_IDENTITY.md`에 둔다.

현재 runtime contract의 canonical file은 `as-usual-rules/core-workflow.md`다.

## STRUCTURE

```text
as-usual/
├── PROJECT_IDENTITY.md   # 프로젝트 정체성과 설계 원칙
├── .claude-plugin/       # Claude plugin과 local marketplace manifest
├── .codex-plugin/        # Codex plugin manifest
├── .agents/plugins/      # Codex local marketplace manifest
├── .agents/skills/       # AsUsual maintainer-only project-local skills
├── .claude/skills/       # Claude-facing mirror of maintainer-only project-local skills
├── as-usual-rules/       # runtime workflow rules; core-workflow.md가 canonical
├── commands/             # local command experiments; public runtime surface가 아님
├── docs/                 # Claude/Codex clone/install/development guide
├── hooks/                # SessionStart hook config와 공용 hook runner
├── plugins/              # local marketplace source symlink workspace
├── templates/            # topic artifact templates (MEMORY.md 포함)
└── skills/               # stable skills only; draft/probe skill은 커밋하지 않음
    ├── hand-off/  # existing topic path를 다른 세션에서 이어받는 resume entrypoint
    ├── explore-codebase/  # read-only codebase discovery util; repository facts before requirements/plan
    ├── manage-self-improvement/  # finalize 시 트리거; cross-topic 교훈을 memory에 기록
    └── search-long-term-memory/  # read-only recall util; .as-usual/memory/ 조회
```

## RUNTIME WORKFLOW MODEL

Runtime workflow는 target project의 하나의 topic에만 적용한다. `.as-usual/`은 두 갈래로 나뉜다: `topic/`(작업 단위)과 `memory/`(topic을 가로지르는 지속 지식). Canonical 구조는 아래와 같다.

```text
.as-usual/
├── topic/
│   └── yyyy-MM-dd-<topic>/
│       ├── question-c1.md
│       ├── question-c2.md
│       ├── requirements.md
│       ├── plan.md
│       ├── execute/
│       │   ├── task-<N>-requirements-review.md
│       │   └── task-<N>-quality-review.md
│       ├── clean-up/
│       │   └── review-result-<type>.md
│       ├── topic.md
│       └── audit.jsonl
└── memory/
    ├── MEMORY.md           # curated cross-topic 지식; 3000자 budget; 커밋 대상
    └── *_MEMORY.md         # 선택적 도메인별 memory 파일
```

기본 cycle:

1. `define-requirements`: material ambiguity가 있으면 `question-cN.md` 파일을 만들고 사용자가 `[Answer]:` field에 직접 답하게 한다. 답변 파일을 검증한 뒤 최초 요청과 모든 answered question files를 종합해 단일 `requirements.md`를 작성/리뷰한다.
2. `plan`: 승인된 `requirements.md`를 기반으로 단일 `plan.md`를 작성한다. Plan 작성/리뷰 중 생기는 좁은 추가 확인은 chat으로 물을 수 있고, 답변은 `scripts/topic-log.py`로 `audit.jsonl`에 기록한다.
3. `execute`: plan을 기반으로 `inline`, `subagent-driven`, 또는 `mixed` mode로 작업을 수행한다. main agent가 controller로 남아 task 순서, audit event, verification, completion claim을 책임진다. 실행 중 단일 사용자 결정이 필요하면 구현을 멈추고 chat으로 확인한 뒤 `scripts/topic-log.py`로 `audit.jsonl`에 기록하고 필요한 requirements/plan 단계로 회송한다. Task-level test strategy, review/fix loop, sweep, verification evidence는 이 단계에서 기록한다.
4. `review-execution`: execute 완료 뒤 자동으로 수행되는 필수 post-execution review 단계다. 실제 변경 코드와 `topic.md`/`requirements.md`/`plan.md`/`audit.jsonl`의 execution evidence를 검토하고 결과를 기록한 뒤, optional code cleanup을 실행할지 사용자에게 묻는다.
5. `cleanup-code`: 사용자가 승인한 경우에만 실행되는 optional cleanup 단계다. 기존 helper 재사용, 단순화, 효율성, 추상화 수준을 네 축으로 검토하고 안전한 behavior-preserving cleanup만 적용한다.
6. `finalize`: review 결과와 code cleanup 결정이 기록된 뒤 topic status를 정리하고, `manage-self-improvement`를 트리거해 `.as-usual/memory/MEMORY.md`에 cross-topic 교훈을 업데이트한 뒤, 사용자에게 post-finalize git action을 선택할지 묻고 멈춘다.

## RUNTIME CONTRACT BOUNDARY

- `as-usual-rules/core-workflow.md`는 AsUsual runtime usage 규칙만 담는다.
- AsUsual plugin 자체의 hook, manifest, docs, skill, install, reload를 개발하는 규칙은 `AGENTS.md`와 `.agents/skills/dev-as-usual/SKILL.md`에 둔다.
- `core-workflow.md`에 plugin 개발 목표, packaging 세부사항, 설치 guide를 섞지 않는다.
- target project에는 runtime workflow prompt를 복사하지 않는다. target project에는 `.as-usual/topic/...` artifact만 만든다.
- AsUsual repository를 수정하는 요청은 plugin development 작업이다. 사용자가 명시적으로 “이 plugin 개발도 AsUsual topic으로 진행해”라고 요청하지 않는 한 `.as-usual/topic/` workflow를 강제하지 않는다.

## HOOK ACTIVATION MODEL

SessionStart hook은 AsUsual capability와 `using-as-usual` entrypoint를 한 문장으로만 알려준다. Full core workflow, topic 후보, memory 내용은 주입하지 않고, AsUsual이 활성화될 때 `using-as-usual`이 파일에서 직접 찾고 읽는다. 이 hook이 주입됐다는 사실만으로 모든 요청에 workflow를 강제하지 않는다.

hook 출력은 호스트별 형식 분기를 포함한다: Claude Code(`CLAUDE_PLUGIN_ROOT`, `COPILOT_CLI` 아님), Codex(`PLUGIN_ROOT`), Cursor(`CURSOR_PLUGIN_ROOT`, 실험적), 그 외 fallback(두 형식 동시 출력). 공식 지원 호스트는 Claude Code와 Codex이며 Cursor 분기는 best-effort다.

AsUsual 작업으로 보는 신호:

1. 사용자가 `as-usual`, `AsUsual`이라고 명시한다.
2. 사용자가 `.as-usual/`, question/requirements/plan/topic.md/audit.jsonl, 또는 특정 topic artifact를 언급한다.
3. 사용자가 “답변했어”, “requirements 작성해”, “plan 작성해”, “계속해”처럼 active topic 재개를 요청하고, `.as-usual/topic/` 아래 진행 중인 topic artifacts와 derived status가 있다.
4. 사용자가 AsUsual workflow로 관리할 기능 개발 작업을 요청한다.

Plugin development 요청은 위 신호가 있어도 plugin development로 분류한다. 단, 사용자가 plugin development 자체를 AsUsual topic으로 진행하라고 명시하면 runtime workflow를 적용한다.

## WHERE TO LOOK

| Task | Location | Notes |
| --- | --- | --- |
| Project identity | `PROJECT_IDENTITY.md` | AsUsual이 막으려는 실패 모드와 설계 원칙을 설명한다. |
| Runtime workflow rules | `as-usual-rules/core-workflow.md` | AsUsual 활성화 시 읽는 canonical workflow다. |
| Hook context injection | `hooks/session-start`, `hooks/run-hook.cmd`, `hooks/hooks.json`, `hooks/hooks-codex.json` | capability summary와 entrypoint skill만 한 문장으로 주입한다. |
| Artifact templates | `templates/question.md`, `templates/requirements.md`, `templates/plan.md`, `templates/topic.md`, `templates/code-review-report.md`, `templates/report.md`, `templates/MEMORY.md` | `.as-usual/topic/yyyy-MM-dd-<topic>/` 아래 생성되는 파일 shape다. `topic.md`와 `audit.jsonl`은 `scripts/topic-log.py init`으로 생성된다. `MEMORY.md`는 `.as-usual/memory/MEMORY.md`의 baseline shape다. |
| Runtime activation skill | `skills/using-as-usual/SKILL.md` | AsUsual 신호를 감지했을 때 core workflow와 topic artifact를 읽고 진행한다. |
| Hand-off resume skill | `skills/hand-off/SKILL.md` | `/as-usual:hand-off <path>` 또는 다른 세션 topic resume 요청을 기존 phase owner skill로 라우팅한다. |
| Requirements definition skill | `skills/define-requirements/SKILL.md` | `question-cN.md` 생성/검증과 `requirements.md` 작성/리뷰를 담당한다. |
| Self-improvement skill | `skills/manage-self-improvement/SKILL.md` | finalize 시 트리거; cross-topic 교훈을 `.as-usual/memory/MEMORY.md`에 기록한다. |
| Long-term memory recall skill | `skills/search-long-term-memory/SKILL.md` | `.as-usual/memory/`에서 과거 결정과 패턴을 조회하는 read-only recall util. |
| Codebase exploration skill | `skills/explore-codebase/SKILL.md` | requirements/plan 작성 전 repository-discoverable facts를 찾는 read-only discovery util. |
| Execution review skill | `skills/review-execution/SKILL.md` | execute 완료 후 mandatory code review와 optional code cleanup 결정을 다룬다. |
| Code cleanup skill | `skills/cleanup-code/SKILL.md` | optional cleanup review와 안전한 simplification 적용을 다룬다. |
| Finalize skill | `skills/finalize/SKILL.md` | topic status를 닫고 post-finalize git action 선택을 묻는다. |
| Plugin development guide | `.agents/skills/dev-as-usual/SKILL.md` | runtime usage와 plugin development boundary를 설명한다. |
| Harness smoke verification | `.agents/skills/verify-as-usual-harness/SKILL.md` | runtime workflow, hook injection, manifests smoke를 검증한다. |
| Runtime surface verification | `.agents/skills/verify-runtime-surface/SKILL.md` | runtime-facing surface에 maintainer guidance가 새지 않았는지 검증한다. |
| Runtime workflow consistency verification | `.agents/skills/verify-runtime-workflow-consistency/SKILL.md` | runtime workflow, public runtime skills, requirements/plan templates, reviewer prompt 일관성을 검증한다. |
| Project identity verification | `.agents/skills/verify-project-identity/SKILL.md` | broad workflow/artifact/verification 변경이 PROJECT_IDENTITY, AGENTS, CLAUDE, README, architecture docs에 반영됐는지 검증한다. |
| Aggregate verification | `.agents/skills/verify-implementation/SKILL.md` | 등록된 verification skill을 순차 실행한다. |
| Skill registry maintenance | `.agents/skills/manage-skills/SKILL.md` | 검증 skill coverage와 AGENTS.md 등록 목록을 동기화한다. |
| Maintainer skill mirror sync | `.agents/skills/skill-registry-sync/SKILL.md` | `.agents/skills`와 `.claude/skills` 중 최신 변경사항을 기준으로 다른 쪽을 동기화한다. |
| Local plugin toggle guide | `.agents/skills/turn-on-off-as-usual/SKILL.md` | 개발 중 local Claude/Codex plugin on/off를 다룬다. |
| Sandbox E2E harness test | `.agents/skills/sandbox-e2e-test/SKILL.md` | hardcoded `as-usual-test-project`에서 Codex 기반 실제 AsUsual runtime E2E를 실행하고 `docs/test/` 보고서를 만든다. |
| E2E result analysis | `.agents/skills/analyze-e2e-results/SKILL.md` | `docs/test/` 아래 기존 sandbox E2E 결과물에서 harness 문제점과 증거 품질을 검토한다. |
| Claude install docs | `docs/CLAUDE-PLUGIN-SETTING.md`, `.claude-plugin/` | public install flow. private absolute path를 넣지 않는다. |
| Codex install/reload docs | `docs/CODEX-PLUGIN-SETTING.md`, `.codex-plugin/`, `.agents/plugins/` | Codex local marketplace와 snapshot reload flow. |

## CODE MAP

| Surface | Type | Location | Role |
| --- | --- | --- | --- |
| Core workflow | Markdown prompt | `as-usual-rules/core-workflow.md` | target project 작업 중 agent가 따라야 하는 runtime contract |
| SessionStart hook | shell + JSON | `hooks/session-start` | `using-as-usual` entrypoint를 한 문장으로 알리는 lightweight bootstrap context injection |
| Hook config | JSON | `hooks/hooks.json`, `hooks/hooks-codex.json` | Claude/Codex SessionStart에서 hook runner 실행 |
| Topic log helper | Python | `scripts/topic-log.py` | `topic.md`/`audit.jsonl` 생성, audit event 기록, derived status 조회 |
| Activation skill | Skill | `skills/using-as-usual/SKILL.md` | AsUsual 작업 판단, first reads, artifact gate 진행 |
| Hand-off resume skill | Skill | `skills/hand-off/SKILL.md` | 기존 `.as-usual/topic/...` path를 재수화하고 현재 phase owner skill로 라우팅 |
| Requirements definition skill | Skill | `skills/define-requirements/SKILL.md` | `question-cN.md` 생성/검증, `requirements.md` 작성/리뷰, plan approval 요청 |
| Self-improvement skill | Skill | `skills/manage-self-improvement/SKILL.md` | finalize 트리거; cross-topic 교훈을 `.as-usual/memory/MEMORY.md`에 distill |
| Long-term memory recall skill | Skill | `skills/search-long-term-memory/SKILL.md` | `.as-usual/memory/` read-only 조회 |
| Codebase exploration skill | Skill | `skills/explore-codebase/SKILL.md` | requirements/plan 이전 repository surface read-only 탐색 |
| Memory template | Markdown | `templates/MEMORY.md` | `.as-usual/memory/MEMORY.md` baseline shape |
| Execution review skill | Skill | `skills/review-execution/SKILL.md` | 실행 결과 검토, optional code cleanup 결정, finalize 회송 |
| Code cleanup skill | Skill | `skills/cleanup-code/SKILL.md` | optional cleanup review와 re-verification |
| Finalize skill | Skill | `skills/finalize/SKILL.md` | topic closure와 post-finalize git action decision prompt |
| Maintainer development skill | Project-local Skill | `.agents/skills/dev-as-usual/SKILL.md` | AsUsual repository 변경을 plugin development로 분류 |
| Harness smoke skill | Project-local Skill | `.agents/skills/verify-as-usual-harness/SKILL.md` | 하네스 smoke 검증 절차 |
| Workflow consistency skill | Project-local Skill | `.agents/skills/verify-runtime-workflow-consistency/SKILL.md` | runtime workflow 관련 파일 간 의미적 일관성 검증 |
| Project identity verification skill | Project-local Skill | `.agents/skills/verify-project-identity/SKILL.md` | durable project identity와 maintainer docs alignment 검증 |
| Verification registry | Project-local Skill | `.agents/skills/verify-implementation/SKILL.md`, `.agents/skills/manage-skills/SKILL.md` | 통합 검증과 검증 skill registry 관리 |
| Test and local admin skills | Project-local Skill | `.agents/skills/sandbox-e2e-test/SKILL.md`, `.agents/skills/analyze-e2e-results/SKILL.md`, `.agents/skills/turn-on-off-as-usual/SKILL.md`, `.agents/skills/skill-registry-sync/SKILL.md` | sandbox E2E, E2E 결과 분석, local plugin on/off, maintainer skill mirror sync |
| Templates | Markdown | `templates/*.md` | topic artifact 생성 기준 |
| Codex plugin | JSON | `.codex-plugin/plugin.json` | Codex plugin metadata, skills, hooks |
| Claude marketplace | JSON | `.claude-plugin/`, `.agents/plugins/` | local marketplace registration |

## CONVENTIONS

- Runtime workflow file은 `as-usual-rules/core-workflow.md` 하나로 유지한다.
- Canonical topic path는 `.as-usual/topic/yyyy-MM-dd-<topic>/`다.
- `topics/`, `yyyyMMdd` 형식은 과거 설계다. 새 runtime artifact에는 사용하지 않는다.
- `question-cN.md`와 `[Answer]:` field는 `define-requirements` 질문 cycle 전용이다.
- Agent는 requirements question file을 만들거나 갱신한 뒤 멈춘다.
- 사용자가 답변했다고 돌아오면 question file을 디스크에서 다시 읽는다.
- Requirements/plan/execute 단계에서 생기는 좁은 clarification은 chat으로 물어볼 수 있다. 단, 답변은 반드시 `scripts/topic-log.py`로 `audit.jsonl`에 기록하고, 필요한 경우 `requirements.md` 또는 `plan.md`를 다시 리뷰한다.
- 여러 결정이 얽힌 broad ambiguity나 topic boundary 변경은 chat 하나로 처리하지 않고 `define-requirements` 또는 `start-work`로 회송한다.
- Requirements 작성 전에는 같은 topic의 `question-cN.md`를 순서대로 읽는다.
- Requirements는 단일 `requirements.md`, plan은 단일 `plan.md`다.
- `requirements.md`에는 사람과 agent가 함께 읽을 수 있는 도메인별 요구사항/제약조건 목록을 담는다.
- Non-trivial implementation은 topic folder 안의 `requirements.md`와 `plan.md` gate를 거친다.
- `executing-plan` 완료 뒤에는 `review-execution`이 자동으로 실행되어야 한다.
- `review-execution` 완료 뒤 code cleanup은 optional이다. 자동으로 실행하지 않고 사용자에게 실행 여부를 묻고, 승인되면 `cleanup-code` skill을 사용한다.
- `finalize`는 topic status를 정리하고 post-finalize git action 선택을 묻는 데서 멈춘다. commit/PR/release/deploy는 사용자가 명시적으로 승인할 때만 수행한다.
- `topic.md`는 initial request, topic boundary, durable notes, artifact orientation을 담는 agent-first low-churn resume document다. 진행 snapshot이나 task list처럼 지속 갱신하지 않는다.
- `audit.jsonl`은 append-only event log이며 현재 phase, next action, blocker, approval, verification은 `scripts/topic-log.py status --json`으로 파생한다.
- 리뷰 판정 어휘는 `passed | findings | blocked`, 검증 판정 어휘는 `PASS | FAIL | INCONCLUSIVE`, 구현 완료 보고는 `DONE | NEEDS_CONTEXT | BLOCKED`를 사용한다. `INCONCLUSIVE`는 PASS가 아니며, `DONE`은 controller가 diff/evidence/verification을 확인하기 전까지 완료 주장이므로 task 완료나 execution-complete의 근거가 될 수 없다.
- task 리뷰 상세는 `execute/task-<N>-requirements-review.md` / `execute/task-<N>-quality-review.md`, cleanup 리뷰 상세는 `clean-up/review-result-<type>.md`에 YAML frontmatter `verdict`와 함께 기록한다.
- Public docs는 `https://github.com/HSRyuuu/harness-as-usual.git`와 `AS_USUAL_REPO`를 사용한다. `/Users/...` 같은 private absolute path를 public install docs에 넣지 않는다.
- `.as-usual/memory/`는 topic을 가로지르는 curated 지식을 저장한다. `MEMORY.md`는 3000자 budget을 유지하고, 도메인별 파일은 `*_MEMORY.md` 명명 규칙을 따른다. `topic/` artifact와 달리 `.as-usual/memory/*`는 커밋 대상이므로 갱신 시 명시적으로 stage한다.
- Draft/probe skill은 커밋하지 않는다. stable skill만 `skills/`에 둔다.
- Maintainer-only project skills live under `.agents/skills/`; `.claude/skills/` mirrors them for Claude-facing local usage. Use `skill-registry-sync` after changing either side.
- 커밋할 때는 path를 명시적으로 stage한다. broad `git add .`를 피한다.

## ANTI-PATTERNS

- `.as-usual/state.md`, `.as-usual/audit.md` 같은 project-global artifact를 만든다 (`.as-usual/memory/`는 의도된 예외이며 curated 커밋 대상이다).
- `.as-usual/` 아래 임의의 project-global 상태/감사 artifact를 만든다.
- 새 runtime topic에 제거된 legacy JSON state artifact를 만들거나 운영 source of truth로 사용한다.
- `.as-usual/topics/yyyyMMdd-<topic>/` 같은 과거 path를 새 artifact에 사용한다.
- Hook이 주입됐다는 이유만으로 일반 요청에 AsUsual workflow를 강제한다.
- `requirements.md`를 여러 파일로 쪼갠다.
- `spec.md`와 `requirements.md`를 같은 topic에 함께 만든다.
- 빠른 구현을 위해 question/requirements/plan gate를 조용히 약화한다.
- Plugin development 지침을 `core-workflow.md`에 섞는다.
- Repo-relative install example을 특정 개인 머신 path로 바꾼다.
- Codex local plugin setup에 default `personal` marketplace를 쓴다.
- `.codegraph/`, `.as-usual/topic/`, installed plugin cache output, local probe output을 커밋한다 (`.as-usual/memory/`는 커밋 허용).

## COMMANDS

```bash
# Manifest 검증
jq empty .claude-plugin/plugin.json .claude-plugin/marketplace.json
jq empty .codex-plugin/plugin.json .agents/plugins/marketplace.json
jq empty hooks/hooks.json hooks/hooks-codex.json
jq '.skills,.hooks' .codex-plugin/plugin.json

# Hook smoke 검증
CLAUDE_PLUGIN_ROOT="$PWD" bash hooks/run-hook.cmd session-start \
  | jq '{event: .hookSpecificOutput.hookEventName, hasUsingSkill: (.hookSpecificOutput.additionalContext | contains("using-as-usual")), isOneSentence: (.hookSpecificOutput.additionalContext | split(".") | length <= 2), hasNoRuleSource: (.hookSpecificOutput.additionalContext | contains("Harness rule source:") | not), hasNoActiveCandidates: (.hookSpecificOutput.additionalContext | contains("Active topic candidates:") | not), hasNoFullCore: (.hookSpecificOutput.additionalContext | contains("## 8. Plan Rules") | not)}'

# Public surface에 draft/cache가 섞였는지 확인
git ls-tree -r --name-only HEAD | rg '^(commands/|skills/as-usual-(interview|execute|test)/)' || true
git grep -n 'private absolute path' HEAD || true

# Codex plugin snapshot reload
codex plugin remove as-usual@as-usual-local --json
codex plugin add as-usual@as-usual-local --json
```

## PROJECT-LOCAL VERIFICATION SKILLS

| Skill | Purpose |
| --- | --- |
| verify-runtime-surface | Runtime-facing surface에 maintainer/plugin-development guidance가 섞였는지 검증한다. |
| verify-as-usual-harness | Runtime workflow, hook injection, plugin manifests smoke test를 검증한다. |
| verify-runtime-workflow-consistency | Runtime workflow, public runtime skills, requirements/plan templates, reviewer prompt 일관성을 검증한다. |
| verify-project-identity | Durable project identity와 maintainer docs가 broad workflow/artifact/verification 변경을 반영했는지 검증한다. |

## NOTES

- `as-usual-rules/core-workflow.md` is the only runtime workflow prompt.
- Runtime workflow skills in `skills/` are stable public plugin surface. Keep maintainer-only skills under `.agents/skills/`.
- Post-execute policy is: task-level test/verification inside `executing-plan`, mandatory `review-execution`, optional `cleanup-code` cleanup after review, and `finalize` asking for post-finalize git action selection.
