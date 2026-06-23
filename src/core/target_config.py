import os
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

from core.config_loader import load_yaml_file, resolve_project_path


TargetConfigValidator = Callable[[dict[str, Any], Path], None]


def select_target_config_path(
    config_path: str | Path | None = None,
    *,
    env_vars: Iterable[str] = (),
    default_path: str | Path | None = None,
) -> str | Path | None:
    """Return the first configured target config path from args, env, or default."""

    if config_path:
        return config_path

    for env_var in env_vars:
        env_path = os.environ.get(env_var)
        if env_path:
            return env_path

    return default_path


def load_target_config(
    config_path: str | Path | None = None,
    *,
    env_vars: Iterable[str] = (),
    default_path: str | Path | None = None,
    target_name: str = "target",
    missing_message: str | None = None,
    require_authorized: bool = False,
    validator: TargetConfigValidator | None = None,
) -> dict[str, Any]:
    """Load and validate a target config from explicit path, env var, or default."""

    selected_path = select_target_config_path(
        config_path,
        env_vars=env_vars,
        default_path=default_path,
    )
    if not selected_path:
        raise ValueError(missing_message or f"{target_name} requires a target config path")

    path = resolve_project_path(selected_path)
    if not path.exists():
        raise FileNotFoundError(f"{target_name} target config not found: {path}")

    config = load_yaml_file(path)
    if require_authorized and config.get("authorized") is not True:
        raise ValueError(f"{target_name} config must set authorized: true")

    if validator:
        validator(config, path)

    return config
