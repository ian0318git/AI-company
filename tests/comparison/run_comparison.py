#!/usr/bin/env python3
"""CLI entry point for the multi-agent vs single-agent comparison experiment.

Usage
-----
    uv run python tests/comparison/run_comparison.py
    uv run python tests/comparison/run_comparison.py --task temperature_logger
    uv run python tests/comparison/run_comparison.py --output results/my_run.json
    uv run python tests/comparison/run_comparison.py --verbose

The script loads the specified task, executes both single-agent and multi-agent
modes, prints a formatted comparison table to stdout, and writes structured
results to ``comparison_result.json`` (or a custom path).
"""

from __future__ import annotations

import argparse
import logging
import sys


def _build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the comparison CLI."""
    parser = argparse.ArgumentParser(
        description="Run a multi-agent vs single-agent comparison experiment.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s                         # run with defaults\n"
            "  %(prog)s --task temperature_logger --output ./results/my_run.json\n"
            "  %(prog)s --verbose               # full debug logging\n"
        ),
    )
    parser.add_argument(
        "--task",
        default="temperature_logger",
        choices=["temperature_logger"],
        help="Task specification module to load (default: %(default)s).",
    )
    parser.add_argument(
        "--output",
        default="comparison_result.json",
        help=(
            "Path for the JSON export file "
            "(default: %(default)s in the current directory)."
        ),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Enable debug-level logging.",
    )
    return parser


def main() -> None:
    """Parse arguments and run the comparison."""
    parser: argparse.ArgumentParser = _build_parser()
    args: argparse.Namespace = parser.parse_args()

    # ------------------------------------------------------------------
    # Logging setup
    # ------------------------------------------------------------------
    log_level: int = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )

    # ------------------------------------------------------------------
    # Load task specification
    # ------------------------------------------------------------------
    if args.task == "temperature_logger":
        from tests.comparison.tasks import temperature_logger as task_mod
    else:
        # argparse restricts choices, so this branch is unreachable in practice,
        # but we keep it as a safety net for future extensibility.
        print(f"Unknown task: {args.task}", file=sys.stderr)
        sys.exit(1)

    task_spec: str = task_mod.TASK_SPEC
    logging.info("Loaded task: %s", args.task)

    # ------------------------------------------------------------------
    # Delegate to the runner
    # ------------------------------------------------------------------
    from tests.comparison.runner import run_comparison

    try:
        run_comparison(task_spec=task_spec, output_path=args.output)
    except KeyboardInterrupt:
        print("\nComparison interrupted by user.", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
