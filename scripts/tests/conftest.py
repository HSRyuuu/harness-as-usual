"""Shared fixtures for record-helper tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from as_usual_record.cli import main  # noqa: E402
from as_usual_record.constants import SCHEMA_VERSION  # noqa: E402
from as_usual_record.contexts import render_contexts  # noqa: E402


@pytest.fixture
def as_usual(tmp_path: Path) -> Path:
    """An empty `.as-usual` root so recorded paths resolve like the real layout."""
    root = tmp_path / ".as-usual"
    root.mkdir()
    return root


@pytest.fixture
def run():
    def _run(*argv: str) -> int:
        return main(list(argv))

    return _run


@pytest.fixture
def events():
    def _events(work_dir: Path) -> list[dict]:
        lines = (work_dir / "audit.jsonl").read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in lines if line.strip()]

    return _events


@pytest.fixture
def make_work(as_usual: Path, run):
    """Initialize a work folder the way `init` does today and return its path."""

    def _make(slug: str = "2026-07-25-sample", request: str = "sample request") -> Path:
        work_dir = as_usual / "work" / slug
        assert (
            run("init", "--dir", str(work_dir), "--request", request, "--actor", "claude") == 0
        )
        return work_dir

    return _make


@pytest.fixture
def make_legacy(as_usual: Path):
    """Hand-write a record the way pre-2.0 `init --unit <unit>` left it.

    `init` no longer creates these units, but their folders stay resumable.
    """

    def _make(unit: str, slug: str = "2026-07-25-legacy", request: str = "legacy request") -> Path:
        work_dir = as_usual / unit / slug
        work_dir.mkdir(parents=True)
        created = {
            "seq": 1,
            "ts": "2026-07-25T10:00:00+09:00",
            "actor": "claude",
            "unit": unit,
            "kind": "lifecycle",
            "status": "success",
            "summary": f"{unit} created: {slug}",
            "phase": "gathering-context",
            "nextAction": "gathering-context",
            "data": {
                "event": "created",
                "initialRequest": request,
                "schemaVersion": SCHEMA_VERSION,
            },
        }
        (work_dir / "audit.jsonl").write_text(json.dumps(created) + "\n", encoding="utf-8")
        (work_dir / "contexts.md").write_text(
            render_contexts(initial_request=request, unit=unit, slug=slug, created="2026-07-25"),
            encoding="utf-8",
        )
        return work_dir

    return _make


@pytest.fixture
def approve_execution(run):
    """Satisfy rule 7 and record the user's execution approval.

    Finalizing is a completion claim only once execution was approved, so most
    closing tests start here.
    """

    def _approve(work_dir: Path) -> None:
        (work_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")
        args = ("add", "--dir", str(work_dir))
        assert run(*args, "--kind", "review", "--phase", "write-plan",
                   "--summary", "plan reviewed") == 0
        assert run(*args, "--kind", "approval", "--action", "execution", "--actor", "user",
                   "--summary", "user said go") == 0

    return _approve
