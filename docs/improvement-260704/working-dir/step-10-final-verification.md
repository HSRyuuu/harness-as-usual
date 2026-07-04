# Step 10. 최종 검증 + maintainer 문서 동기화

- **축:** 전체 마감
- **규모:** — (검증/문서 동기화)
- **선행 조건:** 수행하기로 한 모든 step이 완료(또는 반려 확정)된 후

## 목적

개별 step 검증을 통과했더라도, step들이 **서로** 만든 표면을 어긋나게 했을 수 있다. 전체를 한 번에 재검증하고, 변경 폭에 맞게 maintainer 문서를 동기화한 뒤, 최종 보고서를 남긴다.

## 절차

### 1. 전체 기계 검증

```bash
# 저장소 루트에서
python3 -m unittest discover -s .agents/skills/sandbox-e2e-test/tests -p 'test_*.py'

jq empty .claude-plugin/plugin.json .claude-plugin/marketplace.json
jq empty .codex-plugin/plugin.json .agents/plugins/marketplace.json
jq empty hooks/hooks.json hooks/hooks-codex.json
CLAUDE_PLUGIN_ROOT="$PWD" bash hooks/run-hook.cmd session-start \
  | jq '{event: .hookSpecificOutput.hookEventName, hasUsingSkill: (.hookSpecificOutput.additionalContext | contains("using-as-usual"))}'

# runtime 표면에 draft/maintainer 유출 없는지
git ls-tree -r --name-only HEAD | rg '^(commands/|skills/as-usual-(interview|execute|test)/)' || true
```

### 2. aggregate 의미 검증

`.agents/skills/verify-implementation/SKILL.md` 절차를 따라 등록된 검증 skill을 순차 수행:

- `verify-runtime-surface` — 이번 라운드에서 runtime 표면에 maintainer 규칙이 새지 않았는지 (특히 step-02의 placeholder 정의, step-09 문서화가 올바른 쪽에 들어갔는지)
- `verify-as-usual-harness` — 워크플로우/hook/manifest smoke
- `verify-runtime-workflow-consistency` — step-04/05/06/07/08이 만든 core ↔ skill ↔ template ↔ reviewer prompt 정합
- `verify-project-identity` — step-06(워크플로우 변경) 등 넓은 변경의 정체성/문서 반영

### 3. maintainer 문서 동기화

각 step이 바꾼 내용이 다음 문서의 서술과 어긋나지 않는지 확인하고 갱신한다:

| 문서 | 확인 포인트 |
| --- | --- |
| `CLAUDE.md` / `AGENTS.md` | RUNTIME WORKFLOW MODEL(특히 finalize/상태 목록 — step-06), CONVENTIONS(clarification 문구 — step-04), HOOK ACTIVATION MODEL(step-03/09), COMMANDS의 smoke 필터가 여전히 유효한지. 두 문서는 유사 내용이므로 함께 정합. |
| `docs/ARCHITECTURE-WORKFLOW.md` | phase/상태/전이 서술 (step-04/06), 템플릿 섹션 목록 (step-01의 report 개명, step-07) |
| `PROJECT_IDENTITY.md` | 원칙 문장과의 충돌 여부만 확인. **이 파일은 최종 기준이므로 개선 결과에 맞춰 고치는 대상이 아니다** — 충돌이 보이면 해당 step을 재검토하고 사용자에게 보고. |
| `docs/improvement-260704/hand-off/*` | 갱신하지 않는다 (스냅샷 기록물). |

maintainer skill(`.agents/skills/`)을 이번 라운드에서 수정한 경우에만: `skill-registry-sync` 절차로 `.claude/skills/` 미러 동기화. (계획된 step들은 maintainer skill을 수정하지 않는다 — 수정했다면 그 사유부터 보고.)

### 4. 최종 보고서 작성

`docs/improvement-260704/working-dir/99-FINAL-REPORT.md`에 기록:

- step별 수행 결과: 적용 / 반려 / 보류 + 커밋 SHA (커밋한 경우)
- 각 F-ID의 해소 여부
- 검증 결과 전체 (실패했던 것과 그 해결 포함 — 숨기지 마라)
- 제안했으나 반려된 항목과 사유
- 후속 과제 (01-DIAGNOSIS.md "제외한 항목" 재평가 포함: subagent 이중 리뷰 부담, topic-log.py 분할 등)

### 5. git 처리

커밋/푸시는 사용자 요청·승인 시에만. 스테이징은 경로 명시. step 단위 커밋 경계가 유지되었는지 확인.

## 완료 기준 (DoD)

- [ ] 1-2의 모든 검증 통과 (실패 시 완료 선언 금지, 원인과 함께 보고).
- [ ] 3의 문서 동기화 완료 또는 "갱신 불필요" 판정 근거 기록.
- [ ] 99-FINAL-REPORT.md 작성 완료.
