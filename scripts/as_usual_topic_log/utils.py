"""Small shared helpers for topic-log."""

from __future__ import annotations


def split_csv(value: str) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]
