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


@pytest.fixture
def as_usual(tmp_path: Path) -> Path:
    """An empty `.as-usual` root so move targets resolve like the real layout."""
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
def make_unit(as_usual: Path, run):
    """Initialize a work folder for a unit and return its path."""

    def _make(unit: str, slug: str = "2026-07-25-sample", request: str = "sample request") -> Path:
        work_dir = as_usual / unit / slug
        assert (
            run(
                "init",
                "--dir",
                str(work_dir),
                "--unit",
                unit,
                "--request",
                request,
                "--actor",
                "claude",
            )
            == 0
        )
        return work_dir

    return _make
