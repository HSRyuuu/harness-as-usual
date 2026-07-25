# AsUsual v2 — 구현 작업 계획

기준 명세: `design.md` (충돌 시 design.md가 우선)
브랜치 전략: 단일 브랜치(`refactor/v2-work-units`), 중간 커밋 허용, **중간 상태 배포 금지**.
릴리스는 전 단계 완료 + 검증 후 `publish-as-usual` 명시 실행으로만.
AsUsual 토픽 미사용. 작업 메모는 `.as-usual/tmp/` 아래 자유 사용.

진행 표기: 각 태스크 앞 체크박스를 구현 세션이 갱신한다.

---

## Phase 1 — 기록 레이어 (기반, 최우선)

새 스크립트가 모든 스킬·rules의 참조 대상이므로 먼저 완성하고 테스트로 고정한다.

- [x] 1.1 `scripts/as_usual_record/` 모듈 신규 작성
  - `constants.py`: unit 4종(inbox 포함) · kind 12종 · phase 어휘 · nextAction 3종 ·
    verdict/status/actor 어휘 · 차단 파일 목록. legacy alias **없음**
  - `core.py`: append(read-then-append, seq 부여) · 스키마 검증 · 게이트 검증
  - `commands.py` + `cli.py`: `init` / `add` / `move` / `link` / `status` / `validate`
  - `contexts.py`: `contexts.md` 골격 생성 (상단 고정 섹션)
- [x] 1.2 스크립트 강제 게이트 구현 (design.md §4 표의 7행 전부)
- [x] 1.3 `scripts/as-usual-record.py` 엔트리포인트 교체 (구 래퍼 내용 삭제)
- [x] 1.4 구 스크립트 삭제: `topic-log.py` · `journal-log.py` ·
  `as_usual_topic_log/` · `as_usual_journal_log/`
- [x] 1.5 테스트 재작성: `scripts/tests/` 전면 교체
  - `test_record_core.py`: init/add/seq/어휘 검증/봉인(finalized 후 append 거부, link 예외)
  - `test_record_gates.py`: verdict 필수 · confirmed-요-evidence · approval-요-review ·
    issue finalize-요-conclusion.md
  - `test_record_move.py`: inbox→단위 이동 · slug rename · 차단 파일 거부 · unit-selected 이벤트
  - `test_record_status.py`: 파생 status(phase/nextAction/blockers/links) · validate

**검증**: `python3 -m pytest scripts/tests/ -q` 전체 통과.
수동 스모크: init→add(decision)→move→add(review)→add(approval:execution)→
add(verification PASS)→finalize 시나리오를 3단위 각각 1회.

## Phase 2 — rules 재편 (7개 → 3개)

- [x] 2.1 `as-usual-rules/core-rules.md` 신규 작성 (design.md §1·2·4·5·7 반영:
  단위 정의 · 분류 트리 · 강제 7 · 기록 원칙 · 전환 규칙 · 완료 판정)
- [x] 2.2 `as-usual-rules/safety-rules.md` 갱신 (신뢰 경계 · 고위험 게이트 유지,
  topic-log/journal-log 참조를 as-usual-record로 교체)
- [x] 2.3 `as-usual-rules/record-commands.md` 신규 작성 (커맨드 레퍼런스)
- [x] 2.4 구 rules 삭제: `core-workflow.md` · `find-cause-workflow.md` · `routing-rules.md` ·
  `logging-rules.md` · `completion-rules.md` · `log-audit-commands.md`

**검증**: `rg -l "topic-log|journal-log|core-workflow|find-cause-workflow|routing-rules|logging-rules|completion-rules|log-audit-commands" as-usual-rules/` 결과 0건.

## Phase 3 — 스킬 재작성 (15개)

- [x] 3.1 `using-as-usual` 전면 재작성: 4택 · 분류 트리 적용 · 명시 진입 · 경로/스캔 재개 ·
  inbox 규칙(R1) · 타 세션 상태 검증 규칙 · 오너 위임
- [x] 3.2 `start-work` · `hand-off` 삭제
- [x] 3.3 오너 3개 신설: `run-topic` · `run-direct-work` · `run-issue`
  (매트릭스 선언형. run-issue만 조사 루프 + 결론 절차 포함)
- [x] 3.4 `gathering-context` 신설 (grill-me 엔진, 호출자가 확정 항목 목록 전달,
  contexts.md 중단 기록·갱신 + decision 이벤트, 단위 분기 금지)
- [x] 3.5 개명 + 전면 수정: `define-requirements`→`write-requirements` ·
  `writing-plan`→`write-plan`(끝에 비판적 리뷰 + 실행 모드 통보 + 승인 요청) ·
  `executing-plan`→`execute-plan`(사전 리뷰 단계 제거) · `direct-execute`→`run-direct-work` ·
  `find-cause`→`run-issue` (3.3과 병합 작업)
- [x] 3.6 수정: `review-execution`(→review.md 단일 문서) · `cleanup-code`(리뷰 섹션 누적) ·
  `finalize`(memory 일괄 검토 + report.md + 봉인) · `git-action`(3단위 공유 유틸로) ·
  `manage-self-improvement`(후보/반영 분리) · `search-long-term-memory` ·
  `explore-codebase`(참조 경로만 갱신)
- [x] 3.7 리뷰어 프롬프트 3종을 "품질 기준 참조 자료" 지위로 문구 조정
  (requirements/plan/code reviewer prompt, task-reviewer-prompt는 execute-plan 참조 자료로)

**검증**: `rg -l "start-work|hand-off|topic\.md|question-c|journal-log|topic-log|problem\.md" skills/` 결과 0건 (참조 잔재 없음).
스킬별 frontmatter name과 폴더명 일치 확인.

## Phase 4 — 템플릿

- [x] 4.1 신설: `templates/contexts.md` · `templates/review.md`
- [x] 4.2 축소 재작성: `templates/requirements.md`(6섹션) · `templates/plan.md`(5섹션,
  direct-work 강도 주석) · `templates/report.md` · `templates/conclusion.md`(seq 인용 형식)
- [x] 4.3 삭제: `templates/topic.md` · `templates/question.md` · `templates/problem.md` ·
  `templates/code-review-report.md`
- [x] 4.4 `templates/MEMORY.md` 유지 (변경 없음 확인만)

**검증**: 템플릿에 `Review Status` / `Execution Mode` / `[Answer]:` 문자열 0건.

## Phase 5 — 훅 · 매니페스트 · 검증 스킬 · 문서

- [x] 5.1 `hooks/session-start` 문구 교체 (진입점 1개, 한 문장)
- [x] 5.2 매니페스트 갱신: `.claude-plugin/plugin.json` · `.codex-plugin/plugin.json`
  (스킬 개명/삭제/신설 반영) · marketplace json 2종 무결성 확인
- [x] 5.3 검증 스킬 4개 갱신: `verify-as-usual-harness` · `verify-runtime-surface` ·
  `verify-runtime-workflow-consistency` · `verify-project-identity`
  (+ `.claude/skills/` 미러 동기화, `manage-skills` 등록 목록)
- [x] 5.4 문서 갱신: `CLAUDE.md`(STRUCTURE/WORKFLOW/WHERE-TO-LOOK/CODE-MAP/CONVENTIONS/
  ANTI-PATTERNS/COMMANDS 전면) · `AGENTS.md` · `docs/` 설치 가이드(이름만) ·
  `.agents/skills/dev-as-usual/SKILL.md`
- [x] 5.5 CLAUDE.md COMMANDS 절의 스모크 커맨드를 새 스크립트 기준으로 교체

**검증**:
```bash
jq empty .claude-plugin/plugin.json .claude-plugin/marketplace.json \
        .codex-plugin/plugin.json .agents/plugins/marketplace.json \
        hooks/hooks.json hooks/hooks-codex.json
CLAUDE_PLUGIN_ROOT="$PWD" bash hooks/run-hook.cmd session-start | jq .
python3 -m pytest scripts/tests/ -q
rg -l "topic-log|journal-log|start-work|hand-off|find-cause-workflow|direct-execute" \
   --glob '!.as-usual/**' --glob '!.archived/**' --glob '!docs/test/**' .
```
마지막 rg는 0건이어야 함 (역사적 문서 제외 경로는 상황 보고 조정).

## Phase 6 — 최종 검증 · 릴리스 게이트

- [x] 6.1 E2E 수동 시나리오 3종 (별도 테스트 프로젝트에서):
  topic 풀사이클 / direct-work 경량 사이클 / issue 조사→결론→후속 링크
- [x] 6.2 오분류 전환 시나리오: inbox→move · gathering 중 move · plan 생성 후 move 거부 확인
- [x] 6.3 `.agents/skills/verify-implementation` 절차 실행
- [ ] 6.4 버전 lockstep 범프 + 릴리스는 사용자 명시 승인 후 `publish-as-usual`로만
      **← 남은 유일한 항목. 사용자 승인 대기 중.**

---

## 리스크 메모

- **가장 큰 리스크는 스킬 문구의 상호 참조 누락** (Phase 3). Phase 5.5의 rg 스윕이
  마지막 안전망이므로 패턴 목록을 작업 중 발견되는 대로 늘릴 것
- 사용 중인 다른 프로젝트의 구 포맷 `.as-usual/` 폴더는 릴리스 후 재개 불가 —
  릴리스 노트에 clean-break 명시
- `run-issue`(구 find-cause)의 조사 루프 재작성 시, 구 journal 하드 게이트 5개 중
  스크립트로 간 것(evidence/conclusion)과 규칙으로 남는 것(읽기 전용 기본, 턴 종료 전 기록)을
  구분해 이식할 것
