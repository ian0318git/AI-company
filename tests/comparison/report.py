"""Report generation for the multi-agent comparison experiment.

Produces a human-readable ASCII table on stdout and writes a structured JSON
export to ``comparison_result.json``.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


def print_comparison_table(comparison: dict[str, Any]) -> None:
    """Print a formatted ASCII comparison table to stdout.

    The table shows quantitative metrics (tokens, duration, cost) side-by-side
    with deltas, followed by quality scores.

    Parameters
    ----------
    comparison : dict
        The dict returned by ``metrics.compute_comparison``.
    """
    sep_line: str = "=" * 71
    dash_line: str = "-" * 71

    # Determine task name from the raw metrics (best-effort).
    task_name: str = "Temperature Logger"

    print()
    print(sep_line)
    print(f" COMPARISON RESULT: {task_name} Task")
    print(sep_line)

    # --- Quantitative metrics table ----------------------------------------
    header: str = f"{'Metric':<30} {'Single-Agent':<15} {'Multi-Agent':<15} {'Delta':<10}"
    print(header)
    print(dash_line)

    quant_rows: list[tuple[str, str, str, str]] = [
        _quant_row("Input tokens", comparison, "input_tokens", "tokens"),
        _quant_row("Output tokens", comparison, "output_tokens", "tokens"),
        _quant_row("Total tokens", comparison, "total_tokens", "tokens"),
        _quant_row("Duration (s)", comparison, "duration_seconds", "s"),
        _quant_row("API calls", comparison, "api_calls", ""),
        _quant_row("Est. cost ($)", comparison, "api_cost_estimated", "$"),
    ]

    for label, sv, mv, delta in quant_rows:
        print(f"{label:<30} {sv:<15} {mv:<15} {delta:<10}")

    # Task completed & errors
    single_completed: bool = comparison.get("single", {}).get("task_completed", False)
    multi_completed: bool = comparison.get("multi", {}).get("task_completed", False)
    single_errors: list[str] = comparison.get("single", {}).get("errors", [])
    multi_errors: list[str] = comparison.get("multi", {}).get("errors", [])

    print(f"{'Task completed':<30} {str(single_completed):<15} {str(multi_completed):<15} {'--':<10}")
    print(
        f"{'Errors':<30} {str(len(single_errors)):<15} "
        f"{str(len(multi_errors)):<15} {'--':<10}"
    )

    # --- Quality scores table ----------------------------------------------
    print()
    print(sep_line)
    print(" QUALITY SCORES")
    print(sep_line)
    quality_header: str = f"{'Metric':<30} {'Single-Agent':<15} {'Multi-Agent':<15} {'Diff':<10}"
    print(quality_header)
    print(dash_line)

    quality_fields: list[str] = [
        "code_correctness",
        "code_completeness",
        "code_quality",
        "documentation_quality",
        "overall_score",
    ]
    display_labels: dict[str, str] = {
        "code_correctness": "Code Correctness (1-5)",
        "code_completeness": "Code Completeness (1-5)",
        "code_quality": "Code Quality (1-5)",
        "documentation_quality": "Doc Quality (1-5)",
        "overall_score": "Overall Score (1-5)",
    }

    qd: dict[str, Any] = comparison.get("quality_delta", {})
    for field in quality_fields:
        info: dict[str, Any] | None = qd.get(field)
        if info is None:
            continue
        sv: Any = info.get("single", "N/A")
        mv: Any = info.get("multi", "N/A")
        diff: Any = info.get("diff", "N/A")
        if isinstance(diff, (int, float)):
            diff_str: str = f"{diff:+g}"
        else:
            diff_str = str(diff)
        label: str = display_labels.get(field, field)
        print(f"{label:<30} {str(sv):<15} {str(mv):<15} {diff_str:<10}")

    # --- Derived metrics ---------------------------------------------------
    print()
    print(sep_line)
    print(" DERIVED METRICS")
    print(sep_line)

    tpq: dict[str, Any] = comparison.get("tokens_per_quality_point", {})
    tpq_single: Any = tpq.get("single", "N/A")
    tpq_multi: Any = tpq.get("multi", "N/A")
    tpq_diff: Any = tpq.get("diff", "N/A")
    if isinstance(tpq_diff, (int, float)):
        tpq_diff_str: str = f"{tpq_diff:+g}"
    else:
        tpq_diff_str = str(tpq_diff)
    print(
        f"{'Tokens per Quality Point':<30} {str(tpq_single):<15} "
        f"{str(tpq_multi):<15} {tpq_diff_str:<10}"
    )

    # --- Conclusion line ---------------------------------------------------
    print(sep_line)

    try:
        sv_overall: float = float(qd.get("overall_score", {}).get("single", 0))
        mv_overall = float(qd.get("overall_score", {}).get("multi", 0))
        mv_total_tokens: float = float(
            comparison.get("multi", {}).get("total_tokens", 0)
        )
        sv_total_tokens: float = float(
            comparison.get("single", {}).get("total_tokens", 0)
        )
        quality_diff_pct: float = 0.0
        if sv_overall > 0:
            quality_diff_pct = ((mv_overall - sv_overall) / sv_overall) * 100

        token_diff_pct: float = 0.0
        if sv_total_tokens > 0:
            token_diff_pct = ((mv_total_tokens - sv_total_tokens) / sv_total_tokens) * 100

        print(
            f"Conclusion: Multi-agent scored {quality_diff_pct:+.0f}% quality "
            f"at {token_diff_pct:+.0f}% more tokens."
        )
    except (TypeError, ZeroDivisionError):
        print("Conclusion: Insufficient data to compute conclusion.")
    print(sep_line)
    print()


def export_json(
    comparison: dict[str, Any],
    output_path: str = "comparison_result.json",
) -> str:
    """Export the full comparison data as a JSON file.

    The exported JSON includes run metadata (timestamp, model), both sets of
    raw metrics, the delta, quality scores, and the full comparison dict.

    Parameters
    ----------
    comparison : dict
        The comparison dict from ``metrics.compute_comparison``.
    output_path : str
        Filesystem path for the JSON output.  Defaults to
        ``comparison_result.json`` in the current working directory.

    Returns
    -------
    str
        The absolute path to the written file.
    """
    if not output_path:
        output_path = "comparison_result.json"

    model: str = "unknown"
    single_raw: dict[str, Any] | None = comparison.get("single", {})
    if single_raw and "model" in single_raw:
        model = single_raw["model"]

    export: dict[str, Any] = {
        "run_id": (
            "comparison-"
            + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        ),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "task": "temperature-logger",
        "model": model,
        "modes": {
            "single": {
                "name": "single-agent",
                "agents": ["embedded-firmware-engineer"],
            },
            "multi": {
                "name": "multi-agent",
                "agents": ["embedded-firmware-engineer", "code-reviewer"],
            },
        },
        "single_metrics": comparison.get("single", {}),
        "multi_metrics": comparison.get("multi", {}),
        "delta": comparison.get("delta", {}),
        "quality_delta": comparison.get("quality_delta", {}),
        "tokens_per_quality_point": comparison.get("tokens_per_quality_point", {}),
        "conclusion": _build_conclusion(comparison),
    }

    abs_path: str = os.path.abspath(output_path)
    with open(abs_path, "w", encoding="utf-8") as fh:
        json.dump(export, fh, indent=2, ensure_ascii=False, default=str)

    logger.info("Exported comparison result to %s", abs_path)
    return abs_path


def print_error(message: str) -> None:
    """Print an error message to stderr in a prominent format."""
    print("=" * 60, file=sys.stderr)
    print(f" ERROR: {message}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _quant_row(
    label: str,
    comparison: dict[str, Any],
    key: str,
    unit: str,
) -> tuple[str, str, str, str]:
    """Build one quantitative row for the ASCII table.

    Returns
    -------
    tuple[str, str, str, str]
        ``(label, single_str, multi_str, delta_str)``.
    """
    delta_info: dict[str, Any] | None = comparison.get("delta", {}).get(key)
    if delta_info is None:
        return (label, "N/A", "N/A", "N/A")

    sv: Any = delta_info.get("single", "N/A")
    mv: Any = delta_info.get("multi", "N/A")
    pct: Any = delta_info.get("pct")

    if isinstance(sv, (int, float)):
        single_str: str = _fmt_num(sv, unit)
    else:
        single_str = str(sv)

    if isinstance(mv, (int, float)):
        multi_str: str = _fmt_num(mv, unit)
    else:
        multi_str = str(mv)

    if pct is not None:
        delta_str: str = f"{pct:+.0f}%"
    else:
        delta_str = "--"

    return (label, single_str, multi_str, delta_str)


def _fmt_num(value: int | float, unit: str) -> str:
    """Format a number with thousands separators and an optional unit."""
    if isinstance(value, float) and value < 10:
        return f"{value:.2f}{unit}"
    if isinstance(value, float):
        return f"{value:.2f}{unit}"
    return f"{value:,}{unit}"


def _build_conclusion(comparison: dict[str, Any]) -> str:
    """Build a one-line conclusion string from the comparison data."""
    try:
        qd: dict[str, Any] = comparison.get("quality_delta", {})
        sv_overall: float = float(qd.get("overall_score", {}).get("single", 0))
        mv_overall: float = float(qd.get("overall_score", {}).get("multi", 0))
        sv_total: float = float(comparison.get("single", {}).get("total_tokens", 0))
        mv_total: float = float(comparison.get("multi", {}).get("total_tokens", 0))

        quality_diff_pct: float = 0.0
        if sv_overall > 0:
            quality_diff_pct = ((mv_overall - sv_overall) / sv_overall) * 100

        token_diff_pct: float = 0.0
        if sv_total > 0:
            token_diff_pct = ((mv_total - sv_total) / sv_total) * 100

        return (
            f"Multi-agent scored {quality_diff_pct:+.0f}% quality "
            f"at {token_diff_pct:+.0f}% more tokens."
        )
    except (TypeError, ZeroDivisionError, ValueError):
        return "Insufficient data to compute conclusion."
