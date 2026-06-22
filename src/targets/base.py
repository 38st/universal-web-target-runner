from typing import Protocol, runtime_checkable

from core.context import RunContext


@runtime_checkable
class TargetAdapter(Protocol):
    """Site-specific workflow adapter."""

    name: str
    description: str

    def run(self, context: RunContext):
        """Run the target workflow."""
