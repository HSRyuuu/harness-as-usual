import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
TOPIC_LOG = ROOT / "scripts/topic-log.py"


class TopicLogVerificationVerdictTests(unittest.TestCase):
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
            "2026-07-05-verdict-test",
            "--initial-request",
            "Test verification verdict.",
            "--summary",
            "Verification verdict test topic.",
            "--timestamp",
            "2026-07-05T00:00:00.000Z",
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        return topic_dir

    def run_verification(self, topic_dir, *extra_args):
        return self.run_topic_log(
            "verification",
            "--topic-dir",
            str(topic_dir),
            "--summary",
            "Final command: pytest -> exit 0.",
            "--command",
            "pytest",
            "--result",
            "exit 0",
            *extra_args,
        )

    def last_event(self, topic_dir):
        lines = (topic_dir / "audit.jsonl").read_text(encoding="utf-8").splitlines()
        return json.loads(lines[-1])

    def test_verification_records_pass_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            topic_dir = self.init_topic(tmp)

            result = self.run_verification(topic_dir, "--verdict", "PASS")

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            event = self.last_event(topic_dir)
            self.assertEqual(event["event"], "verification.recorded")
            self.assertEqual(event["data"]["verdict"], "PASS")

    def test_verification_rejects_invalid_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            topic_dir = self.init_topic(tmp)

            result = self.run_verification(topic_dir, "--verdict", "INVALID")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Invalid verification verdict", result.stderr + result.stdout)

    def test_verification_requires_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            topic_dir = self.init_topic(tmp)

            result = self.run_verification(topic_dir)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--verdict", result.stderr + result.stdout)

    def test_verification_records_fail_and_inconclusive_verdicts(self):
        with tempfile.TemporaryDirectory() as tmp:
            topic_dir = self.init_topic(tmp)

            fail = self.run_verification(topic_dir, "--verdict", "FAIL")
            inconclusive = self.run_verification(topic_dir, "--verdict", "INCONCLUSIVE")

            self.assertEqual(fail.returncode, 0, fail.stderr + fail.stdout)
            self.assertEqual(inconclusive.returncode, 0, inconclusive.stderr + inconclusive.stdout)
            self.assertEqual(self.last_event(topic_dir)["data"]["verdict"], "INCONCLUSIVE")


if __name__ == "__main__":
    unittest.main()
