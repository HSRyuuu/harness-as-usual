# 99. AsUsual 개선 라운드 최종 검증 보고서 (step-10)

- **작성:** Claude (Opus 4.8) / 2026-07-04
- **역할:** step-10 실행 에이전트 (전체 재검증 + maintainer 문서 동기화 + 최종 보고)
- **성격:** plugin development. `.as-usual/topic/` runtime workflow는 돌리지 않았다.
- **종합 판정:** **모든 step 적용 완료, 반려/보류 0건. 전체 기계·의미 검증 통과.** step-10에서 maintainer 문서 1건(`docs/ARCHITECTURE-WORKFLOW.md`)의 실질 불일치 1건을 발견·수정했다. `PROJECT_IDENTITY.md` 충돌 없음.

---

## 1. step별 수행 결과 (적용 / 반려 / 보류 + 커밋 SHA)

| Step | F-ID | 결과 | 커밋 SHA | 비고 |
| --- | --- | --- | --- | --- |
| step-01 | F1~F5 | 적용 | `fa40f54` | small 일괄 정정 |
| step-02 | F6 | 적용 | `0355908` | `<plugin-root>` 경로 표기 통일 |
| step-03 | F7 | 적용 | `230bee8` | feature-development 활성화 신호 core §1 반영 |
| step-04 | F8 | 적용 | `5130c88` | Clarification Routing focused/broad 재정의 + Inviolable ALWAYS 재문구 |
| step-05 | F9 | 적용 | `8620ecb` | review-execution 심각도별 disposition 매트릭스 |
| step-06 | F10 | 적용 | `4538f8b` | cancelled 종단 경로 + direct-execute 경량 종단 + Inviolable NEVER 범위 명확화(D5); script+tests+ARCHITECTURE 동기화, 테스트 미러 동기화 |
| step-07 | F11 | 적용 | `abea6cc` | 영어 canonical 템플릿 heading + E2E fill 파서/테스트 + 미러 |
| step-08 | F12 | 적용 | `078aac5` | core §16 트리거 라우팅 표로 슬리밍 (653→631줄) |
| step-09 | F13 | 적용 | `ad484ab` | hook 호스트 분기 문서화 (CLAUDE.md/AGENTS.md/ARCHITECTURE-WORKFLOW) |
| step-10 | — | 적용 | (오케스트레이터 커밋 예정) | 본 보고서 + ARCHITECTURE-WORKFLOW:276 disposition 정합 수정 |

**반려/보류:** 없음. 계획된 9개 F-ID 전부 적용. CRITIC-RESULT에서 사전 확정된 4개 사용자 결정(C1~C4)과 3개 직접 정정(I1~I3)은 실행 전에 이미 계획 문서에 반영되었고, 실행 결과가 이를 준수했음을 확인했다.

## 2. F-ID별 해소 여부 (원본 재확인 결과)

| F-ID | 해소 | 근거 (현재 디스크 상태) |
| --- | --- | --- |
| F1 | ✅ | `writing-plan/SKILL.md:263-267` Complete Plan 번호 1→2→3→4→5 연속 |
| F2 | ✅ | `templates/report.md`에 `## Simplify Decision` 없음; code cleanup 명칭으로 정합 |
| F3 | ✅ | controller 위임 문단 중복 제거 (core §3 ↔ using-as-usual 단일 원본) |
| F4 | ✅ | `finalize/SKILL.md` 전제조건 자기참조 제거; Step 0가 self-improvement pass 수행 |
| F5 | ✅ | `finalize/SKILL.md:101,149` `validate` 호출 명시 ("Do not finalize while validate fails") |
| F6 | ✅ | 명령/비명령 경로 모두 `<plugin-root>` 표기로 통일 (bare `scripts/` 실행 예시 잔존 없음) |
| F7 | ✅ | `core-workflow.md:106` feature-development 신호 행 추가 → hook/skill/CLAUDE/AGENTS와 4표면 정합 |
| F8 | ✅ | Key Terms(47-48)·Clarification Routing(203-213)·§5(289)·§9(411)·executing-plan(226)·plan reviewer(58) 전부 focused/broad 축으로 일치 |
| F9 | ✅ | `review-execution/SKILL.md:105-112` 심각도별 매트릭스; `user-accepted-risk`/`deferred`는 Minor 한정 명문화 |
| F10 | ✅ | `cancelled`가 core §11(451,456-458)·finalize(38,117-119)·`validate` 조건부 면제·direct-execute 경량 종단으로 3표면 노출 |
| F11 | ✅ | `templates/question.md`·`define-requirements:82-86` 영어 canonical heading(순서/개수 고정, 번역 허용); `[Answer]:`/option letter 불변 |
| F12 | ✅ | core §16 트리거 라우팅 표로 축소, 전체 631줄; §16 규범 문장 유실 없음(step-08 8-A 대조표 근거) |
| F13 | ✅ | hook 호스트 분기(Cursor 실험적/Codex/Claude/fallback)가 CLAUDE.md:70·AGENTS.md:74·ARCHITECTURE-WORKFLOW:114에 문서화 |

## 3. 전체 검증 결과 (기계 + 의미)

### 3.1 기계 검증

| 명령 / 절차 | 결과 |
| --- | --- |
| `python3 -m unittest ... .agents/skills/sandbox-e2e-test/tests` | **PASS** — 55 tests OK |
| `python3 -m unittest ... .claude/skills/sandbox-e2e-test/tests` (미러) | **PASS** — 55 tests OK |
| `jq empty` × 6 manifest (claude-plugin/marketplace, codex-plugin, agents/plugins, hooks×2) | **PASS** — 전부 exit 0 |
| Hook smoke (CLAUDE.md COMMANDS 필터) | **PASS** — event=SessionStart, hasUsingSkill=true, isOneSentence=true, hasNoRuleSource/ActiveCandidates/FullCore=true |
| `git ls-tree ... rg '^(commands/\|skills/as-usual-(interview\|execute\|test)/)'` | **PASS** — 매치 없음 (draft/maintainer 유출 없음) |

### 3.2 aggregate 의미 검증 (verify-implementation 절차, 4개 skill END-TO-END)

**verify-runtime-surface — PASS (4/4)**

| Check | 결과 |
| --- | --- |
| Hook output leakage | PASS — 주입 컨텍스트는 runtime-facing 한 문장뿐 |
| Runtime prompt surface | PASS — maintainer 유출 0, stale removed-surface 참조 0 |
| Public skill boundary | PASS — `skills/`에 maintainer skill 없음 |
| Public docs boundary | PASS — 공개 문서에 maintainer 라우팅 없음 |

**verify-as-usual-harness — PASS (5/5)**

| Check | 결과 |
| --- | --- |
| Manifest JSON | PASS |
| Runtime workflow file | PASS — core-workflow.md 비어있지 않음 |
| Hook injection (전체 마커) | PASS — hasNoMemoryContent/hasNoArtifactRules/oldPath=false 포함 전부 통과 |
| Removed surface | PASS — 매치는 CLAUDE.md:150·AGENTS.md:170의 anti-pattern 문서뿐 (Exception 1 해당) |
| Sandbox E2E linter/helper smoke | PASS — topic-log init/status/validate OK; linter fixture는 exit 1이지만 파싱 가능한 JSON(`overallResult=FAIL`) 출력 = 계약 검증 통과 (fixture는 과거 리포트라 PASS/FAIL 무관) |

**verify-runtime-workflow-consistency — PASS (전 Step)**

| Check | 결과 |
| --- | --- |
| Required files | PASS — MISSING 없음, topic-log --help exit 0 |
| Route ownership | PASS |
| Hook/activation alignment | PASS — 4표면 feature-development 신호 일치 |
| Requirements review vocabulary | PASS — `Status: draft\|requirements-complete\|blocked`, `Reviewer Result: not-run\|passed\|issues-fixed\|blocked` |
| Ambiguity/assumptions (F8) | PASS — focused/broad 이분법 전면 일치 |
| Safety gates + review follow-up (F9) | PASS — C/I 3-경로 + 매트릭스 정합 |
| Removed runtime surface | PASS — stale audit-first 참조 0 |

**verify-project-identity — PASS (전 Step)**

| Check | 결과 |
| --- | --- |
| Required durable docs | PASS |
| Changed surface → durable doc review | PASS — 아래 §4 참조 |
| Runtime vocabulary | PASS — stale 용어 0 |
| Identity principles coverage | PASS |
| Durable doc alignment | PASS (ARCHITECTURE-WORKFLOW:276 수정 후) |
| Verification registry | PASS — 4개 verify skill이 레지스트리에 등록됨 |
| Maintainer/runtime boundary | PASS |

### 3.3 검증 중 발견·해결한 이슈 (숨김 없음)

1. **ARCHITECTURE-WORKFLOW.md:276 disposition 드리프트 (실질 불일치 — step-10에서 수정):** 해당 줄이 Critical finding의 예시 disposition으로 `user-accepted risk`를 나열했으나, step-05(F9) 매트릭스는 `user-accepted-risk`/`deferred`가 Critical/Important에 **절대 불가**라고 명문화한다. F9 적용 시 이 maintainer 문서가 함께 갱신되지 않아 남은 드리프트다. → maintainer 표면이므로 직접 수정(아래 §4). runtime 표면 수정은 아님.
2. **미러 diff `__pycache__`:** `.agents/skills` ↔ `.claude/skills` diff에 `.pyc` bytecode 차이만 나타남. git 추적 대상 아님(`git ls-files` empty), 소스 미러는 `--exclude=__pycache__`로 완전 일치. 실질 이슈 아님.

## 4. maintainer 문서 동기화 결과

step-10 표의 확인 포인트별 판정:

| 문서 / 포인트 | 판정 | 근거 |
| --- | --- | --- |
| `docs/ARCHITECTURE-WORKFLOW.md` §8 disposition(:276) | **수정함** | F9 매트릭스와 충돌 → 아래 정확한 문장 참조 |
| `docs/ARCHITECTURE-WORKFLOW.md` phase/state/transition (step-04/06) | 갱신 불필요 | Full Workflow(:94-106)·§10 finalize(:315-326)가 이미 direct-execute·cancelled·경량 종단·report 면제·self-improvement 실행을 정확히 서술 |
| `docs/ARCHITECTURE-WORKFLOW.md` 템플릿 섹션 목록 (step-01 report 개명, step-07) | 갱신 불필요 | 템플릿 목록(:40-49, :365-396)에 `report.md`/`code-review-report.md` 정확히 포함; legacy `Simplify` 명칭 없음 |
| `CLAUDE.md` / `AGENTS.md` RUNTIME WORKFLOW MODEL (finalize/상태 — step-06) | 갱신 불필요 | 두 문서 모두 finalize를 "topic status를 정리"로 **일반 서술**하며 상태 집합을 열거하지 않음 → 정정할 stale 목록이 없음. 상세 종단-상태 모델은 canonical(`core-workflow.md`)과 상세 문서(ARCHITECTURE-WORKFLOW)에 이미 동기화. 요약 문서에 cancelled를 추가하는 것은 정정이 아니라 신규 상술이라 gold-plating으로 판단, 미실시 |
| `CLAUDE.md` / `AGENTS.md` CONVENTIONS (clarification 문구 — step-04) | 갱신 불필요 | 두 문서 CONVENTIONS가 이미 focused/broad 모델 서술 ("좁은 clarification은 chat + audit 기록", "broad ambiguity/topic-boundary는 define-requirements/start-work 회송") — step-04와 정확히 일치 |
| `CLAUDE.md` / `AGENTS.md` HOOK ACTIVATION MODEL (step-03/09) | 갱신 불필요 | 신호 4개(feature-development 포함) + F13 호스트 분기 문단이 양쪽에 존재 |
| `CLAUDE.md` / `AGENTS.md` COMMANDS smoke 필터 | 유효 확인 | 필터 실행 시 전 필드 기대값 반환 (§3.1) |
| `PROJECT_IDENTITY.md` | 충돌 없음 (읽기 전용) | 아래 §5 |

**정확한 수정 문장 (ARCHITECTURE-WORKFLOW.md:276):**

- Before: `Critical finding은 fix, block, user-accepted risk 같은 disposition 없이 finalize로 갈 수 없다.`
- After: ``Critical/Important finding은 `fixed`(재리뷰 통과), `rejected`(기술적 사유 + 재리뷰 통과), 또는 `blocked` disposition 중 하나 없이 finalize로 갈 수 없다. `user-accepted-risk`와 `deferred`는 Minor finding에만 허용된다.``

**maintainer skill 미러 동기화:** 이번 라운드에서 `.agents/skills/`의 maintainer skill을 수정하지 않았다(수정 대상은 runtime 표면 + docs뿐). 소스 미러는 이미 일치하므로 `skill-registry-sync` 불필요. (`__pycache__` bytecode는 추적 대상 아님.)

## 5. PROJECT_IDENTITY 충돌 검사 결과

**충돌 없음.** 적용된 어떤 변경도 `PROJECT_IDENTITY.md` 원칙과 상충하지 않는다.

- `:55` "Focused clarifications may happen in chat only when the answer is recorded in `audit.jsonl`" — F8 focused/broad 재정의의 기준점 그대로. 정합.
- `:28-29` broad ambiguity → 파일 기반 questions, material 결정 기록 — F8과 일치.
- `:63` "Code cleanup is optional and user-approved." — CRITIC C2에서 이미 개명 완료. F2 전제 성립.
- `cancelled`(F10)는 PROJECT_IDENTITY가 상태 집합을 열거하지 않으므로 어떤 원칙과도 충돌하지 않음. "durable topic artifacts"를 종단까지 완성하는 방향과 오히려 정합.

PROJECT_IDENTITY.md는 지시대로 편집하지 않았다(읽기 전용 검사만).

## 6. 표면 간 불일치 (위치 + 오케스트레이터 조치 필요 여부)

| 발견 | 위치 | 성격 | 조치 |
| --- | --- | --- | --- |
| disposition 예시가 F9 매트릭스와 충돌 | `docs/ARCHITECTURE-WORKFLOW.md:276` | maintainer 문서 드리프트 | step-10에서 직접 수정 완료. 오케스트레이터 추가 조치 불필요(커밋만) |

runtime 표면(`as-usual-rules/`, `skills/`, `templates/`, `hooks/`)에서는 조용히 고쳐야 할 불일치를 발견하지 못했다. 오케스트레이터 판단이 필요한 runtime-surface 이슈 없음.

## 7. 후속 과제 (이번 라운드 범위 밖)

01-DIAGNOSIS "제외한 항목" 재평가 + 실행 중 발견 사항:

1. **subagent task 이중 리뷰(requirements review + quality review) 부담** — `executing-plan/SKILL.md`. 제외 판단 타당(PROJECT_IDENTITY 실패 모드 1 예방 장치, 게이트 약화 위험). **재평가 조건:** sandbox E2E 증거가 쌓이면 ceremony 비용 대비 효과 재검토.
2. **`scripts/topic-log.py` 1,524줄 단일 파일 분할** — 테스트 전면 개편 동반 대형 리팩터링. 이번 하네스 품질 목표 대비 이득 불분명해 제외. **재평가 조건:** 스크립트에 신규 상태/커맨드가 더 붙어 유지보수 비용이 오르면 모듈 분리 재검토.
3. **maintainer skill 미러 구조(`.agents/skills` ↔ `.claude/skills`)** — `02-FILE-STRUCTURE §G`가 범위 밖으로 명시. 유지. (참고: 소스는 동기화 상태이나 `__pycache__` bytecode가 두 트리에 생성됨 — `.gitignore`에 이미 미추적이지만, 미러 diff 노이즈를 줄이려면 pycache 정리/무시 규칙을 고려할 수 있음.)
4. **step-07 권장 sandbox E2E 스모크(선택, 비용 큼):** 영어 canonical heading 전환 후 실제 질문 사이클 1회 E2E 스모크(`sandbox-e2e-test` 스킬)를 사용자 승인 하에 1회 실행 권장. 단위 테스트(55×2)는 통과했으나 실주행 파서 검증은 별개. **본 step-10에서는 비용상 미실행** — 후속 권장.
5. **step-06 `--report` 기본값 메모:** `cancelled` 종료 시 `report.md`가 면제인데 `finalize-topic`의 `--report` 인자 처리가 cancelled 경로에서 선택적임을 확인. 회귀 방지를 위해 `--report` 기본/생략 동작에 대한 명시 테스트를 후속으로 보강 권장.
6. **CLAUDE.md 신호 3 vs using-as-usual 신호 3 문구 차이(CRITIC 5장 지적):** CLAUDE.md 신호 3은 "in-progress topic artifacts + derived status" 조건을 붙이고 using-as-usual 신호 3은 조건 없음. 의미 충돌은 아니나 미세 문구 차이 — 다음 라운드에서 정리 가능(이번 범위 비대상).

## 8. 이 step에서 수정한 파일

- `docs/improvement-260704/working-dir/99-FINAL-REPORT.md` (신규 — 본 보고서)
- `docs/ARCHITECTURE-WORKFLOW.md` (:276 disposition 문장 F9 매트릭스와 정합)

`PROJECT_IDENTITY.md`, `hand-off/*`, runtime 표면은 수정하지 않았다. 커밋/스테이징/푸시는 하지 않았다(오케스트레이터 담당).
