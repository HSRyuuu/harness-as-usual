import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[4]
TOPIC_LOG = ROOT / "scripts/topic-log.py"
REMOVED_STATE_ARTIFACT = "state" + ".json"


class TopicLogTests(unittest.TestCase):
    def run_topic_log(self, *args):
        return subprocess.run(
            [sys.executable, str(TOPIC_LOG), *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )

    def init_topic(self, tmp):
        topic_dir = Path(tmp) / "topic"
        result = self.run_topic_log(
            "init",
            "--topic-dir",
            str(topic_dir),
            "--topic",
            "2026-06-27-task-priority",
            "--initial-request",
            "Add task priority.",
            "--summary",
            "Task priority workflow test.",
            "--timestamp",
            "2026-06-27T00:00:00.000Z",
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        return topic_dir

    def test_init_creates_topic_md_and_audit_without_state_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            topic_dir = self.init_topic(tmp)
            self.assertFalse((topic_dir / REMOVED_STATE_ARTIFACT).exists())
            topic_text = (topic_dir / "topic.md").read_text(encoding="utf-8")
            events = [
                json.loads(line)
                for line in (topic_dir / "audit.jsonl").read_text(encoding="utf-8").splitlines()
            ]

            self.assertIn("# Topic", topic_text)
            self.assertIn("## Initial Request", topic_text)
            self.assertIn("Add task priority.", topic_text)
            self.assertIn("## Topic Boundary", topic_text)
            self.assertIn("## Agent Resume Notes", topic_text)
            self.assertEqual(events[0]["event"], "topic.created")
            self.assertEqual(events[0]["actor"], "codex")
            self.assertEqual(events[0]["seq"], 1)
            self.assertEqual(events[0]["phase"], "start-work")
            self.assertEqual(events[0]["nextAction"], "route")
            self.assertEqual(events[0]["artifacts"], ["topic.md", "audit.jsonl"])

    def test_init_invalid_actor_fails_before_writing_topic_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            topic_dir = Path(tmp) / "topic"
            result = self.run_topic_log(
                "init",
                "--topic-dir",
                str(topic_dir),
                "--topic",
                "2026-06-27-task-priority",
                "--actor",
                "agent",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Invalid actor", result.stderr + result.stdout)
            self.assertFalse((topic_dir / REMOVED_STATE_ARTIFACT).exists())
            self.assertFalse((topic_dir / "topic.md").exists())
            self.assertFalse((topic_dir / "audit.jsonl").exists())

    def test_status_json_derives_phase_next_action_and_artifacts_from_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            topic_dir = self.init_topic(tmp)
            for command in [
                (
                    "complete-requirements",
                    "--topic-dir",
                    str(topic_dir),
                    "--summary",
                    "Requirements review passed.",
                ),
                (
                    "complete-plan",
                    "--topic-dir",
                    str(topic_dir),
                    "--summary",
                    "Plan review passed.",
                ),
            ]:
                result = self.run_topic_log(*command)
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

            result = self.run_topic_log("status", "--topic-dir", str(topic_dir), "--json")

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            status = json.loads(result.stdout)
            self.assertEqual(status["topic"], "2026-06-27-task-priority")
            self.assertEqual(status["status"], "active")
            self.assertEqual(status["phase"], "plan-review")
            self.assertEqual(status["nextAction"], "approve-execute")
            self.assertEqual(status["artifacts"]["requirements"], "requirements.md")
            self.assertEqual(status["artifacts"]["plan"], "plan.md")
            self.assertEqual(status["lastEvent"], "plan.completed")
            self.assertFalse((topic_dir / REMOVED_STATE_ARTIFACT).exists())

    def test_state_field_mutation_commands_are_removed(self):
        with tempfile.TemporaryDirectory() as tmp:
            topic_dir = self.init_topic(tmp)
            for command in ("current", "append", "check"):
                result = self.run_topic_log(command, "--topic-dir", str(topic_dir))
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("invalid choice", result.stderr + result.stdout)

    def test_high_churn_task_completion_does_not_update_topic_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            topic_dir = self.init_topic(tmp)
            before = (topic_dir / "topic.md").read_text(encoding="utf-8")

            result = self.run_topic_log(
                "complete-task",
                "--topic-dir",
                str(topic_dir),
                "--task",
                "Task 1: Add review evidence",
                "--summary",
                "Task completed.",
                "--verification",
                "Final command: npm test exited 0.",
                "--mode",
                "tdd",
                "--test-target",
                "tests/review-evidence.test.ts",
                "--red-evidence",
                "npm test failed before implementation.",
                "--green-evidence",
                "npm test passed after implementation.",
                "--expected-result",
                "review evidence is recorded",
                "--result",
                "PASS",
                "--artifacts",
                "audit.jsonl",
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            after = (topic_dir / "topic.md").read_text(encoding="utf-8")
            self.assertEqual(after, before)

            status_result = self.run_topic_log("status", "--topic-dir", str(topic_dir), "--json")
            self.assertEqual(status_result.returncode, 0, status_result.stderr + status_result.stdout)
            status = json.loads(status_result.stdout)
            self.assertEqual(status["verification"][0]["task"], "Task 1: Add review evidence")
            self.assertEqual(status["verification"][0]["result"], "PASS")
            task = status["tasks"]["Task 1: Add review evidence"]
            self.assertEqual(task["completed"]["result"], "PASS")
            self.assertEqual(task["completed"]["mode"], "tdd")

    def test_complete_task_rejects_tdd_without_red_and_green_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            topic_dir = self.init_topic(tmp)

            result = self.run_topic_log(
                "complete-task",
                "--topic-dir",
                str(topic_dir),
                "--task",
                "Task 1: Add behavior",
                "--summary",
                "Should reject missing RED evidence.",
                "--mode",
                "tdd",
                "--test-target",
                "tests/behavior.test.ts",
                "--green-evidence",
                "npm test passed after implementation.",
                "--result",
                "PASS",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("TDD task requires RED evidence", result.stderr + result.stdout)

    def test_complete_task_rejects_removed_weak_verification_modes(self):
        with tempfile.TemporaryDirectory() as tmp:
            topic_dir = self.init_topic(tmp)

            for mode in ("verification-only", "manual-qa", "test-first-where-possible", "strict-tdd"):
                result = self.run_topic_log(
                    "complete-task",
                    "--topic-dir",
                    str(topic_dir),
                    "--task",
                    f"Task 1: Reject {mode}",
                    "--summary",
                    "Should reject weak or stale mode.",
                    "--mode",
                    mode,
                    "--result",
                    "PASS",
                )

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Unsupported task mode", result.stderr + result.stdout)

    def test_complete_task_allows_human_approved_tdd_exception_only_for_allowed_categories(self):
        with tempfile.TemporaryDirectory() as tmp:
            topic_dir = self.init_topic(tmp)

            missing_approval = self.run_topic_log(
                "complete-task",
                "--topic-dir",
                str(topic_dir),
                "--task",
                "Task 1: Generated code",
                "--summary",
                "Should reject exception without human approval source.",
                "--mode",
                "approved-tdd-exception",
                "--exception-category",
                "generated-code",
                "--result",
                "PASS",
            )
            self.assertNotEqual(missing_approval.returncode, 0)
            self.assertIn("human approval", missing_approval.stderr + missing_approval.stdout)

            bad_category = self.run_topic_log(
                "complete-task",
                "--topic-dir",
                str(topic_dir),
                "--task",
                "Task 1: Unsupported exception",
                "--summary",
                "Should reject unsupported exception category.",
                "--mode",
                "approved-tdd-exception",
                "--exception-category",
                "docs-only",
                "--exception-approval",
                "user approved in current turn",
                "--result",
                "PASS",
            )
            self.assertNotEqual(bad_category.returncode, 0)
            self.assertIn("Invalid TDD exception category", bad_category.stderr + bad_category.stdout)

            approved = self.run_topic_log(
                "complete-task",
                "--topic-dir",
                str(topic_dir),
                "--task",
                "Task 1: Generated code",
                "--summary",
                "Human approved generated-code exception.",
                "--mode",
                "approved-tdd-exception",
                "--exception-category",
                "generated-code",
                "--exception-approval",
                "user approved in current turn",
                "--verification",
                "Generated output reviewed.",
                "--result",
                "PASS",
            )
            self.assertEqual(approved.returncode, 0, approved.stderr + approved.stdout)

    def test_execute_event_macros_capture_subagent_review_and_sweep_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            topic_dir = self.init_topic(tmp)
            before = (topic_dir / "topic.md").read_text(encoding="utf-8")

            for command in [
                (
                    "dispatch-task",
                    "--topic-dir",
                    str(topic_dir),
                    "--task",
                    "Task 1: Add review evidence",
                    "--mode",
                    "subagent-driven",
                    "--role",
                    "implementer",
                    "--context",
                    "requirements.md,plan.md#Task 1",
                    "--summary",
                    "Dispatched a fresh implementer with bounded context.",
                ),
                (
                    "record-task-review",
                    "--topic-dir",
                    str(topic_dir),
                    "--task",
                    "Task 1: Add review evidence",
                    "--review-type",
                    "requirements",
                    "--status",
                    "passed",
                    "--summary",
                    "Task output matches requirements.",
                ),
                (
                    "record-task-fix",
                    "--topic-dir",
                    str(topic_dir),
                    "--task",
                    "Task 1: Add review evidence",
                    "--finding-id",
                    "T1-Q1",
                    "--status",
                    "completed",
                    "--summary",
                    "Fixed review finding T1-Q1 and rechecked.",
                ),
                (
                    "record-task-commit",
                    "--topic-dir",
                    str(topic_dir),
                    "--task",
                    "Task 1: Add review evidence",
                    "--sha",
                    "abc1234",
                    "--summary",
                    "Committed the task-sized slice.",
                ),
                (
                    "record-sweep",
                    "--topic-dir",
                    str(topic_dir),
                    "--kind",
                    "stale-reference",
                    "--command",
                    "rg state.json",
                    "--result",
                    "exit 1 expected; no stale runtime references.",
                    "--summary",
                    "Stale reference scan completed.",
                ),
            ]:
                result = self.run_topic_log(*command)
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

            after = (topic_dir / "topic.md").read_text(encoding="utf-8")
            self.assertEqual(after, before)

            status_result = self.run_topic_log("status", "--topic-dir", str(topic_dir), "--json")
            self.assertEqual(status_result.returncode, 0, status_result.stderr + status_result.stdout)
            status = json.loads(status_result.stdout)
            task = status["tasks"]["Task 1: Add review evidence"]
            self.assertEqual(task["mode"], "subagent-driven")
            self.assertEqual(task["dispatches"][0]["role"], "implementer")
            self.assertEqual(task["reviews"][0]["reviewType"], "requirements")
            self.assertEqual(task["reviews"][0]["status"], "passed")
            self.assertEqual(task["fixes"][0]["findingId"], "T1-Q1")
            self.assertEqual(task["commits"][0]["sha"], "abc1234")
            self.assertEqual(status["sweeps"][0]["kind"], "stale-reference")

    def test_approved_tdd_exception_still_derives_task_completion(self):
        with tempfile.TemporaryDirectory() as tmp:
            topic_dir = self.init_topic(tmp)

            result = self.run_topic_log(
                "complete-task",
                "--topic-dir",
                str(topic_dir),
                "--task",
                "Task 1: Generated config",
                "--summary",
                "Task completed with human-approved TDD exception.",
                "--mode",
                "approved-tdd-exception",
                "--exception-category",
                "configuration",
                "--exception-approval",
                "user approved in current turn",
                "--result",
                "SKIPPED",
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

            status_result = self.run_topic_log("status", "--topic-dir", str(topic_dir), "--json")
            self.assertEqual(status_result.returncode, 0, status_result.stderr + status_result.stdout)
            status = json.loads(status_result.stdout)
            task = status["tasks"]["Task 1: Generated config"]
            self.assertEqual(task["completed"]["result"], "SKIPPED")
            self.assertEqual(task["completed"]["exceptionCategory"], "configuration")
            self.assertEqual(status["verification"], [])

    def test_task_review_findings_route_to_review_follow_up(self):
        with tempfile.TemporaryDirectory() as tmp:
            topic_dir = self.init_topic(tmp)

            result = self.run_topic_log(
                "record-task-review",
                "--topic-dir",
                str(topic_dir),
                "--task",
                "Task 1: Add review evidence",
                "--review-type",
                "quality",
                "--status",
                "findings",
                "--important",
                "1",
                "--finding-ids",
                "T1-Q1",
                "--summary",
                "Quality review found one important issue.",
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

            status_result = self.run_topic_log("status", "--topic-dir", str(topic_dir), "--json")
            self.assertEqual(status_result.returncode, 0, status_result.stderr + status_result.stdout)
            status = json.loads(status_result.stdout)
            self.assertEqual(status["phase"], "executing")
            self.assertEqual(status["nextAction"], "address-review-findings")
            self.assertEqual(status["tasks"]["Task 1: Add review evidence"]["reviews"][0]["important"], 1)
            self.assertEqual(status["taskFindings"][0]["id"], "T1-Q1")

    def test_complete_execution_rejects_unresolved_task_review_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            topic_dir = self.init_topic(tmp)

            result = self.run_topic_log(
                "record-task-review",
                "--topic-dir",
                str(topic_dir),
                "--task",
                "Task 1: Add review evidence",
                "--review-type",
                "quality",
                "--status",
                "findings",
                "--important",
                "1",
                "--finding-ids",
                "T1-Q1",
                "--summary",
                "Quality review found one important issue.",
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

            blocked = self.run_topic_log(
                "complete-execution",
                "--topic-dir",
                str(topic_dir),
                "--summary",
                "Should not complete with open task findings.",
            )
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("unresolved task findings", blocked.stderr + blocked.stdout)

            fixed = self.run_topic_log(
                "record-task-fix",
                "--topic-dir",
                str(topic_dir),
                "--task",
                "Task 1: Add review evidence",
                "--finding-id",
                "T1-Q1",
                "--status",
                "completed",
                "--summary",
                "Fixed T1-Q1.",
            )
            self.assertEqual(fixed.returncode, 0, fixed.stderr + fixed.stdout)

            completed = self.run_topic_log(
                "complete-execution",
                "--topic-dir",
                str(topic_dir),
                "--summary",
                "Execution can complete after task finding fix.",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)

    def test_task_review_findings_require_finding_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            topic_dir = self.init_topic(tmp)

            result = self.run_topic_log(
                "record-task-review",
                "--topic-dir",
                str(topic_dir),
                "--task",
                "Task 1: Add review evidence",
                "--review-type",
                "quality",
                "--status",
                "findings",
                "--important",
                "1",
                "--summary",
                "Quality review found one important issue.",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("finding ids", result.stderr + result.stdout)

    def test_event_first_note_does_not_update_topic_md_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            topic_dir = self.init_topic(tmp)
            before = (topic_dir / "topic.md").read_text(encoding="utf-8")

            result = self.run_topic_log(
                "note",
                "--topic-dir",
                str(topic_dir),
                "--summary",
                "Keep this as audit evidence only.",
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            after = (topic_dir / "topic.md").read_text(encoding="utf-8")
            self.assertEqual(after, before)

            status_result = self.run_topic_log("status", "--topic-dir", str(topic_dir), "--json")
            self.assertEqual(status_result.returncode, 0, status_result.stderr + status_result.stdout)
            status = json.loads(status_result.stdout)
            self.assertEqual(status["lastEvent"], "note.recorded")

    def test_validate_requires_review_code_cleanup_decision_and_report_for_finalized_topic(self):
        with tempfile.TemporaryDirectory() as tmp:
            topic_dir = self.init_topic(tmp)

            result = self.run_topic_log(
                "finalize-topic",
                "--topic-dir",
                str(topic_dir),
                "--status",
                "complete",
                "--summary",
                "Finished without required review evidence.",
                "--report",
                "report.md",
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

            validate = self.run_topic_log("validate", "--topic-dir", str(topic_dir))

            self.assertNotEqual(validate.returncode, 0)
            self.assertIn("review.completed", validate.stderr + validate.stdout)

    def test_validate_rejects_complete_finalization_after_latest_review_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            topic_dir = self.init_topic(tmp)
            for command in [
                (
                    "record-review",
                    "--topic-dir",
                    str(topic_dir),
                    "--mode",
                    "self",
                    "--status",
                    "passed",
                    "--reason",
                    "Initial review passed.",
                ),
                (
                    "record-review",
                    "--topic-dir",
                    str(topic_dir),
                    "--mode",
                    "self",
                    "--status",
                    "findings",
                    "--important",
                    "1",
                    "--reason",
                    "Later review found an important issue.",
                ),
                (
                    "skip-code-cleanup",
                    "--topic-dir",
                    str(topic_dir),
                    "--reason",
                    "No simplification.",
                ),
                (
                    "finalize-topic",
                    "--topic-dir",
                    str(topic_dir),
                    "--status",
                    "complete",
                    "--summary",
                    "Incorrectly finalized with open findings.",
                    "--report",
                    "report.md",
                ),
            ]:
                result = self.run_topic_log(*command)
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

            validate = self.run_topic_log("validate", "--topic-dir", str(topic_dir))

            self.assertNotEqual(validate.returncode, 0)
            self.assertIn("latest review.completed status must be passed", validate.stderr + validate.stdout)

    def test_clean_review_without_report_does_not_set_code_review_report_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            topic_dir = self.init_topic(tmp)

            result = self.run_topic_log(
                "record-review",
                "--topic-dir",
                str(topic_dir),
                "--mode",
                "self",
                "--status",
                "passed",
                "--critical",
                "0",
                "--important",
                "0",
                "--minor",
                "0",
                "--reason",
                "Clean review.",
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

            status_result = self.run_topic_log("status", "--topic-dir", str(topic_dir), "--json")
            self.assertEqual(status_result.returncode, 0, status_result.stderr + status_result.stdout)
            status = json.loads(status_result.stdout)
            self.assertIsNone(status["artifacts"]["codeReviewReport"])

    def test_skip_simplify_alias_records_code_cleanup_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            topic_dir = self.init_topic(tmp)

            result = self.run_topic_log(
                "skip-simplify",
                "--topic-dir",
                str(topic_dir),
                "--reason",
                "Legacy command alias.",
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

            events = [
                json.loads(line)
                for line in (topic_dir / "audit.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(events[-1]["event"], "code_cleanup.skipped")
            self.assertEqual(events[-1]["phase"], "review-complete")
            self.assertEqual(events[-1]["nextAction"], "finalize")

    def test_validate_accepts_legacy_simplify_decision_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            topic_dir = self.init_topic(tmp)
            for command in [
                (
                    "record-review",
                    "--topic-dir",
                    str(topic_dir),
                    "--mode",
                    "self",
                    "--status",
                    "passed",
                    "--reason",
                    "Clean review.",
                ),
                (
                    "audit",
                    "--topic-dir",
                    str(topic_dir),
                    "--event",
                    "simplify.skipped",
                    "--phase",
                    "simplify-complete",
                    "--next-action",
                    "finalize",
                    "--summary",
                    "Legacy simplify decision.",
                ),
                (
                    "finalize-topic",
                    "--topic-dir",
                    str(topic_dir),
                    "--status",
                    "complete",
                    "--summary",
                    "Finished with legacy simplify decision.",
                    "--report",
                    "report.md",
                ),
            ]:
                result = self.run_topic_log(*command)
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

            validate = self.run_topic_log("validate", "--topic-dir", str(topic_dir))
            self.assertEqual(validate.returncode, 0, validate.stderr + validate.stdout)

            status_result = self.run_topic_log("status", "--topic-dir", str(topic_dir), "--json")
            self.assertEqual(status_result.returncode, 0, status_result.stderr + status_result.stdout)
            status = json.loads(status_result.stdout)
            self.assertEqual(status["phase"], "finalized")
            self.assertEqual(status["nextAction"], "git-action-decision")

    def test_validate_rejects_complete_finalization_with_unresolved_important_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            topic_dir = self.init_topic(tmp)
            for command in [
                (
                    "record-review",
                    "--topic-dir",
                    str(topic_dir),
                    "--mode",
                    "self",
                    "--status",
                    "passed",
                    "--important",
                    "1",
                    "--reason",
                    "Review says passed but still has an important finding.",
                ),
                (
                    "skip-code-cleanup",
                    "--topic-dir",
                    str(topic_dir),
                    "--reason",
                    "No simplification.",
                ),
                (
                    "finalize-topic",
                    "--topic-dir",
                    str(topic_dir),
                    "--status",
                    "complete",
                    "--summary",
                    "Incorrectly finalized with unresolved important finding.",
                    "--report",
                    "report.md",
                ),
            ]:
                result = self.run_topic_log(*command)
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

            validate = self.run_topic_log("validate", "--topic-dir", str(topic_dir))

            self.assertNotEqual(validate.returncode, 0)
            self.assertIn("no unresolved critical or important review findings", validate.stderr + validate.stdout)

    def test_blocker_sets_blocked_status_and_none_next_action(self):
        with tempfile.TemporaryDirectory() as tmp:
            topic_dir = self.init_topic(tmp)

            result = self.run_topic_log(
                "blocker",
                "--topic-dir",
                str(topic_dir),
                "--id",
                "missing-decision",
                "--summary",
                "Need a user decision.",
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

            status_result = self.run_topic_log("status", "--topic-dir", str(topic_dir), "--json")
            self.assertEqual(status_result.returncode, 0, status_result.stderr + status_result.stdout)
            status = json.loads(status_result.stdout)
            self.assertEqual(status["status"], "blocked")
            self.assertEqual(status["phase"], "blocked")
            self.assertEqual(status["nextAction"], "none")
            self.assertEqual(status["blockers"][0]["id"], "missing-decision")

    def test_resolved_blocker_returns_status_to_active(self):
        with tempfile.TemporaryDirectory() as tmp:
            topic_dir = self.init_topic(tmp)
            for command in [
                (
                    "blocker",
                    "--topic-dir",
                    str(topic_dir),
                    "--id",
                    "missing-decision",
                    "--summary",
                    "Need a user decision.",
                ),
                (
                    "audit",
                    "--topic-dir",
                    str(topic_dir),
                    "--event",
                    "blocker.resolved",
                    "--summary",
                    "missing-decision",
                    "--next-action",
                    "execute",
                    "--notes",
                    "Resolved missing-decision.",
                ),
            ]:
                result = self.run_topic_log(*command)
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

            status_result = self.run_topic_log("status", "--topic-dir", str(topic_dir), "--json")
            self.assertEqual(status_result.returncode, 0, status_result.stderr + status_result.stdout)
            status = json.loads(status_result.stdout)
            self.assertEqual(status["status"], "active")
            self.assertEqual(status["nextAction"], "execute")
            self.assertEqual(status["blockers"], [])

    def test_non_init_commands_fail_without_creating_topic_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            topic_dir = Path(tmp) / "missing-topic"

            for command in [
                (
                    "note",
                    "--topic-dir",
                    str(topic_dir),
                    "--summary",
                    "Should not create orphan audit history.",
                ),
                ("status", "--topic-dir", str(topic_dir), "--json"),
            ]:
                result = self.run_topic_log(*command)

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Missing required file", result.stderr + result.stdout)
                self.assertFalse(topic_dir.exists())

    def test_complete_plan_rejects_noncanonical_plan_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            topic_dir = self.init_topic(tmp)

            result = self.run_topic_log(
                "complete-plan",
                "--topic-dir",
                str(topic_dir),
                "--plan",
                "../outside.md",
                "--summary",
                "Should reject noncanonical plan path.",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("plan must be plan.md", result.stderr + result.stdout)


if __name__ == "__main__":
    unittest.main()
