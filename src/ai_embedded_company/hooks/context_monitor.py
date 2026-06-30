#!/usr/bin/env python3
"""UserPromptSubmit hook — monitor context usage.

Warns when context is getting full so the user can compact/summarize
before hitting the limit.
"""

from __future__ import annotations

import os
import sys


def main():
    """Check context usage and warn if high."""
    # Claude Code exposes context usage via environment vars
    context_used = os.environ.get("CLAUDE_CONTEXT_USED", "0")
    context_total = os.environ.get("CLAUDE_CONTEXT_TOTAL", "200000")

    try:
        used = int(context_used)
        total = int(context_total)
        if total > 0:
            pct = (used / total) * 100
            if pct > 80:
                print(
                    f"[AI Embedded Company] ⚠️ Context: {pct:.0f}% used ({used}/{total}). "
                    "Consider compacting or starting a fresh session soon.",
                    file=sys.stderr,
                )
    except (ValueError, ZeroDivisionError):
        pass


if __name__ == "__main__":
    main()
