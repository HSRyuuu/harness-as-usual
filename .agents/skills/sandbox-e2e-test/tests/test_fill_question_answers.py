import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[4]
HELPER_PATH = ROOT / ".agents/skills/sandbox-e2e-test/scripts/fill-question-answers.py"


def load_helper():
    module_spec = importlib.util.spec_from_file_location("fill_question_answers", HELPER_PATH)
    module = importlib.util.module_from_spec(module_spec)
    assert module_spec.loader is not None
    module_spec.loader.exec_module(module)
    return module


class FillQuestionAnswersTests(unittest.TestCase):
    def test_fills_localized_answer_heading(self):
        helper = load_helper()
        with tempfile.TemporaryDirectory() as tmp:
            topic = Path(tmp)
            question_file = topic / "question-c1.md"
            question_file.write_text(
                "# Demo 질문 c1\n\n"
                "## Question 1: Scope?\n\n"
                "### ✍️ Answer\n\n"
                "[Answer]:\n",
                encoding="utf-8",
            )

            changed = helper.fill_answers(topic)

            self.assertEqual(changed, [question_file])
            text = question_file.read_text(encoding="utf-8")
            self.assertIn("[Answer]: A) Full stack", text)

    def test_fills_answer_after_new_prompt_line(self):
        helper = load_helper()
        with tempfile.TemporaryDirectory() as tmp:
            topic = Path(tmp)
            question_file = topic / "question-c1.md"
            question_file.write_text(
                "# Demo 질문 c1\n\n"
                "## 💡 Question 1: Scope?\n\n"
                "### 왜 중요한가요?\n\n"
                "Scope changes implementation.\n\n"
                "### Requirements 반영\n\n"
                "Requirements scope.\n\n"
                "### 선택\n\n"
                "A) Full stack\n\n"
                "B) Backend only\n\n"
                "X) Other (`[Answer]:` 뒤에 직접 작성)\n\n"
                "**추천**: A를 추천합니다.\n\n"
                "✅ 답변을 입력하세요.\n"
                "[Answer]:\n",
                encoding="utf-8",
            )

            changed = helper.fill_answers(topic)

            self.assertEqual(changed, [question_file])
            text = question_file.read_text(encoding="utf-8")
            self.assertIn("[Answer]: A) Full stack", text)


if __name__ == "__main__":
    unittest.main()
