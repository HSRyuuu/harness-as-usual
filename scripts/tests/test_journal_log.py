import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
JOURNAL_LOG = ROOT / "scripts/journal-log.py"


class JournalLogTestBase(unittest.TestCase):
    def run_journal_log(self, *args):
        return subprocess.run(
            [sys.executable, str(JOURNAL_LOG), *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )

    def init_issue(self, tmp):
        issue_dir = Path(tmp) / "issue" / "2026-07-12-order-timeout"
        result = self.run_journal_log(
            "init",
            "--issue-dir",
            str(issue_dir),
            "--initial-request",
            "order API intermittent timeout",
            "--actor",
            "claude",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return issue_dir

    def read_journal(self, issue_dir):
        lines = (issue_dir / "journal.jsonl").read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in lines if line.strip()]


class JournalLogInitTests(JournalLogTestBase):
    def test_init_creates_journal_problem_and_created_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            issue_dir = self.init_issue(tmp)
            self.assertTrue((issue_dir / "journal.jsonl").exists())
            self.assertTrue((issue_dir / "problem.md").exists())
            entries = self.read_journal(issue_dir)
            self.assertEqual(len(entries), 1)
            first = entries[0]
            self.assertEqual(first["seq"], 1)
            self.assertEqual(first["kind"], "lifecycle")
            self.assertEqual(first["event"], "created")
            self.assertEqual(first["status"], "added")
            self.assertEqual(first["actor"], "claude")
            self.assertEqual(first["initialRequest"], "order API intermittent timeout")
            self.assertIn("ts", first)

    def test_init_writes_initial_request_into_problem_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            issue_dir = self.init_issue(tmp)
            problem = (issue_dir / "problem.md").read_text(encoding="utf-8")
            self.assertIn("order API intermittent timeout", problem)

    def test_init_refuses_existing_journal(self):
        with tempfile.TemporaryDirectory() as tmp:
            issue_dir = self.init_issue(tmp)
            result = self.run_journal_log(
                "init",
                "--issue-dir",
                str(issue_dir),
                "--initial-request",
                "again",
                "--actor",
                "claude",
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("already exists", result.stderr)

    def test_init_rejects_unknown_actor(self):
        with tempfile.TemporaryDirectory() as tmp:
            issue_dir = Path(tmp) / "issue" / "2026-07-12-x"
            result = self.run_journal_log(
                "init",
                "--issue-dir",
                str(issue_dir),
                "--initial-request",
                "x",
                "--actor",
                "agent",
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("actor", result.stderr)


class JournalLogAddTests(JournalLogTestBase):
    def add_entry(self, issue_dir, kind, content, *extra):
        return self.run_journal_log(
            "add", "--issue-dir", str(issue_dir), "--kind", kind, "--content", content, *extra
        )

    def test_add_appends_reasoning_entry_with_incremented_seq(self):
        with tempfile.TemporaryDirectory() as tmp:
            issue_dir = self.init_issue(tmp)
            result = self.add_entry(
                issue_dir, "hypothesis", "connection pool exhaustion", "--evidence", "journal #1"
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            entries = self.read_journal(issue_dir)
            self.assertEqual(len(entries), 2)
            entry = entries[-1]
            self.assertEqual(entry["seq"], 2)
            self.assertEqual(entry["kind"], "hypothesis")
            self.assertEqual(entry["status"], "added")
            self.assertEqual(entry["content"], "connection pool exhaustion")
            self.assertEqual(entry["evidence"], "journal #1")
            self.assertEqual(entry["actor"], "claude")

    def test_add_rejects_non_reasoning_kind(self):
        with tempfile.TemporaryDirectory() as tmp:
            issue_dir = self.init_issue(tmp)
            result = self.add_entry(issue_dir, "lifecycle", "nope")
            self.assertEqual(result.returncode, 1)
            self.assertIn("kind", result.stderr)

    def test_approve_records_user_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            issue_dir = self.init_issue(tmp)
            result = self.run_journal_log(
                "approve", "--issue-dir", str(issue_dir), "--content", "repro test code approved"
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            entry = self.read_journal(issue_dir)[-1]
            self.assertEqual(entry["kind"], "approval")
            self.assertEqual(entry["actor"], "user")
            self.assertEqual(entry["content"], "repro test code approved")


class JournalLogStatusChangeTests(JournalLogTestBase):
    def seed_hypothesis(self, tmp):
        issue_dir = self.init_issue(tmp)
        result = self.run_journal_log(
            "add", "--issue-dir", str(issue_dir),
            "--kind", "hypothesis", "--content", "pool exhaustion",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return issue_dir, json.loads(result.stdout)["seq"]

    def test_confirm_appends_status_change_with_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            issue_dir, seq = self.seed_hypothesis(tmp)
            result = self.run_journal_log(
                "confirm", "--issue-dir", str(issue_dir),
                "--target", str(seq), "--evidence", "reproduced by load test",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            entry = self.read_journal(issue_dir)[-1]
            self.assertEqual(entry["kind"], "status-change")
            self.assertEqual(entry["status"], "confirmed")
            self.assertEqual(entry["target"], seq)
            self.assertEqual(entry["evidence"], "reproduced by load test")

    def test_cancel_requires_reason_and_appends_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            issue_dir, seq = self.seed_hypothesis(tmp)
            result = self.run_journal_log(
                "cancel", "--issue-dir", str(issue_dir),
                "--target", str(seq), "--reason", "contradicted by #18",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            entry = self.read_journal(issue_dir)[-1]
            self.assertEqual(entry["status"], "cancelled")
            self.assertEqual(entry["reason"], "contradicted by #18")

    def test_confirm_rejects_missing_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            issue_dir, _ = self.seed_hypothesis(tmp)
            result = self.run_journal_log(
                "confirm", "--issue-dir", str(issue_dir), "--target", "99",
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("target", result.stderr)

    def test_confirm_rejects_non_reasoning_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            issue_dir, _ = self.seed_hypothesis(tmp)
            result = self.run_journal_log(
                "confirm", "--issue-dir", str(issue_dir), "--target", "1",
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("target", result.stderr)


if __name__ == "__main__":
    unittest.main()
