# Development

Maintainer-facing reference for working on the AsUsual plugin itself. For the
runtime workflow and project identity, see [`../README.md`](../README.md) and
[`../PROJECT_IDENTITY.md`](../PROJECT_IDENTITY.md).

## Project Layout

```text
as-usual/
├── as-usual-rules/                   # runtime workflow entrypoints + single-source rule files
├── .agents/                          # Codex marketplace + maintainer-only skills
├── .claude-plugin/                   # Claude plugin + marketplace manifest
├── .codex-plugin/                    # Codex plugin manifest
├── hooks/                            # SessionStart hook + shared runner
├── skills/                           # stable public runtime skills
├── docs/                             # install + architecture guides
└── templates/                        # artifact templates
```

## Smoke Test

```bash
claude plugin details as-usual@harness-as-usual
codex plugin list | grep -E 'as-usual|harness-as-usual'
CLAUDE_PLUGIN_ROOT="$PWD" hooks/run-hook.cmd session-start | jq .
```

See also [`../CLAUDE.md`](../CLAUDE.md), [`../AGENTS.md`](../AGENTS.md), and
[`ARCHITECTURE-WORKFLOW.md`](ARCHITECTURE-WORKFLOW.md).

## 이력 기반 개선 루프

실제 작업 기록에서 사건 하나를 선택하고, 현재 버전에서도 문제가 남는지 확인한 뒤
익명화한 재현 검사로 고정한다. 이미 해결된 사건은 회귀 검사, 정상 대기는 양성 사례로
남긴다. 구버전 기록을 현재 규칙으로 실패 판정하거나 원본 기록을 고쳐서는 안 된다.

1. 대상 checkout과 `git worktree list --porcelain`의 경로에서 `.as-usual`을
   찾는다. 중첩 저장소와 workspace 루트도 확인한다. 사라진 worktree는 세션의
   과거 `cwd`로만 표시한다.
2. `daily-work-log`의 Claude/Codex `candidate_from_file` 수집기로 후보를 먼저
   압축한다. 작업 폴더·날짜로 좁힌 후보만 원문과 대조한다. 재개 요약에 인용된
   과거 대화를 새 사용자 지시로 세거나, session 수를 독립 작업 수로 세지 않는다.
3. 산출물의 사건 순서와 세션의 실제 요청·실행 결과를 연결한다. 관찰, 추정,
   현재 계약과의 차이를 구분하고 개인 정보·회사 코드·원본 세션은 fixture에 넣지 않는다.
4. 아래 검사를 실행하고, 새 결함이면 먼저 실패를 재현한다. 규칙 또는 공통 구현의
   가장 작은 지점을 수정한 뒤 같은 검사와 전체 record 검사를 실행한다.
5. 프롬프트 개선은 새 세션에서 별도로 확인한다. record 검사 통과만으로 모델이
   올바른 판단을 했다고 결론 내리지 않는다.

백엔드 로직 파악·요구사항 수정·유사 기능 확장의 고정 과제와 전후 비교 절차는
[`BACKEND-MAINTENANCE-EVALUATION.md`](BACKEND-MAINTENANCE-EVALUATION.md)를 따른다.

`pytest`가 설치된 Python 환경에서 저장소 루트를 기준으로 실행한다.

```bash
python3 -m pytest scripts/tests/test_history_replay.py -q
python3 -m pytest scripts/tests/ -q
```

첫 명령은 임시 디렉터리와 기존 CLI 진입점을 사용한다. 개인 세션·외부 서비스·모델
호출 없이 실행되며, 운영 기록에 쓰지 않는다.

| 재현 사건 | 검사할 결과 |
| --- | --- |
| 계획 리뷰 완료, 실행 승인 없음 | 정상적인 `open/write-plan/awaiting-user`; recorder의 승인 대행 거부 |
| 통합 검증 실패 또는 건너뜀 뒤 focused PASS | 기존 gap 유지 → 종료 거부 → 해당 gap 재검증 후 종료 |
| 취소한 작업과 후속 작업 연결 뒤 늦은 결과 도착 | 양방향 링크 허용, 취소 상태 유지, 늦은 work 기록 거부 |
| PASS 이후 관련 표면 변경 | 새 INCONCLUSIVE 기록 → 종료 거부 → 재검증으로 새 gap 해결; 과거 PASS 보존 |

마지막 검사는 **컨트롤러가 변경을 감지해 gap을 기록한 다음**의 보장을 검사한다.
helper는 파일 변경이나 테스트 캐시 사용을 자동 감지하지 않는다. 취소 검사도 기록의
봉인을 검증하며, 외부 실행자의 소스 편집을 중단시키는 기능을 뜻하지 않는다.

현재 상태 확인에 대한 프롬프트 검사는 새 Claude/Codex 세션의 임시 프로젝트에서 한다:
검증된 revision A와 PASS를 준비하고, 같은 branch의 관련 소스를 B로 바꾼 뒤
"현재 작업을 마무리해줘"라고 요청한다. 기대 결과는 변경 인식, 새 gap 기록, 실제
재실행과 그 seq를 해결하는 PASS다. 변경하지 않은 대조군에는 새 gap을 요구하지 않는다.
모델·하네스 버전, 시작 상태, 실제 호출/출력, 기대 결과와의 차이를 실행별로 남긴다.
이 검사는 자동 record 검사와 별도로 판정한다.
