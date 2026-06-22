#!/usr/bin/env python3
"""
Universal Web Target Runner entry point.

Site-specific behavior lives in target adapters. `aws_builder` is the default
built-in target for backward compatibility.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.context import RunContext
from targets.registry import get_target, list_targets


DEFAULT_TARGET = "aws_builder"


def _normalize_target_name(target_name: str | None) -> str:
    return (target_name or os.environ.get("TARGET_NAME") or DEFAULT_TARGET).strip().lower().replace("-", "_")


def run(target_name: str | dict[str, Any] | None = None, fixed_account: dict[str, Any] | None = None, **options):
    """
    Run a target adapter.

    Backward compatibility:
    - run() still runs the default target.
    - run(fixed_account=account) still works for Outlook-based runs.
    - run(account_dict) is treated as the old positional fixed_account style.
    """

    if isinstance(target_name, dict) and fixed_account is None:
        fixed_account = target_name
        target_name = DEFAULT_TARGET

    normalized_target = _normalize_target_name(target_name if isinstance(target_name, str) else None)
    context = RunContext(
        target_name=normalized_target,
        fixed_account=fixed_account,
        options=options,
    )
    target = get_target(normalized_target)
    return target.run(context)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a configured web automation target")
    parser.add_argument(
        "--target",
        default=os.environ.get("TARGET_NAME", DEFAULT_TARGET),
        help=f"Target to run (default: {DEFAULT_TARGET})",
    )
    parser.add_argument(
        "--list-targets",
        action="store_true",
        help="List available targets and exit",
    )
    parser.add_argument(
        "--target-config",
        help="Path to a target-specific YAML config",
    )
    return parser


def main(argv: list[str] | None = None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_targets:
        for target_name in list_targets():
            print(target_name)
        return 0

    run(target_name=args.target, target_config=args.target_config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
