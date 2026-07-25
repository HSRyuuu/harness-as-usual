import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[4]
LINTER_PATH = ROOT / ".agents/skills/sandbox-e2e-test/scripts/e2e-report-linter.py"


def load_linter():
    module_spec = importlib.util.spec_from_file_location("e2e_report_linter", LINTER_PATH)
    module = importlib.util.module_from_spec(module_spec)
    assert module_spec.loader is not None
    module_spec.loader.exec_module(module)
    return module


class E2EReportLinterTests(unittest.TestCase):
    def make_report_dir(self):
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        (root / "logs/artifacts/copied-topic-files").mkdir(parents=True)
        (root / "logs/codex").mkdir(parents=True)
        (root / "logs/claude").mkdir(parents=True)
        (root / "logs/terminal").mkdir(parents=True)
        self.addCleanup(tmp.cleanup)
        return root

    def write_minimal_topic(self, report_dir):
        topic = report_dir / "logs/artifacts/copied-topic-files"
        (topic / "topic.md").write_text(
            "# Topic\n\n"
            "## Initial Request\n\n"
            "Add task priority.\n\n"
            "## Topic Boundary\n\n"
            "Task priority workflow test.\n\n"
            "## Agent Resume Notes\n\n"
            "- Continue from audit.jsonl.\n",
            encoding="utf-8",
        )
        audit_events = [
            {
                "seq": 1,
                "timestamp": "2026-06-24T12:57:15.000Z",
                "event": "topic.created",
                "actor": "codex",
                "status": "success",
                "summary": "Task priority workflow test.",
                "phase": "start-work",
                "nextAction": "route",
                "artifacts": ["topic.md", "audit.jsonl"],
                "route": None,
                "notes": "Topic created.",
                "data": {
                    "schemaVersion": "as-usual.audit.v1",
                    "topic": "2026-06-24-task-priority",
                    "initialRequest": "Add task priority.",
                    "runtimeHost": "codex",
                    "sessionId": "",
                },
                "initialRequestRef": "topic.md#Initial Request",
            },
            {
                "seq": 2,
                "timestamp": "2026-06-24T13:08:11.000Z",
                "event": "approval.execution",
                "actor": "user",
                "status": "success",
                "summary": "Approved.",
                "phase": "executing",
                "nextAction": "execute",
                "artifacts": ["topic.md", "audit.jsonl", "plan.md"],
                "route": None,
                "notes": "Approved.",
                "data": {"approvedBy": "user", "source": "current user turn"},
            },
            {
                "seq": 3,
                "timestamp": "2026-06-24T13:08:11.001Z",
                "event": "approval.high_risk",
                "actor": "user",
                "status": "success",
                "summary": "Approved DB schema operation.",
                "phase": "executing",
                "nextAction": "execute",
                "artifacts": ["plan.md"],
                "route": None,
                "notes": "Approved DB schema operation.",
                "data": {
                    "operationId": "db-task-priority",
                    "description": "Add persisted Task.priority enum field.",
                    "approvedBy": "user",
                    "rollback": "Revert backend/frontend changed files.",
                },
            },
            {
                "seq": 4,
                "timestamp": "2026-06-24T13:10:00.000Z",
                "event": "task.completed",
                "actor": "codex",
                "status": "success",
                "summary": "Completed task: Task priority.",
                "phase": "executing",
                "nextAction": "execute",
                "artifacts": [],
                "route": None,
                "task": "Task priority",
                "result": "PASS",
                "notes": "",
                "data": {
                    "task": "Task priority",
                    "verification": "Final command: cd backend && mvn test && cd ../frontend && npm run build -> exit 0.",
                    "mode": "",
                    "testTarget": "",
                    "redEvidence": "",
                    "greenEvidence": "",
                    "expectedResult": "",
                    "result": "PASS",
                    "artifacts": [],
                },
            },
            {
                "seq": 5,
                "timestamp": "2026-06-24T13:12:00.000Z",
                "event": "review.completed",
                "actor": "codex",
                "status": "success",
                "summary": "Clean review.",
                "phase": "review-complete",
                "nextAction": "decide-code-cleanup",
                "artifacts": [],
                "route": None,
                "notes": "Clean review.",
                "data": {
                    "mode": "self",
                    "status": "passed",
                    "critical": 0,
                    "important": 0,
                    "minor": 0,
                    "reason": "Clean review.",
                    "report": "",
                },
            },
            {
                "seq": 6,
                "timestamp": "2026-06-24T13:13:00.000Z",
                "event": "code_cleanup.skipped",
                "actor": "codex",
                "status": "success",
                "summary": "No code cleanup.",
                "phase": "review-complete",
                "nextAction": "finalize",
                "artifacts": [],
                "route": None,
                "notes": "No code cleanup.",
                "data": {"reason": "No code cleanup."},
            },
            {
                "seq": 7,
                "timestamp": "2026-06-24T13:14:49.000Z",
                "event": "topic.finalized",
                "actor": "codex",
                "status": "success",
                "summary": "Finalized.",
                "phase": "finalized",
                "nextAction": "git-action-decision",
                "artifacts": ["report.md"],
                "route": None,
                "notes": "Finalized.",
                "data": {"status": "complete", "report": "report.md"},
            },
        ]
        (topic / "audit.jsonl").write_text(
            "".join(json.dumps(event) + "\n" for event in audit_events),
            encoding="utf-8",
        )
        (topic / "requirements.md").write_text("# Requirements\n", encoding="utf-8")
        (topic / "plan.md").write_text(
            "### Files\n- `backend/src/main/java/com/hsryuuu/asusualtest/task/TaskPriority.java`\n",
            encoding="utf-8",
        )
        (topic / "question-c1.md").write_text(
            "## Question 1\n### Answer\n[Answer]: A) Full stack\n",
            encoding="utf-8",
        )
        (topic / "report.md").write_text("# Report\n", encoding="utf-8")

    def test_dirty_baseline_without_allow_flag_fails_environment(self):
        linter = load_linter()
        report_dir = self.make_report_dir()
        self.write_minimal_topic(report_dir)
        artifacts = report_dir / "logs/artifacts"
        (artifacts / "sandbox-status-before.txt").write_text(" M .gitignore\n", encoding="utf-8")
        (artifacts / "sandbox-status-after.txt").write_text(" M .gitignore\n", encoding="utf-8")
        result = linter.lint_report(report_dir, allow_dirty_baseline=False)
        self.assertEqual(result["segments"]["environmentCleanliness"], "FAIL")
        self.assertTrue(
            any(check["id"] == "sandbox.clean.start" for check in result["checks"])
        )

    def test_clean_baseline_passes_environment(self):
        linter = load_linter()
        report_dir = self.make_report_dir()
        self.write_minimal_topic(report_dir)
        artifacts = report_dir / "logs/artifacts"
        (artifacts / "sandbox-status-before.txt").write_text("", encoding="utf-8")
        (artifacts / "sandbox-status-after.txt").write_text(
            " M backend/src/main/java/com/hsryuuu/asusualtest/task/Task.java\n"
            "?? backend/src/main/java/com/hsryuuu/asusualtest/task/TaskPriority.java\n",
            encoding="utf-8",
        )
        result = linter.lint_report(report_dir, allow_dirty_baseline=False)
        self.assertEqual(result["segments"]["environmentCleanliness"], "PASS")

    def test_high_risk_audit_requires_structured_approval_payload(self):
        linter = load_linter()
        report_dir = self.make_report_dir()
        self.write_minimal_topic(report_dir)
        artifacts = report_dir / "logs/artifacts"
        (artifacts / "sandbox-status-before.txt").write_text("", encoding="utf-8")
        audit_path = artifacts / "copied-topic-files/audit.jsonl"
        events = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]
        events[2]["data"].pop("rollback")
        audit_path.write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")
        result = linter.lint_report(report_dir)
        self.assertEqual(result["segments"]["artifactIntegrity"], "FAIL")
        self.assertTrue(
            any(check["id"] == "approval.high_risk.structured" for check in result["checks"])
        )

    def test_mixed_audit_actor_values_fail_artifact_integrity(self):
        linter = load_linter()
        report_dir = self.make_report_dir()
        self.write_minimal_topic(report_dir)
        artifacts = report_dir / "logs/artifacts"
        (artifacts / "sandbox-status-before.txt").write_text("", encoding="utf-8")
        audit_path = artifacts / "copied-topic-files/audit.jsonl"
        events = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]
        events[-1]["actor"] = "agent"
        audit_path.write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")
        result = linter.lint_report(report_dir)
        self.assertEqual(result["segments"]["artifactIntegrity"], "FAIL")
        self.assertTrue(any(check["id"] == "audit.actor.consistent" for check in result["checks"]))

    def test_missing_review_mode_warns(self):
        linter = load_linter()
        report_dir = self.make_report_dir()
        self.write_minimal_topic(report_dir)
        artifacts = report_dir / "logs/artifacts"
        (artifacts / "sandbox-status-before.txt").write_text("", encoding="utf-8")
        audit_path = artifacts / "copied-topic-files/audit.jsonl"
        events = [
            event
            for event in (json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines())
            if event["event"] != "review.completed"
        ]
        for index, event in enumerate(events, start=1):
            event["seq"] = index
        audit_path.write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")
        result = linter.lint_report(report_dir)
        self.assertEqual(result["segments"]["artifactIntegrity"], "WARNING")
        self.assertTrue(any(check["id"] == "review.execution.mode" for check in result["checks"]))

    def test_missing_runtime_host_warns(self):
        linter = load_linter()
        report_dir = self.make_report_dir()
        self.write_minimal_topic(report_dir)
        artifacts = report_dir / "logs/artifacts"
        (artifacts / "sandbox-status-before.txt").write_text("", encoding="utf-8")
        audit_path = artifacts / "copied-topic-files/audit.jsonl"
        events = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]
        events[0]["data"]["runtimeHost"] = ""
        audit_path.write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")
        result = linter.lint_report(report_dir)
        self.assertEqual(result["segments"]["artifactIntegrity"], "WARNING")
        self.assertTrue(any(check["id"] == "runtime.host.present" for check in result["checks"]))

    def write_codex_event(self, report_dir, command, exit_code, output):
        event = {
            "type": "item.completed",
            "item": {
                "id": "item_1",
                "type": "command_execution",
                "command": command,
                "exit_code": exit_code,
                "aggregated_output": output,
            },
        }
        path = report_dir / "logs/codex/04-execute-events.jsonl"
        path.write_text(json.dumps(event) + "\n", encoding="utf-8")

    def write_codex_events(self, report_dir, events):
        path = report_dir / "logs/codex/04-execute-events.jsonl"
        path.write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")

    def final_verification_codex_event(self):
        return {
            "type": "item.completed",
            "item": {
                "id": "item_final",
                "type": "command_execution",
                "command": "/bin/zsh -lc 'cd backend && mvn test && cd ../frontend && npm run build'",
                "exit_code": 0,
                "aggregated_output": "BUILD SUCCESS",
            },
        }

    def write_started_and_completed_codex_event(self, report_dir, command, exit_code, output):
        events = [
            {
                "type": "item.started",
                "item": {
                    "type": "command_execution",
                    "command": command,
                    "exit_code": None,
                    "aggregated_output": "",
                },
            },
            {
                "type": "item.completed",
                "item": {
                    "type": "command_execution",
                    "command": command,
                    "exit_code": exit_code,
                    "aggregated_output": output,
                },
            },
        ]
        path = report_dir / "logs/codex/04-execute-events.jsonl"
        path.write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")

    def test_claimed_final_verification_must_match_codex_events(self):
        linter = load_linter()
        report_dir = self.make_report_dir()
        self.write_minimal_topic(report_dir)
        artifacts = report_dir / "logs/artifacts"
        (artifacts / "sandbox-status-before.txt").write_text("", encoding="utf-8")
        self.write_codex_event(
            report_dir,
            "/bin/zsh -lc 'mvn test && cd ../frontend && npm run build'",
            1,
            "BUILD FAILURE",
        )
        result = linter.lint_report(report_dir)
        self.assertEqual(result["segments"]["evidenceIntegrity"], "FAIL")
        self.assertTrue(any(check["id"] == "verification.claims.match.logs" for check in result["checks"]))

    def test_task_final_verification_claim_matches_codex_events(self):
        linter = load_linter()
        report_dir = self.make_report_dir()
        self.write_minimal_topic(report_dir)
        artifacts = report_dir / "logs/artifacts"
        (artifacts / "sandbox-status-before.txt").write_text("", encoding="utf-8")
        audit_path = artifacts / "copied-topic-files/audit.jsonl"
        events = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]
        events[3]["data"]["verification"] = (
            "Task 3 final verification: cd backend && mvn test && cd ../frontend && npm run build passed."
        )
        audit_path.write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")
        self.write_codex_event(
            report_dir,
            "/bin/zsh -lc 'cd backend && mvn test && cd ../frontend && npm run build'",
            0,
            "BUILD SUCCESS",
        )
        result = linter.lint_report(report_dir)
        self.assertEqual(result["segments"]["evidenceIntegrity"], "PASS")
        self.assertTrue(
            any(
                check["id"] == "verification.claims.match.logs" and check["status"] == "PASS"
                for check in result["checks"]
            )
        )

    def test_started_command_event_does_not_shadow_completed_final_verification(self):
        linter = load_linter()
        report_dir = self.make_report_dir()
        self.write_minimal_topic(report_dir)
        artifacts = report_dir / "logs/artifacts"
        (artifacts / "sandbox-status-before.txt").write_text("", encoding="utf-8")
        self.write_started_and_completed_codex_event(
            report_dir,
            "/bin/zsh -lc 'cd backend && mvn test && cd ../frontend && npm run build'",
            0,
            "BUILD SUCCESS",
        )
        result = linter.lint_report(report_dir)
        self.assertEqual(result["segments"]["evidenceIntegrity"], "PASS")

    def test_failed_codex_command_warns_without_failing_workflow_result(self):
        linter = load_linter()
        report_dir = self.make_report_dir()
        self.write_minimal_topic(report_dir)
        artifacts = report_dir / "logs/artifacts"
        (artifacts / "sandbox-status-before.txt").write_text("", encoding="utf-8")
        self.write_codex_events(
            report_dir,
            [
                {
                    "type": "item.completed",
                    "item": {
                        "id": "item_1",
                        "type": "command_execution",
                        "command": "/bin/zsh -lc 'echo boom && exit 1'",
                        "exit_code": 1,
                        "aggregated_output": "boom",
                    },
                },
                self.final_verification_codex_event(),
            ],
        )
        result = linter.lint_report(report_dir)
        self.assertEqual(result["overallResult"], "PASS")
        self.assertEqual(result["segments"]["workflowResult"], "PASS")
        self.assertEqual(result["segments"]["evidenceIntegrity"], "WARNING")
        self.assertEqual(len(result["commandFailures"]["nonBlocking"]), 1)
        self.assertTrue(
            any(
                check["id"] == "agent.command_failures" and check["status"] == "WARNING"
                for check in result["checks"]
            )
        )

    def test_expected_no_match_search_does_not_fail_workflow_result(self):
        linter = load_linter()
        report_dir = self.make_report_dir()
        self.write_minimal_topic(report_dir)
        artifacts = report_dir / "logs/artifacts"
        (artifacts / "sandbox-status-before.txt").write_text("", encoding="utf-8")
        self.write_codex_event(
            report_dir,
            "/bin/zsh -lc 'rg -n \"TODO|TBD|<name>\" .as-usual/topic/2026-06-25-task-priority/plan.md'",
            1,
            "",
        )
        result = linter.lint_report(report_dir)
        self.assertEqual(result["segments"]["workflowResult"], "PASS")
        self.assertTrue(
            any(check["id"] == "workflow.agent_steps" and check["status"] == "PASS" for check in result["checks"])
        )

    def test_failed_command_details_are_structured_for_reports(self):
        linter = load_linter()
        report_dir = self.make_report_dir()
        self.write_minimal_topic(report_dir)
        artifacts = report_dir / "logs/artifacts"
        (artifacts / "sandbox-status-before.txt").write_text("", encoding="utf-8")
        self.write_codex_events(
            report_dir,
            [
                {
                    "type": "item.completed",
                    "item": {
                        "id": "item_expected",
                        "type": "command_execution",
                        "command": "/bin/zsh -lc 'rg -n \"TODO|TBD\" plan.md'",
                        "exit_code": 1,
                        "aggregated_output": "",
                    },
                },
                {
                    "type": "item.completed",
                    "item": {
                        "id": "item_fatal",
                        "type": "command_execution",
                        "command": "/bin/zsh -lc 'python3 scripts/topic-log.py audit --topic-dir /tmp/topic --phase executing-plan'",
                        "exit_code": 1,
                        "aggregated_output": "Invalid phase: executing-plan",
                    },
                },
                self.final_verification_codex_event(),
            ],
        )
        result = linter.lint_report(report_dir)
        self.assertEqual(result["overallResult"], "PASS")
        self.assertEqual(result["segments"]["workflowResult"], "PASS")
        self.assertEqual(result["segments"]["evidenceIntegrity"], "WARNING")
        self.assertEqual(len(result["commandFailures"]["expected"]), 1)
        self.assertEqual(len(result["commandFailures"]["nonBlocking"]), 1)
        self.assertEqual(len(result["commandFailures"]["fatal"]), 1)
        self.assertIn("executing-plan", result["commandFailures"]["fatal"][0]["output"])

    def write_claude_tool_result(self, report_dir, command, exit_code, output):
        events = [
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {
                            "type": "tool_use",
                            "id": "toolu_1",
                            "name": "Bash",
                            "input": {"command": command},
                        }
                    ]
                },
            },
            {
                "type": "user",
                "message": {
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": "toolu_1",
                            "content": output,
                            "is_error": exit_code != 0,
                        }
                    ]
                },
            },
        ]
        path = report_dir / "logs/claude/04-execute-events.jsonl"
        path.write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")

    def write_claude_tool_results(self, report_dir, tool_results):
        events = []
        for index, (command, exit_code, output) in enumerate(tool_results, start=1):
            tool_id = f"toolu_{index}"
            events.extend(
                [
                    {
                        "type": "assistant",
                        "message": {
                            "content": [
                                {
                                    "type": "tool_use",
                                    "id": tool_id,
                                    "name": "Bash",
                                    "input": {"command": command},
                                }
                            ]
                        },
                    },
                    {
                        "type": "user",
                        "message": {
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": tool_id,
                                    "content": output,
                                    "is_error": exit_code != 0,
                                }
                            ]
                        },
                    },
                ]
            )
        path = report_dir / "logs/claude/04-execute-events.jsonl"
        path.write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")

    def test_claude_command_events_are_linted(self):
        linter = load_linter()
        report_dir = self.make_report_dir()
        self.write_minimal_topic(report_dir)
        artifacts = report_dir / "logs/artifacts"
        (artifacts / "sandbox-status-before.txt").write_text("", encoding="utf-8")
        self.write_claude_tool_result(
            report_dir,
            "/bin/zsh -lc 'cd backend && mvn test && cd ../frontend && npm run build'",
            0,
            "BUILD SUCCESS",
        )
        result = linter.lint_report(report_dir)
        self.assertEqual(result["segments"]["evidenceIntegrity"], "PASS")
        self.assertTrue(
            any(
                check["id"] == "workflow.agent_steps" and check["status"] == "PASS"
                for check in result["checks"]
            )
        )

    def test_failed_claude_command_warns_without_failing_workflow_result(self):
        linter = load_linter()
        report_dir = self.make_report_dir()
        self.write_minimal_topic(report_dir)
        artifacts = report_dir / "logs/artifacts"
        (artifacts / "sandbox-status-before.txt").write_text("", encoding="utf-8")
        self.write_claude_tool_results(
            report_dir,
            [
                ("/bin/zsh -lc 'echo boom && exit 1'", 1, "boom"),
                (
                    "/bin/zsh -lc 'cd backend && mvn test && cd ../frontend && npm run build'",
                    0,
                    "BUILD SUCCESS",
                ),
            ],
        )
        result = linter.lint_report(report_dir)
        self.assertEqual(result["overallResult"], "PASS")
        self.assertEqual(result["segments"]["workflowResult"], "PASS")
        self.assertEqual(result["segments"]["evidenceIntegrity"], "WARNING")
        self.assertEqual(len(result["commandFailures"]["nonBlocking"]), 1)
        self.assertEqual(len(result["commandFailures"]["fatal"]), 1)
        self.assertIn("boom", result["commandFailures"]["fatal"][0]["output"])

    def test_failed_claude_preflight_is_reported_as_workflow_failure(self):
        linter = load_linter()
        report_dir = self.make_report_dir()
        self.write_minimal_topic(report_dir)
        artifacts = report_dir / "logs/artifacts"
        (artifacts / "sandbox-status-before.txt").write_text("", encoding="utf-8")
        terminal_log = report_dir / "logs/terminal/20260625-061009-claude-preflight.log"
        terminal_log.write_text(
            "cwd: /tmp/project\n"
            "started_at: 2026-06-25T06:10:09Z\n"
            "command: claude -p --model sonnet AsUsual sandbox E2E preflight. Do not edit files. Reply OK only.\n"
            "--- output ---\n"
            "You've hit your session limit · resets 6:10pm (Asia/Seoul)\n"
            "--- result ---\n"
            "exit_code: 1\n"
            "finished_at: 2026-06-25T06:10:12Z\n",
            encoding="utf-8",
        )
        result = linter.lint_report(report_dir)
        self.assertEqual(result["segments"]["workflowResult"], "FAIL")
        self.assertTrue(
            any(
                check["id"] == "workflow.claude_preflight"
                and "session limit" in check["message"]
                for check in result["checks"]
            )
        )

    def test_untracked_after_status_is_reported_as_changed_file(self):
        linter = load_linter()
        report_dir = self.make_report_dir()
        self.write_minimal_topic(report_dir)
        artifacts = report_dir / "logs/artifacts"
        (artifacts / "sandbox-status-before.txt").write_text("", encoding="utf-8")
        (artifacts / "sandbox-status-after.txt").write_text(
            "?? backend/src/main/java/com/hsryuuu/asusualtest/task/TaskPriority.java\n",
            encoding="utf-8",
        )
        result = linter.lint_report(report_dir)
        self.assertIn(
            "backend/src/main/java/com/hsryuuu/asusualtest/task/TaskPriority.java",
            result["changedFiles"]["untracked"],
        )

    def test_skill_telemetry_warning_is_known_host_noise_not_evidence_warning(self):
        linter = load_linter()
        report_dir = self.make_report_dir()
        self.write_minimal_topic(report_dir)
        artifacts = report_dir / "logs/artifacts"
        (artifacts / "sandbox-status-before.txt").write_text("", encoding="utf-8")
        self.write_codex_event(
            report_dir,
            "/bin/zsh -lc 'cd backend && mvn test && cd ../frontend && npm run build'",
            0,
            "BUILD SUCCESS",
        )
        stderr_path = report_dir / "logs/codex/01-start-topic-stderr.log"
        stderr_path.write_text(
            "2026-06-28T05:20:50.120568Z  WARN codex_otel::events::session_telemetry: "
            "metrics counter [codex.skill.injected] failed: tag value contains invalid characters: "
            "as-usual:using-as-usual\n",
            encoding="utf-8",
        )
        result = linter.lint_report(report_dir)
        self.assertEqual(result["segments"]["evidenceIntegrity"], "PASS")
        self.assertEqual(len(result["stderrSummary"]["skillTelemetryWarnings"]), 1)
        self.assertFalse(
            any(check["id"] == "stderr.telemetry.skill_tags" for check in result["checks"])
        )


if __name__ == "__main__":
    unittest.main()
