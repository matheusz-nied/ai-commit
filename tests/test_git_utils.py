import unittest

from ai_commit.git_utils import parse_name_status


class ParseNameStatusTests(unittest.TestCase):
    def test_parses_added_modified_and_deleted_files(self):
        files = parse_name_status("M\tsrc/foo.ts\nA\ttests/foo.test.ts\nD\told.txt\n")

        self.assertEqual([item.status for item in files], ["M", "A", "D"])
        self.assertEqual([item.path for item in files], ["src/foo.ts", "tests/foo.test.ts", "old.txt"])

    def test_parses_renamed_files(self):
        files = parse_name_status("R100\told_name.py\tnew_name.py\n")

        self.assertEqual(files[0].status, "R")
        self.assertEqual(files[0].path, "old_name.py -> new_name.py")

    def test_ignores_blank_lines(self):
        self.assertEqual(parse_name_status("\n\n"), [])


if __name__ == "__main__":
    unittest.main()
