import argparse
import unittest

from ai_commit.cli import build_parser, resolve_bool, resolve_int, resolve_model_selection
from ai_commit.errors import AICommitError


class CliTests(unittest.TestCase):
    def test_parser_defaults_staged_only_to_none(self):
        args = build_parser().parse_args([])

        self.assertIsNone(args.staged_only)
        self.assertIsNone(args.shortcut)

    def test_parser_handles_staged_only_and_provider(self):
        args = build_parser().parse_args(
            [
                "--provider",
                "opencode",
                "--model",
                "opencode-go/kimi-k2.5",
                "--staged-only",
                "--dry-run",
                "--quiet",
            ]
        )

        self.assertEqual(args.provider, "opencode")
        self.assertEqual(args.model, "opencode-go/kimi-k2.5")
        self.assertTrue(args.staged_only)
        self.assertTrue(args.dry_run)
        self.assertTrue(args.quiet)

    def test_parser_handles_model_shortcut(self):
        args = build_parser().parse_args(["kimi", "--dry-run"])

        self.assertEqual(args.shortcut, "kimi")
        self.assertTrue(args.dry_run)

    def test_default_model_selection_uses_config(self):
        args = argparse.Namespace(shortcut=None, provider=None, model=None)

        selection = resolve_model_selection(
            args,
            {
                "provider": "codex",
                "codex_model": "gpt-5.4-mini",
                "opencode_model": "opencode-go/kimi-k2.5",
            },
        )

        self.assertEqual(selection.provider, "codex")
        self.assertEqual(selection.model, "gpt-5.4-mini")

    def test_kimi_shortcut_forces_opencode_go_model(self):
        args = argparse.Namespace(shortcut="kimi", provider=None, model=None)

        selection = resolve_model_selection(
            args,
            {
                "provider": "codex",
                "codex_model": "gpt-5.4-mini",
                "opencode_model": "opencode-go/kimi-k2.5",
            },
        )

        self.assertEqual(selection.provider, "opencode")
        self.assertEqual(selection.model, "opencode-go/kimi-k2.5")

    def test_shortcuts_resolve_to_expected_models(self):
        config = {
            "provider": "codex",
            "codex_model": "gpt-5.4-mini",
            "opencode_model": "opencode-go/kimi-k2.5",
        }

        expected = {
            "gpt": ("codex", "gpt-5.4-mini"),
            "codex": ("codex", "gpt-5.4-mini"),
            "kimi": ("opencode", "opencode-go/kimi-k2.5"),
            "qwen": ("opencode", "opencode-go/qwen3.6-plus"),
            "glm": ("opencode", "opencode-go/glm-5"),
            "minimax": ("opencode", "opencode-go/minimax-m2.5"),
        }

        for shortcut, values in expected.items():
            with self.subTest(shortcut=shortcut):
                args = argparse.Namespace(shortcut=shortcut, provider=None, model=None)
                selection = resolve_model_selection(args, config)
                self.assertEqual((selection.provider, selection.model), values)

    def test_model_flag_overrides_shortcut_model(self):
        args = argparse.Namespace(shortcut="kimi", provider=None, model="opencode-go/custom")

        selection = resolve_model_selection(
            args,
            {
                "provider": "codex",
                "codex_model": "gpt-5.4-mini",
                "opencode_model": "opencode-go/kimi-k2.5",
            },
        )

        self.assertEqual(selection.provider, "opencode")
        self.assertEqual(selection.model, "opencode-go/custom")

    def test_provider_flag_overrides_shortcut_provider(self):
        args = argparse.Namespace(shortcut="kimi", provider="codex", model=None)

        selection = resolve_model_selection(
            args,
            {
                "provider": "codex",
                "codex_model": "gpt-5.4-mini",
                "opencode_model": "opencode-go/kimi-k2.5",
            },
        )

        self.assertEqual(selection.provider, "codex")
        self.assertEqual(selection.model, "opencode-go/kimi-k2.5")

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
