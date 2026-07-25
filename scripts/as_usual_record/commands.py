"""Command implementations for the AsUsual record helper."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from .constants import (
    AUDIT_FILE,
    CONTEXTS_FILE,
    MOVE_TARGETS,
    SCHEMA_VERSION,
    JsonObject,
)
from .contexts import render_contexts, update_unit_line
from .gates import (
    check_kind_payload,
    check_move_allowed,
    check_not_closed,
    validate_vocabulary,
)
from .paths import (
    RecordError,
    as_usual_root,
    audit_path,
    contexts_path,
    require_existing_dir,
    resolve_dir,
)
from .records import append_entry, build_entry, current_unit, read_events
from .status import derive_status
from .validation import validate_record


def _collect_data(args: argparse.Namespace) -> JsonObject:
    data: JsonObject = {}
    for field in ("event", "verdict", "action", "to", "evidence", "reason"):
        value = getattr(args, field, None)
        if value:
            data[field] = value
    for field in ("target", "resolves"):
        value = getattr(args, field, None)
        if value is not None:
            data[field] = value
    for pair in getattr(args, "data", None) or []:
        if "=" not in pair:
            raise RecordError(f"--data expects key=value, got: {pair}")
        key, value = pair.split("=", 1)
        key = key.strip()
        if not key:
            raise RecordError(f"--data expects a non-empty key, got: {pair}")
        data[key] = value
    return data


def cmd_init(args: argparse.Namespace) -> int:
    work_dir = resolve_dir(args.dir)
    if audit_path(work_dir).exists():
        raise RecordError(f"record already exists: {audit_path(work_dir)}")

    validate_vocabulary(
        unit=args.unit,
        kind="lifecycle",
        actor=args.actor,
        status="success",
        phase="gathering-context",
        next_action="",
    )

    work_dir.mkdir(parents=True, exist_ok=True)
    audit_path(work_dir).touch()

    entry = build_entry(
        [],
        unit=args.unit,
        kind="lifecycle",
        actor=args.actor,
        summary=f"{args.unit} created: {work_dir.name}",
        phase="gathering-context",
        next_action="gathering-context",
        data={
            "event": "created",
            "initialRequest": args.request,
            "schemaVersion": SCHEMA_VERSION,
        },
    )
    append_entry(work_dir, entry)

    if not contexts_path(work_dir).exists():
        contexts_path(work_dir).write_text(
            render_contexts(initial_request=args.request, unit=args.unit),
            encoding="utf-8",
        )

    print(f"initialized {args.unit} at {work_dir}")
    print(f"  {CONTEXTS_FILE}")
    print(f"  {AUDIT_FILE}")
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    work_dir = require_existing_dir(args.dir)
    events = read_events(work_dir)
    unit = current_unit(events)
    data = _collect_data(args)

    validate_vocabulary(
        unit=unit,
        kind=args.kind,
        actor=args.actor,
        status=args.status,
        phase=args.phase or "",
        next_action=args.next_action or "",
    )
    check_not_closed(events, args.kind, data)
    check_kind_payload(work_dir, events, unit=unit, kind=args.kind, data=data)

    entry = build_entry(
        events,
        unit=unit,
        kind=args.kind,
        actor=args.actor,
        summary=args.summary,
        status=args.status,
        phase=args.phase or "",
        next_action=args.next_action or "",
        data=data,
    )
    append_entry(work_dir, entry)
    print(f"seq {entry['seq']}  {args.kind}  {args.summary}")
    return 0


def cmd_move(args: argparse.Namespace) -> int:
    work_dir = require_existing_dir(args.dir)
    events = read_events(work_dir)
    unit = current_unit(events)

    if args.to not in MOVE_TARGETS:
        raise RecordError(
            f"invalid move target: {args.to}. allowed: {', '.join(sorted(MOVE_TARGETS))}"
        )
    check_not_closed(events, "lifecycle", {"event": "unit-selected"})
    check_move_allowed(work_dir)

    slug = args.slug or work_dir.name
    target_dir = as_usual_root(work_dir) / args.to / slug
    if target_dir == work_dir:
        raise RecordError(f"already at {target_dir}")
    if target_dir.exists():
        raise RecordError(f"target already exists: {target_dir}")

    validate_vocabulary(
        unit=args.to,
        kind="lifecycle",
        actor=args.actor,
        status="success",
        phase="",
        next_action="",
    )

    source = str(work_dir)
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(source, str(target_dir))

    entry = build_entry(
        read_events(target_dir),
        unit=args.to,
        kind="lifecycle",
        actor=args.actor,
        summary=f"unit selected: {unit} -> {args.to}",
        data={"event": "unit-selected", "from": source, "to": str(target_dir)},
    )
    append_entry(target_dir, entry)
    update_unit_line(target_dir, args.to)

    print(f"moved to {target_dir}")
    return 0


def cmd_link(args: argparse.Namespace) -> int:
    work_dir = require_existing_dir(args.dir)
    other_dir = require_existing_dir(args.to_dir)
    if work_dir == other_dir:
        raise RecordError("cannot link a work unit to itself")

    for source, target in ((work_dir, other_dir), (other_dir, work_dir)):
        events = read_events(source)
        entry = build_entry(
            events,
            unit=current_unit(events),
            kind="lifecycle",
            actor=args.actor,
            summary=args.summary or f"linked to {target}",
            data={"event": "linked", "to": str(target)},
        )
        append_entry(source, entry)

    print(f"linked {work_dir} <-> {other_dir}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    work_dir = require_existing_dir(args.dir)
    status = derive_status(work_dir)
    if args.json:
        print(json.dumps(status, ensure_ascii=False, indent=2))
        return 0
    print(f"dir        {status['dir']}")
    print(f"unit       {status['unit']}")
    print(f"state      {status['state']}")
    print(f"phase      {status['phase']}")
    print(f"nextAction {status['nextAction']}")
    print(f"events     {status['eventCount']}")
    if status["blockers"]:
        print(f"blockers   {len(status['blockers'])} open")
    if status["verification"]:
        print(f"verified   {status['verification']['verdict']}")
    if status["links"]:
        for link in status["links"]:
            print(f"linked     {link}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    work_dir = require_existing_dir(args.dir)
    problems = validate_record(work_dir)
    if problems:
        for problem in problems:
            print(f"invalid: {problem}")
        return 1
    print(f"valid: {work_dir}")
    return 0


def resolve_lock_dir(args: argparse.Namespace) -> Path:
    return resolve_dir(args.dir)
