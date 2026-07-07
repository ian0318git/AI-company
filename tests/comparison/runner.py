"""Comparison runner -- orchestrates a single agent-vs-multi-agent experiment.

Loads a task specification, runs both execution modes, collects and compares
metrics, then prints a report and exports the data as JSON.
"""

from __future__ import annotations

import logging
import sys
import time
from typing import Any

from tests.comparison import metrics as metrics_mod
from tests.comparison import report as report_mod
from tests.comparison.modes import multi as multi_mode
from tests.comparison.modes import single as single_mode
from tests.comparison.tasks import temperature_logger

logger = logging.getLogger(__name__)


def run_comparison(
    task_spec: str | None = None,
    output_path: str = "comparison_result.json",
) -> dict[str, Any]:
    """Run the full single-vs-multi comparison experiment.

    Parameters
    ----------
    task_spec : str, optional
        The task specification text.  Defaults to
        ``temperature_logger.TASK_SPEC``.
    output_path : str
        Path for the JSON export file.  Defaults to
        ``comparison_result.json`` in the current working directory.

    Returns
    -------
    dict
        The full comparison dictionary from ``metrics.compute_comparison``.
    """
    if task_spec is None:
        task_spec = temperature_logger.TASK_SPEC

    overall_start: float = time.monotonic()
    errors: list[str] = []

    # ------------------------------------------------------------------
    # 1. Validate the task spec (basic sanity)
    # ------------------------------------------------------------------
    validate_result: tuple[bool, list[str]] = temperature_logger.validate(
        {"text": task_spec}
    )
    if not validate_result[0]:
        logger.warning(
            "Task spec self-validation produced warnings; continuing anyway: %s",
            validate_result[1],
        )

    # ------------------------------------------------------------------
    # 2. Check for API key early -- fail fast before any work.
    # ------------------------------------------------------------------
    import os

    if not os.environ.get("ANTHROPIC_API_KEY"):
        report_mod.print_error(
            "ANTHROPIC_API_KEY environment variable is not set.\n"
            "  Set it with:  export ANTHROPIC_API_KEY='sk-ant-...'\n"
            "  Then re-run:  uv run python tests/comparison/run_comparison.py"
        )
        sys.exit(1)

    # ------------------------------------------------------------------
    # 3. Run single-agent mode
    # ------------------------------------------------------------------
    print()
    print("=" * 50)
    print(" RUNNING SINGLE-AGENT MODE")
    print("=" * 50)
    try:
        single_start: float = time.monotonic()
        single_result: dict[str, Any] = single_mode.run(task_spec)
        single_duration: float = time.monotonic() - single_start
        logger.info(
            "Single-agent mode completed in %.1fs (wall clock)", single_duration
        )
    except Exception as exc:
        errors.append(f"Single-agent mode raised an exception: {exc}")
        logger.exception("Single-agent mode failed")
        report_mod.print_error(f"Single-agent mode crashed: {exc}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # 4. Run multi-agent mode
    # ------------------------------------------------------------------
    print()
    print("=" * 50)
    print(" RUNNING MULTI-AGENT MODE")
    print("=" * 50)
    try:
        multi_start: float = time.monotonic()
        multi_result: dict[str, Any] = multi_mode.run(task_spec)
        multi_duration: float = time.monotonic() - multi_start
        logger.info(
            "Multi-agent mode completed in %.1fs (wall clock)", multi_duration
        )
    except Exception as exc:
        errors.append(f"Multi-agent mode raised an exception: {exc}")
        logger.exception("Multi-agent mode failed")
        report_mod.print_error(f"Multi-agent mode crashed: {exc}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # 5. Extract & merge metrics
    # ------------------------------------------------------------------
    single_metrics: dict[str, Any] = single_result.get("metrics", {})
    multi_metrics: dict[str, Any] = multi_result.get("metrics", {})

    # Validate single-agent response.
    single_text: str = single_result.get("response_text", "")
    single_validation: tuple[bool, list[str]] = temperature_logger.validate(
        {"text": single_text}
    )
    single_metrics["validation_passed"] = single_validation[0]
    single_metrics["validation_messages"] = single_validation[1]
    if not single_validation[0] and not single_metrics.get("errors"):
        single_metrics["errors"] = single_validation[1]

    # Validate multi-agent response (use Agent 2's output text).
    multi_text: str = multi_result.get("response_text", "")
    if not multi_text:
        multi_text = multi_result.get("agent1_text", "")
    multi_validation: tuple[bool, list[str]] = temperature_logger.validate(
        {"text": multi_text}
    )
    multi_metrics["validation_passed"] = multi_validation[0]
    multi_metrics["validation_messages"] = multi_validation[1]
    if not multi_validation[0] and not multi_metrics.get("errors"):
        multi_metrics["errors"] = multi_validation[1]

    # Ensure the completion status reflects validation.
    if not single_validation[0]:
        single_metrics["task_completed"] = False
    if not multi_validation[0]:
        multi_metrics["task_completed"] = False

    # ------------------------------------------------------------------
    # 6. Compute comparison
    # ------------------------------------------------------------------
    comparison: dict[str, Any] = metrics_mod.compute_comparison(
        single_metrics, multi_metrics
    )

    # ------------------------------------------------------------------
    # 7. Print report
    # ------------------------------------------------------------------
    report_mod.print_comparison_table(comparison)

    # ------------------------------------------------------------------
    # 8. Export JSON
    # ------------------------------------------------------------------
    exported_path: str = report_mod.export_json(comparison, output_path)

    overall_elapsed: float = time.monotonic() - overall_start
    logger.info(
        "Full comparison completed in %.1fs. Results written to %s",
        overall_elapsed,
        exported_path,
    )

    return comparison


# ---------------------------------------------------------------------------
# CLI convenience
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    run_comparison()
