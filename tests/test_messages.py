import unittest

from ai_commit.errors import AICommitError
from ai_commit.messages import sanitize_message


class SanitizeMessageTests(unittest.TestCase):
    def test_returns_first_useful_line(self):
        self.assertEqual(
            sanitize_message("feat(cli): add provider selection\n\nextra text"),
            "feat(cli): add provider selection",
        )

    def test_removes_markdown_fence_and_prefix(self):
        self.assertEqual(
            sanitize_message('```text\nCommit message: "fix: handle empty diff"\n```'),
            "fix: handle empty diff",
        )

    def test_truncates_long_messages(self):
        message = sanitize_message("feat: " + "a" * 200, max_length=20)
        self.assertEqual(len(message), 20)

    def test_rejects_empty_message(self):
        with self.assertRaises(AICommitError):
            sanitize_message("   \n")


if __name__ == "__main__":
    unittest.main()
