"""Single-agent execution mode.

Makes *one* call to the Anthropic Messages API with a prompt that asks the
model (acting as an embedded-firmware engineer) to implement the full task.
Returns the raw response and extracted metrics.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------

SINGLE_PROMPT_TEMPLATE: str = """\
You are an embedded firmware engineer. Implement the following complete firmware \
for the M5Stack Core S3. Include all edge case handling, error paths, and comments.

Task:
{task_spec}

Deliver a single .ino file and a brief README with build instructions.
"""


# ---------------------------------------------------------------------------
# Mode entry point
# ---------------------------------------------------------------------------


def run(task_spec: str) -> dict[str, Any]:
    """Execute the task in single-agent mode.

    Parameters
    ----------
    task_spec : str
        The plain-text task specification to send to the model.

    Returns
    -------
    dict
        A dictionary with:

        - ``raw_response`` (dict): the full Anthropic API response.
        - ``response_text`` (str): extracted text from the assistant message.
        - ``metrics`` (dict): extracted metrics (tokens, timing, error info).
        - ``mode`` (str): ``"single-agent"``.
    """
    api_key: str | None = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY environment variable is not set. "
            "Please set it to your Anthropic API key before running."
        )

    # Lazy import so the SDK dependency is only needed at call time.
    try:
        from anthropic import Anthropic
    except ImportError:
        raise ImportError(
            "The `anthropic` package is required. Install it with:\n"
            "  uv add anthropic>=0.49"
        )

    client = Anthropic(api_key=api_key)

    prompt: str = SINGLE_PROMPT_TEMPLATE.format(task_spec=task_spec)

    logger.info("Single-agent: calling Claude API ...")
    start_time: float = time.monotonic()
    errors: list[str] = []

    try:
        response: Any = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8192,
            messages=[
                {"role": "user", "content": prompt},
            ],
        )
    except Exception as exc:
        elapsed: float = time.monotonic() - start_time
        error_msg: str = f"API call failed after {elapsed:.1f}s: {exc}"
        logger.error(error_msg)
        return {
            "raw_response": None,
            "response_text": "",
            "metrics": {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "duration_seconds": elapsed,
                "task_completed": False,
                "errors": [error_msg],
                "api_calls": 1,
                "api_cost_estimated": 0.0,
                # Qualitative scores are zeroed when the call fails
                "code_correctness": 0,
                "code_completeness": 0,
                "code_quality": 0,
                "documentation_quality": 0,
                "overall_score": 0.0,
            },
            "mode": "single-agent",
        }

    elapsed = time.monotonic() - start_time

    # Safely extract text content
    response_text: str = ""
    try:
        for block in response.content:
            if hasattr(block, "text"):
                response_text = block.text
                break
            if isinstance(block, dict) and block.get("type") == "text":
                response_text = block.get("text", "")
                break
    except Exception:
        response_text = str(response.content)

    usage: Any = getattr(response, "usage", None) or {}
    input_tokens: int = getattr(usage, "input_tokens", 0) or 0
    output_tokens: int = getattr(usage, "output_tokens", 0) or 0

    # Rough cost estimate: $3/MTok input, $15/MTok output for Sonnet 4
    input_cost: float = input_tokens * 3.0 / 1_000_000
    output_cost: float = output_tokens * 15.0 / 1_000_000

    metrics: dict[str, Any] = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "duration_seconds": round(elapsed, 2),
        "task_completed": True,
        "errors": errors,
        "api_calls": 1,
        "api_cost_estimated": round(input_cost + output_cost, 6),
        # Qualitative scores are *not* determined by the API -- they are
        # placeholders that the runner can override after human review.
        "code_correctness": 0,
        "code_completeness": 0,
        "code_quality": 0,
        "documentation_quality": 0,
        "overall_score": 0.0,
    }

    # Convert response to a plain dict for consistent downstream handling.
    raw_response: dict[str, Any]
    try:
        raw_response = response.model_dump()
    except AttributeError:
        raw_response = {
            "id": getattr(response, "id", ""),
            "model": getattr(response, "model", ""),
            "stop_reason": getattr(response, "stop_reason", ""),
            "content": [{"type": "text", "text": response_text}],
            "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
        }

    logger.info(
        "Single-agent complete: %d in / %d out / %.1fs",
        input_tokens,
        output_tokens,
        elapsed,
    )

    return {
        "raw_response": raw_response,
        "response_text": response_text,
        "metrics": metrics,
        "mode": "single-agent",
    }
