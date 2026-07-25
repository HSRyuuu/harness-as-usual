"""`contexts.md` skeleton creation.

The document has three bands with different mutability rules:
top is near-fixed, middle is freely updatable, bottom is append-only.
"""

from __future__ import annotations

from pathlib import Path

from .constants import CONTEXTS_FILE


CONTEXTS_FALLBACK = """# Context

<!-- Top band: near-fixed. Middle band: update freely. Bottom band: append-only. -->

## Initial Request

{initial_request}

## Work Unit

{unit}

## Boundary

### In Scope

(What this work covers.)

### Out Of Scope

(What it deliberately does not cover.)

## Artifacts

(Links to requirements.md / plan.md / review.md / report.md / conclusion.md as they appear.)

## Linked Work

(Paths of other work units linked to this one, and why.)

---

## Decisions

(Decisions agreed with the user. Update freely: when a later decision reverses an
earlier one, edit the earlier entry so this section always reads as the current
agreement. The append-only record keeps the history.)

---

## Q&A Log

(Append-only. Questions raised after the gathering stage and the answers given.
Never edit or remove an existing entry.)
"""


def contexts_template() -> str:
    template_path = Path(__file__).resolve().parents[2] / "templates" / CONTEXTS_FILE
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return CONTEXTS_FALLBACK


def render_contexts(*, initial_request: str, unit: str) -> str:
    return (
        contexts_template()
        .replace("{initial_request}", initial_request)
        .replace("{unit}", unit)
    )


def update_unit_line(work_dir: Path, unit: str) -> None:
    """Rewrite the `## Work Unit` value after a move.

    Best effort: if the section is missing (the user restructured the document),
    leave the file untouched rather than guessing where the value belongs.
    """
    path = work_dir / CONTEXTS_FILE
    if not path.exists():
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if line.strip() != "## Work Unit":
            continue
        for offset in range(index + 1, min(index + 5, len(lines))):
            if lines[offset].strip():
                lines[offset] = unit
                path.write_text("\n".join(lines) + "\n", encoding="utf-8")
                return
        return
