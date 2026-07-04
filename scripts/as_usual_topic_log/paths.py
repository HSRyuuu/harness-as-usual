"""Path helpers and locking for topic-log artifacts."""

from __future__ import annotations

from contextlib import contextmanager
import fcntl
import hashlib
from pathlib import Path
import tempfile


def topic_dir(value: str) -> Path:
    path = Path(value).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def resolve_topic_dir(value: str) -> Path:
    return Path(value).expanduser().resolve()


def require_existing_topic_dir(value: str) -> Path:
    topic = resolve_topic_dir(value)
    if not topic_md_path(topic).exists():
        raise SystemExit(f"Missing required file: {topic_md_path(topic)}")
    if not audit_path(topic).exists():
        raise SystemExit(f"Missing required file: {audit_path(topic)}")
    return topic


def topic_md_path(topic: Path) -> Path:
    return topic / "topic.md"


def audit_path(topic: Path) -> Path:
    return topic / "audit.jsonl"


@contextmanager
def topic_lock(topic: Path):
    digest = hashlib.sha256(str(topic).encode("utf-8")).hexdigest()
    lock_path = Path(tempfile.gettempdir()) / f"as-usual-topic-log-{digest}.lock"
    with lock_path.open("w", encoding="utf-8") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)
