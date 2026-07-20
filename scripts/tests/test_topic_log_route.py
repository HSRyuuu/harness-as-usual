import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
TOPIC_LOG = ROOT / "scripts/topic-log.py"


class TopicLogRouteTests(unittest.TestCase):
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
            "2026-07-20-route-test",
            "--initial-request",
            "Bug with unconfirmed cause.",
            "--summary",
            "Route test topic.",
            "--timestamp",
            "2026-07-20T00:00:00.000Z",
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        return topic_dir

    def route(self, topic_dir, route, *extra):
        return self.run_topic_log(
            "route-start-work",
            "--topic-dir",
            str(topic_dir),
            "--route",
            route,
            "--reason",
            f"routed to {route}",
            "--actor",
            "claude",
            *extra,
        )

    def status(self, topic_dir):
        result = self.run_topic_log("status", "--topic-dir", str(topic_dir), "--json")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        return json.loads(result.stdout)

    def test_find_cause_route_parks_topic(self):
        with tempfile.TemporaryDirectory() as tmp:
            topic_dir = self.init_topic(tmp)

            routed = self.route(topic_dir, "find-cause")
            self.assertEqual(routed.returncode, 0, routed.stderr + routed.stdout)

            status = self.status(topic_dir)
            self.assertEqual(status["phase"], "routed-to-find-cause")
            self.assertEqual(status["nextAction"], "investigate-cause")

            validated = self.run_topic_log("validate", "--topic-dir", str(topic_dir))
            self.assertEqual(validated.returncode, 0, validated.stderr + validated.stdout)

    def test_standard_route_still_uses_start_work_phase(self):
        with tempfile.TemporaryDirectory() as tmp:
            topic_dir = self.init_topic(tmp)

            routed = self.route(topic_dir, "requirements")
            self.assertEqual(routed.returncode, 0, routed.stderr + routed.stdout)

            status = self.status(topic_dir)
            self.assertEqual(status["phase"], "start-work")
            self.assertEqual(status["nextAction"], "answer-questions")

    def test_unknown_route_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            topic_dir = self.init_topic(tmp)

            result = self.route(topic_dir, "not-a-route")
            self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
