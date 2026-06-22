import os
import time
from string import Template
from typing import Any

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from core.actions import click_element, type_text
from core.browser import create_browser_session
from core.config_loader import load_yaml_file
from core.context import RunContext, RunResult


DEFAULT_CONFIG_ENV = "GENERIC_SIGNUP_CONFIG"


def _selector_by(selector_type: str) -> str:
    selector_map = {
        "css": By.CSS_SELECTOR,
        "xpath": By.XPATH,
        "id": By.ID,
        "name": By.NAME,
        "tag": By.TAG_NAME,
    }
    normalized = (selector_type or "css").strip().lower()
    if normalized not in selector_map:
        raise ValueError(f"Unsupported selector type: {selector_type}")
    return selector_map[normalized]


def _render_value(value: Any, variables: dict[str, Any]) -> Any:
    if not isinstance(value, str):
        return value
    return Template(value).safe_substitute({key: str(val) for key, val in variables.items()})


def _load_target_config(context: RunContext) -> dict[str, Any]:
    config_path = context.options.get("target_config") or os.environ.get(DEFAULT_CONFIG_ENV)
    if not config_path:
        raise ValueError(
            "generic_signup requires --target-config or GENERIC_SIGNUP_CONFIG. "
            "Use it only for owned, test, or explicitly authorized flows."
        )
    config = load_yaml_file(config_path)
    if config.get("authorized") is not True:
        raise ValueError("generic_signup config must set authorized: true")
    return config


def _step_selector(step: dict[str, Any]) -> tuple[str, str]:
    selector = step.get("selector")
    if not selector:
        raise ValueError(f"Step missing selector: {step}")
    return _selector_by(step.get("by", "css")), selector


def execute_steps(driver, wait, steps: list[dict[str, Any]], variables: dict[str, Any]) -> None:
    """Execute a config-driven sequence of browser actions."""

    for index, raw_step in enumerate(steps, start=1):
        if not isinstance(raw_step, dict):
            raise ValueError(f"Step {index} must be a mapping")

        action = str(raw_step.get("action", "")).strip().lower()
        step = {key: _render_value(value, variables) for key, value in raw_step.items()}

        if action == "goto":
            url = step.get("url")
            if not url:
                raise ValueError(f"Step {index} missing url")
            driver.get(url)
        elif action == "wait":
            by, selector = _step_selector(step)
            wait.until(EC.presence_of_element_located((by, selector)))
        elif action == "fill":
            by, selector = _step_selector(step)
            value = step.get("value", "")
            element = wait.until(EC.element_to_be_clickable((by, selector)))
            element.click()
            element.clear()
            type_text(element, str(value))
        elif action == "click":
            by, selector = _step_selector(step)
            element = wait.until(EC.element_to_be_clickable((by, selector)))
            click_element(driver, element)
        elif action == "sleep":
            seconds = float(step.get("seconds", 1))
            time.sleep(seconds)
        elif action == "screenshot":
            path = step.get("path")
            if not path:
                raise ValueError(f"Step {index} missing path")
            driver.save_screenshot(path)
        else:
            raise ValueError(f"Unsupported step action at {index}: {action}")


class GenericSignupTarget:
    name = "generic_signup"
    description = "Config-driven browser workflow for authorized signup or form flows"

    def run(self, context: RunContext):
        config = _load_target_config(context)
        variables = dict(config.get("variables") or {})
        if context.fixed_account:
            variables.update(context.fixed_account)

        steps = config.get("steps")
        if not isinstance(steps, list) or not steps:
            raise ValueError("generic_signup config requires a non-empty steps list")

        target_name = str(config.get("name") or self.name)
        region_name = config.get("region")
        use_proxy = bool(config.get("use_configured_proxy", False))

        with create_browser_session(
            region_name=region_name,
            profile_prefix=f"{target_name}_",
            use_configured_proxy=use_proxy,
        ) as session:
            execute_steps(session.driver, session.wait, steps, variables)

        return RunResult(
            target_name=self.name,
            status="completed",
            metadata={"config_name": target_name},
        )


TARGET = GenericSignupTarget()
