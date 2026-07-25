"""Path helpers and locking for AsUsual work-unit records."""

from __future__ import annotations

from contextlib import contextmanager
import fcntl
import hashlib
from pathlib import Path
import tempfile

from .constants import AUDIT_FILE, CONTEXTS_FILE


class RecordError(ValueError):
    """Raised for invalid record operations."""


def resolve_dir(value: str) -> Path:
    return Path(value).expanduser().resolve()


def audit_path(work_dir: Path) -> Path:
    return work_dir / AUDIT_FILE


def contexts_path(work_dir: Path) -> Path:
    return work_dir / CONTEXTS_FILE


def require_existing_dir(value: str) -> Path:
    work_dir = resolve_dir(value)
    if not audit_path(work_dir).exists():
        raise RecordError(f"missing required file: {audit_path(work_dir)}")
    if not contexts_path(work_dir).exists():
        raise RecordError(f"missing required file: {contexts_path(work_dir)}")
    return work_dir


def as_usual_root(work_dir: Path) -> Path:
    """Return the `.as-usual` directory that contains this work folder.

    A work folder always lives at `.as-usual/<unit>/<slug>/`, so the root is two
    levels up. Falling back to the parent keeps non-standard layouts usable
    instead of crashing.
    """
    parent = work_dir.parent
    if parent.parent.name == ".as-usual" or parent.name in {
        "inbox",
        "topic",
        "direct-work",
        "issue",
    }:
        return parent.parent
    return parent


@contextmanager
def work_lock(work_dir: Path):
    digest = hashlib.sha256(str(work_dir).encode("utf-8")).hexdigest()
    lock_path = Path(tempfile.gettempdir()) / f"as-usual-record-{digest}.lock"
    with lock_path.open("w", encoding="utf-8") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)
