# Find-Cause Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** AsUsual에 두 번째 워크플로우 포맷 `find-cause`(문제 원인/해결 방향 확정)를 추가한다 — `.as-usual/issue/` 작업 단위, append-only `journal.jsonl` 장부, 전용 헬퍼 `scripts/journal-log.py`, 규칙 `as-usual-rules/find-cause-workflow.md`, 스킬 `skills/find-cause/`.

**Architecture:** topic과 완전히 평행한 수직 구조. `core-workflow.md`와 `scripts/topic-log.py`는 한 줄도 수정하지 않는다. issue는 `problem.md`(살아있는 스냅샷) + `journal.jsonl`(단일 append-only 로그) + `conclusion.md`(종결 산출물)로 구성되고, 상태는 journal의 lifecycle 이벤트에서 파생한다.

**Tech Stack:** Python 3 표준 라이브러리만 (기존 `topic-log.py`와 동일), unittest + subprocess CLI 테스트, Markdown 프롬프트/템플릿.

**Spec:** `docs/design/2026-07-12-find-cause-workflow-design.md` (이 계획의 유일한 요구사항 원천)

## Global Constraints

- `core-workflow.md`, `scripts/topic-log.py`, coding 스킬/템플릿은 **변경 금지**.
- 새 규칙 파일은 반드시 `as-usual-rules/` 아래: `as-usual-rules/find-cause-workflow.md`.
- 공개 런타임 스킬은 `skills/find-cause/`에 둔다 (`.agents/skills/`는 개발용 — dev-as-usual 스킬의 Skill Placement 규칙).
- journal.jsonl은 append-only: 어떤 코드 경로도 기존 줄을 수정·삭제하지 않는다.
- 어휘 고정 — entry kind: `finding | decision | hypothesis | interview | status-change | approval | lifecycle`, entry status: `added | confirmed | cancelled`, lifecycle event: `created | concluded | cancelled | follow-up-linked`, actor: `claude | codex | user`, issue status: `open | concluded | cancelled`.
- `confirmed`/`cancelled` 전이는 항상 `kind: status-change` + `target` 필수. 신규 추론 엔트리는 `status: added`로 시작.
- 테스트는 `scripts/tests/`의 기존 unittest + subprocess 패턴을 따른다. 실행: `python3 -m unittest discover -s scripts/tests -v` (리포 루트에서).
- 프롬프트/템플릿 파일은 기존 runtime surface와 같이 영어로 쓴다 (runtime 산출물 언어는 규칙이 사용자 언어를 따르게 함).
- 커밋 메시지는 기존 스타일: `feat:`, `fix:`, `docs:` prefix.
- 리포 루트: `/Users/happyhsryu/dev/personal/harness-as-usual`. 모든 경로는 리포 루트 기준.

## File Structure

```text
scripts/
├── journal-log.py                      # 신규: 얇은 entrypoint (topic-log.py와 동형)
├── as_usual_journal_log/               # 신규 패키지
│   ├── __init__.py
│   ├── core.py                        # 어휘 상수, append/read/derive/validate
│   └── cli.py                         # argparse subcommands
└── tests/
    └── test_journal_log.py            # 신규: CLI 테스트
as-usual-rules/
└── find-cause-workflow.md              # 신규: canonical 규칙
skills/
├── find-cause/SKILL.md                 # 신규 스킬
├── using-as-usual/SKILL.md             # 수정: issue 활성화 분기
└── hand-off/SKILL.md                   # 수정: issue 경로 인지
templates/
├── problem.md                          # 신규
└── conclusion.md                       # 신규
hooks/session-start                     # 수정: find-cause 안내 한 문장
docs/ARCHITECTURE-WORKFLOW.md           # 수정: find-cause 섹션
```

Task 1–5가 스크립트(TDD), Task 6–11이 템플릿/프롬프트/문서(TDD 예외: configuration/documentation — 각 태스크에 명시된 검증 커맨드로 대체), Task 12가 최종 스윕이다.

---

### Task 1: journal-log 패키지 골격 + `init` 커맨드

**Files:**
- Create: `scripts/journal-log.py`
- Create: `scripts/as_usual_journal_log/__init__.py`
- Create: `scripts/as_usual_journal_log/core.py`
- Create: `scripts/as_usual_journal_log/cli.py`
- Test: `scripts/tests/test_journal_log.py`

**Interfaces:**
- Consumes: 없음 (독립 신규 패키지)
- Produces: CLI `python3 scripts/journal-log.py init --issue-dir <dir> --initial-request <text> --actor <claude|codex|user>` — issue 폴더, `journal.jsonl`(첫 lifecycle 엔트리), `problem.md` 생성. 이후 태스크는 `core.py`의 `read_entries(issue_dir) -> list[dict]`, `build_entry(entries, *, actor, kind, status, **fields) -> dict`, `append_entry(issue_dir, entry) -> dict`, `JournalError`, 어휘 상수(`KINDS`, `REASONING_KINDS`, `ENTRY_STATUSES`, `LIFECYCLE_EVENTS`, `ACTORS`)를 사용한다. 모든 커맨드는 성공 시 stdout에 한 줄 JSON receipt(`{"ok": true, "seq": N, ...}`)를 출력하고, 실패 시 stderr에 `error: <message>` 출력 후 exit code 1.

- [ ] **Step 1: 실패하는 테스트 작성**

`scripts/tests/test_journal_log.py` 생성 (기존 `test_topic_log_verdict.py`의 subprocess 패턴을 따른다):

```python
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
JOURNAL_LOG = ROOT / "scripts/journal-log.py"


class JournalLogTestBase(unittest.TestCase):
    def run_journal_log(self, *args):
        return subprocess.run(
            [sys.executable, str(JOURNAL_LOG), *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )

    def init_issue(self, tmp):
        issue_dir = Path(tmp) / "issue" / "2026-07-12-order-timeout"
        result = self.run_journal_log(
            "init",
            "--issue-dir",
            str(issue_dir),
            "--initial-request",
            "order API intermittent timeout",
            "--actor",
            "claude",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return issue_dir

    def read_journal(self, issue_dir):
        lines = (issue_dir / "journal.jsonl").read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in lines if line.strip()]


class JournalLogInitTests(JournalLogTestBase):
    def test_init_creates_journal_problem_and_created_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            issue_dir = self.init_issue(tmp)
            self.assertTrue((issue_dir / "journal.jsonl").exists())
            self.assertTrue((issue_dir / "problem.md").exists())
            entries = self.read_journal(issue_dir)
            self.assertEqual(len(entries), 1)
            first = entries[0]
            self.assertEqual(first["seq"], 1)
            self.assertEqual(first["kind"], "lifecycle")
            self.assertEqual(first["event"], "created")
            self.assertEqual(first["status"], "added")
            self.assertEqual(first["actor"], "claude")
            self.assertEqual(first["initialRequest"], "order API intermittent timeout")
            self.assertIn("ts", first)

    def test_init_writes_initial_request_into_problem_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            issue_dir = self.init_issue(tmp)
            problem = (issue_dir / "problem.md").read_text(encoding="utf-8")
            self.assertIn("order API intermittent timeout", problem)

    def test_init_refuses_existing_journal(self):
        with tempfile.TemporaryDirectory() as tmp:
            issue_dir = self.init_issue(tmp)
            result = self.run_journal_log(
                "init",
                "--issue-dir",
                str(issue_dir),
                "--initial-request",
                "again",
                "--actor",
                "claude",
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("already exists", result.stderr)

    def test_init_rejects_unknown_actor(self):
        with tempfile.TemporaryDirectory() as tmp:
            issue_dir = Path(tmp) / "issue" / "2026-07-12-x"
            result = self.run_journal_log(
                "init",
                "--issue-dir",
                str(issue_dir),
                "--initial-request",
                "x",
                "--actor",
                "agent",
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("actor", result.stderr)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `cd /Users/happyhsryu/dev/personal/harness-as-usual && python3 -m unittest discover -s scripts/tests -p "test_journal_log.py" -v`
Expected: ERROR/FAIL — `journal-log.py` 부재로 `FileNotFoundError` 또는 returncode 검증 실패.

- [ ] **Step 3: 구현 — entrypoint**

`scripts/journal-log.py` (기존 `topic-log.py`와 동형):

```python
#!/usr/bin/env python3
"""Manage AsUsual find-cause issue journals.

Issue runtime state is journal-first. This public entrypoint delegates to
the internal as_usual_journal_log package while preserving the CLI contract.
"""

from __future__ import annotations

import sys

from as_usual_journal_log.cli import main


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

Run: `chmod +x scripts/journal-log.py`

`scripts/as_usual_journal_log/__init__.py`:

```python
"""Internal package backing scripts/journal-log.py."""
```

- [ ] **Step 4: 구현 — core.py**

`scripts/as_usual_journal_log/core.py`:

```python
"""Core journal operations for AsUsual find-cause issues."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

JsonObject = dict[str, Any]

SCHEMA_VERSION = "as-usual.journal.v1"

REASONING_KINDS = {"finding", "decision", "hypothesis", "interview"}
KINDS = REASONING_KINDS | {"status-change", "approval", "lifecycle"}
ENTRY_STATUSES = {"added", "confirmed", "cancelled"}
LIFECYCLE_EVENTS = {"created", "concluded", "cancelled", "follow-up-linked"}
ACTORS = {"claude", "codex", "user"}
ISSUE_STATUSES = {"open", "concluded", "cancelled"}

JOURNAL_FILE = "journal.jsonl"
PROBLEM_FILE = "problem.md"

PROBLEM_FALLBACK = """# Problem

## Initial Request

{initial_request}

## Current Understanding

(Symptoms, impact, reproduction conditions, and problem boundary. Update freely as the investigation evolves.)

## Background Knowledge

(Domain/background knowledge confirmed through user interviews.)

## Active Hypotheses

(Currently active hypotheses with journal seq references.)
"""


class JournalError(ValueError):
    """Raised for invalid journal operations."""


def now_ts() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def journal_path(issue_dir: Path) -> Path:
    return issue_dir / JOURNAL_FILE


def read_entries(issue_dir: Path) -> list[JsonObject]:
    path = journal_path(issue_dir)
    if not path.exists():
        raise JournalError(f"journal not found: {path}")
    entries: list[JsonObject] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise JournalError(f"invalid json at line {line_no}: {exc}") from exc
    return entries


def next_seq(entries: list[JsonObject]) -> int:
    return max((entry.get("seq", 0) for entry in entries), default=0) + 1


def build_entry(
    entries: list[JsonObject],
    *,
    actor: str,
    kind: str,
    status: str,
    **fields: Any,
) -> JsonObject:
    if actor not in ACTORS:
        raise JournalError(f"invalid actor: {actor} (allowed: {sorted(ACTORS)})")
    if kind not in KINDS:
        raise JournalError(f"invalid kind: {kind} (allowed: {sorted(KINDS)})")
    if status not in ENTRY_STATUSES:
        raise JournalError(f"invalid status: {status} (allowed: {sorted(ENTRY_STATUSES)})")
    entry: JsonObject = {
        "seq": next_seq(entries),
        "ts": now_ts(),
        "actor": actor,
        "kind": kind,
        "status": status,
    }
    entry.update({key: value for key, value in fields.items() if value is not None})
    return entry


def append_entry(issue_dir: Path, entry: JsonObject) -> JsonObject:
    with journal_path(issue_dir).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def problem_template() -> str:
    template_path = Path(__file__).resolve().parents[2] / "templates" / PROBLEM_FILE
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return PROBLEM_FALLBACK


def init_issue(issue_dir: Path, *, initial_request: str, actor: str) -> JsonObject:
    if journal_path(issue_dir).exists():
        raise JournalError(f"journal already exists: {journal_path(issue_dir)}")
    issue_dir.mkdir(parents=True, exist_ok=True)
    entry = build_entry(
        [],
        actor=actor,
        kind="lifecycle",
        status="added",
        event="created",
        content=f"issue created: {issue_dir.name}",
        initialRequest=initial_request,
        schemaVersion=SCHEMA_VERSION,
    )
    append_entry(issue_dir, entry)
    problem = problem_template().replace("{initial_request}", initial_request)
    (issue_dir / PROBLEM_FILE).write_text(problem, encoding="utf-8")
    return entry
```

- [ ] **Step 5: 구현 — cli.py**

`scripts/as_usual_journal_log/cli.py`:

```python
"""CLI parser and entrypoint for journal-log."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import JournalError, init_issue


def emit(receipt: dict) -> int:
    print(json.dumps(receipt, ensure_ascii=False))
    return 0


def fail(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return 1


def cmd_init(args: argparse.Namespace) -> int:
    entry = init_issue(
        Path(args.issue_dir),
        initial_request=args.initial_request,
        actor=args.actor,
    )
    return emit({"ok": True, "seq": entry["seq"], "issueDir": args.issue_dir})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="journal-log")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="create an issue folder, journal, and problem.md")
    init_parser.add_argument("--issue-dir", required=True)
    init_parser.add_argument("--initial-request", required=True)
    init_parser.add_argument("--actor", required=True)
    init_parser.set_defaults(func=cmd_init)

    return parser


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except JournalError as exc:
        return fail(str(exc))
```

주의: `--actor`에 argparse `choices`를 쓰지 않는다. `choices`는 exit code 2로 종료하는데, 테스트와 receipt 계약은 어휘 위반을 `JournalError` 경로(exit 1 + `error: invalid actor ...`)로 기대한다. actor 검증은 `build_entry`가 담당한다 (`ACTORS` import는 이 검증 위임 때문에 cli.py에서 사용하지 않게 되면 제거한다).

- [ ] **Step 6: 테스트 통과 확인**

Run: `cd /Users/happyhsryu/dev/personal/harness-as-usual && python3 -m unittest discover -s scripts/tests -p "test_journal_log.py" -v`
Expected: `test_init_*` 4건 모두 OK.

- [ ] **Step 7: 기존 테스트 회귀 확인**

Run: `cd /Users/happyhsryu/dev/personal/harness-as-usual && python3 -m unittest discover -s scripts/tests -v`
Expected: 전체 OK (topic-log 테스트 무손상).

- [ ] **Step 8: Commit**

```bash
git add scripts/journal-log.py scripts/as_usual_journal_log/ scripts/tests/test_journal_log.py
git commit -m "feat: add journal-log helper skeleton with issue init"
```

---

### Task 2: `add` / `approve` 커맨드 (추론 엔트리 + 승인 기록)

**Files:**
- Modify: `scripts/as_usual_journal_log/cli.py`
- Test: `scripts/tests/test_journal_log.py`

**Interfaces:**
- Consumes: Task 1의 `read_entries`, `build_entry`, `append_entry`, `REASONING_KINDS`.
- Produces: `add --issue-dir <dir> --kind <finding|decision|hypothesis|interview> --content <text> [--evidence <text>] [--actor <a>]` (actor 기본 `claude`), `approve --issue-dir <dir> --content <text> [--actor <a>]` (actor 기본 `user`). 둘 다 `status: added`로 append하고 receipt에 `seq` 반환.

- [ ] **Step 1: 실패하는 테스트 작성** — `test_journal_log.py`에 클래스 추가:

```python
class JournalLogAddTests(JournalLogTestBase):
    def add_entry(self, issue_dir, kind, content, *extra):
        return self.run_journal_log(
            "add", "--issue-dir", str(issue_dir), "--kind", kind, "--content", content, *extra
        )

    def test_add_appends_reasoning_entry_with_incremented_seq(self):
        with tempfile.TemporaryDirectory() as tmp:
            issue_dir = self.init_issue(tmp)
            result = self.add_entry(
                issue_dir, "hypothesis", "connection pool exhaustion", "--evidence", "journal #1"
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            entries = self.read_journal(issue_dir)
            self.assertEqual(len(entries), 2)
            entry = entries[-1]
            self.assertEqual(entry["seq"], 2)
            self.assertEqual(entry["kind"], "hypothesis")
            self.assertEqual(entry["status"], "added")
            self.assertEqual(entry["content"], "connection pool exhaustion")
            self.assertEqual(entry["evidence"], "journal #1")
            self.assertEqual(entry["actor"], "claude")

    def test_add_rejects_non_reasoning_kind(self):
        with tempfile.TemporaryDirectory() as tmp:
            issue_dir = self.init_issue(tmp)
            result = self.add_entry(issue_dir, "lifecycle", "nope")
            self.assertEqual(result.returncode, 1)
            self.assertIn("kind", result.stderr)

    def test_approve_records_user_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            issue_dir = self.init_issue(tmp)
            result = self.run_journal_log(
                "approve", "--issue-dir", str(issue_dir), "--content", "repro test code approved"
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            entry = self.read_journal(issue_dir)[-1]
            self.assertEqual(entry["kind"], "approval")
            self.assertEqual(entry["actor"], "user")
            self.assertEqual(entry["content"], "repro test code approved")
```

- [ ] **Step 2: 실패 확인**

Run: `cd /Users/happyhsryu/dev/personal/harness-as-usual && python3 -m unittest discover -s scripts/tests -p "test_journal_log.py" -v`
Expected: `JournalLogAddTests` 3건 FAIL/ERROR (unknown command `add`).

- [ ] **Step 3: 구현** — `cli.py`에 커맨드 추가:

```python
from .core import (
    REASONING_KINDS,
    JournalError,
    append_entry,
    build_entry,
    init_issue,
    read_entries,
)


def cmd_add(args: argparse.Namespace) -> int:
    if args.kind not in REASONING_KINDS:
        raise JournalError(
            f"invalid kind: {args.kind} (allowed: {sorted(REASONING_KINDS)})"
        )
    issue_dir = Path(args.issue_dir)
    entries = read_entries(issue_dir)
    entry = build_entry(
        entries,
        actor=args.actor,
        kind=args.kind,
        status="added",
        content=args.content,
        evidence=args.evidence,
    )
    append_entry(issue_dir, entry)
    return emit({"ok": True, "seq": entry["seq"]})


def cmd_approve(args: argparse.Namespace) -> int:
    issue_dir = Path(args.issue_dir)
    entries = read_entries(issue_dir)
    entry = build_entry(
        entries,
        actor=args.actor,
        kind="approval",
        status="added",
        content=args.content,
    )
    append_entry(issue_dir, entry)
    return emit({"ok": True, "seq": entry["seq"]})
```

`build_parser()`에 등록:

```python
    add_parser = subparsers.add_parser("add", help="append a reasoning entry")
    add_parser.add_argument("--issue-dir", required=True)
    add_parser.add_argument("--kind", required=True)
    add_parser.add_argument("--content", required=True)
    add_parser.add_argument("--evidence")
    add_parser.add_argument("--actor", default="claude")
    add_parser.set_defaults(func=cmd_add)

    approve_parser = subparsers.add_parser("approve", help="record a user approval")
    approve_parser.add_argument("--issue-dir", required=True)
    approve_parser.add_argument("--content", required=True)
    approve_parser.add_argument("--actor", default="user")
    approve_parser.set_defaults(func=cmd_approve)
```

- [ ] **Step 4: 통과 확인**

Run: `cd /Users/happyhsryu/dev/personal/harness-as-usual && python3 -m unittest discover -s scripts/tests -p "test_journal_log.py" -v`
Expected: 전체 OK.

- [ ] **Step 5: Commit**

```bash
git add scripts/as_usual_journal_log/cli.py scripts/tests/test_journal_log.py
git commit -m "feat: add journal-log add and approve commands"
```

---

### Task 3: `confirm` / `cancel` 커맨드 (status-change 이벤트)

**Files:**
- Modify: `scripts/as_usual_journal_log/core.py`
- Modify: `scripts/as_usual_journal_log/cli.py`
- Test: `scripts/tests/test_journal_log.py`

**Interfaces:**
- Consumes: Task 1–2 산출물.
- Produces: `confirm --issue-dir <dir> --target <seq> [--evidence <text>] [--actor <a>]`, `cancel --issue-dir <dir> --target <seq> --reason <text> [--actor <a>]`. 둘 다 `kind: status-change` 이벤트를 append. `core.py`에 `find_reasoning_entry(entries, seq) -> JsonObject`(없거나 추론 엔트리가 아니면 `JournalError`) 추가 — Task 4·5도 사용.

- [ ] **Step 1: 실패하는 테스트 작성**

```python
class JournalLogStatusChangeTests(JournalLogTestBase):
    def seed_hypothesis(self, tmp):
        issue_dir = self.init_issue(tmp)
        result = self.run_journal_log(
            "add", "--issue-dir", str(issue_dir),
            "--kind", "hypothesis", "--content", "pool exhaustion",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return issue_dir, json.loads(result.stdout)["seq"]

    def test_confirm_appends_status_change_with_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            issue_dir, seq = self.seed_hypothesis(tmp)
            result = self.run_journal_log(
                "confirm", "--issue-dir", str(issue_dir),
                "--target", str(seq), "--evidence", "reproduced by load test",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            entry = self.read_journal(issue_dir)[-1]
            self.assertEqual(entry["kind"], "status-change")
            self.assertEqual(entry["status"], "confirmed")
            self.assertEqual(entry["target"], seq)
            self.assertEqual(entry["evidence"], "reproduced by load test")

    def test_cancel_requires_reason_and_appends_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            issue_dir, seq = self.seed_hypothesis(tmp)
            result = self.run_journal_log(
                "cancel", "--issue-dir", str(issue_dir),
                "--target", str(seq), "--reason", "contradicted by #18",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            entry = self.read_journal(issue_dir)[-1]
            self.assertEqual(entry["status"], "cancelled")
            self.assertEqual(entry["reason"], "contradicted by #18")

    def test_confirm_rejects_missing_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            issue_dir, _ = self.seed_hypothesis(tmp)
            result = self.run_journal_log(
                "confirm", "--issue-dir", str(issue_dir), "--target", "99",
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("target", result.stderr)

    def test_confirm_rejects_non_reasoning_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            issue_dir, _ = self.seed_hypothesis(tmp)
            result = self.run_journal_log(
                "confirm", "--issue-dir", str(issue_dir), "--target", "1",
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("target", result.stderr)
```

- [ ] **Step 2: 실패 확인**

Run: `cd /Users/happyhsryu/dev/personal/harness-as-usual && python3 -m unittest discover -s scripts/tests -p "test_journal_log.py" -v`
Expected: 신규 4건 FAIL/ERROR.

- [ ] **Step 3: 구현** — `core.py`에 추가:

```python
def find_reasoning_entry(entries: list[JsonObject], seq: int) -> JsonObject:
    for entry in entries:
        if entry.get("seq") == seq:
            if entry.get("kind") not in REASONING_KINDS:
                raise JournalError(
                    f"invalid target: seq {seq} is kind {entry.get('kind')}, "
                    f"not a reasoning entry"
                )
            return entry
    raise JournalError(f"invalid target: seq {seq} not found")
```

`cli.py`에 추가:

```python
from .core import find_reasoning_entry


def _status_change(args: argparse.Namespace, *, status: str, **fields) -> int:
    issue_dir = Path(args.issue_dir)
    entries = read_entries(issue_dir)
    find_reasoning_entry(entries, args.target)
    entry = build_entry(
        entries,
        actor=args.actor,
        kind="status-change",
        status=status,
        target=args.target,
        **fields,
    )
    append_entry(issue_dir, entry)
    return emit({"ok": True, "seq": entry["seq"], "target": args.target, "status": status})


def cmd_confirm(args: argparse.Namespace) -> int:
    return _status_change(args, status="confirmed", evidence=args.evidence)


def cmd_cancel(args: argparse.Namespace) -> int:
    return _status_change(args, status="cancelled", reason=args.reason)
```

`build_parser()`에 등록:

```python
    confirm_parser = subparsers.add_parser("confirm", help="mark an entry confirmed")
    confirm_parser.add_argument("--issue-dir", required=True)
    confirm_parser.add_argument("--target", required=True, type=int)
    confirm_parser.add_argument("--evidence")
    confirm_parser.add_argument("--actor", default="claude")
    confirm_parser.set_defaults(func=cmd_confirm)

    cancel_parser = subparsers.add_parser("cancel", help="mark an entry cancelled")
    cancel_parser.add_argument("--issue-dir", required=True)
    cancel_parser.add_argument("--target", required=True, type=int)
    cancel_parser.add_argument("--reason", required=True)
    cancel_parser.add_argument("--actor", default="claude")
    cancel_parser.set_defaults(func=cmd_cancel)
```

- [ ] **Step 4: 통과 확인**

Run: `cd /Users/happyhsryu/dev/personal/harness-as-usual && python3 -m unittest discover -s scripts/tests -p "test_journal_log.py" -v`
Expected: 전체 OK.

- [ ] **Step 5: Commit**

```bash
git add scripts/as_usual_journal_log/ scripts/tests/test_journal_log.py
git commit -m "feat: add journal-log confirm and cancel status-change events"
```

---

### Task 4: 상태 파생(`derive_status`) + `status` / `conclude` 커맨드

**Files:**
- Modify: `scripts/as_usual_journal_log/core.py`
- Modify: `scripts/as_usual_journal_log/cli.py`
- Test: `scripts/tests/test_journal_log.py`

**Interfaces:**
- Consumes: Task 1–3 산출물.
- Produces: `core.derive_status(entries) -> dict` — `{"issueStatus": "open|concluded|cancelled", "active": [seq...], "confirmed": [seq...], "cancelled": [seq...], "followUps": [path...], "lastSeq": N}`. CLI `status --issue-dir <dir> [--json]`(파생 결과 출력), `conclude --issue-dir <dir> --summary <text> [--status <concluded|cancelled>] [--follow-up <topic-dir>] [--force-without-confirmed --reason <text>] [--actor <a>]`. Task 5의 `view`/`validate`도 `derive_status`를 사용.

- [ ] **Step 1: 실패하는 테스트 작성**

```python
class JournalLogStatusAndConcludeTests(JournalLogTestBase):
    def seed_confirmed(self, tmp):
        issue_dir = self.init_issue(tmp)
        add = self.run_journal_log(
            "add", "--issue-dir", str(issue_dir),
            "--kind", "hypothesis", "--content", "dns cache expiry",
        )
        seq = json.loads(add.stdout)["seq"]
        self.run_journal_log(
            "confirm", "--issue-dir", str(issue_dir),
            "--target", str(seq), "--evidence", "reproduced",
        )
        return issue_dir, seq

    def status_json(self, issue_dir):
        result = self.run_journal_log("status", "--issue-dir", str(issue_dir), "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_status_derives_open_and_entry_buckets(self):
        with tempfile.TemporaryDirectory() as tmp:
            issue_dir, seq = self.seed_confirmed(tmp)
            status = self.status_json(issue_dir)
            self.assertEqual(status["issueStatus"], "open")
            self.assertEqual(status["confirmed"], [seq])
            self.assertEqual(status["active"], [])

    def test_cancel_moves_confirmed_entry_to_cancelled_bucket(self):
        with tempfile.TemporaryDirectory() as tmp:
            issue_dir, seq = self.seed_confirmed(tmp)
            self.run_journal_log(
                "cancel", "--issue-dir", str(issue_dir),
                "--target", str(seq), "--reason", "refuted by logs",
            )
            status = self.status_json(issue_dir)
            self.assertEqual(status["confirmed"], [])
            self.assertEqual(status["cancelled"], [seq])

    def test_conclude_records_lifecycle_and_status_becomes_concluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            issue_dir, _ = self.seed_confirmed(tmp)
            result = self.run_journal_log(
                "conclude", "--issue-dir", str(issue_dir),
                "--summary", "root cause: dns cache expiry",
                "--follow-up", ".as-usual/topic/2026-07-12-fix-dns-cache",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            entry = self.read_journal(issue_dir)[-1]
            self.assertEqual(entry["kind"], "lifecycle")
            self.assertEqual(entry["event"], "concluded")
            self.assertEqual(entry["followUp"], ".as-usual/topic/2026-07-12-fix-dns-cache")
            status = self.status_json(issue_dir)
            self.assertEqual(status["issueStatus"], "concluded")
            self.assertEqual(
                status["followUps"], [".as-usual/topic/2026-07-12-fix-dns-cache"]
            )

    def test_conclude_refuses_without_confirmed_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            issue_dir = self.init_issue(tmp)
            result = self.run_journal_log(
                "conclude", "--issue-dir", str(issue_dir), "--summary", "done",
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("confirmed", result.stderr)

    def test_conclude_force_without_confirmed_requires_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            issue_dir = self.init_issue(tmp)
            missing = self.run_journal_log(
                "conclude", "--issue-dir", str(issue_dir), "--summary", "inconclusive",
                "--force-without-confirmed",
            )
            self.assertEqual(missing.returncode, 1)
            self.assertIn("reason", missing.stderr)
            forced = self.run_journal_log(
                "conclude", "--issue-dir", str(issue_dir), "--summary", "inconclusive",
                "--force-without-confirmed", "--reason", "cannot reproduce in local env",
            )
            self.assertEqual(forced.returncode, 0, forced.stderr)
            self.assertEqual(self.status_json(issue_dir)["issueStatus"], "concluded")

    def test_conclude_cancelled_closes_issue_without_confirmed_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            issue_dir = self.init_issue(tmp)
            result = self.run_journal_log(
                "conclude", "--issue-dir", str(issue_dir),
                "--status", "cancelled", "--summary", "user abandoned investigation",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(self.status_json(issue_dir)["issueStatus"], "cancelled")

    def test_conclude_refuses_already_closed_issue(self):
        with tempfile.TemporaryDirectory() as tmp:
            issue_dir, _ = self.seed_confirmed(tmp)
            self.run_journal_log(
                "conclude", "--issue-dir", str(issue_dir), "--summary", "done",
            )
            again = self.run_journal_log(
                "conclude", "--issue-dir", str(issue_dir), "--summary", "again",
            )
            self.assertEqual(again.returncode, 1)
            self.assertIn("already", again.stderr)
```

- [ ] **Step 2: 실패 확인**

Run: `cd /Users/happyhsryu/dev/personal/harness-as-usual && python3 -m unittest discover -s scripts/tests -p "test_journal_log.py" -v`
Expected: 신규 7건 FAIL/ERROR.

- [ ] **Step 3: 구현** — `core.py`에 추가:

```python
def derive_status(entries: list[JsonObject]) -> JsonObject:
    entry_status: dict[int, str] = {}
    issue_status = "open"
    follow_ups: list[str] = []
    last_seq = 0
    for entry in entries:
        last_seq = max(last_seq, entry.get("seq", 0))
        kind = entry.get("kind")
        if kind in REASONING_KINDS:
            entry_status[entry["seq"]] = "added"
        elif kind == "status-change":
            target = entry.get("target")
            if target in entry_status:
                entry_status[target] = entry.get("status", "added")
        elif kind == "lifecycle":
            event = entry.get("event")
            if event == "concluded":
                issue_status = "concluded"
            elif event == "cancelled":
                issue_status = "cancelled"
            if entry.get("followUp"):
                follow_ups.append(entry["followUp"])

    def bucket(status: str) -> list[int]:
        return sorted(seq for seq, value in entry_status.items() if value == status)

    return {
        "issueStatus": issue_status,
        "active": bucket("added"),
        "confirmed": bucket("confirmed"),
        "cancelled": bucket("cancelled"),
        "followUps": follow_ups,
        "lastSeq": last_seq,
    }
```

`cli.py`에 추가:

```python
from .core import derive_status


def cmd_status(args: argparse.Namespace) -> int:
    entries = read_entries(Path(args.issue_dir))
    return emit(derive_status(entries))


def cmd_conclude(args: argparse.Namespace) -> int:
    issue_dir = Path(args.issue_dir)
    entries = read_entries(issue_dir)
    derived = derive_status(entries)
    if derived["issueStatus"] != "open":
        raise JournalError(f"issue already {derived['issueStatus']}")
    if args.status == "concluded" and not derived["confirmed"]:
        if not args.force_without_confirmed:
            raise JournalError(
                "no confirmed entry: confirm a hypothesis first, or pass "
                "--force-without-confirmed with --reason"
            )
        if not args.reason:
            raise JournalError("--force-without-confirmed requires --reason")
    entry = build_entry(
        entries,
        actor=args.actor,
        kind="lifecycle",
        status="added",
        event=args.status,
        content=args.summary,
        followUp=args.follow_up,
        reason=args.reason,
    )
    append_entry(issue_dir, entry)
    return emit({"ok": True, "seq": entry["seq"], "issueStatus": args.status})
```

`build_parser()`에 등록:

```python
    status_parser = subparsers.add_parser("status", help="derive issue status from the journal")
    status_parser.add_argument("--issue-dir", required=True)
    status_parser.add_argument("--json", action="store_true")
    status_parser.set_defaults(func=cmd_status)

    conclude_parser = subparsers.add_parser("conclude", help="close the issue")
    conclude_parser.add_argument("--issue-dir", required=True)
    conclude_parser.add_argument("--summary", required=True)
    conclude_parser.add_argument("--status", default="concluded", choices=["concluded", "cancelled"])
    conclude_parser.add_argument("--follow-up", dest="follow_up")
    conclude_parser.add_argument("--force-without-confirmed", action="store_true")
    conclude_parser.add_argument("--reason")
    conclude_parser.add_argument("--actor", default="claude")
    conclude_parser.set_defaults(func=cmd_conclude)
```

(`status`의 `--json` 플래그는 현재 출력이 이미 JSON이므로 수용만 하고 동작은 동일하다 — 계약 안정성을 위해 받아둔다.)

- [ ] **Step 4: 통과 확인**

Run: `cd /Users/happyhsryu/dev/personal/harness-as-usual && python3 -m unittest discover -s scripts/tests -p "test_journal_log.py" -v`
Expected: 전체 OK.

- [ ] **Step 5: Commit**

```bash
git add scripts/as_usual_journal_log/ scripts/tests/test_journal_log.py
git commit -m "feat: add journal-log status derivation and conclude gate"
```

---

### Task 5: `view` / `validate` 커맨드

**Files:**
- Modify: `scripts/as_usual_journal_log/core.py`
- Modify: `scripts/as_usual_journal_log/cli.py`
- Test: `scripts/tests/test_journal_log.py`

**Interfaces:**
- Consumes: Task 1–4 산출물 (`derive_status`, `read_entries`).
- Produces: `view --issue-dir <dir> [--md]` — 기본은 `{"derived": ..., "entries": [...]}` JSON, `--md`는 사람이 읽는 마크다운 렌더(Confirmed/Active/Cancelled 그룹 + 시간순 로그). `validate --issue-dir <dir>` — 구조 검증, 문제 없으면 `{"ok": true, "problems": []}`, 있으면 exit 1 + problems 목록. `core.validate_entries(entries) -> list[str]`, `core.render_markdown(entries) -> str`.

- [ ] **Step 1: 실패하는 테스트 작성**

```python
class JournalLogViewValidateTests(JournalLogTestBase):
    def test_view_md_groups_by_derived_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            issue_dir = self.init_issue(tmp)
            add = self.run_journal_log(
                "add", "--issue-dir", str(issue_dir),
                "--kind", "hypothesis", "--content", "dns cache expiry",
            )
            seq = json.loads(add.stdout)["seq"]
            self.run_journal_log(
                "confirm", "--issue-dir", str(issue_dir), "--target", str(seq),
                "--evidence", "reproduced",
            )
            result = self.run_journal_log("view", "--issue-dir", str(issue_dir), "--md")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("## Confirmed", result.stdout)
            self.assertIn("dns cache expiry", result.stdout)
            self.assertIn("## Log", result.stdout)

    def test_validate_passes_on_wellformed_journal(self):
        with tempfile.TemporaryDirectory() as tmp:
            issue_dir = self.init_issue(tmp)
            result = self.run_journal_log("validate", "--issue-dir", str(issue_dir))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["problems"], [])

    def test_validate_flags_duplicate_seq_and_bad_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            issue_dir = self.init_issue(tmp)
            with (issue_dir / "journal.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(json.dumps({
                    "seq": 1, "ts": "2026-07-12T10:00:00+09:00", "actor": "claude",
                    "kind": "status-change", "status": "confirmed", "target": 99,
                }) + "\n")
            result = self.run_journal_log("validate", "--issue-dir", str(issue_dir))
            self.assertEqual(result.returncode, 1)
            problems = json.loads(result.stdout)["problems"]
            self.assertTrue(any("seq" in problem for problem in problems))
            self.assertTrue(any("target" in problem for problem in problems))
```

- [ ] **Step 2: 실패 확인**

Run: `cd /Users/happyhsryu/dev/personal/harness-as-usual && python3 -m unittest discover -s scripts/tests -p "test_journal_log.py" -v`
Expected: 신규 3건 FAIL/ERROR.

- [ ] **Step 3: 구현** — `core.py`에 추가:

```python
def validate_entries(entries: list[JsonObject]) -> list[str]:
    problems: list[str] = []
    seen_seq: set[int] = set()
    reasoning_seqs: set[int] = set()
    previous_seq = 0
    for index, entry in enumerate(entries, 1):
        seq = entry.get("seq")
        if not isinstance(seq, int) or seq <= 0:
            problems.append(f"entry {index}: invalid seq {seq!r}")
            continue
        if seq in seen_seq:
            problems.append(f"entry {index}: duplicate seq {seq}")
        if seq <= previous_seq:
            problems.append(f"entry {index}: seq {seq} not increasing")
        seen_seq.add(seq)
        previous_seq = max(previous_seq, seq)

        kind = entry.get("kind")
        status = entry.get("status")
        actor = entry.get("actor")
        if kind not in KINDS:
            problems.append(f"seq {seq}: invalid kind {kind!r}")
        if status not in ENTRY_STATUSES:
            problems.append(f"seq {seq}: invalid status {status!r}")
        if actor not in ACTORS:
            problems.append(f"seq {seq}: invalid actor {actor!r}")

        if kind in REASONING_KINDS:
            reasoning_seqs.add(seq)
            if status != "added":
                problems.append(f"seq {seq}: reasoning entry must start as added")
        elif kind == "status-change":
            target = entry.get("target")
            if target not in reasoning_seqs:
                problems.append(f"seq {seq}: target {target!r} is not an earlier reasoning entry")
            if status not in {"confirmed", "cancelled"}:
                problems.append(f"seq {seq}: status-change must be confirmed or cancelled")
            if status == "cancelled" and not entry.get("reason"):
                problems.append(f"seq {seq}: cancelled status-change requires reason")
        elif kind == "lifecycle":
            if entry.get("event") not in LIFECYCLE_EVENTS:
                problems.append(f"seq {seq}: invalid lifecycle event {entry.get('event')!r}")

    if entries:
        first = entries[0]
        if first.get("kind") != "lifecycle" or first.get("event") != "created":
            problems.append("entry 1: journal must start with a lifecycle created event")
    else:
        problems.append("journal is empty")
    return problems


def render_markdown(entries: list[JsonObject]) -> str:
    derived = derive_status(entries)
    by_seq = {entry["seq"]: entry for entry in entries if "seq" in entry}

    def section(title: str, seqs: list[int]) -> list[str]:
        lines = [f"## {title}", ""]
        if not seqs:
            lines.append("(none)")
        for seq in seqs:
            entry = by_seq[seq]
            lines.append(f"- #{seq} [{entry.get('kind')}] {entry.get('content', '')}")
        lines.append("")
        return lines

    lines = [f"# Journal View (issue: {derived['issueStatus']})", ""]
    lines += section("Confirmed", derived["confirmed"])
    lines += section("Active", derived["active"])
    lines += section("Cancelled", derived["cancelled"])
    lines += ["## Log", ""]
    for entry in entries:
        seq = entry.get("seq")
        detail = entry.get("content") or entry.get("reason") or entry.get("evidence") or ""
        suffix = f" -> #{entry['target']}" if entry.get("target") else ""
        lines.append(
            f"- #{seq} {entry.get('ts', '')} [{entry.get('kind')}/{entry.get('status')}]"
            f"{suffix} {detail}"
        )
    lines.append("")
    return "\n".join(lines)
```

`cli.py`에 추가:

```python
from .core import render_markdown, validate_entries


def cmd_view(args: argparse.Namespace) -> int:
    entries = read_entries(Path(args.issue_dir))
    if args.md:
        print(render_markdown(entries))
        return 0
    return emit({"derived": derive_status(entries), "entries": entries})


def cmd_validate(args: argparse.Namespace) -> int:
    entries = read_entries(Path(args.issue_dir))
    problems = validate_entries(entries)
    emit({"ok": not problems, "problems": problems})
    return 1 if problems else 0
```

`build_parser()`에 등록:

```python
    view_parser = subparsers.add_parser("view", help="render the journal")
    view_parser.add_argument("--issue-dir", required=True)
    view_parser.add_argument("--md", action="store_true")
    view_parser.set_defaults(func=cmd_view)

    validate_parser = subparsers.add_parser("validate", help="validate journal structure")
    validate_parser.add_argument("--issue-dir", required=True)
    validate_parser.set_defaults(func=cmd_validate)
```

- [ ] **Step 4: 통과 확인 + 전체 회귀**

Run: `cd /Users/happyhsryu/dev/personal/harness-as-usual && python3 -m unittest discover -s scripts/tests -v`
Expected: journal-log + topic-log 테스트 전체 OK.

- [ ] **Step 5: Commit**

```bash
git add scripts/as_usual_journal_log/ scripts/tests/test_journal_log.py
git commit -m "feat: add journal-log view rendering and structural validation"
```

---

### Task 6: `templates/problem.md` + `templates/conclusion.md`

**Files:**
- Create: `templates/problem.md`
- Create: `templates/conclusion.md`

**Interfaces:**
- Consumes: Task 1의 `problem_template()`이 `templates/problem.md`를 읽는다 — `{initial_request}` 자리표시자와 4개 섹션 헤딩(`Initial Request`, `Current Understanding`, `Background Knowledge`, `Active Hypotheses`)은 core.py의 `PROBLEM_FALLBACK`과 동일해야 한다.
- Produces: find-cause 스킬(Task 8)과 규칙 파일(Task 7)이 참조하는 canonical 템플릿 2개.

- [ ] **Step 1: `templates/problem.md` 작성** — `PROBLEM_FALLBACK`과 동일 내용:

```markdown
# Problem

## Initial Request

{initial_request}

## Current Understanding

(Symptoms, impact, reproduction conditions, and problem boundary. Update freely as the investigation evolves.)

## Background Knowledge

(Domain/background knowledge confirmed through user interviews.)

## Active Hypotheses

(Currently active hypotheses with journal seq references.)
```

- [ ] **Step 2: `templates/conclusion.md` 작성**

```markdown
# Conclusion

## Confirmed Cause / Direction

(The confirmed root cause, or the confirmed solution/improvement direction.)

## Supporting Evidence

(Evidence summary citing journal seq numbers, e.g. journal #12, #18.)

## Reproduction

(How the problem was reproduced, or an explicit note that reproduction was not possible and why.)

## Recommended Verification Plan

(Suggested tests/verification for the follow-up coding topic.)

## Follow-Up

(Linked follow-up topic path, or `none`.)
```

- [ ] **Step 3: 검증 — init이 템플릿을 사용하는지 확인**

Run: `cd /Users/happyhsryu/dev/personal/harness-as-usual && python3 -m unittest discover -s scripts/tests -p "test_journal_log.py" -v && rm -rf /tmp/fc-check && python3 scripts/journal-log.py init --issue-dir /tmp/fc-check --initial-request "template check" --actor claude && grep -c "## " /tmp/fc-check/problem.md && rm -rf /tmp/fc-check`
Expected: 테스트 전체 OK, `grep -c` 출력 `4` (템플릿의 섹션 4개가 사용됨).

- [ ] **Step 4: Commit**

```bash
git add templates/problem.md templates/conclusion.md
git commit -m "feat: add problem and conclusion templates for find-cause issues"
```

---

### Task 7: `as-usual-rules/find-cause-workflow.md` (canonical 규칙)

**Files:**
- Create: `as-usual-rules/find-cause-workflow.md`

**Interfaces:**
- Consumes: Task 1–5의 CLI 계약 (커맨드명·플래그 정확히 일치해야 함), Task 6의 템플릿 경로.
- Produces: find-cause 스킬(Task 8)과 using-as-usual/hand-off(Task 9)가 참조하는 canonical 규칙. 설계 문서 `docs/design/2026-07-12-find-cause-workflow-design.md`의 Runtime Model / Hard Gates / User-Interview / 종결 섹션을 runtime 규칙으로 옮긴 것.

- [ ] **Step 1: 파일 작성** — 다음 구조와 내용으로 작성한다 (core-workflow.md의 문체를 따르되 훨씬 짧게, 절차서가 아닌 원칙 목록으로):

```markdown
# AsUsual Find-Cause Workflow

<Role>
You are the AsUsual find-cause controller for one issue in one target project.

Your job is not to fix code. Your job is to help the user precisely
understand and confirm a problem: its root cause, or the confirmed
solution/improvement direction. You record the reasoning trail (findings,
decisions, hypotheses, retractions) in an append-only journal so the full
thought process can be reconstructed at the end and resumed across sessions.
</Role>

## Relationship To The Coding Workflow

- find-cause is a separate work unit (`issue`), parallel to the coding
  workflow's `topic`. It runs before, and never inside, the coding workflow.
- Never modify production code in a find-cause issue. When the user wants
  the fix implemented, propose a follow-up coding topic.
- `as-usual-rules/core-workflow.md` still owns coding topics. This file owns
  issues only. Shared principles apply unchanged: the Trust Boundary,
  secret-handling rules, and the High-Risk Operation Gate defined in
  core-workflow.md.

## Artifact Contract

```text
<project-root>/
└── .as-usual/
    └── issue/
        └── yyyy-MM-dd-<slug>/
            ├── problem.md       # living snapshot: current understanding
            ├── journal.jsonl    # append-only reasoning + lifecycle log
            ├── evidence/        # optional: log excerpts, run outputs
            └── conclusion.md    # written only at conclusion
```

- Create issue artifacts only under `.as-usual/issue/yyyy-MM-dd-<slug>/`,
  using the actual current date and a lowercase kebab-case slug.
- `journal.jsonl` is append-only and script-managed. Never hand-edit it and
  never rewrite existing lines. Use `scripts/journal-log.py` for every
  journal update; if the helper cannot express an update, stop and report
  the missing capability.
- `problem.md` is a freely updated living snapshot (no freeze, no review
  gate). A new session reads `problem.md` first, then
  `journal-log.py status --issue-dir <dir> --json`.
- `conclusion.md` follows `templates/conclusion.md` and cites journal seq
  numbers as evidence provenance.
- Issue status is derived from the journal: `open`, `concluded`, or
  `cancelled`. There is no phase pipeline. Problem definition, hypothesis
  work, reproduction, and retraction are journal entries, not phases.

## Journal Vocabulary

- kinds: `finding | decision | hypothesis | interview` (reasoning),
  `status-change`, `approval`, `lifecycle`.
- entry statuses: `added | confirmed | cancelled`. New reasoning entries
  start as `added`. `confirmed`/`cancelled` transitions are always separate
  `status-change` events with a `target` seq — the original line is never
  edited, so the record shows when and why a conclusion was reversed.
- Record retractions promptly: when a confirmed item turns out to be wrong,
  append a `cancel` with the contradicting evidence as the reason.

## Hard Gates

1. Journal is append-only; all updates go through `scripts/journal-log.py`.
2. No confirmation without evidence: do not `confirm` an entry or conclude
   the issue without reproduction evidence or an explicit
   "could not reproduce because ... " judgment recorded as evidence/reason.
   (`journal-log.py conclude` enforces this; `--force-without-confirmed`
   requires a recorded reason.)
3. Read-only by default: reading code, running the app, and analyzing logs
   are free. Writing reproduction tests/scripts requires an explicit user
   request or approval recorded with `journal-log.py approve`. Production
   code changes are always out of scope.
4. High-risk operations (production access, shared-DB queries, etc.) follow
   core-workflow.md's High-Risk Operation Gate; record the fresh approval
   with `journal-log.py approve`.
5. Before ending a turn, record this turn's meaningful findings, decisions,
   and retractions in the journal.

Everything else — investigation order, number of questions, number of
hypotheses, entry length — is free-form. Do not impose coding-workflow
formality on the investigation.

## User Interview

Interview the user in grilling style: one question at a time, each with your
recommended answer. Never ask what the codebase or logs can answer directly.

Trigger an interview when:

1. Entering the issue: capture symptoms, impact, reproduction conditions,
   and problem boundary into `problem.md`.
2. A domain/background knowledge gap blocks the investigation.
3. Hypotheses conflict, or evidence contradicts the user's stated belief:
   summarize the evidence so far and ask for the user's judgment.

Record interview answers as journal `interview` entries and transcribe
domain knowledge into `problem.md` Background Knowledge.

## Conclusion

When a hypothesis (or solution direction) is confirmed with evidence,
continue in the same turn:

1. Write `conclusion.md` from `templates/conclusion.md` and self-review it.
2. If reproduction code exists, ask the user: delete it, or keep it as a
   regression-test seed for the follow-up topic.
3. Record closure: `journal-log.py conclude --issue-dir <dir> --summary ...`
   (use `--status cancelled` with the reason when the user abandons the
   investigation).
4. Offer a follow-up coding topic. If accepted, create it with the existing
   `scripts/topic-log.py init`, pass `conclusion.md` as a source input, and
   link both directions: the topic records the conclusion path, and the
   journal records the topic path via `conclude --follow-up <topic-dir>`.
5. Offer memory candidates for knowledge that outlives the issue via the
   `manage-self-improvement` skill; reflect only after explicit user
   approval.

Do not ask the git-action question for issues. Confirming the cause and
stopping without a follow-up topic is a normal terminal path.
```

- [ ] **Step 2: 검증 — CLI 계약 일치 확인**

Run: `cd /Users/happyhsryu/dev/personal/harness-as-usual && grep -oE "journal-log\.py [a-z-]+" as-usual-rules/find-cause-workflow.md | sort -u && python3 scripts/journal-log.py --help 2>&1 | head -5`
Expected: 규칙 파일이 언급하는 서브커맨드(`approve`, `conclude`, `status`)가 모두 CLI `--help`의 서브커맨드 목록에 존재.

- [ ] **Step 3: Commit**

```bash
git add as-usual-rules/find-cause-workflow.md
git commit -m "feat: add find-cause canonical workflow rules"
```

---

### Task 8: `skills/find-cause/SKILL.md`

**Files:**
- Create: `skills/find-cause/SKILL.md`

**Interfaces:**
- Consumes: Task 7의 규칙 파일 (canonical 참조 대상), Task 1–5 CLI 계약, Task 6 템플릿.
- Produces: 공개 런타임 스킬. Claude는 `skills/` 자동 발견, Codex는 `.codex-plugin/plugin.json`의 `"skills": "./skills/"`로 이미 노출되므로 manifest 수정 불필요.

- [ ] **Step 1: 파일 작성**

```markdown
---
name: find-cause
description: Use when the user wants to investigate and confirm a problem's root cause or a solution/improvement direction without implementing code changes, or when resuming a `.as-usual/issue/` investigation.
---

# Find Cause

This skill owns the whole find-cause issue lifecycle. The canonical rules
live in `as-usual-rules/find-cause-workflow.md`; read that file fully before
acting, then follow it. This skill adds only operational defaults.

## First Reads

1. Read `as-usual-rules/find-cause-workflow.md` from the AsUsual plugin
   root (the parent directory of the `skills/` directory containing this
   skill, or the path announced by the SessionStart hook).
2. For an existing issue: read `problem.md`, then run
   `python3 <plugin-root>/scripts/journal-log.py status --issue-dir <dir> --json`,
   then read `conclusion.md` if it exists. Use `view --md` when you need the
   full reasoning trail.
3. For a new issue: choose `.as-usual/issue/yyyy-MM-dd-<slug>/` with the
   actual current date, then run
   `python3 <plugin-root>/scripts/journal-log.py init --issue-dir <dir>
   --initial-request "<request>" --actor claude` (use `--actor codex` on
   Codex), tell the user the issue path in one line, and start the entry
   interview.

## Operating Loop

- Interview first (one question at a time, with your recommended answer),
  then investigate, then record. Keep `problem.md` current as understanding
  changes.
- Record meaningful findings/decisions/hypotheses as journal entries when
  they happen, not in a batch at the end:
  `journal-log.py add --issue-dir <dir> --kind <kind> --content "..."
  [--evidence "..."]`.
- Confirm or cancel with `confirm --target <seq>` / `cancel --target <seq>
  --reason "..."`. Never edit journal lines.
- Enforce the hard gates from the workflow file: read-only default,
  approval-gated reproduction code (`approve`), evidence-gated confirmation,
  inherited high-risk gate, record-before-turn-end.

## Stop Conditions

Stop and tell the user the issue path and required input when:

- An interview question is waiting for the user's answer.
- Reproduction code needs user approval.
- A high-risk operation needs fresh approval.
- Conflicting hypotheses need the user's judgment.
- The conclusion is written and the follow-up topic decision is pending.
```

- [ ] **Step 2: 검증**

Run: `cd /Users/happyhsryu/dev/personal/harness-as-usual && head -5 skills/find-cause/SKILL.md && grep -l "find-cause-workflow.md" skills/find-cause/SKILL.md as-usual-rules/find-cause-workflow.md`
Expected: frontmatter에 `name: find-cause` 존재, 두 파일 모두 상호 참조 확인.

- [ ] **Step 3: Commit**

```bash
git add skills/find-cause/SKILL.md
git commit -m "feat: add find-cause runtime skill"
```

---

### Task 9: `using-as-usual` / `hand-off` issue 인지 수정

**Files:**
- Modify: `skills/using-as-usual/SKILL.md`
- Modify: `skills/hand-off/SKILL.md`

**Interfaces:**
- Consumes: Task 7 규칙 파일 경로, Task 8 스킬 이름.
- Produces: 활성화·재개 라우팅. `core-workflow.md`는 수정하지 않는다.

- [ ] **Step 1: `skills/using-as-usual/SKILL.md` 수정**

(1) `## Activation` 섹션의 불릿 목록 마지막에 추가:

```markdown
- The user mentions `.as-usual/issue/`, `journal.jsonl`, `problem.md`, or asks to investigate/confirm a problem's cause or a solution direction without implementing it. This activates the find-cause workflow, not the coding topic workflow.
```

(2) `## Responsibility Boundary` 표의 `hand-off` 행 바로 아래에 행 추가:

```markdown
| `find-cause` | Own the whole `.as-usual/issue/` investigation lifecycle per `as-usual-rules/find-cause-workflow.md`; not a coding topic phase |
```

(3) `## Phase Handoff` 섹션 마지막에 단락 추가:

```markdown
When the request is find-cause work (investigation/cause-confirmation, new or resumed issue under `.as-usual/issue/`), do not run coding-topic first reads or `start-work`. Hand off to the `find-cause` skill, which owns its own first reads against `as-usual-rules/find-cause-workflow.md`.
```

- [ ] **Step 2: `skills/hand-off/SKILL.md` 수정** — path 해석 규칙을 설명하는 섹션(파일을 열어 path resolution을 다루는 위치를 찾는다)에 단락 추가:

```markdown
## Issue Hand-Off

If the supplied path resolves inside `.as-usual/issue/` (an issue directory, a file inside one, or the `issue/` collection), this is a find-cause issue, not a coding topic. Do not apply topic first reads or completion verification. Read `problem.md`, run `python3 <plugin-root>/scripts/journal-log.py status --issue-dir <dir> --json`, then route to the `find-cause` skill. When no path is supplied and both recent topics and recent issues exist, list both and ask the user which to resume.
```

- [ ] **Step 3: 검증 — core-workflow 무수정 확인**

Run: `cd /Users/happyhsryu/dev/personal/harness-as-usual && git diff --stat as-usual-rules/core-workflow.md scripts/topic-log.py scripts/as_usual_topic_log/ && grep -c "find-cause" skills/using-as-usual/SKILL.md skills/hand-off/SKILL.md`
Expected: `git diff --stat` 출력 없음 (무수정), 두 스킬 모두 `find-cause` 언급 1회 이상.

- [ ] **Step 4: Commit**

```bash
git add skills/using-as-usual/SKILL.md skills/hand-off/SKILL.md
git commit -m "feat: route find-cause issue activation and hand-off"
```

---

### Task 10: `hooks/session-start` 안내 문장 추가

**Files:**
- Modify: `hooks/session-start`

**Interfaces:**
- Consumes: Task 8 스킬 이름.
- Produces: SessionStart 주입 문장에 find-cause entrypoint 안내 포함.

- [ ] **Step 1: `content` 변수 수정** — 기존:

```bash
content="AsUsual is available: for explicit AsUsual work, AsUsual topic/artifact resumes, or feature-development work that should use the AsUsual workflow, use the \`using-as-usual\` skill first; otherwise handle the request normally."
```

를 다음으로 교체:

```bash
content="AsUsual is available: for explicit AsUsual work, AsUsual topic/artifact resumes, or feature-development work that should use the AsUsual workflow, use the \`using-as-usual\` skill first; for problem-cause investigation (\`.as-usual/issue/\`), use the \`find-cause\` skill; otherwise handle the request normally."
```

- [ ] **Step 2: 검증 — hook 출력이 유효한 JSON인지 확인**

Run: `cd /Users/happyhsryu/dev/personal/harness-as-usual && CLAUDE_PLUGIN_ROOT=. bash hooks/session-start | python3 -m json.tool > /dev/null && echo OK && CLAUDE_PLUGIN_ROOT=. bash hooks/session-start | grep -c "find-cause"`
Expected: `OK` 출력, grep 카운트 1.

- [ ] **Step 3: Commit**

```bash
git add hooks/session-start
git commit -m "feat: announce find-cause entrypoint in session-start hook"
```

---

### Task 11: `docs/ARCHITECTURE-WORKFLOW.md` find-cause 섹션 추가

**Files:**
- Modify: `docs/ARCHITECTURE-WORKFLOW.md`

**Interfaces:**
- Consumes: Task 1–10의 최종 결과 (경로·커맨드·스킬 이름을 실제 구현과 일치시켜야 함).
- Produces: 아키텍처 문서의 find-cause 설명.

- [ ] **Step 1: 수정 내용 적용** — 세 곳:

(1) `## Core Architecture`의 디렉토리 트리에서 `as-usual-rules/` 아래 `find-cause-workflow.md`, `skills/` 아래 `find-cause/`, `scripts/` 아래 `journal-log.py`, `templates/` 아래 `problem.md`/`conclusion.md`를 추가.

(2) `## Runtime Artifact Model`의 target-project 트리에서 `.as-usual/` 아래 `issue/` 갈래 추가:

```text
    ├── issue/
    │   └── yyyy-MM-dd-<slug>/
    │       ├── problem.md       # 살아있는 현재 스냅샷 (resume 문서 겸함)
    │       ├── journal.jsonl    # append-only 추론 + lifecycle 로그
    │       ├── evidence/        # 선택: 조사 증거
    │       └── conclusion.md    # 종결 산출물
```

(3) 문서 끝의 `## Prompt And Template Map` 표 앞에 새 최상위 섹션 추가:

```markdown
## Find-Cause Workflow (Issue)

find-cause는 topic과 평행한 두 번째 작업 단위 `issue`다. 코드를 수정하지 않고
문제의 원인 또는 해결·개선 방향을 확정하는 것이 목적이며, 확정된
`conclusion.md`가 후속 coding topic의 입력이 된다.

| 구분 | coding | find-cause |
| --- | --- | --- |
| 작업 단위 | `.as-usual/topic/` | `.as-usual/issue/` |
| canonical 규칙 | `as-usual-rules/core-workflow.md` | `as-usual-rules/find-cause-workflow.md` |
| 헬퍼 | `scripts/topic-log.py` | `scripts/journal-log.py` |
| 종착점 | finalize + git action | `conclusion.md` (git action 없음) |

- phase 파이프라인이 없다. issue 상태(`open → concluded | cancelled`)는
  journal의 lifecycle 이벤트에서 파생한다.
- `journal.jsonl`은 append-only다. 확정 항목의 번복은 `status-change` +
  `cancelled` 이벤트를 append하고 현재 상태는 파생한다. entry status 어휘는
  `added | confirmed | cancelled`.
- 하드 게이트: journal append-only, 증거 없는 확정 금지, 재현 코드 사용자
  승인, high-risk 게이트 상속, 턴 종료 전 기록. 나머지 조사 방식은 자유.
- 상세 규칙: `as-usual-rules/find-cause-workflow.md`. 스킬:
  `skills/find-cause/SKILL.md`. 설계:
  `docs/design/2026-07-12-find-cause-workflow-design.md`.
```

(4) `## Prompt And Template Map` 표에 행 추가:

```markdown
| Find-cause workflow rules | `as-usual-rules/find-cause-workflow.md` |
| Find-cause skill | `skills/find-cause/SKILL.md` |
| Problem template | `templates/problem.md` |
| Conclusion template | `templates/conclusion.md` |
| Issue journal helper | `scripts/journal-log.py` |
```

- [ ] **Step 2: 검증**

Run: `cd /Users/happyhsryu/dev/personal/harness-as-usual && grep -c "find-cause\|journal-log\|issue/" docs/ARCHITECTURE-WORKFLOW.md`
Expected: 10 이상.

- [ ] **Step 3: Commit**

```bash
git add docs/ARCHITECTURE-WORKFLOW.md
git commit -m "docs: document find-cause issue workflow in architecture doc"
```

---

### Task 12: 최종 일관성 스윕

**Files:**
- Modify: 발견된 불일치 파일 (없을 수도 있음)

**Interfaces:**
- Consumes: Task 1–11 전체.
- Produces: 검증된 일관 상태.

- [ ] **Step 1: 전체 테스트**

Run: `cd /Users/happyhsryu/dev/personal/harness-as-usual && python3 -m unittest discover -s scripts/tests -v`
Expected: 전체 OK.

- [ ] **Step 2: 무수정 불변식 확인**

Run: `cd /Users/happyhsryu/dev/personal/harness-as-usual && git log --oneline -12 && git diff HEAD~11 --stat -- as-usual-rules/core-workflow.md scripts/topic-log.py scripts/as_usual_topic_log/`
Expected: `git diff --stat` 출력 없음 — coding 워크플로우 표면 무수정. (HEAD~11이 이 계획의 첫 커밋 이전을 가리키는지 `git log`로 먼저 확인하고 오프셋을 조정한다.)

- [ ] **Step 3: 어휘/계약 교차 확인** — 설계 문서·규칙·스킬·구현 간 어휘 불일치 grep:

Run: `cd /Users/happyhsryu/dev/personal/harness-as-usual && grep -rnE "cause-confirmed|finding-cause|hypotheses\.md|diagnosis\.md|[^-]cause\.md" as-usual-rules/find-cause-workflow.md skills/find-cause/ skills/using-as-usual/ skills/hand-off/ templates/problem.md templates/conclusion.md docs/ARCHITECTURE-WORKFLOW.md scripts/as_usual_journal_log/ || echo CLEAN`
Expected: `CLEAN` — 폐기된 초기 설계 어휘(`cause-confirmed` phase, `hypotheses.md`, `diagnosis.md`, `cause.md`)가 구현 표면에 없음.

Run: `cd /Users/happyhsryu/dev/personal/harness-as-usual && for cmd in init add confirm cancel approve conclude status view validate; do grep -q "add_parser(\"$cmd\"" scripts/as_usual_journal_log/cli.py || echo "MISSING CLI: $cmd"; done; for cmd in add confirm cancel approve conclude status view; do grep -q "$cmd" as-usual-rules/find-cause-workflow.md skills/find-cause/SKILL.md || echo "MISSING DOC: $cmd"; done; echo DONE`
Expected: `MISSING` 없이 `DONE`.

- [ ] **Step 4: E2E 시나리오 수동 확인** — 사례 1 흐름을 CLI로 재연:

Run:

```bash
cd /Users/happyhsryu/dev/personal/harness-as-usual && rm -rf /tmp/fc-e2e && \
python3 scripts/journal-log.py init --issue-dir /tmp/fc-e2e --initial-request "order API intermittent timeout" --actor claude && \
python3 scripts/journal-log.py add --issue-dir /tmp/fc-e2e --kind hypothesis --content "connection pool exhaustion" && \
python3 scripts/journal-log.py confirm --issue-dir /tmp/fc-e2e --target 2 --evidence "load test reproduced" && \
python3 scripts/journal-log.py add --issue-dir /tmp/fc-e2e --kind finding --content "pool was healthy in real logs; DNS cache expiry is the cause" --evidence "evidence/app.log" && \
python3 scripts/journal-log.py cancel --issue-dir /tmp/fc-e2e --target 2 --reason "contradicted by #4" && \
python3 scripts/journal-log.py add --issue-dir /tmp/fc-e2e --kind hypothesis --content "DNS cache expiry" && \
python3 scripts/journal-log.py confirm --issue-dir /tmp/fc-e2e --target 6 --evidence "TTL trace confirms" && \
python3 scripts/journal-log.py conclude --issue-dir /tmp/fc-e2e --summary "root cause: DNS cache expiry" --follow-up ".as-usual/topic/2026-07-12-fix-dns" && \
python3 scripts/journal-log.py validate --issue-dir /tmp/fc-e2e && \
python3 scripts/journal-log.py view --issue-dir /tmp/fc-e2e --md && \
rm -rf /tmp/fc-e2e
```

Expected: 모든 커맨드 성공, `validate` problems 빈 배열, `view --md` 출력에서 `## Confirmed`에 #6(DNS), `## Cancelled`에 #2(pool)가 보이고 Log 섹션에서 확정→번복 궤적이 시간순으로 읽힌다.

- [ ] **Step 5: 불일치 발견 시 수정 후 Commit**

```bash
git add -A -- as-usual-rules skills templates docs scripts
git commit -m "fix: align find-cause vocabulary across rules, skills, and docs"
```

(발견된 불일치가 없으면 이 커밋은 생략한다.)
