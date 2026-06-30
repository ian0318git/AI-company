#!/usr/bin/env python3
"""SessionEnd / SubagentStop / PostToolUse / Stop hook — record lifecycle events.

This script sends event records to the OS API for activity tracking.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request

API_BASE = os.environ.get("AI_EMBEDDED_API_URL", "http://127.0.0.1:8765")


def main():
    """Send the event to the API."""
    event_type = os.environ.get("CLAUDE_HOOK_EVENT", "unknown")
    payload = {}

    # Gather available context
    for key in ("CLAUDE_SESSION_ID", "CLAUDE_PROJECT_DIR", "CLAUDE_HOOK_EVENT"):
        val = os.environ.get(key)
        if val:
            payload[key.lower().replace("claude_", "")] = val

    # Also capture stdin if piped
    if not sys.stdin.isatty():
        try:
            stdin_data = sys.stdin.read()
            if stdin_data.strip():
                payload["stdin"] = stdin_data.strip()[:8192]
        except Exception:
            pass

    try:
        data = json.dumps({
            "event_type": event_type,
            "source": "hook",
            "payload": json.dumps(payload),
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{API_BASE}/api/system/event",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            pass  # Fire and forget
    except Exception:
        pass  # Non-critical — don't block the session


if __name__ == "__main__":
    main()
