# Step 03. 활성화 신호 정합 (F7)

- **축:** ② 워크플로우 (정합 수정 — 이미 hook/skill/CLAUDE.md가 합의한 신호를 canonical contract에 반영)
- **규모:** Medium — 신규 게이트 추가가 아니라 표면 간 불일치 해소이므로 제안서 불필요. 단, 변경 후 사용자에게 보고한다.
- **대상 finding:** F7
- **선행 조건:** step-01 완료

## 문제

"feature-development work that should use the AsUsual workflow"가 활성화 신호로:

- `hooks/session-start:10` ✅ 있음
- `skills/using-as-usual/SKILL.md:28-33` ✅ 있음 (4번째 신호)
- `CLAUDE.md` HOOK ACTIVATION MODEL ✅ 있음 (신호 4)
- `as-usual-rules/core-workflow.md:97-104` §1 Activation Signals 표 ❌ **없음** (신호 3개만)

canonical contract가 나머지 표면보다 좁다. core-workflow만 읽은 agent는 feature-development 요청에서 AsUsual을 활성화하지 못한다.

## 변경 명세

**파일:** `as-usual-rules/core-workflow.md` §1 Activation Signals 표

표의 3번째 행("resume" 신호)과 4번째 행("Ordinary coding...") 사이에 다음 행을 추가한다:

```markdown
| The user asks for feature-development work that should use the AsUsual workflow | AsUsual active | Use this workflow. |
```

**문구 정합 주의:** `skills/using-as-usual/SKILL.md`와 hook의 표현("feature-development work that should use the AsUsual workflow")을 **그대로** 사용해 세 표면의 문구를 일치시킨다. 새 표현을 발명하지 마라.

**같이 검토(변경 아님):** §1의 Activation Decision Procedure(:108-113)는 "IF user gives any activation signal: activate"이므로 표에 행이 추가되면 자동으로 커버된다 — 수정 불필요, 확인만.

## 경계 주의 (게이트 확장 오해 방지)

이 신호는 "모든 코딩 요청을 AsUsual로 강제"가 아니다. 다음 반대 신호들이 유지되는지 확인하라:

- §1 표의 마지막 행: "Ordinary coding or question request with no AsUsual signal → Not active → Do not force AsUsual." — 유지.
- §15 Anti-Patterns 첫 항목: "Forcing AsUsual onto unrelated work only because hook injection happened." — 유지.
- `skills/using-as-usual/SKILL.md:8`: "Do not force AsUsual onto every request just because the hook announced..." — 유지.

## 함께 갱신할 파일

- `as-usual-rules/core-workflow.md` §1 (유일한 실변경)
- `hooks/session-start`, `skills/using-as-usual/SKILL.md`, `CLAUDE.md`, `AGENTS.md` — 변경 없음, 문구 일치 확인만. (`AGENTS.md`에 HOOK ACTIVATION MODEL 상당 섹션이 있으면 신호 4개인지 확인.)

## 검증

```bash
# 세 표면의 신호 문구 일치 확인
grep -n "feature-development work" as-usual-rules/core-workflow.md skills/using-as-usual/SKILL.md hooks/session-start CLAUDE.md

CLAUDE_PLUGIN_ROOT="$PWD" bash hooks/run-hook.cmd session-start | jq .
python3 -m unittest discover -s .agents/skills/sandbox-e2e-test/tests -p 'test_*.py'
# verify-runtime-workflow-consistency + verify-as-usual-harness 절차 수행
```

## 완료 기준 (DoD)

- [ ] core §1 표에 feature-development 신호 행이 추가되었고 문구가 skill/hook과 일치한다.
- [ ] "Do not force AsUsual" 계열 반대 신호가 모든 표면에서 유지된다.
- [ ] hook smoke + 유닛 테스트 통과.

## 롤백

`git checkout -- as-usual-rules/core-workflow.md`
