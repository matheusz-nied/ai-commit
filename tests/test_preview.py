import unittest

from ai_commit.git_utils import ChangedFile
from ai_commit.preview import render_preview


class RenderPreviewTests(unittest.TestCase):
    def test_renders_expected_plain_preview(self):
        preview = render_preview(
            [
                ChangedFile("M", "src/foo.ts"),
                ChangedFile("A", "tests/foo.test.ts"),
            ],
            "feat(cli): add provider selection",
            color=False,
        )

        self.assertEqual(
            preview,
            "\n".join(
                [
                    "Files changed:",
                    "  M src/foo.ts",
                    "  A tests/foo.test.ts",
                    "",
                    "Suggested:",
                    "  feat(cli): add provider selection",
                ]
            ),
        )

    def test_renders_empty_file_list(self):
        preview = render_preview([], "chore: update project", color=False)

        self.assertIn("  (none)", preview)
        self.assertIn("  chore: update project", preview)


if __name__ == "__main__":
    unittest.main()
