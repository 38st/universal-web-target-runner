import time
from string import Template
from typing import Any

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from core.actions import click_element, type_text
from core.browser import create_browser_session
from core.context import RunContext, RunResult
from core.target_config import load_target_config
from core.workflow import execute_workflow_steps, validate_workflow_steps


DEFAULT_CONFIG_ENV = "GENERIC_SIGNUP_CONFIG"
GENERIC_SIGNUP_STEP_ACTIONS = {
    "goto",
    "wait",
    "fill",
    "click",
    "sleep",
    "screenshot",
}
STEP_FIELD_REQUIREMENTS = {
    "goto": ("url",),
    "wait": ("selector",),
    "fill": ("selector",),
    "click": ("selector",),
    "screenshot": ("path",),
}


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
    return load_target_config(
        context.options.get("target_config"),
        env_vars=(DEFAULT_CONFIG_ENV,),
        target_name="generic_signup",
        missing_message=(
            "generic_signup requires --target-config or GENERIC_SIGNUP_CONFIG. "
            "Use it only for owned, test, or explicitly authorized flows."
        ),
        require_authorized=True,
        validator=_validate_generic_signup_config,
    )


def _validate_generic_signup_config(config: dict[str, Any], path=None) -> None:
    validate_workflow_steps(
        config.get("steps"),
        {action: None for action in GENERIC_SIGNUP_STEP_ACTIONS},
        required_fields=STEP_FIELD_REQUIREMENTS,
        source=f"generic_signup config {path}" if path else "generic_signup config",
        workflow_name="Generic signup",
    )


def _step_selector(step: dict[str, Any]) -> tuple[str, str]:
    selector = step.get("selector")
    if not selector:
        raise ValueError(f"Step missing selector: {step}")
    return _selector_by(step.get("by", "css")), selector


def _render_step(step: dict[str, Any], variables: dict[str, Any]) -> dict[str, Any]:
    return {key: _render_value(value, variables) for key, value in step.items()}


def _build_generic_signup_handlers(driver, wait, variables: dict[str, Any]):
    def handle_goto(step, runtime):
        rendered = _render_step(step, variables)
        driver.get(rendered["url"])

    def handle_wait(step, runtime):
        rendered = _render_step(step, variables)
        by, selector = _step_selector(rendered)
        wait.until(EC.presence_of_element_located((by, selector)))

    def handle_fill(step, runtime):
        rendered = _render_step(step, variables)
        by, selector = _step_selector(rendered)
        value = rendered.get("value", "")
        element = wait.until(EC.element_to_be_clickable((by, selector)))
        element.click()
        element.clear()
        type_text(element, str(value))

    def handle_click(step, runtime):
        rendered = _render_step(step, variables)
        by, selector = _step_selector(rendered)
        element = wait.until(EC.element_to_be_clickable((by, selector)))
        click_element(driver, element)

    def handle_sleep(step, runtime):
        rendered = _render_step(step, variables)
        seconds = float(rendered.get("seconds", 1))
        time.sleep(seconds)

    def handle_screenshot(step, runtime):
        rendered = _render_step(step, variables)
        driver.save_screenshot(rendered["path"])

    return {
        "goto": handle_goto,
        "wait": handle_wait,
        "fill": handle_fill,
        "click": handle_click,
        "sleep": handle_sleep,
        "screenshot": handle_screenshot,
    }


def execute_steps(driver, wait, steps: list[dict[str, Any]], variables: dict[str, Any]) -> None:
    """Execute a config-driven sequence of browser actions."""

    execute_workflow_steps(
        steps,
        _build_generic_signup_handlers(driver, wait, variables),
        {"variables": variables},
        workflow_name="Generic signup",
    )


class GenericSignupTarget:
    name = "generic_signup"
    description = "Config-driven browser workflow for authorized signup or form flows"

    def run(self, context: RunContext):
        config = _load_target_config(context)
        variables = dict(config.get("variables") or {})
        if context.fixed_account:
            variables.update(context.fixed_account)

        target_name = str(config.get("name") or self.name)
        region_name = config.get("region")
        use_proxy = bool(config.get("use_configured_proxy", False))

        with create_browser_session(
            region_name=region_name,
            profile_prefix=f"{target_name}_",
            use_configured_proxy=use_proxy,
        ) as session:
            execute_steps(session.driver, session.wait, config["steps"], variables)

        return RunResult(
            target_name=self.name,
            status="completed",
            metadata={"config_name": target_name},
        )


TARGET = GenericSignupTarget()
