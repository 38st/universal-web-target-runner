from dataclasses import dataclass, field
from typing import Any


@dataclass
class RunContext:
    """Runtime data passed from runners into target adapters."""

    target_name: str
    fixed_account: dict[str, Any] | None = None
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class RunResult:
    """Normalized result shape for target adapters."""

    target_name: str
    status: str
    metadata: dict[str, Any] = field(default_factory=dict)
