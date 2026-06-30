"""Shared helpers and constants for MCP tools.

All MCP tools delegate to the FastAPI REST API. This module provides
a thin helper for making those HTTP calls and shared constants.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

import anyio

from ai_embedded_company.config import get_settings

logger = logging.getLogger(__name__)


def _get_api_base() -> str:
    settings = get_settings()
    return settings.api_base_url


async def _api_call(
    method: str,
    path: str,
    *,
    json_data: Optional[dict[str, Any]] = None,
    params: Optional[dict[str, Any]] = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Make an async HTTP call to the FastAPI backend.

    Uses anyio + low-level socket so we don't need httpx as a dependency.
    Falls back to urllib on import error.
    """
    import urllib.request
    import urllib.error
    from urllib.parse import urlencode

    base = _get_api_base()
    url = f"{base}{path}"
    if params:
        query = urlencode({k: v for k, v in params.items() if v is not None})
        url = f"{url}?{query}"

    data_bytes = None
    if json_data is not None:
        data_bytes = json.dumps(json_data).encode("utf-8")

    try:
        req = urllib.request.Request(
            url,
            data=data_bytes,
            method=method,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )

        def _do_request():
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    body = resp.read().decode("utf-8")
                    if resp.status == 204:
                        return {}
                    return json.loads(body)
            except urllib.error.HTTPError as e:
                try:
                    detail = json.loads(e.read().decode("utf-8"))
                except Exception:
                    detail = {"detail": str(e)}
                raise RuntimeError(f"API error {e.code}: {detail.get('detail', str(e))}")

        # Run blocking HTTP in a thread
        return await anyio.to_thread.run_sync(_do_request)

    except RuntimeError:
        raise
    except Exception as e:
        logger.error(f"API call failed: {method} {url}: {e}")
        raise RuntimeError(f"API call failed: {e}")


def _resolve_project_id(project_id: Optional[str] = None) -> str:
    """Resolve a project ID, raising if none is provided.

    In future versions this could look up a 'currently active' project
    from session state.
    """
    if project_id:
        return project_id
    raise ValueError(
        "No project_id provided. Use project_list to see available projects, "
        "or project_create to start a new one."
    )
