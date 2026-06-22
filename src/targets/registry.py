from importlib import import_module

from targets.base import TargetAdapter


_TARGET_MODULES = {
    "web_signup": "targets.web_signup",
    "generic_signup": "targets.generic_signup",
}

_TARGET_ALIASES = {
    "aws_builder": "web_signup",
}

DEFAULT_TARGET = "web_signup"


def list_targets() -> list[str]:
    """Return registered target names."""

    return sorted(_TARGET_MODULES)


def get_target(name: str) -> TargetAdapter:
    """Load a target adapter by name."""

    target_name = (name or DEFAULT_TARGET).strip().lower().replace("-", "_")
    target_name = _TARGET_ALIASES.get(target_name, target_name)
    module_path = _TARGET_MODULES.get(target_name)
    if not module_path:
        available = ", ".join(list_targets())
        raise ValueError(f"Unknown target '{name}'. Available targets: {available}")

    module = import_module(module_path)
    target = getattr(module, "TARGET", None)
    if target is None:
        raise ValueError(f"Target module '{module_path}' does not expose TARGET")
    return target
