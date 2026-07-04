"""Derived status calculation for topic-log audit events."""

from __future__ import annotations

from pathlib import Path

from .audit import audit_events
from .constants import ARTIFACT_FIELD_BY_FILE, LEGACY_NEXT_ACTION_ALIASES, LEGACY_PHASE_ALIASES, JsonObject
from .paths import audit_path, topic_md_path


def _record_artifact(status: JsonObject, artifact: str, artifact_name: str = "") -> None:
    artifacts = status["artifacts"]
    field = artifact_name or ARTIFACT_FIELD_BY_FILE.get(artifact, "")
    if field == "question" or artifact.startswith("question-c"):
        questions = artifacts["questions"]
        if artifact not in questions:
            questions.append(artifact)
        return
    if field in {"requirements", "plan", "codeReviewReport", "report", "topic", "audit"}:
        artifacts[field] = artifact


def derive_status(topic: Path) -> JsonObject:
    events = audit_events(topic)
    status: JsonObject = {
        "topic": topic.name,
        "status": "active",
        "phase": "",
        "nextAction": "",
        "lastEventSeq": 0,
        "lastEvent": "",
        "artifacts": {
            "questions": [],
            "requirements": None,
            "plan": None,
            "codeReviewReport": None,
            "report": None,
            "topic": "topic.md" if topic_md_path(topic).exists() else None,
            "audit": "audit.jsonl" if audit_path(topic).exists() else None,
        },
        "blockers": [],
        "openItems": [],
        "approvals": [],
        "verification": [],
        "review": None,
        "tasks": {},
        "taskFindings": [],
        "sweeps": [],
    }
    blockers: dict[str, JsonObject] = {}
    task_findings: dict[str, JsonObject] = {}
    for event in events:
        if event.get("status") == "error":
            continue
        seq = event.get("seq")
        name = event.get("event")
        data = event.get("data") if isinstance(event.get("data"), dict) else {}
        if name == "topic.created" and data.get("topic"):
            status["topic"] = data["topic"]
        if isinstance(seq, int):
            status["lastEventSeq"] = seq
        if name:
            status["lastEvent"] = name
        if event.get("phase"):
            status["phase"] = LEGACY_PHASE_ALIASES.get(event["phase"], event["phase"])
        if event.get("nextAction"):
            status["nextAction"] = LEGACY_NEXT_ACTION_ALIASES.get(event["nextAction"], event["nextAction"])
        if name == "topic.finalized":
            status["status"] = data.get("status", "complete")
        for artifact in event.get("artifacts") or []:
            if isinstance(artifact, str):
                _record_artifact(status, artifact)
        if name == "artifact.recorded" and data.get("artifactName") and data.get("artifactValue"):
            _record_artifact(status, data["artifactValue"], data["artifactName"])
        if name == "blocker.recorded":
            blocker_id = data.get("id") or event.get("summary") or str(seq)
            blockers[blocker_id] = {"id": blocker_id, "summary": event.get("summary"), "data": data}
        elif name == "blocker.resolved":
            blocker_id = data.get("id") or event.get("summary")
            if blocker_id in blockers:
                blockers.pop(blocker_id)
        elif str(name).startswith("approval."):
            status["approvals"].append(event)
        elif name == "verification.recorded":
            status["verification"].append(event)
        elif name == "task.completed":
            if data.get("verification"):
                status["verification"].append(data)
            if data.get("task"):
                task = status["tasks"].setdefault(
                    data["task"],
                    {"dispatches": [], "reviews": [], "fixes": [], "commits": []},
                )
                task["completed"] = data
        elif name == "task.dispatched" and data.get("task"):
            task = status["tasks"].setdefault(
                data["task"],
                {"dispatches": [], "reviews": [], "fixes": [], "commits": []},
            )
            task["mode"] = data.get("mode") or task.get("mode")
            task["dispatches"].append(data)
        elif name == "task.review_completed" and data.get("task"):
            task = status["tasks"].setdefault(
                data["task"],
                {"dispatches": [], "reviews": [], "fixes": [], "commits": []},
            )
            task["reviews"].append(data)
            if data.get("status") in {"findings", "blocked"}:
                for finding_id in data.get("findingIds") or []:
                    task_findings[finding_id] = {
                        "id": finding_id,
                        "task": data.get("task"),
                        "reviewType": data.get("reviewType"),
                        "status": data.get("status"),
                        "critical": data.get("critical"),
                        "important": data.get("important"),
                        "minor": data.get("minor"),
                        "summary": event.get("summary"),
                    }
        elif name in {"task.fix_requested", "task.fix_completed"} and data.get("task"):
            task = status["tasks"].setdefault(
                data["task"],
                {"dispatches": [], "reviews": [], "fixes": [], "commits": []},
            )
            task["fixes"].append(data)
            if name == "task.fix_completed" and data.get("findingId") in task_findings:
                task_findings.pop(data["findingId"])
        elif name == "task.commit_recorded" and data.get("task"):
            task = status["tasks"].setdefault(
                data["task"],
                {"dispatches": [], "reviews": [], "fixes": [], "commits": []},
            )
            task["commits"].append(data)
        elif name == "sweep.completed":
            status["sweeps"].append(data)
        elif name == "review.completed":
            status["review"] = data
    status["blockers"] = list(blockers.values())
    status["taskFindings"] = list(task_findings.values())
    if status["blockers"] and status["status"] == "active":
        status["status"] = "blocked"
    return status
