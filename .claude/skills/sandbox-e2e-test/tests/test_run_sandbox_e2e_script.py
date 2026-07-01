from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[4]
RUNNER_PATH = ROOT / ".agents/skills/sandbox-e2e-test/scripts/run-sandbox-e2e.sh"


class RunSandboxE2EScriptTests(unittest.TestCase):
    def test_runner_script_has_valid_bash_syntax(self):
        subprocess.run(["bash", "-n", str(RUNNER_PATH)], check=True)

    def test_runner_accepts_claude_host(self):
        text = RUNNER_PATH.read_text(encoding="utf-8")
        self.assertIn("--host codex|claude", text)
        self.assertIn("--scenario NAME", text)
        self.assertIn('scenario="scenario_1_priority"', text)
        self.assertIn("scenario_2_complex_workflow", text)
        self.assertIn("scenario_3_self_improvement", text)
        self.assertIn('test_name="$scenario"', text)
        self.assertIn('echo "[INFO] Scenario: $scenario"', text)
        self.assertIn('SCENARIO="$scenario"', text)
        self.assertIn('scenario = os.environ["SCENARIO"]', text)
        self.assertIn("copied-memory-files", text)
        self.assertIn('[ "$host" != "codex" ] && [ "$host" != "claude" ]', text)
        self.assertIn('idle_timeout_user_set="false"', text)
        self.assertIn('if [ "$host" = "claude" ] && [ "$idle_timeout_user_set" = "false" ]; then', text)
        self.assertIn("terminate_step_process()", text)
        self.assertIn('claude_model="sonnet"', text)
        self.assertIn('claude_setting_sources="project"', text)
        self.assertIn('claude_plugin_dir="$as_usual_repo"', text)
        self.assertIn('claude_preflight="true"', text)
        self.assertIn("--claude-model", text)
        self.assertIn("--claude-setting-sources", text)
        self.assertIn("--claude-plugin-dir", text)
        self.assertIn("--skip-claude-preflight", text)
        self.assertIn('--no-preclean', text)
        self.assertIn('expected_sandbox_repo="/Users/happyhsryu/dev/personal/as-usual-test-project"', text)
        self.assertIn('Sandbox git root mismatch', text)
        self.assertIn('preclean_sandbox="true"', text)
        self.assertIn('preclean_sandbox_repo()', text)
        self.assertIn('sandbox-status-before-preclean.txt', text)
        self.assertIn('git -C "$sandbox_repo" restore --worktree --staged .', text)
        self.assertIn('git -C "$sandbox_repo" clean -fd', text)
        self.assertIn('sandboxPrecleaned', text)
        self.assertIn('--model "$claude_model"', text)
        self.assertIn('--setting-sources "$claude_setting_sources"', text)
        self.assertIn('--plugin-dir "$claude_plugin_dir"', text)
        self.assertIn("run_claude_preflight()", text)
        self.assertIn('if [ "$host" = "claude" ] && [ "$claude_preflight" = "true" ]; then', text)
        self.assertIn("topic_log_prompt_contract()", text)
        self.assertIn("Valid artifact names are exactly: `question`, `requirements`, `plan`, `codeReviewReport`, `report`, `topic`, `audit`.", text)
        self.assertIn("--name question --value question-c1.md --append --actor __AS_USUAL_HOST__", text)
        self.assertIn("Never use artifact names such as `questionsC1`, `questions`, `question-c1`, or `audit.jsonl`.", text)
        self.assertIn("use actor `__AS_USUAL_HOST__`", text)
        self.assertIn("the removed legacy state artifact, or `audit.jsonl` as an artifact name", text)
        self.assertIn("topic-log.py complete-task --topic-dir <topicDir>", text)
        self.assertIn("--mode tdd --test-target <test> --red-evidence <red-command-and-result> --green-evidence <green-command-and-result>", text)
        self.assertIn("task.dispatched` event with mode `subagent-driven`", text)
        self.assertIn("Subagent dispatch evidence", text)
        self.assertIn("TDD RED/GREEN evidence", text)
        self.assertIn("improvement-plan.md", text)
        self.assertIn("Wrote improvement plan", text)
        self.assertIn("topic-log.py complete-execution --topic-dir <topicDir>", text)
        self.assertIn("topic-log.py status --topic-dir <topicDir> --json", text)
        self.assertIn("Valid phases are exactly:", text)
        self.assertIn("Valid next actions are exactly:", text)
        self.assertIn("--name <artifactName> --value <file>", text)
        self.assertIn("--operation-id <id> --description <description>", text)
        self.assertIn("run_claude_step()", text)
        self.assertIn("scenario_start_prompt()", text)
        self.assertIn("scenario_execute_prompt()", text)
        self.assertIn('run_agent_step "05-finalize" "$(scenario_finalize_prompt)"', text)
        self.assertNotIn("Only --host codex is currently supported", text)


if __name__ == "__main__":
    unittest.main()
