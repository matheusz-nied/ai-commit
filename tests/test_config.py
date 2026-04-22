import json
import tempfile
import unittest
from pathlib import Path

from ai_commit.config import load_config
from ai_commit.errors import AICommitError


class LoadConfigTests(unittest.TestCase):
    def test_returns_defaults_when_file_does_not_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = load_config(Path(tmp) / "missing.json")

        self.assertEqual(config["provider"], "codex")
        self.assertFalse(config["staged_only"])

    def test_merges_user_config_with_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text(json.dumps({"provider": "opencode"}), encoding="utf-8")

            config = load_config(path)

        self.assertEqual(config["provider"], "opencode")
        self.assertIn("codex_model", config)

    def test_rejects_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text("{", encoding="utf-8")

            with self.assertRaises(AICommitError):
                load_config(path)


if __name__ == "__main__":
    unittest.main()
