# AsUsual 개선 작업 Hand-off 패키지

이 폴더는 **Fable에게 AsUsual harness 개선 작업을 맡기기 위한 hand-off 문서 묶음**이다.
목적은 Fable이 저장소를 처음부터 탐색하며 토큰을 낭비하지 않고, 이 문서들만 읽고도
어디를 어떻게 고쳐야 하는지 판단할 수 있게 하는 것이다.

## Fable을 위한 읽기 순서

작업 종류와 무관하게 **아래 순서로 읽으면 탐색 없이 바로 작업에 들어갈 수 있다.**

| 순서 | 문서 | 언제 필요한가 | 대략 비용 |
| --- | --- | --- | --- |
| 1 | `00-ORIENTATION.md` | 항상. AsUsual이 무엇이고 파일이 어디 있는지 한 번에 파악 | 필수 1회 |
| 2 | `01-IMPROVEMENT-PLAN.md` | 항상. 4개 개선 축과 각 축의 작업 프로토콜 | 필수 1회 |
| 3 | `02-FILE-STRUCTURE.md` | 특정 파일을 고칠 때. "무엇을 건드리고 무엇을 건드리면 안 되는가" | 참조용 |

세 문서를 읽은 뒤에는 **실제 원본 파일을 직접 열어 확인**하고 고친다.
이 hand-off는 지도일 뿐 source of truth가 아니다. 최종 진실은 항상 디스크의 실제 파일이다.

## 이 저장소의 성격 (반드시 먼저 이해)

- 이 저장소는 **AsUsual harness 그 자체를 개발하는 저장소**다(plugin development).
- 여기서의 작업은 **runtime workflow를 "사용"하는 것이 아니라 harness를 "개선"하는 것**이다.
- 따라서 `.as-usual/topic/...` 작업 단위 workflow를 강제로 돌리지 않는다.
  (사용자가 "이 개선 작업을 AsUsual topic으로 돌려라"라고 명시할 때만 예외.)
- 판단 기준: `.agents/skills/dev-as-usual/SKILL.md` 참고.

## Fable에게 주는 핵심 원칙 (요약)

1. **AsUsual은 안전 도구다.** prompt/gate/workflow는 "agent가 위험한 짓을 못 하게" 막는 장치다.
   개선한다고 gate를 약화시키면 프로젝트의 존재 이유를 무너뜨린다. `PROJECT_IDENTITY.md`가 최종 기준.
2. **큰 변경은 먼저 제안하고, 승인 뒤 반영한다.** 특히 `as-usual-rules/core-workflow.md`와
   runtime skill prompt는 파급이 크다. `docs/improvement-260704/proposals/`에 제안서를 먼저 쓴다.
3. **runtime 표면과 maintainer 표면을 섞지 않는다.** runtime 문서에 plugin 개발/설치 규칙을 넣지 않는다.
4. **변경 후 검증은 필수.** `01-IMPROVEMENT-PLAN.md`의 "검증 게이트"를 통과하지 않으면 완료라고 하지 않는다.
5. **maintainer skill은 2곳에 미러링되어 있다** (`.agents/skills/`와 `.claude/skills/`).
   한쪽만 고치면 동기화가 깨진다. `02-FILE-STRUCTURE.md`의 미러 규칙을 반드시 지킨다.

## 산출물 위치 규칙

| 산출물 | 위치 |
| --- | --- |
| 개선 제안서(승인 전) | `docs/improvement-260704/proposals/<yyyy-MM-dd>-<slug>.md` |
| 설계 문서 | `docs/design/<yyyy-MM-dd>-<slug>-design.md` (기존 관례) |
| 실제 코드/prompt 변경 | 해당 원본 파일 직접 수정 |
