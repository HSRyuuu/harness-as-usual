<!--
AsUsual long-term memory. Project-scoped, curated, size-bounded.
RULES:
- budget: 3000 characters total for this file.
- NOT append-only. On every update, prefer simplify / consolidate / dedup.
- Store form == inject form: compact, durable, reusable knowledge only.
- Do NOT store: one-off logs, dated incidents, conversation history, unverified guesses.
- When this file would exceed budget even after consolidation, split a dominant
  domain into <domain>_MEMORY.md and add an index line under "Domain Memory Index".
-->

# Project Memory

## User Preferences

<!-- durable user preferences (style, review format, communication) -->

## Project Knowledge

- **탐색 서브에이전트의 부정 주장은 제거의 근거가 될 수 없다.** "X는 어디서도 쓰이지
  않는다" 류의 주장을 받으면, 지우기 전에 실제 호출 형태로 직접 재확인한다 —
  `--kind X`, `--phase X`처럼 문서에 등장하는 형태 그대로. 인용 없는 부정은 검색이
  좁았다는 뜻일 뿐이다.
- **어휘·규칙을 제거한 뒤에는 런타임 표면 전체를 스윕한다.** `as-usual-rules/`,
  `skills/`, `templates/`, `scripts/`를 한 번에 grep해 잔존 사용처를 찾는다. 제거가
  스킬의 명령을 깨뜨리는 것이 이 저장소에서 가장 흔한 자해다.
- **스텝 스킬의 유닛 분기는 고칠 때도 늘어난다.** 공유 스텝 스킬을 수정할 때는
  "topic은 …, issue는 …" 형태로 쓰고 싶어지는데, 같은 조건을 파일·아티팩트 존재
  여부로 다시 쓸 수 있는지 먼저 확인한다. 그쪽이 유닛 불가지성을 지킨다.
- **호스트 설정값은 추측 대신 확인한다.** 훅 matcher처럼 호스트가 정의하는 어휘는
  `claude-code-guide`로 공식 문서를 확인하면 즉시 판정된다. "비대칭에 근거를 단다"가
  아니라 "실제 결함이었다"로 결론이 뒤집힐 수 있다.

## Domain Memory Index

<!-- one line per split file, e.g.: BACKEND_MEMORY.md — backend review criteria -->
