import tempfile
import unittest
from pathlib import Path

from core.storage import append_jsonl, read_jsonl
from runners.main import _normalize_target_name
from services.email_service import message_matches_filters
from targets.web_signup import _markers, _selectors, load_web_signup_config
from targets.generic_signup import _render_value
from targets.registry import get_target, list_targets


class UniversalRunnerTests(unittest.TestCase):
    def test_registry_lists_web_signup_target(self):
        self.assertIn("web_signup", list_targets())

    def test_registry_accepts_legacy_aws_builder_alias(self):
        self.assertEqual(get_target("aws_builder").name, "web_signup")
        self.assertEqual(get_target("aws-builder").name, "web_signup")

    def test_registry_lists_generic_signup_target(self):
        self.assertIn("generic_signup", list_targets())

    def test_registry_rejects_unknown_target(self):
        with self.assertRaises(ValueError):
            get_target("missing-target")

    def test_target_name_normalization(self):
        self.assertEqual(_normalize_target_name("web-signup"), "web_signup")

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

    def test_web_signup_config_loads_selectors_and_markers(self):
        target_config = load_web_signup_config()

        self.assertEqual(target_config["start_url"], "https://builder.aws.com/start")
        self.assertIn("email_input_css", _selectors(target_config))
        self.assertIn("account created", _markers(target_config, "success"))

    def test_email_filters_are_configurable(self):
        filters = {
            "sender_contains": ["example"],
            "subject_contains": ["login"],
            "body_contains": ["approval"],
        }

        self.assertTrue(message_matches_filters(sender="noreply@example.test", filters=filters))
        self.assertTrue(message_matches_filters(subject="Login code", filters=filters))
        self.assertTrue(message_matches_filters(body="Approval code 123456", filters=filters))
        self.assertFalse(message_matches_filters(sender="other.test", subject="hello", body="nothing", filters=filters))


if __name__ == "__main__":
    unittest.main()
