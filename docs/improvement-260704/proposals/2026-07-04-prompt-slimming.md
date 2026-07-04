# 개선 제안: 프롬프트 슬리밍 — core §16 축소 + start-work 중복 정리 (F12, 동작 보존)

- **작성:** Fable / 2026-07-04
- **개선 축:** ④ 프롬프트 (동작 보존 — 의미/게이트 변경 절대 금지)
- **규모:** Medium
- **상태:** 기록용 (사전 승인 — working-dir/00-README.md §공통 프로토콜 2, 02-DECISIONS 범위 내; 권고안에서 벗어나지 않음) → 적용

## 1. 문제 (근거 인용)

1. `as-usual-rules/core-workflow.md` §16 Required Skills가 각 skill마다 (a) 트리거 문장 + (b) 2-단락 동작 요약을 담아 ~39줄(현재 615-653행). (b)의 동작 요약은 각 `skills/*/SKILL.md`의 Responsibility Boundary/서두 및 core §4-§13과 실질 중복이다. §16의 고유 정보는 **트리거(언제 어느 skill)** 뿐이다.
   - 예: line 629 `define-requirements` 동작 요약("writes/updates requirements.md, runs reviewer prompt, marks requirements-complete, asks for plan approval, stops … cannot be paused")은 §6:327과 중복.
   - 예: line 637 `executing-plan` 요약은 §9:401-413과 중복.
   - 예: line 653 `git-action` 요약("stages paths explicitly …")은 §12:485-489와 중복.
2. `skills/start-work/SKILL.md` Routing Principle(현재 27-34행)이 core §4 Routing principle(현재 182-190행)과 준-verbatim 중복. 같은 파일 Route Table 섹션(36-38행)은 이미 "core §4 참조"로 처리하고 있어 자기모순적.
3. core-workflow 내 "Do not hand-edit" 계열 3곳: Inviolable(:32), §2(:154), §13(:512).

## 2. 변경 제안

### 8-A. §16을 트리거 라우팅 테이블로 축소 (615-653행 교체)

각 skill의 "무엇을 하는지" 서술을 제거하고 "언제 부르는지" 트리거만 표로 남긴다. "무엇을 하는지"는 각 SKILL.md와 core §4-§13이 소유. **삭제 전, 아래 8-A 대조 표로 §16의 모든 규범 문장이 다른 곳에 이미 존재함을 문장 단위로 입증**했다. 대응 위치가 없어 이동(MOVE)해야 하는 문장: **0건**.

before(요지): 트리거 문장 + skill별 2-단락 동작 요약 (39줄).
after: 1문장 intro + 11행 트리거 테이블 (아래 §"적용된 §16").

step-06이 추가한 `finalize`의 cancelled 트리거("or when the user explicitly abandons the topic (`cancelled`)", line 647)는 규범이므로 테이블 `finalize` 행에 보존한다(홈: §11:451).

### 8-B. start-work Routing Principle 중복 제거

`skills/start-work/SKILL.md` Routing Principle(27-34행)을 §4 참조형으로 교체. High-Risk/heavier-gate 문장은 안전 중복으로 의도적 유지. Route Table 섹션(36-38행)은 이미 참조형이므로 불변.

### 8-C. core 내부 "Do not hand-edit" 반복 — **유지 결정 (변경 없음)**

Inviolable(:32)과 §13(:512)은 유지(안전 중복 + 상세 규칙 위치). §2의 해당 문구(line 154)는 **유지**한다.
- 판단: §2 line 154는 독립된 "Do not hand-edit" 중복이 아니라 **"topic.md/audit.jsonl은 topic-log.py로만 갱신하고 phase 매크로 명령을 선호하라"** 는 Artifact Contract 규칙 bullet에 매크로 목록과 함께 임베드되어 있고, "instead of hand-editing those files"는 그 규칙의 꼬리절이다. §13 참조로 축약하면 매크로-선호 규칙과 매크로 목록을 훼손할 위험이 있고 이득이 미미하다.
- step-08 지침("판단이 애매하면 유지, 이 step에서 안전 중복 제거는 loss가 더 크다") 및 D-guardrail("when in doubt, keep")에 따라 유지. 깔끔한 standalone 중복은 §13:512 하나뿐이며 그대로 둔다.

## 8-A. 문장 단위 대조 표 (삭제 전 필수 증거)

§16 전문을 규범 문장으로 분해하고 각 문장의 처분을 기록한다. 처분 유형: **TRIGGER**(테이블 행으로 보존) / **EVIDENCE-DELETED**(동작 서술 — 홈 확인 후 산문에서 제거) / **MOVED**(홈 없음 → 소유자 파일로 이동).

| # | §16 원문 문장(요지) | 유형 | 확인된 홈 |
| --- | --- | --- | --- |
| 1 | "When AsUsual is active, use `using-as-usual` skill first." | TRIGGER (intro 보존) | §3:161, §5:227, using-as-usual SKILL |
| 2 | "`using-as-usual` is the activation and first-read helper." | TRIGGER 행 | 테이블 `using-as-usual` 행; skills/using-as-usual/SKILL.md |
| 3 | "The canonical runtime workflow is this `core-workflow.md`." | intro 보존 | 새 intro 문장에 유지; §0:59 |
| 4 | "After first reads, use `start-work` when starting a new topic or the next phase is unclear." | TRIGGER 행 | 테이블 `start-work` 행; §4:180, §5:227 |
| 5 | "`start-work` is the gate routing helper. It does not replace activation decisions, first reads, or full requirements/plan authoring." | EVIDENCE-DELETED | §4:180 ("start-work does not decide AsUsual activation. Activation and first reads are the responsibility of using-as-usual"); start-work SKILL:8,12 |
| 6 | "Use `define-requirements` when route is `requirements`, answered files need validation, or user asks to write/update requirements." | TRIGGER 행 | 테이블 행; §5:229-263 |
| 7 | "`define-requirements` handles question file creation/update, answer validation, next-cycle decisions, requirements writing/review. It does not replace … Requirements Rules." | EVIDENCE-DELETED | §6:319-331, §7; define-requirements SKILL:14-23 |
| 8 | "`define-requirements` writes/updates requirements.md, runs reviewer prompt, marks requirements-complete, asks plan approval, stops." | EVIDENCE-DELETED | §6:327 (동일 서술 + "cannot be paused mid-synthesis") |
| 9 | "It absorbs requirements revisions before plan approval and routes artifact-changing answers through requirements review again." | EVIDENCE-DELETED | §5:265-270; define-requirements SKILL |
| 10 | "Follows Clarification Routing." (define-requirements) | EVIDENCE-DELETED | Clarification Routing §203-213; define-requirements SKILL:23 |
| 11 | "It does not write `plan.md`." (define-requirements) | EVIDENCE-DELETED | define-requirements SKILL:23,271; §8 (writing-plan owns plan.md) |
| 12 | "Use `writing-plan` when user approves moving from completed requirements to plan, or asks to write/update plan.md." | TRIGGER 행 | 테이블 행; §5:272, §8:369 |
| 13 | "`writing-plan` analyzes dependencies, writes/updates one plan.md, runs self-review + plan reviewer prompt, records plan-review/approve-execute, asks execution approval, stops." | EVIDENCE-DELETED | §8:364-385; writing-plan SKILL:26 |
| 14 | "It routes requirements-changing answers back to `define-requirements`." | EVIDENCE-DELETED | §5:278-283; §8:385; writing-plan SKILL |
| 15 | "Follows Clarification Routing." (writing-plan) | EVIDENCE-DELETED | Clarification Routing §203-213; writing-plan SKILL |
| 16 | "It does not execute work." (writing-plan) | EVIDENCE-DELETED | writing-plan SKILL:26 ("does not execute work … stops before any implementation") |
| 17 | "Use `executing-plan` when requirements.md and plan.md are current and user explicitly approves/requests execution." | TRIGGER 행 | 테이블 행; §5:285, §9:393-397 |
| 18 | "`executing-plan` re-reads context; critically reviews plan; executes tasks in order in approved inline/subagent-driven/mixed mode; records progress, task review loops, final sweeps, verification via topic-log.py." | EVIDENCE-DELETED | §9:401-409 |
| 19 | "stops at blockers, unresolved task findings, repeated verification failure, new material user decisions, missing high-risk approvals, requirements/plan contradictions." | EVIDENCE-DELETED | §9:410-412 |
| 20 | "routes back to writing-plan/define-requirements if artifacts must change." | EVIDENCE-DELETED | §9:411 |
| 21 | "Follows Clarification Routing." (executing-plan) | EVIDENCE-DELETED | §9:411; Clarification Routing §203-213 |
| 22 | "does not use plan.md as progress ledger; keeps main agent controller even when subagents implement/review." | EVIDENCE-DELETED | §9:404-405,408 |
| 23 | "invokes review-execution after execution completion instead of commit/PR/release/deploy behavior." | EVIDENCE-DELETED | §9:413; §5:294 |
| 24 | "Use `review-execution` when executing-plan completed or topic waiting for optional code cleanup decision." | TRIGGER 행 | 테이블 행; §5:294,302, §10 |
| 25 | "`review-execution` reviews actual changed code + evidence against requirements/plan; records findings via topic-log.py; handles review follow-up dispositions for Critical/Important." | EVIDENCE-DELETED | §10:429-433; §5:297-300 |
| 26 | "ends response by asking whether to run optional code cleanup or skip+finalize only after dispositions clear." | EVIDENCE-DELETED | §10:434; review-execution SKILL:134 |
| 27 | "handles a decline by routing to finalize; invokes cleanup-code when user approves." | EVIDENCE-DELETED | §5:302-308; review-execution SKILL:53,134 |
| 28 | "It does not treat code cleanup as correctness review." | EVIDENCE-DELETED | §10:438 |
| 29 | "Use `cleanup-code` after review-execution records review completion and user approves code cleanup." | TRIGGER 행 | 테이블 행; §5:305, §10:438 |
| 30 | "`cleanup-code` runs four cleanup reviews (reuse, simplification, efficiency, abstraction level)." | EVIDENCE-DELETED | cleanup-code SKILL:17,55-58 |
| 31 | "applies only safe behavior-preserving cleanup within approved change surface; reruns verification when files change; records result via topic-log.py; routes to finalize." | EVIDENCE-DELETED | §10:438; §5:308 |
| 32 | "Use `finalize` after execution review + code cleanup decision recorded, or when user explicitly abandons the topic (`cancelled`)." | TRIGGER 행 (cancelled 보존) | 테이블 행; §5:308, §11:451 |
| 33 | "`finalize` checks topic record, sets final status complete/follow-up-needed/blocked/cancelled, records finalization, asks which git action, stops." | EVIDENCE-DELETED | §11:453-460 |
| 34 | "It does not run git commands, create PR, release, or deploy." | EVIDENCE-DELETED | §11:455 |
| 35 | "Use `git-action` after finalization when user chooses none/commit/commit+push/commit+push+PR." | TRIGGER 행 | 테이블 행; §5:311, §12:474-479 |
| 36 | "`git-action` records selected action, follows git-master commit discipline, stages paths explicitly, creates atomic commits when selected, pushes only when selected, creates PR only when selected+supported, records outcomes, stops." | EVIDENCE-DELETED | §12:481-489; git-action SKILL |

**집계:** 총 규범 문장 36. TRIGGER(테이블 행/intro로 보존) = 12. EVIDENCE-DELETED(홈 확인 후 산문 제거) = 24. **MOVED = 0** (홈 없는 문장 없음).

**추가된 트리거 행 2개(순 증가, 삭제 아님):** `manage-self-improvement`(홈 §11:461) 및 `search-long-term-memory`(홈 skills/search-long-term-memory/SKILL.md). 둘 다 Required Skills인데 기존 §16 산문엔 트리거 행이 없었다. 라우팅 테이블 완결성을 위해 추가하며 어떤 게이트도 변경하지 않는다.

## 적용된 §16 (after)

```markdown
## 16. Required Skills

When AsUsual is active, use `using-as-usual` first. The canonical runtime workflow is this `core-workflow.md`; each skill file owns its own detailed behavior.

| Skill | Invoke When |
| --- | --- |
| `using-as-usual` | AsUsual activates; owns activation confirmation and first reads |
| `start-work` | New topic or the next phase is unclear after first reads |
| `define-requirements` | Route is `requirements`, answered question files need validation, or the user asks to write/update requirements |
| `writing-plan` | User approves moving from completed requirements to plan, or asks to write/update `plan.md` |
| `executing-plan` | `requirements.md` and `plan.md` are current and the user explicitly approves or requests execution |
| `review-execution` | Execution completed, review follow-up is needed, or the optional code cleanup decision is pending |
| `cleanup-code` | Review recorded and the user approves code cleanup |
| `finalize` | Execution review and the code cleanup decision are recorded, or the user explicitly abandons the topic (`cancelled`) |
| `git-action` | Topic finalized and the user chooses `none`, `commit`, `commit + push`, or `commit + push + PR` |
| `manage-self-improvement` | Triggered by `finalize` before topic closure |
| `search-long-term-memory` | Read-only recall from `.as-usual/memory/*`; typically dispatched as a subagent |
```

## start-work Routing Principle (before/after)

before (skills/start-work/SKILL.md:27-34):
```
## Routing Principle

- Treat the High-Risk Operation Gate in `core-workflow.md` as a hard gate.
- Route to `requirements` when material ambiguity exists or the work needs a reviewed `requirements.md`.
- Route to `plan` when `requirements.md` is complete/current, the user approved moving on to plan, and execution order or verification needs definition.
- Route to `execute` when `requirements.md` and approved/current `plan.md` exist and the user asks to execute.
- Route to `direct-execute` only for very simple, low-risk, reversible work.
- When borderline, choose the heavier gate.
```

after:
```
## Routing Principle

Use the canonical routing principle and Route table in `core-workflow.md` §4 (Start Work Gate Routing); do not maintain a second copy here. Treat the High-Risk Operation Gate as a hard gate, and when borderline, choose the heavier gate.
```

## 3. 함께 갱신할 대상 (정합성)

- `as-usual-rules/core-workflow.md` §16 — 트리거 테이블로 축소 (본 변경).
- `skills/start-work/SKILL.md` Routing Principle — §4 참조형 교체 (본 변경).
- 소유권 이동 없음: reviewer 체크리스트 ↔ core, machine-readable 값(phase/next-action/status/이벤트명) 전부 불변.

## 4. 가드레일 점검

- [x] 안전 게이트 약화 없음 — 규범 문장은 삭제만 하지 않고 8-A 대조 표로 홈 입증(MOVED 0). 게이트 의미 불변.
- [x] runtime ↔ maintainer 경계 유지 — maintainer 규칙을 core/skill에 넣지 않음.
- [x] 단일 원본 원칙 강화 — §16의 중복 동작 서술 제거로 SKILL.md/core §4-§13이 단일 소유자가 됨.
- [x] machine-readable marker/status 값 보존 — 표에 `none/commit/commit + push/commit + push + PR`, `cancelled` 등 값을 원문 그대로 유지.
- [x] step-04~07 신규 문장 무손상 — Key Terms focused/broad(§43-48), Clarification Routing cascade(§203-213), §11 cancelled(:451), §5 direct-execute terminal note(:239-243), Inviolable NEVER scoping(:33), marker 언어 정책(§144-146)은 §16/start-work 밖이라 미접촉. §16의 cancelled 트리거는 표에 보존.

## 5. 검증 계획

```bash
python3 -m unittest discover -s .agents/skills/sandbox-e2e-test/tests -p 'test_*.py'
wc -l as-usual-rules/core-workflow.md   # before 653 → after 감소
# verify-runtime-workflow-consistency (필수) + verify-runtime-surface 절차
```
탁상 검증: 새 §16 표만 보고 "리뷰 완료 + 사용자 cleanup 승인" → `cleanup-code` 판정 가능(기대 일치).

## 6. 롤백

```bash
git checkout -- as-usual-rules/core-workflow.md skills/start-work/SKILL.md
```
