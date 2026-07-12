import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]

EXPECTED_RUNTIME_SKILLS = {
    "using-as-usual",
    "hand-off",
    "find-cause",
    "start-work",
    "define-requirements",
    "writing-plan",
    "executing-plan",
    "review-execution",
    "cleanup-code",
    "finalize",
    "git-action",
    "manage-self-improvement",
    "search-long-term-memory",
    "explore-codebase",
}


class RuntimeSurfaceManifestTests(unittest.TestCase):
    def load_json(self, relative_path):
        return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))

    def public_skill_names(self):
        return {
            path.parent.name
            for path in (ROOT / "skills").glob("*/SKILL.md")
        }

    def frontmatter_value(self, source, key):
        lines = source.splitlines()
        self.assertGreaterEqual(len(lines), 3)
        self.assertEqual(lines[0], "---")
        for line in lines[1:]:
            if line == "---":
                break
            prefix = f"{key}:"
            if line.startswith(prefix):
                return line[len(prefix):].strip()
        return None

    def test_public_runtime_skill_surface_matches_expected_workflow(self):
        self.assertEqual(self.public_skill_names(), EXPECTED_RUNTIME_SKILLS)

    def test_public_skill_frontmatter_names_match_directories(self):
        for skill_name in sorted(EXPECTED_RUNTIME_SKILLS):
            path = ROOT / "skills" / skill_name / "SKILL.md"
            source = path.read_text(encoding="utf-8")
            self.assertEqual(self.frontmatter_value(source, "name"), skill_name)
            self.assertTrue(
                self.frontmatter_value(source, "description"),
                f"{path} should declare a description",
            )

    def test_codex_manifest_points_to_real_runtime_surfaces(self):
        manifest = self.load_json(".codex-plugin/plugin.json")
        self.assertEqual(manifest["name"], "as-usual")
        self.assertEqual(manifest["skills"], "./skills/")
        self.assertEqual(manifest["hooks"], "./hooks/hooks-codex.json")
        self.assertTrue((ROOT / "skills").is_dir())
        self.assertTrue((ROOT / "hooks/hooks-codex.json").is_file())
        self.assertTrue((ROOT / "hooks/run-hook.cmd").is_file())
        self.assertTrue((ROOT / "hooks/session-start").is_file())

    def test_claude_and_marketplace_versions_match(self):
        codex = self.load_json(".codex-plugin/plugin.json")
        claude = self.load_json(".claude-plugin/plugin.json")
        claude_marketplace = self.load_json(".claude-plugin/marketplace.json")
        codex_marketplace = self.load_json(".agents/plugins/marketplace.json")

        self.assertEqual(claude["name"], codex["name"])
        self.assertEqual(claude["version"], codex["version"])
        self.assertEqual(claude_marketplace["plugins"][0]["name"], codex["name"])
        self.assertEqual(claude_marketplace["plugins"][0]["version"], codex["version"])
        self.assertEqual(codex_marketplace["plugins"][0]["name"], codex["name"])
        self.assertEqual(codex_marketplace["plugins"][0]["source"]["path"], "./plugins/as-usual")

    def test_hook_configs_invoke_session_start_runner(self):
        for relative_path, expected_root_var in [
            ("hooks/hooks.json", "CLAUDE_PLUGIN_ROOT"),
            ("hooks/hooks-codex.json", "PLUGIN_ROOT"),
        ]:
            config = self.load_json(relative_path)
            hooks = config["hooks"]["SessionStart"][0]["hooks"]
            self.assertEqual(len(hooks), 1)
            command = hooks[0]["command"]
            self.assertIn(expected_root_var, command)
            self.assertIn("hooks/run-hook.cmd", command)
            self.assertIn("session-start", command)


if __name__ == "__main__":
    unittest.main()
