import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
TOPIC_LOG = ROOT / "scripts/topic-log.py"


class TopicLogTaskModeTests(unittest.TestCase):
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
            "2026-07-20-task-mode-test",
            "--initial-request",
            "Test task completion modes.",
            "--summary",
            "Task mode test topic.",
            "--timestamp",
            "2026-07-20T00:00:00.000Z",
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        return topic_dir

    def complete_task(self, topic_dir, task, *extra_args):
        return self.run_topic_log(
            "complete-task",
            "--topic-dir",
            str(topic_dir),
            "--task",
            task,
            "--actor",
            "claude",
            *extra_args,
        )

    def last_event(self, topic_dir):
        lines = (topic_dir / "audit.jsonl").read_text(encoding="utf-8").splitlines()
        return json.loads(lines[-1])

    def test_test_required_needs_target_and_passing_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            topic_dir = self.init_topic(tmp)

            missing_green = self.complete_task(
                topic_dir, "Task 1: x", "--mode", "test-required", "--test-target", "t.py"
            )
            self.assertNotEqual(missing_green.returncode, 0)

            ok = self.complete_task(
                topic_dir,
                "Task 1: x",
                "--mode",
                "test-required",
                "--test-target",
                "t.py",
                "--green-evidence",
                "pytest -> pass",
            )
            self.assertEqual(ok.returncode, 0, ok.stderr + ok.stdout)
            self.assertEqual(self.last_event(topic_dir)["data"]["mode"], "test-required")

    def test_no_test_requires_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            topic_dir = self.init_topic(tmp)

            missing_reason = self.complete_task(topic_dir, "Task 2: y", "--mode", "no-test")
            self.assertNotEqual(missing_reason.returncode, 0)

            ok = self.complete_task(
                topic_dir,
                "Task 2: y",
                "--mode",
                "no-test",
                "--no-test-reason",
                "configuration only, no behavior to test",
            )
            self.assertEqual(ok.returncode, 0, ok.stderr + ok.stdout)
            event = self.last_event(topic_dir)
            self.assertEqual(event["data"]["mode"], "no-test")
            self.assertIn("configuration only", event["data"]["noTestReason"])

    def test_retired_tdd_mode_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            topic_dir = self.init_topic(tmp)

            result = self.complete_task(topic_dir, "Task 3: z", "--mode", "tdd")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Unsupported task mode", result.stderr + result.stdout)


if __name__ == "__main__":
    unittest.main()
