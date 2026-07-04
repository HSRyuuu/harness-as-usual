# Step 02. `topic-log.py` 경로 표기 통일 (F6)

- **축:** ④ 프롬프트 (동작 보존)
- **규모:** Medium — 기계적 수정이므로 제안서 불필요. 단, canonical 표기 선택은 아래 결정 규칙을 따른다.
- **대상 finding:** F6
- **선행 조건:** step-01 완료

## 문제

runtime skill들의 명령 예시가 3가지 표기를 혼용한다 (2026-07-04 grep 기준):

```
 2 python3 <as-usual-plugin-root>/scripts/topic-log.py   # core-workflow.md §13 (:483), using-as-usual/SKILL.md (:80)
 3 python3 <plugin-root>/scripts/topic-log.py            # 각 skill의 record-memory-candidate 예시
21 python3 scripts/topic-log.py                          # 대다수 skill 예시
```

추가로 실행 명령이 아닌 경로에도 옛 placeholder가 1곳 있다: `skills/manage-self-improvement/SKILL.md:51`의 `<as-usual-plugin-root>/templates/MEMORY.md`. (2026-07-04 최종 검토에서 확인 — 수치는 실행 시점에 재확인하라.)

AsUsual은 **target project에서 실행**되므로 target project 루트에 `scripts/topic-log.py`가 없다. bare 표기 21곳은 agent가 그대로 복사 실행하면 실패하는 잘못된 지시다.

## Canonical 표기 결정

**`<plugin-root>`를 canonical placeholder로 통일한다.** 이유:

- 가장 짧고, 이미 3곳에서 사용 중이며, 의미가 자명하다.
- `<as-usual-plugin-root>`는 1곳뿐이고 장황하다.

core-workflow.md에 placeholder 정의를 **한 곳**만 둔다. §13 Topic Log Rules의 명령 블록(:481-484)을 다음처럼 바꾼다:

```markdown
For topic and audit updates, use the audit-first helper. `<plugin-root>` is the installed AsUsual plugin root (the directory containing `scripts/` and `skills/`); resolve it from the SessionStart hook announcement or the parent directory of the running skill:

```bash
python3 <plugin-root>/scripts/topic-log.py ...
```
```

> 참고: `skills/using-as-usual/SKILL.md:39`에 이미 유사한 해석 규칙("resolve it from the AsUsual plugin root, which is the parent directory of the `skills/` directory containing this skill")이 core-workflow.md 경로에 대해 존재한다. 표현을 그 문장과 어긋나지 않게 맞춰라.

## 작업 절차

1. 전체 발생 위치 나열:

```bash
grep -rn "topic-log.py" as-usual-rules/ skills/ templates/ | grep -v "<plugin-root>"
```

2. 다음 규칙으로 치환한다:
   - ` python3 scripts/topic-log.py` → ` python3 <plugin-root>/scripts/topic-log.py` (명령 예시 코드 블록)
   - `python3 <as-usual-plugin-root>/scripts/topic-log.py` → `python3 <plugin-root>/scripts/topic-log.py`
   - `<as-usual-plugin-root>`의 **비명령 경로 사용도 전부** `<plugin-root>`로 통일한다 (예: `skills/manage-self-improvement/SKILL.md:51`의 `<as-usual-plugin-root>/templates/MEMORY.md`). 그래야 아래 잔존 검증 grep이 통과한다. 전수 확인: `grep -rn "as-usual-plugin-root" as-usual-rules/ skills/ templates/`
   - **예외:** 산문 속에서 도구를 지칭하는 `scripts/topic-log.py` 언급(예: "through `scripts/topic-log.py`", "`scripts/topic-log.py status --json`으로 파생")은 파일 식별자이지 실행 명령이 아니므로 **그대로 둔다**. 치환 대상은 `python3 `가 붙은 실행 예시와, 사용자가 복사-실행할 것으로 기대되는 코드 블록만이다.
   - 템플릿 front matter의 `statusCommand: "scripts/topic-log.py status --json"` (`templates/plan.md:6`, `templates/code-review-report.md:5`)은 machine-readable 값이므로 **바꾸지 않는다**. 바꾸려면 이 값을 읽는 코드가 있는지 먼저 확인해야 한다: `grep -n "statusCommand" scripts/topic-log.py .agents/skills/sandbox-e2e-test/tests/*.py`
3. 각 파일 수정 후 diff를 열어 코드 블록 이외의 위치가 바뀌지 않았는지 확인한다.

## 함께 갱신할 파일

- `as-usual-rules/core-workflow.md` (placeholder 정의 1곳 + 실행 예시)
- `skills/*/SKILL.md` 전부 (명령 예시)
- maintainer 문서(`CLAUDE.md`, `AGENTS.md`, `docs/ARCHITECTURE-WORKFLOW.md`)의 runtime 명령 예시는 **저장소 루트에서 실행하는 개발용 예시**이므로 bare 경로가 정당하다 — 바꾸지 마라. (runtime 지시와 maintainer 명령의 컨텍스트 차이에 주의.)

## 검증

```bash
# 잔존 bare 실행 예시가 없는지 (runtime 표면 한정)
grep -rn "python3 scripts/topic-log.py" as-usual-rules/ skills/ templates/   # 기대: 없음
grep -rn "as-usual-plugin-root" as-usual-rules/ skills/                      # 기대: 없음(또는 정의 문장 내 의도적 사용만)

python3 -m unittest discover -s .agents/skills/sandbox-e2e-test/tests -p 'test_*.py'
# verify-runtime-workflow-consistency 절차 수행
```

## 완료 기준 (DoD)

- [ ] runtime 표면의 실행 예시가 전부 `<plugin-root>/scripts/topic-log.py` 표기다.
- [ ] placeholder 해석 규칙이 core-workflow.md 한 곳에 정의되어 있다.
- [ ] 산문 속 파일 지칭과 템플릿 front matter 값은 변경되지 않았다.
- [ ] 유닛 테스트 전체 통과.

## 롤백

`git checkout -- as-usual-rules/ skills/`
