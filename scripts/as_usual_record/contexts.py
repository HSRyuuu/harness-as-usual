"""`contexts.md` skeleton creation.

The document opens with frontmatter (`unit`, `slug`, `created`) and continues in
three bands. `core-rules.md` §3 owns what each band means and how it may change;
this module only renders the skeleton and keeps the frontmatter in step with the
folder the record actually lives in.
"""

from __future__ import annotations

from pathlib import Path
import re

from .constants import CONTEXTS_FILE


CONTEXTS_FALLBACK = """---
unit: {unit}
slug: {slug}
created: {created}
---

# Context

## Initial Request

{initial_request}

## Boundary

### In Scope

_Not set._

### Out Of Scope

_Not set._

## Linked Work

_None._

---

## Decisions

_None yet._

---

## Q&A Log

_No questions raised yet._
"""

_PLACEHOLDER = re.compile(r"\{(initial_request|unit|slug|created)\}")

_FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)


def contexts_template() -> str:
    template_path = Path(__file__).resolve().parents[2] / "templates" / CONTEXTS_FILE
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return CONTEXTS_FALLBACK


def render_contexts(*, initial_request: str, unit: str, slug: str, created: str) -> str:
    values = {
        "initial_request": initial_request,
        "unit": unit,
        "slug": slug,
        "created": created,
    }
    # One pass, so a value that happens to contain `{slug}` is not substituted
    # again. The initial request is the user's verbatim text and may contain
    # anything.
    return _PLACEHOLDER.sub(lambda match: values[match.group(1)], contexts_template())


def read_declared_unit(work_dir: Path) -> str | None:
    """Return the unit `contexts.md` claims, or None when it claims none.

    Frontmatter is the authority: once a document has it, a leftover
    `## Work Unit` section below is stale text, not a second opinion. The
    section is read only when there is no frontmatter at all, which is how
    folders created before the format change still resolve.

    The reading counterpart of `update_frontmatter`, and deliberately built from
    the same two rules — a format read one way and written another is how the
    document and the record start disagreeing.
    """
    path = work_dir / CONTEXTS_FILE
    if not path.exists():
        return None
    body = path.read_text(encoding="utf-8")

    match = _FRONTMATTER.match(body)
    if match is not None:
        return _read_field(match.group(1), "unit")
    return _read_legacy_unit_section(body)


def _read_field(block: str, key: str) -> str | None:
    for line in block.split("\n"):
        name, separator, value = line.partition(":")
        if separator and name.strip() == key:
            return value.strip() or None
    return None


def _read_legacy_unit_section(body: str) -> str | None:
    """Mirror of `_update_legacy_unit_section`, in the reading direction."""
    lines = body.splitlines()
    for index, line in enumerate(lines):
        if line.strip() != "## Work Unit":
            continue
        for offset in range(index + 1, min(index + 5, len(lines))):
            if lines[offset].strip():
                return lines[offset].strip()
        return None
    return None


def update_frontmatter(work_dir: Path, *, unit: str, slug: str) -> None:
    """Rewrite `unit` and `slug` in the frontmatter after a move.

    Best effort: if the document has neither frontmatter nor the pre-frontmatter
    `## Work Unit` section, leave the file untouched rather than guessing where
    the values belong.
    """
    path = work_dir / CONTEXTS_FILE
    if not path.exists():
        return
    body = path.read_text(encoding="utf-8")

    match = _FRONTMATTER.match(body)
    if match is None:
        _update_legacy_unit_section(path, body, unit)
        return

    updated = _rewrite_fields(match.group(1), {"unit": unit, "slug": slug})
    path.write_text(body[: match.start(1)] + updated + body[match.end(1) :], encoding="utf-8")


def _rewrite_fields(block: str, values: dict[str, str]) -> str:
    lines = block.split("\n")
    for index, line in enumerate(lines):
        key = line.split(":", 1)[0].strip()
        if key in values:
            lines[index] = f"{key}: {values[key]}"
    return "\n".join(lines)


def _update_legacy_unit_section(path: Path, body: str, unit: str) -> None:
    """Update a `## Work Unit` section written before the frontmatter format.

    AsUsual shipped the section form, so work folders in other projects still
    use it. Without this, `move` would silently leave those documents claiming a
    unit the record no longer agrees with.
    """
    lines = body.splitlines()
    for index, line in enumerate(lines):
        if line.strip() != "## Work Unit":
            continue
        for offset in range(index + 1, min(index + 5, len(lines))):
            if lines[offset].strip():
                lines[offset] = unit
                path.write_text("\n".join(lines) + "\n", encoding="utf-8")
                return
        return
