# Find-Cause Workflow Design

## Purpose

이 설계는 AsUsual에 두 번째 워크플로우 포맷인 `find-cause`를 추가한다.

기존 `core-workflow.md`는 하나의 코딩 topic을 requirements → plan → execute →
review로 이끄는 구현 중심 워크플로우다. 그러나 실무에서는 구현 못지않게 "문제가
정확히 무엇인지 파악하고 확정하는 과정"에 시간이 든다. `find-cause`는 이 과정을
전담한다:

- 버그가 발생했을 때 가설을 세우고 재현하여 **원인을 확정**한다.
- 개선 작업에서 여러 방식을 검토하여 **해결·개선 방향을 확정**한다.
- 그 과정에서 나온 발견, 결정, 가설, 번복을 append-only 장부로 남겨
  최종 완료 시 **사고의 과정을 재구성**할 수 있게 한다.

`find-cause`는 코드를 수정하지 않는다. 확정된 결론(`conclusion.md`)이 후속
coding topic의 입력이 되는 것으로 역할이 끝난다. 즉 이 워크플로우는 기존
워크플로우와 단계가 겹치지 않으며, 기존 워크플로우의 상류(시작 이전) 단계다.

```text
[find-cause / issue]  문제 인터뷰 → 조사 루프(장부 기록) → 결론 확정 ──┐
                                                                      ↓ 사용자 승인 시
[coding / topic]      requirements → plan → execute → review → finalize
```

## Design Goals

- 세션이 끊겨도 `problem.md` + `journal.jsonl`만 읽으면 조사 맥락이 복원되는
  파일 기반 컨텍스트를 제공한다.
- 확정했던 항목이 틀린 것으로 판명나면 지우지 않고 번복 이벤트를 append하여
  상태(추가됨/확정됨/취소됨)를 파생 관리한다.
- 조사 진행은 phase 파이프라인이 아니라 대화 루프로 본다. 기록 규율만 강제하고
  조사 방식 자체는 러프하게 둔다.
- 문제 정의와 조사 중 막히는 지점(도메인 지식 공백, 가설 충돌)은 grilling
  스타일 user-interview로 해소한다: 한 번에 하나씩, 각 질문에 추천 답을 붙여서.
- 두 워크플로우를 평행한 수직 구조로 유지한다: 폴더(`topic/` vs `issue/`),
  규칙 파일(`core-workflow.md` vs `find-cause-workflow.md`), 헬퍼 스크립트
  (`topic-log.py` vs `journal-log.py`)가 각각 분리되어 서로를 오염시키지 않는다.

## Non-Goals

- 코드 수정은 다루지 않는다. 프로덕션 코드 수정 요구가 나오면 후속 coding
  topic으로 넘긴다.
- 여러 topic/issue를 아우르는 장기 과제(initiative/epic) 우산 개념은 이번
  스코프가 아니다. 별도 설계로 미룬다.
- `core-workflow.md`와 `scripts/topic-log.py`는 변경하지 않는다.
- coding 워크플로우의 phase/route/이벤트 어휘에 find-cause 개념을 추가하지
  않는다 (kind 필드 없음).
- requirements/plan 스타일의 고정 섹션 템플릿과 리뷰어 프롬프트를 이 워크플로우에
  도입하지 않는다. 검증 대상 문서가 아니라 사고의 궤적이 산출물이기 때문이다.

## 평행 구조: topic과 issue

find-cause는 topic의 변형이 아니라 **별도 작업 단위 `issue`** 다.
`.as-usual/`은 세 갈래가 된다.

```text
<target-project>/
└── .as-usual/
    ├── topic/     # coding 워크플로우 (기존, 변경 없음)
    ├── issue/     # find-cause 워크플로우 (신규)
    │   └── yyyy-MM-dd-<slug>/
    │       ├── problem.md       # 살아있는 현재 스냅샷 (resume 문서 겸함)
    │       ├── journal.jsonl    # append-only 장부 (canonical, 단일 로그)
    │       ├── evidence/        # 선택. 로그 발췌, 실행 결과 등 조사 증거
    │       └── conclusion.md    # 종결 산출물
    └── memory/    # 공유 (기존)
```

| 구분 | coding | find-cause |
| --- | --- | --- |
| 작업 단위 폴더 | `.as-usual/topic/yyyy-MM-dd-<slug>/` | `.as-usual/issue/yyyy-MM-dd-<slug>/` |
| canonical 규칙 | `as-usual-rules/core-workflow.md` | `as-usual-rules/find-cause-workflow.md` (신규) |
| 헬퍼 스크립트 | `scripts/topic-log.py` | `scripts/journal-log.py` (신규) |
| 기록 파일 | `topic.md` + `audit.jsonl` (+ 산출물) | `problem.md` + `journal.jsonl` (+ `conclusion.md`) |
| 종착점 | 구현 완료 + 리뷰 + finalize + git action | 확정된 `conclusion.md` (git action 없음) |

issue에는 `topic.md`와 `audit.jsonl`을 두지 않는다. resume 스냅샷 역할은
`problem.md`가, 이벤트 이력 역할은 `journal.jsonl`이 겸한다. find-cause의
워크플로우 이벤트는 몇 개 되지 않으므로(생성, 재현 코드 승인, 종결, 후속 링크)
journal의 `lifecycle`/`approval` kind로 흡수하여 **issue당 로그 파일을 하나로**
유지한다.

새 규칙 파일은 반드시 `as-usual-rules/` 아래에 둔다. 공유 원칙(trust boundary,
secret 금지, 헬퍼 스크립트 전용 갱신)은 `find-cause-workflow.md`가
core-workflow의 해당 절을 중복 서술 없이 짧게 참조한다.

## Runtime Model: 대화 루프 + Append-Only 장부

find-cause에는 phase 파이프라인이 없다. issue 상태는 세 개뿐이며 journal의
`lifecycle` 이벤트에서 파생한다.

```text
open (조사 중) → concluded (종결)
              → cancelled (포기)
```

문제 정의, 가설 수립, 재현, 번복, 재정의는 모두 상태 전환이 아니라 journal
엔트리다. 조사 순서, 질문 개수, 가설 개수, 엔트리 길이는 강제하지 않는다.

### journal.jsonl

append-only 장부. 한 줄이 하나의 이벤트이며, 추론 내용과 워크플로우 생명주기를
모두 담는 issue의 단일 로그다.

```jsonl
{"seq":1,"ts":"2026-07-12T09:00:00+09:00","actor":"claude","kind":"lifecycle","status":"added","content":"issue 생성: 주문 API 간헐적 타임아웃","initialRequest":"..."}
{"seq":12,"ts":"2026-07-12T10:21:00+09:00","actor":"claude","kind":"hypothesis","status":"added","content":"커넥션 풀 고갈이 원인","evidence":null}
{"seq":15,"ts":"2026-07-12T11:02:00+09:00","actor":"claude","kind":"status-change","status":"confirmed","target":12,"evidence":"부하 테스트에서 재현, journal #14"}
{"seq":18,"ts":"2026-07-12T14:30:00+09:00","actor":"claude","kind":"finding","status":"added","content":"실측 로그 확인 결과 풀은 여유 있었음. 원인은 DNS 캐시 만료","evidence":"evidence/app-0712.log 발췌"}
{"seq":19,"ts":"2026-07-12T14:31:00+09:00","actor":"claude","kind":"status-change","status":"cancelled","target":12,"reason":"#18과 상충 — 실측 로그가 반증"}
```

필드와 어휘:

- `seq`: 단조 증가 정수. 파일 내 유일.
- `ts`, `actor`: 시각과 행위자 (`claude | codex | user`).
- `kind`: `finding | decision | hypothesis | interview | status-change |
  approval | lifecycle`
  - `finding`/`decision`/`hypothesis`/`interview`: 추론 엔트리.
  - `approval`: 재현 코드 승인, high-risk 승인 등 사용자 승인 기록.
  - `lifecycle`: issue 생성, 종결, 취소, 후속 topic 링크.
- `status`: `added`(추가됨) `| confirmed`(확정됨) `| cancelled`(취소됨)
- 신규 엔트리는 `status: added`로 시작한다. `confirmed`/`cancelled` 전이는 항상
  `kind: status-change` 이벤트로 append하며 `target`이 필수다.
- `target`: `status-change`가 가리키는 기존 엔트리 `seq`.
- `content` / `evidence` / `reason`: 자유 산문. 형식을 강제하지 않는다.

Append-only 원칙: 기존 줄은 절대 수정·삭제하지 않는다. 확정했던 항목이 틀린
것으로 판명나면 `status-change` + `cancelled` 이벤트를 append하고, 현재 상태는
이벤트 재생으로 파생한다. 이렇게 하면 "언제, 왜 뒤집었는지"가 보존되어 최종
완료 시 사고의 과정을 그대로 재구성할 수 있다. 기각된 가설도 별도 상태 없이
`cancelled` + `reason`으로 통일한다.

### 전용 헬퍼 스크립트: journal-log.py

journal과 issue 생명주기 전체를 `scripts/journal-log.py`(신규)가 관리한다.
`topic-log.py`와 코드를 섞지 않는다.

| 커맨드 | 역할 |
| --- | --- |
| `init --issue-dir <dir> --initial-request <text>` | issue 폴더 + `problem.md` 뼈대 + journal 생성, `lifecycle` 첫 엔트리 기록 |
| `add --kind <finding\|decision\|hypothesis\|interview> --content <text> [--evidence <text>]` | 추론 엔트리 추가 (`added`) |
| `confirm --target <seq> [--evidence <text>]` | 확정 이벤트 append |
| `cancel --target <seq> --reason <text>` | 취소 이벤트 append |
| `approve --content <text>` | 사용자 승인 기록 (`approval`) |
| `conclude --summary <text> [--follow-up <topic-dir>]` | 종결/후속 링크 `lifecycle` 이벤트 append |
| `status [--json]` | issue 상태(`open\|concluded\|cancelled`)와 활성/확정/취소 엔트리 파생 |
| `view [--json\|--md]` | 장부 렌더링 (md 렌더는 conclusion.md 작성과 최종 회고 때 사용) |
| `validate` | seq 유일성, target 존재, 어휘 검증 |

`topic.md`/`audit.jsonl`과 동일한 원칙으로 journal도 손편집을 금지하고
스크립트로만 기록한다. 스크립트가 표현하지 못하는 갱신이 필요하면 멈추고 누락
기능을 보고한다. 구현은 `scripts/as_usual_topic_log/`처럼 테스트 가능한 패키지
구조를 따른다.

### problem.md

살아있는 현재 스냅샷이자 issue의 resume 문서. 갱신이 자유롭다 (동결·리뷰
게이트 없음).

- 현재의 문제 이해: 증상, 영향, 재현 조건, 문제 경계
- 사용자에게 들은 배경/도메인 지식 (user-interview 전사)
- 현재 유효한 가설 목록 (journal seq 참조)

새 세션은 journal 전체를 재생하지 않고 `problem.md`만 읽으면 현재 지점에 설 수
있다. material한 이해 변경(문제 경계가 바뀌는 수준)은 journal에도 `decision`
또는 `finding` 엔트리로 남긴다.

### conclusion.md

종결 시에만 작성하는 최종 산출물.

- 확정된 원인 **또는** 확정된 해결·개선 방향
- 근거 증거 요약 (journal seq 인용)
- 재현 방법 (재현했다면)
- 권장 검증/테스트 계획 (후속 coding topic의 입력)
- 후속 topic 링크 (생성했다면)

## User-Interview 메커니즘

조사 전 과정에서 발동 가능한 공통 메커니즘이다. grilling 스타일을 따른다:
**한 번에 하나씩** 묻고, 각 질문에 에이전트의 추천 답(또는 현재 증거 기준 우세
가설)을 붙인다. 코드베이스·로그에서 직접 확인 가능한 사실은 사용자에게 묻지
않는다.

발동 조건:

1. **진입 시 문제 인터뷰**: 증상, 영향, 재현 조건, 문제 경계를 파악해
   `problem.md` 초안을 만든다.
2. **도메인 지식 공백**: 코드·로그로 알 수 없는 배경 지식이 필요할 때
   (예: "이 배치가 새벽에만 도는 게 의도인가요?").
3. **가설 충돌**: 두 가설이 모두 그럴듯하거나 증거가 사용자의 기존 믿음과
   모순될 때, 현재까지의 증거를 요약해 보여주고 사용자의 판단을 묻는다.

기록 방식:

| 답변 종류 | 기록 위치 |
| --- | --- |
| 도메인/배경 지식 | `problem.md` Background Knowledge + journal `interview` 엔트리 |
| 가설 충돌 판단 | journal `decision` 엔트리 (해당 가설 seq 참조) |
| issue를 넘어 유용한 지식 | 종결 시 `manage-self-improvement`가 `.as-usual/memory/` 후보로 제안 |

coding 워크플로우의 file-backed `question-cN.md` 사이클은 이 워크플로우에서
사용하지 않는다. 빠른 왕복이 본질이고, durable record는 journal과 problem.md가
담당한다.

## Hard Gates

이 워크플로우의 하드 게이트는 다음뿐이다. 나머지는 전부 가이드다.

1. **journal append-only**: 기존 엔트리 수정·삭제 금지. 번복은 `cancelled`
   이벤트 append.
2. **증거 없는 확정 금지**: 재현 증거 또는 명시적 "재현 불가 사유 + 정황 근거"
   없이 엔트리를 `confirmed`로 올리거나 issue를 `concluded`로 전환할 수 없다.
3. **재현 코드 승인 게이트**: 기본은 읽기 전용(코드 읽기, 실행, 로그 분석).
   재현용 테스트/스크립트 작성은 사용자가 명시 요청·승인할 때만 하고 journal
   `approval` 엔트리로 기록한다. 프로덕션 코드 수정은 항상 금지 — coding
   워크플로우 게이트의 우회로가 되지 않는다.
4. **high-risk 게이트 상속**: 프로덕션 환경 조회·실행 등은 core-workflow의
   High-Risk Operation Gate와 동일한 fresh approval을 요구하고 journal
   `approval` 엔트리로 기록한다.
5. **턴 종료 전 기록**: 턴을 끝내기 전에 이번 턴의 의미있는 발견·결정·번복을
   journal에 기록한다.

## 종결과 후속 연결

가설(또는 해결 방향)이 confirmed에 도달하면 별도 스킬 전환 없이 **같은 턴에서**
종결을 진행한다:

1. 증거 체크 (게이트 2) 후 `conclusion.md` 작성과 셀프 리뷰
2. 재현 코드가 있으면 처분 결정: 삭제 / 후속 topic의 회귀 테스트 씨앗으로 유지
3. `journal-log.py conclude`로 종결 기록 (`open` → `concluded`)
4. **"후속 coding topic을 만들까요?"** 제안. 승인 시 기존 `topic-log.py init`으로
   새 coding topic을 만들고, `conclusion.md` 경로를 source input으로 topic 쪽
   `topic.md`/`audit.jsonl`에, topic 경로를 journal `lifecycle` 엔트리에 상호
   링크한다. 후속 topic의 requirements는 conclusion을 provenance로 인용한다.

issue는 커밋할 것이 없으므로 git-action 질문은 하지 않는다 (재현 코드를
남기기로 하면 후속 coding topic에서 처리). 원인만 확인하고 후속 없이 종료하는
것도 정상 경로다. 사용자가 조사를 포기하면 `conclude` 대신 취소 사유와 함께
`cancelled` lifecycle 이벤트로 닫는다.

## Skill Surface

신규 스킬은 **`find-cause` 1개**다. 짧은 원칙 목록 + 하드 게이트로 쓰고,
절차서로 만들지 않는다. 소유 범위:

1. issue 생성(`journal-log.py init`)과 진입 문제 인터뷰 → `problem.md` 초안
2. 조사 루프: journal 기록 규율, user-interview 발동
3. 하드 게이트 5개 집행
4. 종결: conclusion → 처분 → conclude → 후속 topic 제안

기존 스킬 소폭 수정 2건:

| 스킬 | 수정 내용 |
| --- | --- |
| `using-as-usual` | 활성화 분기 한 단락: 요청이 "조사/원인 파악/방식 확정" 성격이면 topic 대신 issue + `find-cause` 스킬로 라우팅. `.as-usual/issue/` 언급도 활성화 신호에 추가 |
| `hand-off` | `.as-usual/issue/` 경로 인지 한 단락: issue면 `problem.md` → `journal-log.py status` 순으로 first reads 후 `find-cause`로 라우팅 |

coding 워크플로우의 나머지 스킬·템플릿·리뷰어 프롬프트, `core-workflow.md`,
`topic-log.py`는 수정하지 않는다.

## Implementation Change Map

| 대상 | 변경 |
| --- | --- |
| `as-usual-rules/find-cause-workflow.md` | 신규. find-cause의 canonical 규칙 |
| `skills/find-cause/SKILL.md` | 신규 스킬 1개 |
| `templates/problem.md`, `templates/conclusion.md` | 신규 템플릿 2개 (최소 뼈대만; journal은 스크립트가 생성하므로 템플릿 불필요) |
| `scripts/journal-log.py` (+ 패키지, 테스트) | 신규 전용 헬퍼. issue 생명주기 전체 담당 |
| `skills/using-as-usual/SKILL.md`, `skills/hand-off/SKILL.md` | issue 인지 소폭 수정 |
| `hooks/session-start` | 규칙 소스 안내에 `find-cause-workflow.md` 경로와 active issue 후보 추가 |
| `docs/ARCHITECTURE-WORKFLOW.md` | find-cause 워크플로우 섹션 추가 |

`core-workflow.md`, `topic-log.py`, coding 스킬/템플릿: **변경 없음.**

## Decision Log

이 설계에서 사용자가 확정한 결정. (#2는 이후 번복 — 이 워크플로우가 다루려는
"확정 후 번복"의 실례이므로 지우지 않고 남긴다.)

1. 1차 타겟: 문제를 정확히 인지·확정하는 것까지가 스코프인 범용 포맷 하나
   (코드 수정 제외, 버그 원인 + 개선 방향 모두 커버).
2. ~~저장 구조: `.as-usual/topic/` 재사용 + workflow kind 필드.~~
   **#10으로 번복.** 당시 근거였던 "topic 인프라 재사용"이 #3(phase 없음)과
   #9(전용 스크립트)로 사라졌기 때문.
3. phase 파이프라인 없음: 대화 루프 + 확정 장부 모델. 문제 정의는 별도 단계가
   아니라 루프의 첫 대화.
4. 문제 정의·조사 중 상호작용은 grilling식 채팅 1문1답 + 파일 전사.
   도메인 지식 공백과 가설 충돌 시 user-interview 발동.
5. 기본 읽기 전용, 재현 코드는 사용자 명시 요청 시만 (journal 기록).
6. 종결 후 느슨한 연결 + 후속 coding topic 생성 제안.
7. 이름: `find-cause`, 규칙 `as-usual-rules/find-cause-workflow.md`.
8. 장부는 md가 아닌 jsonl. 상태 어휘 `added | confirmed | cancelled`.
   상태 변경은 in-place 수정이 아니라 append 이벤트로, 현재 상태는 파생.
9. journal 헬퍼는 `topic-log.py`가 아닌 전용 스크립트(`journal-log.py`)로 분리.
10. 작업 단위를 topic이 아닌 **issue**로 분리: `.as-usual/issue/` 아래에서
    작업하고, `core-workflow.md`/`topic-log.py`는 변경하지 않는다.
11. issue에는 `topic.md`/`audit.jsonl`을 두지 않고 journal.jsonl 하나로 통일
    (`lifecycle`/`approval` kind로 워크플로우 이벤트 흡수).
