from collections.abc import Callable, Mapping
from typing import Any


StepHandler = Callable[[dict[str, Any], dict[str, Any]], None]
StepValidator = Callable[[dict[str, Any], int, list[str]], None]


def normalize_step(raw_step: Any, index: int, *, workflow_name: str = "Workflow") -> dict[str, Any]:
    """Normalize a YAML step into a mapping with a canonical action name."""

    if isinstance(raw_step, str):
        step = {"action": raw_step}
    elif isinstance(raw_step, dict):
        step = dict(raw_step)
    else:
        raise ValueError(f"{workflow_name} step {index} must be a string or mapping")

    action = str(step.get("action", "")).strip()
    if not action:
        raise ValueError(f"{workflow_name} step {index} is missing action")

    step["action"] = action.lower().replace("-", "_")
    return step


def step_enabled(step: Mapping[str, Any]) -> bool:
    """Return False only when a step explicitly disables itself."""

    return step.get("enabled", True) is not False


def resolve_step_config(
    target_config: Mapping[str, Any],
    step: Mapping[str, Any],
    *,
    legacy_field_map: Mapping[str, Mapping[str, str]] | None = None,
    legacy_selectors_key: str = "selectors",
) -> dict[str, Any]:
    """Merge target-specific compatibility fields into a normalized step."""

    merged = dict(step)
    field_map = (legacy_field_map or {}).get(str(merged.get("action")), {})
    legacy_selectors = target_config.get(legacy_selectors_key) or {}
    if not isinstance(legacy_selectors, Mapping):
        legacy_selectors = {}

    for step_key, legacy_key in field_map.items():
        if merged.get(step_key) is None and legacy_key in legacy_selectors:
            merged[step_key] = legacy_selectors[legacy_key]

    return merged


def iter_workflow_steps(
    steps: list[Any],
    *,
    target_config: Mapping[str, Any] | None = None,
    legacy_field_map: Mapping[str, Mapping[str, str]] | None = None,
    workflow_name: str = "Workflow",
):
    """Yield normalized and resolved steps with one-based indexes."""

    target_config = target_config or {}
    for index, raw_step in enumerate(steps, start=1):
        step = normalize_step(raw_step, index, workflow_name=workflow_name)
        step = resolve_step_config(
            target_config,
            step,
            legacy_field_map=legacy_field_map,
        )
        yield index, step


def validate_workflow_steps(
    steps: Any,
    handlers: Mapping[str, Any],
    *,
    required_fields: Mapping[str, tuple[str, ...]] | None = None,
    target_config: Mapping[str, Any] | None = None,
    legacy_field_map: Mapping[str, Mapping[str, str]] | None = None,
    step_validators: Mapping[str, StepValidator] | None = None,
    source: str = "Workflow config",
    workflow_name: str = "Workflow",
) -> None:
    """Validate step structure, handler support, and handler field requirements."""

    missing: list[str] = []
    if not isinstance(steps, list) or not steps:
        missing.append("steps")
    else:
        for index, step in iter_workflow_steps(
            steps,
            target_config=target_config,
            legacy_field_map=legacy_field_map,
            workflow_name=workflow_name,
        ):
            if not step_enabled(step):
                continue

            action = step["action"]
            if action not in handlers:
                raise ValueError(f"{source} has unsupported step action at steps[{index}]: {action}")

            missing.extend(
                f"steps[{index}].{key} for {action}"
                for key in (required_fields or {}).get(action, ())
                if not step.get(key)
            )

            validator = (step_validators or {}).get(action)
            if validator:
                validator(step, index, missing)

    if missing:
        raise ValueError(f"{source} is missing: {', '.join(missing)}")


def execute_workflow_steps(
    steps: list[Any],
    handlers: Mapping[str, StepHandler],
    runtime: dict[str, Any],
    *,
    target_config: Mapping[str, Any] | None = None,
    legacy_field_map: Mapping[str, Mapping[str, str]] | None = None,
    workflow_name: str = "Workflow",
) -> dict[str, Any]:
    """Execute a config-driven workflow using registered action handlers."""

    for index, step in iter_workflow_steps(
        steps,
        target_config=target_config,
        legacy_field_map=legacy_field_map,
        workflow_name=workflow_name,
    ):
        if not step_enabled(step):
            print(f"\nSkipping disabled workflow step {index}/{len(steps)}: {step['action']}")
            continue

        action = step["action"]
        handler = handlers.get(action)
        if not handler:
            raise ValueError(f"Unsupported workflow step action: {action}")

        print(f"\nWorkflow step {index}/{len(steps)}: {action}")
        try:
            handler(step, runtime)
        except Exception as e:
            if step.get("optional") is True:
                print(f"⚠️ Optional workflow step failed ({action}): {e}")
                continue
            raise

    return runtime
