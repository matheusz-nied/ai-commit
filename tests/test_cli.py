import unittest

from ai_commit.cli import build_parser, resolve_bool, resolve_int
from ai_commit.errors import AICommitError


class CliTests(unittest.TestCase):
    def test_parser_defaults_staged_only_to_none(self):
        args = build_parser().parse_args([])

        self.assertIsNone(args.staged_only)

    def test_parser_handles_staged_only_and_provider(self):
        args = build_parser().parse_args(["--provider", "opencode", "--staged-only", "--dry-run", "--quiet"])

        self.assertEqual(args.provider, "opencode")
        self.assertTrue(args.staged_only)
        self.assertTrue(args.dry_run)
        self.assertTrue(args.quiet)

    def test_resolve_bool_accepts_common_strings(self):
        self.assertTrue(resolve_bool("yes", "confirm"))
        self.assertFalse(resolve_bool("off", "confirm"))

    def test_resolve_bool_rejects_invalid_values(self):
        with self.assertRaises(AICommitError):
            resolve_bool("maybe", "confirm")

    def test_resolve_int_requires_positive_integer(self):
        self.assertEqual(resolve_int("10", "max_diff_chars"), 10)
        with self.assertRaises(AICommitError):
            resolve_int("0", "max_diff_chars")


if __name__ == "__main__":
    unittest.main()
