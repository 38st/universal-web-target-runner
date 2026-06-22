from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def resolve_project_path(path_value: str | Path) -> Path:
    """Resolve a path relative to the project root when it is not absolute."""

    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_yaml_file(path_value: str | Path) -> dict[str, Any]:
    """Load a YAML file and return an object mapping."""

    path = resolve_project_path(path_value)
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")
    return data
