import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from core.storage import append_jsonl, read_jsonl
from runners.main import _normalize_target_name
from services.email_service import message_matches_filters
from targets.web_signup import (
    _markers,
    execute_web_signup_steps,
    load_web_signup_config,
)
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

    def test_web_signup_config_loads_step_fields_and_markers(self):
        target_config = load_web_signup_config()

        self.assertEqual(
            [step["action"] for step in target_config["steps"]],
            [
                "open_start_page",
                "dismiss_cookies",
                "enter_signup_flow",
                "submit_email",
                "submit_name",
                "fetch_and_submit_otp",
                "set_password",
                "detect_result",
            ],
        )
        self.assertNotIn("selectors", target_config)
        self.assertEqual(target_config["steps"][0]["url"], "https://builder.aws.com/start")
        self.assertEqual(
            target_config["steps"][3]["input_css"],
            'input[placeholder="username@example.com"]',
        )
        self.assertEqual(
            target_config["steps"][3]["submit_css"],
            '[data-testid="test-primary-button"]',
        )
        self.assertIn("account created", _markers(target_config, "success"))

    def test_web_signup_config_validates_only_selected_steps(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "minimal_web_signup.yaml"
            path.write_text(
                "\n".join([
                    "name: minimal_web_signup",
                    "steps:",
                    "  - action: open_start_page",
                    "    url: https://example.test",
                    "",
                ]),
                encoding="utf-8",
            )

            target_config = load_web_signup_config(path)

        self.assertEqual(target_config["steps"][0]["action"], "open_start_page")

    def test_web_signup_config_accepts_legacy_selector_fallbacks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "legacy_web_signup.yaml"
            path.write_text(
                "\n".join([
                    "name: legacy_web_signup",
                    "steps:",
                    "  - action: submit_email",
                    "selectors:",
                    "  email_input_css: input[type=email]",
                    "  primary_button_css: button[type=submit]",
                    "",
                ]),
                encoding="utf-8",
            )

            target_config = load_web_signup_config(path)

        self.assertEqual(target_config["steps"][0]["action"], "submit_email")

    def test_web_signup_steps_execute_from_config_order(self):
        target_config = {
            "steps": [
                {"action": "open_start_page", "url": "https://example.test"},
                {"action": "dismiss_cookies", "accept_xpaths": ["//button"]},
                {"action": "enter_signup_flow", "texts": ["Sign up"]},
                {
                    "action": "submit_email",
                    "input_css": "input[type=email]",
                    "submit_css": "button",
                },
                {"action": "submit_name", "input_css": "input[name=name]"},
                {
                    "action": "fetch_and_submit_otp",
                    "input_css": "input[name=otp]",
                },
                {"action": "set_password", "input_css": "input[type=password]"},
                {"action": "detect_result"},
            ],
        }
        runtime = {
            "fixed_account": None,
            "email_address": "user@example.test",
            "jwt_token": "jwt",
            "email_filters": {},
            "success_markers": [],
            "blocking_markers": [],
            "output_file": "accounts.jsonl",
        }
        calls = []

        with (
            redirect_stdout(io.StringIO()),
            patch(
                "targets.web_signup.open_start_page",
                side_effect=lambda *args, **kwargs: calls.append("open_start_page"),
            ),
            patch(
                "targets.web_signup.dismiss_cookies",
                side_effect=lambda *args, **kwargs: calls.append("dismiss_cookies") or True,
            ),
            patch(
                "targets.web_signup.enter_signup_flow",
                side_effect=lambda *args, **kwargs: calls.append("enter_signup_flow") or True,
            ),
            patch(
                "targets.web_signup.submit_email",
                side_effect=lambda *args, **kwargs: calls.append("submit_email"),
            ),
            patch(
                "targets.web_signup.submit_name",
                side_effect=lambda *args, **kwargs: calls.append("submit_name") or "Example User",
            ),
            patch(
                "targets.web_signup.fetch_and_submit_otp",
                side_effect=lambda *args, **kwargs: calls.append("fetch_and_submit_otp") or "123456",
            ),
            patch(
                "targets.web_signup.set_password",
                side_effect=lambda *args, **kwargs: calls.append("set_password") or ("Passw0rd!", True),
            ),
            patch(
                "targets.web_signup.detect_result",
                side_effect=lambda *args, **kwargs: calls.append("detect_result") or "registered",
            ),
        ):
            execute_web_signup_steps(object(), object(), target_config, runtime)

        self.assertEqual(
            calls,
            [
                "open_start_page",
                "dismiss_cookies",
                "enter_signup_flow",
                "submit_email",
                "submit_name",
                "fetch_and_submit_otp",
                "set_password",
                "detect_result",
            ],
        )
        self.assertEqual(runtime["random_name"], "Example User")
        self.assertEqual(runtime["verification_code"], "123456")
        self.assertEqual(runtime["password"], "Passw0rd!")
        self.assertTrue(runtime["password_submitted"])
        self.assertEqual(runtime["status"], "registered")

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
