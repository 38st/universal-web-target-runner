import tempfile
import unittest
from pathlib import Path

from core.storage import append_jsonl, read_jsonl
from runners.main import _normalize_target_name
from targets.generic_signup import _render_value
from targets.registry import get_target, list_targets


class UniversalRunnerTests(unittest.TestCase):
    def test_registry_lists_aws_builder_target(self):
        self.assertIn("aws_builder", list_targets())

    def test_registry_lists_generic_signup_target(self):
        self.assertIn("generic_signup", list_targets())

    def test_registry_rejects_unknown_target(self):
        with self.assertRaises(ValueError):
            get_target("missing-target")

    def test_target_name_normalization(self):
        self.assertEqual(_normalize_target_name("aws-builder"), "aws_builder")

    def test_jsonl_storage_round_trip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "rows.jsonl"
            append_jsonl(path, {"target": "demo", "status": "ok"})

            self.assertEqual(read_jsonl(path), [{"target": "demo", "status": "ok"}])

    def test_generic_signup_template_rendering(self):
        rendered = _render_value("hello $name <$email>", {
            "name": "Example User",
            "email": "user@example.test",
        })

        self.assertEqual(rendered, "hello Example User <user@example.test>")


if __name__ == "__main__":
    unittest.main()
