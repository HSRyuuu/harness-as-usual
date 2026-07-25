#!/usr/bin/env python3
"""Lint AsUsual sandbox E2E report artifacts.

The runner produces raw logs. This linter turns those logs into segmented,
machine-readable evidence so report PASS means more than "Codex exited 0".
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
TOPIC_LOG = ROOT / "scripts/topic-log.py"

SEGMENTS = (
    "workflowResult",
    "artifactIntegrity",
    "evidenceIntegrity",
    "environmentCleanliness",
)


def read_text(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8", errors="replace")
    return ""


def parse_json(path: Path) -> tuple[dict[str, Any], str | None]:
    text = read_text(path)
    if not text.strip():
        return {}, f"missing or empty JSON file: {path}"
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        return {}, f"invalid JSON in {path}: {exc}"
    if not isinstance(value, dict):
        return {}, f"JSON root must be an object: {path}"
    return value, None


def parse_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(read_text(path).splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"invalid JSONL in {path}:{line_number}: {exc}")
            continue
        if not isinstance(value, dict):
            errors.append(f"JSONL line must be an object: {path}:{line_number}")
            continue
        events.append(value)
    return events, errors


def new_result() -> dict[str, Any]:
    return {
        "segments": {segment: "PASS" for segment in SEGMENTS},
        "overallResult": "PASS",
        "checks": [],
        "warnings": [],
        "changedFiles": {
            "baseline": [],
            "after": [],
            "agentProduced": [],
            "untracked": [],
        },
        "commandFailures": {
            "fatal": [],
            "nonBlocking": [],
            "expected": [],
        },
        "markdown": {},
    }


def add_check(result: dict[str, Any], check_id: str, segment: str, status: str, message: str) -> None:
    result["checks"].append(
        {"id": check_id, "segment": segment, "status": status, "message": message}
    )
    if status == "FAIL":
        result["segments"][segment] = "FAIL"
    elif status == "WARNING" and result["segments"][segment] == "PASS":
        result["segments"][segment] = "WARNING"


def status_paths(status_text: str) -> list[str]:
    paths: list[str] = []
    for line in status_text.splitlines():
        if not line.strip():
            continue
        marker = line[:2]
        path = line[3:].strip() if len(line) > 3 else ""
        if marker == "??" and path:
            paths.append(path)
        elif marker and path:
            paths.append(path)
    return paths


def lint_environment(report_dir: Path, result: dict[str, Any], allow_dirty_baseline: bool) -> None:
    artifacts = report_dir / "logs/artifacts"
    before_text = read_text(artifacts / "sandbox-status-before.txt")
    after_text = read_text(artifacts / "sandbox-status-after.txt")
    baseline = status_paths(before_text)
    after = status_paths(after_text)
    untracked = [
        line[3:].strip()
        for line in after_text.splitlines()
        if line.startswith("?? ") and line[3:].strip()
    ]
    result["changedFiles"]["baseline"] = baseline
    result["changedFiles"]["after"] = after
    result["changedFiles"]["untracked"] = untracked
    result["changedFiles"]["agentProduced"] = [path for path in after if path not in baseline]
    if baseline and not allow_dirty_baseline:
        add_check(
            result,
            "sandbox.clean.start",
            "environmentCleanliness",
            "FAIL",
            "Sandbox started dirty: " + ", ".join(baseline),
        )
        return
    if baseline and allow_dirty_baseline:
        add_check(
            result,
            "sandbox.clean.start",
            "environmentCleanliness",
            "WARNING",
            "Sandbox started dirty but dirty baseline was explicitly allowed: " + ", ".join(baseline),
        )
        return
    add_check(
        result,
        "sandbox.clean.start",
        "environmentCleanliness",
        "PASS",
        "Sandbox started with no tracked or untracked changes.",
    )


def lint_artifacts(report_dir: Path, result: dict[str, Any]) -> None:
    topic_dir = report_dir / "logs/artifacts/copied-topic-files"
    audit_events, audit_errors = parse_jsonl(topic_dir / "audit.jsonl")
    topic_text = read_text(topic_dir / "topic.md")

    if not topic_text.strip():
        add_check(result, "topic.present", "artifactIntegrity", "FAIL", "topic.md is missing or empty.")
        return
    add_check(result, "topic.present", "artifactIntegrity", "PASS", "topic.md exists.")

    if audit_errors:
        add_check(
            result,
            "audit.parse",
            "artifactIntegrity",
            "FAIL",
            "; ".join(audit_errors),
        )
        return
    add_check(result, "audit.parse", "artifactIntegrity", "PASS", f"{len(audit_events)} audit events parsed.")

    lint_runtime_metadata(audit_events, result)
    lint_safety_gate_sync(audit_events, result)
    lint_audit_actor_consistency(audit_events, result)
    lint_audit_sequence(audit_events, result)

    status, status_error = derive_topic_status(topic_dir)
    if status_error:
        add_check(result, "topic.status", "artifactIntegrity", "FAIL", status_error)
        return
    add_check(result, "topic.status", "artifactIntegrity", "PASS", "topic-log.py status --json derived topic status.")
    lint_review_mode(status, result)


def derive_topic_status(topic_dir: Path) -> tuple[dict[str, Any], str | None]:
    if not TOPIC_LOG.exists():
        return {}, f"missing helper: {TOPIC_LOG}"
    completed = subprocess.run(
        [sys.executable, str(TOPIC_LOG), "status", "--topic-dir", str(topic_dir), "--json"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if completed.returncode != 0:
        return {}, (completed.stderr or completed.stdout).strip()
    try:
        value = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        return {}, f"invalid topic-log status JSON: {exc}"
    if not isinstance(value, dict):
        return {}, "topic-log status JSON root must be an object."
    return value, None


def lint_runtime_metadata(audit_events: list[dict[str, Any]], result: dict[str, Any]) -> None:
    topic_created = next((event for event in audit_events if event.get("event") == "topic.created"), {})
    data = topic_created.get("data") if isinstance(topic_created, dict) else {}
    host = data.get("runtimeHost") if isinstance(data, dict) else ""
    if host not in {"codex", "claude"}:
        add_check(
            result,
            "runtime.host.present",
            "artifactIntegrity",
            "WARNING",
            "topic.created data.runtimeHost is missing or not one of codex, claude.",
        )
        return
    add_check(
        result,
        "runtime.host.present",
        "artifactIntegrity",
        "PASS",
        f"topic.created data.runtimeHost recorded as {host}.",
    )


def lint_safety_gate_sync(
    audit_events: list[dict[str, Any]], result: dict[str, Any]
) -> None:
    audit_names = {str(event.get("event", "")) for event in audit_events}
    execution_approved = "approval.execution" in audit_names
    if not execution_approved:
        add_check(
            result,
            "approval.execution.present",
            "artifactIntegrity",
            "FAIL",
            "audit.jsonl does not contain approval.execution before execution.",
        )
    else:
        add_check(
            result,
            "approval.execution.present",
            "artifactIntegrity",
            "PASS",
            "audit.jsonl contains approval.execution.",
        )

    high_risk_approvals = [event for event in audit_events if event.get("event") == "approval.high_risk"]
    invalid_high_risk = [
        event
        for event in high_risk_approvals
        if not isinstance(event.get("data"), dict)
        or not event["data"].get("operationId")
        or not event["data"].get("approvedBy")
        or not event["data"].get("rollback")
    ]
    if invalid_high_risk:
        add_check(
            result,
            "approval.high_risk.structured",
            "artifactIntegrity",
            "FAIL",
            "approval.high_risk events must include operationId, approvedBy, and rollback.",
        )
    else:
        add_check(
            result,
            "approval.high_risk.structured",
            "artifactIntegrity",
            "PASS",
            "high-risk approval events are structured.",
        )


def lint_audit_actor_consistency(audit_events: list[dict[str, Any]], result: dict[str, Any]) -> None:
    actors = sorted({str(event.get("actor", "")) for event in audit_events if event.get("actor")})
    # "agent" is a known token, so it passes the enum gate and is flagged below
    # as a consistency violation (generic instead of host-specific codex/claude).
    allowed = {"codex", "claude", "user", "system", "agent"}
    invalid = [actor for actor in actors if actor not in allowed]
    if invalid:
        add_check(
            result,
            "audit.actor.enum",
            "artifactIntegrity",
            "FAIL",
            "audit actor contains invalid values: " + ", ".join(invalid),
        )
        return
    if len([actor for actor in actors if actor in {"codex", "claude"}]) > 1:
        add_check(
            result,
            "audit.actor.consistent",
            "artifactIntegrity",
            "FAIL",
            "audit events mix multiple host actors: " + ", ".join(actors),
        )
        return
    if "agent" in actors:
        add_check(
            result,
            "audit.actor.consistent",
            "artifactIntegrity",
            "FAIL",
            "audit actor uses generic 'agent' instead of host actor codex or claude.",
        )
        return
    add_check(
        result,
        "audit.actor.consistent",
        "artifactIntegrity",
        "PASS",
        "audit actor values are host-specific and consistent.",
    )


def lint_audit_sequence(audit_events: list[dict[str, Any]], result: dict[str, Any]) -> None:
    seq_values = [event.get("seq") for event in audit_events]
    if any(not isinstance(seq, int) for seq in seq_values):
        add_check(
            result,
            "audit.seq.present",
            "artifactIntegrity",
            "WARNING",
            "audit events do not all include integer seq values.",
        )
        return
    expected = list(range(1, len(seq_values) + 1))
    if seq_values != expected:
        add_check(
            result,
            "audit.seq.present",
            "artifactIntegrity",
            "FAIL",
            f"audit seq values are {seq_values}; expected {expected}.",
        )
        return
    add_check(result, "audit.seq.present", "artifactIntegrity", "PASS", "audit seq values are monotonic.")


def lint_review_mode(status: dict[str, Any], result: dict[str, Any]) -> None:
    execution_review = status.get("review", {})
    mode = execution_review.get("mode") if isinstance(execution_review, dict) else ""
    allowed = {"independent", "self", "local-prompt"}
    if mode not in allowed:
        add_check(
            result,
            "review.execution.mode",
            "artifactIntegrity",
            "WARNING",
            "execution review mode is missing or not one of independent, self, local-prompt.",
        )
        return
    add_check(
        result,
        "review.execution.mode",
        "artifactIntegrity",
        "PASS",
        f"execution review mode recorded as {mode}.",
    )


def collect_codex_command_events(report_dir: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    codex_dir = report_dir / "logs/codex"
    for path in sorted(codex_dir.glob("*-events.jsonl")):
        for line in read_text(path).splitlines():
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            item = event.get("item") if isinstance(event, dict) else None
            if (
                event.get("type") == "item.completed"
                and isinstance(item, dict)
                and item.get("type") == "command_execution"
            ):
                events.append(
                    {
                        "provider": "codex",
                        "path": str(path),
                        "id": str(item.get("id", "")),
                        "command": str(item.get("command", "")),
                        "exit_code": item.get("exit_code"),
                        "output": str(item.get("aggregated_output", "")),
                    }
                )
    return events


def iter_claude_content_blocks(event: dict[str, Any]) -> list[dict[str, Any]]:
    message = event.get("message")
    if not isinstance(message, dict):
        return []
    content = message.get("content")
    if not isinstance(content, list):
        return []
    return [block for block in content if isinstance(block, dict)]


def infer_claude_exit_code(block: dict[str, Any]) -> int:
    if block.get("is_error") is True:
        return 1
    return 0


def collect_claude_command_events(report_dir: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    claude_dir = report_dir / "logs/claude"
    for path in sorted(claude_dir.glob("*-events.jsonl")):
        pending: dict[str, dict[str, str]] = {}
        for line in read_text(path).splitlines():
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict):
                continue
            for block in iter_claude_content_blocks(event):
                block_type = block.get("type")
                if block_type == "tool_use" and block.get("name") == "Bash":
                    tool_input = block.get("input")
                    command = ""
                    if isinstance(tool_input, dict):
                        command = str(tool_input.get("command", ""))
                    pending[str(block.get("id", ""))] = {
                        "command": command,
                    }
                elif block_type == "tool_result":
                    tool_id = str(block.get("tool_use_id", ""))
                    command_info = pending.get(tool_id)
                    if not command_info:
                        continue
                    events.append(
                        {
                            "provider": "claude",
                            "path": str(path),
                            "id": tool_id,
                            "command": command_info.get("command", ""),
                            "exit_code": infer_claude_exit_code(block),
                            "output": str(block.get("content", "")),
                        }
                    )
    return events


def collect_command_events(report_dir: Path) -> list[dict[str, Any]]:
    return collect_codex_command_events(report_dir) + collect_claude_command_events(report_dir)


def is_expected_no_match_search(event: dict[str, Any]) -> bool:
    command = event.get("command", "")
    output = event.get("output", "")
    return (
        event.get("exit_code") == 1
        and "rg " in command
        and not output.strip()
    )


def is_failed_command_event(event: dict[str, Any]) -> bool:
    exit_code = event.get("exit_code")
    if exit_code in (0, None):
        return False
    if is_expected_no_match_search(event):
        return False
    return True


def summarize_command_event(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": event.get("path", ""),
        "id": event.get("id", ""),
        "exitCode": event.get("exit_code"),
        "command": str(event.get("command", ""))[:500],
        "output": str(event.get("output", "")).strip()[:500],
    }


def is_final_verification_claim(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    lowered = value.lower()
    has_final_label = "final command:" in lowered or "final verification" in lowered
    has_expected_command = "mvn test" in lowered and "npm run build" in lowered
    return has_final_label and has_expected_command


def claim_says_success(value: str) -> bool:
    lowered = value.lower()
    return (
        "exit 0" in lowered
        or " passed" in lowered
        or "build success" in lowered
        or "succeeded" in lowered
        or "completed successfully" in lowered
    )


def summarize_stderr(report_dir: Path) -> dict[str, list[str]]:
    summary = {
        "skillTelemetryWarnings": [],
        "unrelatedManifestWarnings": [],
        "otherWarnings": [],
    }
    for path in sorted((report_dir / "logs/codex").glob("*-stderr.log")):
        for line in read_text(path).splitlines():
            if "codex.skill.injected" in line:
                summary["skillTelemetryWarnings"].append(f"{path.name}: {line}")
            elif "codex_core_plugins::manifest" in line:
                summary["unrelatedManifestWarnings"].append(f"{path.name}: {line}")
            elif "WARN" in line or "ERROR" in line:
                summary["otherWarnings"].append(f"{path.name}: {line}")
    for path in sorted((report_dir / "logs/claude").glob("*-stderr.log")):
        for line in read_text(path).splitlines():
            if "WARN" in line or "ERROR" in line:
                summary["otherWarnings"].append(f"{path.name}: {line}")
    return summary


def collect_failed_claude_preflights(report_dir: Path) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for path in sorted((report_dir / "logs/terminal").glob("*claude-preflight.log")):
        text = read_text(path)
        if not text.strip():
            continue
        exit_code = None
        for line in text.splitlines():
            if line.startswith("exit_code: "):
                try:
                    exit_code = int(line.split(": ", 1)[1])
                except ValueError:
                    exit_code = -1
        if exit_code in (0, None):
            continue
        output = ""
        if "--- output ---" in text:
            output = text.split("--- output ---", 1)[1].split("--- result ---", 1)[0].strip()
        failures.append(
            {
                "path": str(path),
                "exitCode": exit_code,
                "output": output,
            }
        )
    return failures


def lint_workflow(report_dir: Path, result: dict[str, Any]) -> None:
    preflight_failures = collect_failed_claude_preflights(report_dir)
    if preflight_failures:
        first = preflight_failures[0]
        add_check(
            result,
            "workflow.claude_preflight",
            "workflowResult",
            "FAIL",
            f"Claude preflight failed before sandbox reset: {first.get('output', '')[:500]}",
        )
        return

    command_events = collect_command_events(report_dir)
    expected = [event for event in command_events if is_expected_no_match_search(event)]
    command_failures = [event for event in command_events if is_failed_command_event(event)]
    result["commandFailures"]["expected"] = [summarize_command_event(event) for event in expected]
    summarized_command_failures = [summarize_command_event(event) for event in command_failures]
    result["commandFailures"]["nonBlocking"] = summarized_command_failures
    # Backward-compatible alias for older report consumers. These failures are no longer
    # overall-fatal when the user task reaches final verification/finalization.
    result["commandFailures"]["fatal"] = summarized_command_failures

    topic_dir = report_dir / "logs/artifacts/copied-topic-files"
    status, status_error = derive_topic_status(topic_dir)
    if status_error:
        add_check(result, "workflow.finalized", "workflowResult", "FAIL", status_error)
        return

    finalized = status.get("phase") == "finalized" and status.get("nextAction") == "git-action-decision"
    if not finalized:
        add_check(
            result,
            "workflow.finalized",
            "workflowResult",
            "FAIL",
            "Topic did not reach finalized phase with git-action-decision next action.",
        )
        return

    add_check(
        result,
        "workflow.agent_steps",
        "workflowResult",
        "PASS",
        "Agent steps reached finalized topic state.",
    )

    if command_failures:
        expected_text = (
            f"; {len(expected)} expected no-match command(s) ignored" if expected else ""
        )
        add_check(
            result,
            "agent.command_failures",
            "evidenceIntegrity",
            "WARNING",
            f"{len(command_failures)} non-blocking agent command failure(s) recorded{expected_text}.",
        )


def lint_evidence(report_dir: Path, result: dict[str, Any]) -> None:
    topic_dir = report_dir / "logs/artifacts/copied-topic-files"
    status, status_error = derive_topic_status(topic_dir)
    if status_error:
        add_check(result, "verification.claims.match.logs", "evidenceIntegrity", "FAIL", status_error)
        return
    command_events = collect_command_events(report_dir)
    final_claims = [
        " ".join(
            str(value)
            for value in (
                entry.get("summary", ""),
                entry.get("verification", ""),
                entry.get("command", ""),
                entry.get("result", ""),
                (entry.get("data") or {}).get("command", "") if isinstance(entry.get("data"), dict) else "",
                (entry.get("data") or {}).get("result", "") if isinstance(entry.get("data"), dict) else "",
                (entry.get("data") or {}).get("verification", "") if isinstance(entry.get("data"), dict) else "",
            )
            if value
        )
        for entry in status.get("verification", [])
        if isinstance(entry, dict)
    ]
    final_claims = [claim for claim in final_claims if is_final_verification_claim(claim)]
    if not final_claims:
        add_check(
            result,
            "verification.claims.match.logs",
            "evidenceIntegrity",
            "WARNING",
            "audit-derived verification does not contain a Final command verification claim.",
        )
        return
    final_event = next(
        (
            event
            for event in command_events
            if "mvn test" in event["command"] and "npm run build" in event["command"]
        ),
        None,
    )
    if final_event is None:
        add_check(
            result,
            "verification.claims.match.logs",
            "evidenceIntegrity",
            "FAIL",
            "Final verification claim exists but no matching Codex command execution event was found.",
        )
        return
    claim_text = " ".join(final_claims)
    claim_says_success_value = claim_says_success(claim_text)
    event_says_success = final_event.get("exit_code") == 0
    if claim_says_success_value != event_says_success:
        add_check(
            result,
            "verification.claims.match.logs",
            "evidenceIntegrity",
            "FAIL",
            f"Final verification claim success={claim_says_success_value} but event exit_code={final_event.get('exit_code')}.",
        )
        return
    add_check(
        result,
        "verification.claims.match.logs",
        "evidenceIntegrity",
        "PASS",
        "Final verification claim matches Codex command execution event.",
    )


def compute_overall(result: dict[str, Any]) -> None:
    segment_values = set(result["segments"].values())
    if "FAIL" in segment_values:
        result["overallResult"] = "FAIL"
    else:
        result["overallResult"] = "PASS"


def lint_report(report_dir: Path, allow_dirty_baseline: bool = False) -> dict[str, Any]:
    result = new_result()
    lint_environment(report_dir, result, allow_dirty_baseline)
    lint_workflow(report_dir, result)
    lint_artifacts(report_dir, result)
    lint_evidence(report_dir, result)
    result["stderrSummary"] = summarize_stderr(report_dir)
    compute_overall(result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lint AsUsual sandbox E2E report artifacts.")
    parser.add_argument("--report-dir", required=True)
    parser.add_argument("--allow-dirty-baseline", action="store_true")
    parser.add_argument("--json-output")
    args = parser.parse_args(argv)

    result = lint_report(Path(args.report_dir), allow_dirty_baseline=args.allow_dirty_baseline)
    output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.json_output:
        Path(args.json_output).write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 1 if result["overallResult"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
