"""Metrics collection and comparison computation for multi-agent experiments.

This module provides functions to extract structured metrics from Anthropic API
responses, and to compute a side-by-side comparison dict from the metrics of two
experimental modes.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def extract_metrics(api_response: dict[str, Any]) -> dict[str, Any]:
    """Extract structured metrics from a raw Anthropic Messages API response.

    The function reads token usage from ``api_response["usage"]`` (which contains
    ``input_tokens`` and ``output_tokens``) and copies through the top-level
    ``stop_reason`` and ``stop_sequence`` fields.

    Parameters
    ----------
    api_response : dict
        The full response returned by the ``anthropic`` SDK.  Expected shape:

        .. code:: python

            {
                "id": "msg_...",
                "type": "message",
                "role": "assistant",
                "content": [{"type": "text", "text": "..."}],
                "model": "claude-sonnet-4-20250514",
                "stop_reason": "end_turn",
                "stop_sequence": None,
                "usage": {"input_tokens": 123, "output_tokens": 456},
            }

    Returns
    -------
    dict
        A flat dictionary with the following keys:

        - ``input_tokens`` (int)
        - ``output_tokens`` (int)
        - ``total_tokens`` (int)
        - ``stop_reason`` (str | None)
        - ``model`` (str | None)
    """
    usage: dict[str, int] = api_response.get("usage", {}) or {}
    input_tokens: int = usage.get("input_tokens", 0) or 0
    output_tokens: int = usage.get("output_tokens", 0) or 0

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "stop_reason": api_response.get("stop_reason"),
        "model": api_response.get("model"),
    }


def compute_comparison(
    single_metrics: dict[str, Any],
    multi_metrics: dict[str, Any],
) -> dict[str, Any]:
    """Compute a side-by-side comparison from single-agent and multi-agent metrics.

    The returned dict contains every metric present in either input, plus
    derived metrics (``tokens_per_quality_point``), and a ``delta`` sub-dict
    that reports absolute and percentage differences (where meaningful).

    Parameters
    ----------
    single_metrics : dict
        Metrics dict produced by ``extract_metrics`` for the single-agent run,
        merged with timing and quality data (see Notes).
    multi_metrics : dict
        Same shape as ``single_metrics`` for the multi-agent run.

    Returns
    -------
    dict
        Comparison dictionary with keys:

        - ``single`` -- single-agent metrics
        - ``multi`` -- multi-agent metrics
        - ``delta`` -- {metric: {"abs": ..., "pct": ...}} for quantitative fields
        - ``quality_delta`` -- {metric: {"single": ..., "multi": ..., "diff": ...}}
        - ``tokens_per_quality_point`` -- {metric: {"single": ..., "multi": ..., "diff": ...}}

    Notes
    -----
    Expected input metric keys include the quantitative values from
    ``extract_metrics`` plus:

    - ``duration_seconds`` (float)
    - ``task_completed`` (bool)
    - ``errors`` (list[str])
    - ``api_calls`` (int)
    - ``api_cost_estimated`` (float)
    - ``code_correctness`` (int, 1-5)
    - ``code_completeness`` (int, 1-5)
    - ``code_quality`` (int, 1-5)
    - ``documentation_quality`` (int, 1-5)
    - ``overall_score`` (float, 1-5)
    """
    comparison: dict[str, Any] = {}

    # --- Quantitative deltas ------------------------------------------------
    quant_fields: list[tuple[str, str, str]] = [
        ("input_tokens", "tokens", "tokens"),
        ("output_tokens", "tokens", "tokens"),
        ("total_tokens", "tokens", "tokens"),
        ("duration_seconds", "s", "seconds"),
        ("api_calls", "", "calls"),
        ("api_cost_estimated", "$", "USD"),
    ]

    deltas: dict[str, dict[str, Any]] = {}
    for key, _label, _unit in quant_fields:
        sv = single_metrics.get(key, 0)
        mv = multi_metrics.get(key, 0)
        diff_val: float | int | None = _safe_sub(mv, sv)
        pct_val: float | None = _safe_pct(diff_val, sv)
        deltas[key] = {
            "single": sv,
            "multi": mv,
            "abs": diff_val,
            "pct": pct_val,
        }

    comparison["delta"] = deltas

    # --- Quality score deltas (1-5 scale) -----------------------------------
    quality_fields: list[str] = [
        "code_correctness",
        "code_completeness",
        "code_quality",
        "documentation_quality",
    ]

    quality_delta: dict[str, dict[str, Any]] = {}
    for field in quality_fields:
        sv = single_metrics.get(field, 0)
        mv = multi_metrics.get(field, 0)
        quality_delta[field] = {
            "single": sv,
            "multi": mv,
            "diff": _safe_sub(mv, sv),
        }

    sv_overall: float = single_metrics.get("overall_score", 0) or 0.0
    mv_overall: float = multi_metrics.get("overall_score", 0) or 0.0
    quality_delta["overall_score"] = {
        "single": sv_overall,
        "multi": mv_overall,
        "diff": round(mv_overall - sv_overall, 2),
    }
    comparison["quality_delta"] = quality_delta

    # --- Derived: tokens per quality point ----------------------------------
    sv_tpq: float | None = _safe_div(
        single_metrics.get("total_tokens", 0), sv_overall
    )
    mv_tpq: float | None = _safe_div(
        multi_metrics.get("total_tokens", 0), mv_overall
    )
    comparison["tokens_per_quality_point"] = {
        "single": sv_tpq,
        "multi": mv_tpq,
        "diff": _safe_sub(mv_tpq, sv_tpq) if mv_tpq is not None and sv_tpq is not None else None,
    }

    # --- Store raw metrics for reference ------------------------------------
    comparison["single"] = single_metrics
    comparison["multi"] = multi_metrics

    return comparison


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _safe_sub(a: float | int | None, b: float | int | None) -> float | int | None:
    """Return ``a - b``, handling ``None`` gracefully."""
    if a is None or b is None:
        return None
    return a - b


def _safe_pct(diff: float | int | None, base: float | int | None) -> float | None:
    """Return ``diff / base * 100``, handling zeros and ``None``."""
    if diff is None or base is None or base == 0:
        return None
    return round((diff / base) * 100, 1)


def _safe_div(num: float | int | None, denom: float | int | None) -> float | None:
    """Return ``num / denom``, guarding against ``None`` and zero."""
    if num is None or denom is None or denom == 0:
        return None
    return round(num / denom, 1)
