"""Multi-agent execution mode.

Implements a fixed 2-agent pipeline:

1. **Agent 1** (embedded-firmware-engineer) -- writes the full firmware.
2. **Agent 2** (code-reviewer) -- receives Agent 1's output in its prompt and
   produces a review with a revised .ino file.

A 3-second delay is inserted between the two calls to avoid rate-limit issues.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

AGENT1_PROMPT_TEMPLATE: str = """\
You are an embedded firmware engineer specialized in M5Stack Core S3 (ESP32-S3). \
Implement the following firmware:

Task:
{task_spec}

Deliver a single .ino file with complete implementation.
Include all error handling, initialization checks, and comments.
"""

AGENT2_PROMPT_TEMPLATE: str = """\
You are a senior code reviewer for embedded systems. Review the following firmware \
implementation for the M5Stack Core S3 temperature logger.

TASK SPECIFICATION:
{task_spec}

IMPLEMENTATION TO REVIEW:
{agent1_output}

Your review should check:
1. Code correctness -- does it compile and run?
2. Completeness -- are all 6 requirements implemented?
3. Error handling -- SD card, sensor, edge cases?
4. Code quality -- naming, structure, comments?
5. Safety -- buffer overflows, race conditions, resource leaks?

Provide:
- A score (1-5) for each category listed above
- Specific improvement suggestions (minimum 2 if score < 4)
- A final revised .ino file incorporating your suggested fixes
- Brief README with build instructions
"""


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


def _call_claude(
    client: Any,
    prompt: str,
    agent_label: str,
    max_tokens: int = 8192,
) -> dict[str, Any]:
    """Make a single blocking call to the Claude Messages API.

    Parameters
    ----------
    client : anthropic.Anthropic
        Initialised SDK client.
    prompt : str
        The user-turn message content.
    agent_label : str
        Human-readable label for logging (e.g. ``"Agent 1 (firmware)"``).
    max_tokens : int
        Maximum tokens in the response.

    Returns
    -------
    dict
        ``{"response": ..., "response_text": ..., "elapsed": ..., "error": ...}``
    """
    logger.info("Multi-agent: calling %s ...", agent_label)
    start: float = time.monotonic()
    error: str | None = None

    try:
        response: Any = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as exc:
        elapsed: float = time.monotonic() - start
        error = f"{agent_label} failed after {elapsed:.1f}s: {exc}"
        logger.error(error)
        return {
            "response": None,
            "response_text": "",
            "elapsed": elapsed,
            "error": error,
        }

    elapsed = time.monotonic() - start

    # Extract text from response.
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

    return {
        "response": response,
        "response_text": response_text,
        "elapsed": elapsed,
        "error": error,
    }


def _aggregate_metrics(
    agent1_result: dict[str, Any],
    agent2_result: dict[str, Any],
) -> dict[str, Any]:
    """Aggregate per-agent results into a single metrics dict.

    Parameters
    ----------
    agent1_result, agent2_result : dict
        Results from two ``_call_claude`` calls.

    Returns
    -------
    dict
        Flat metrics dict compatible with ``metrics.extract_metrics``.
    """
    metrics: dict[str, Any] = {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "duration_seconds": 0.0,
        "task_completed": True,
        "errors": [],
        "api_calls": 2,
        "api_cost_estimated": 0.0,
        "code_correctness": 0,
        "code_completeness": 0,
        "code_quality": 0,
        "documentation_quality": 0,
        "overall_score": 0.0,
    }

    for i, result in enumerate([agent1_result, agent2_result], start=1):
        err = result.get("error")
        if err:
            metrics["errors"].append(err)
            metrics["task_completed"] = False
            continue

        resp = result["response"]
        if resp is None:
            continue

        usage: Any = getattr(resp, "usage", None) or {}
        in_tok: int = getattr(usage, "input_tokens", 0) or 0
        out_tok: int = getattr(usage, "output_tokens", 0) or 0

        metrics["input_tokens"] += in_tok
        metrics["output_tokens"] += out_tok

        input_cost: float = in_tok * 3.0 / 1_000_000
        output_cost: float = out_tok * 15.0 / 1_000_000
        metrics["api_cost_estimated"] += input_cost + output_cost

    metrics["total_tokens"] = metrics["input_tokens"] + metrics["output_tokens"]
    metrics["api_cost_estimated"] = round(metrics["api_cost_estimated"], 6)

    # Total wall-clock time includes the 3 s delay between calls.
    total_elapsed: float = agent1_result["elapsed"] + agent2_result["elapsed"] + 3.0
    metrics["duration_seconds"] = round(total_elapsed, 2)

    return metrics


# ---------------------------------------------------------------------------
# Mode entry point
# ---------------------------------------------------------------------------


def run(task_spec: str) -> dict[str, Any]:
    """Execute the task in multi-agent mode (2-agent pipeline).

    The pipeline is:

    1. Agent 1 (embedded-firmware-engineer) produces the firmware.
    2. A 3-second delay to avoid rate-limit issues.
    3. Agent 2 (code-reviewer) reviews Agent 1's output and produces scores +
       a revised .ino file.

    Parameters
    ----------
    task_spec : str
        The plain-text task specification.

    Returns
    -------
    dict
        A dictionary with:

        - ``raw_response`` (dict): Agent 2's full Anthropic API response.
        - ``response_text`` (str): Agent 2's extracted text (the review).
        - ``agent1_response`` (dict): Agent 1's full Anthropic API response.
        - ``agent1_text`` (str): Agent 1's extracted text (the implementation).
        - ``metrics`` (dict): Aggregated metrics across both agents.
        - ``mode`` (str): ``"multi-agent"``.
    """
    api_key: str | None = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY environment variable is not set. "
            "Please set it to your Anthropic API key before running."
        )

    try:
        from anthropic import Anthropic
    except ImportError:
        raise ImportError(
            "The `anthropic` package is required. Install it with:\n"
            "  uv add anthropic>=0.49"
        )

    client = Anthropic(api_key=api_key)

    # --- Agent 1: Firmware engineer ----------------------------------------
    agent1_prompt: str = AGENT1_PROMPT_TEMPLATE.format(task_spec=task_spec)
    agent1_result: dict[str, Any] = _call_claude(
        client, agent1_prompt, "Agent 1 (firmware-engineer)"
    )

    # --- Delay between calls -----------------------------------------------
    logger.info("Multi-agent: 3-second delay between calls ...")
    time.sleep(3.0)

    # --- Agent 2: Code reviewer --------------------------------------------
    if agent1_result["error"]:
        # If Agent 1 failed, we still call Agent 2 with an empty implementation.
        logger.warning(
            "Agent 1 failed; Agent 2 will receive an empty implementation to review."
        )
        agent1_output: str = "[Agent 1 failed -- no implementation produced]"
    else:
        agent1_output = agent1_result["response_text"]

    agent2_prompt: str = AGENT2_PROMPT_TEMPLATE.format(
        task_spec=task_spec,
        agent1_output=agent1_output,
    )
    agent2_result: dict[str, Any] = _call_claude(
        client, agent2_prompt, "Agent 2 (code-reviewer)"
    )

    # --- Aggregate metrics --------------------------------------------------
    metrics: dict[str, Any] = _aggregate_metrics(agent1_result, agent2_result)

    # --- Convert responses to plain dicts ----------------------------------
    def _to_dict(resp: Any) -> dict[str, Any]:
        if resp is None:
            return {}
        try:
            return resp.model_dump()
        except AttributeError:
            return {
                "id": getattr(resp, "id", ""),
                "model": getattr(resp, "model", ""),
                "stop_reason": getattr(resp, "stop_reason", ""),
            }

    logger.info(
        "Multi-agent complete: %d in / %d out / %.1fs (incl. 3s delay)",
        metrics["input_tokens"],
        metrics["output_tokens"],
        metrics["duration_seconds"],
    )

    return {
        "raw_response": _to_dict(agent2_result["response"]),
        "response_text": agent2_result["response_text"],
        "agent1_response": _to_dict(agent1_result["response"]),
        "agent1_text": agent1_result["response_text"],
        "metrics": metrics,
        "mode": "multi-agent",
    }
