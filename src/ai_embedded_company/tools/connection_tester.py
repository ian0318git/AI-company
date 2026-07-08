"""
API Connection Tester — verify the Autonomous API server is reachable and responsive.

Usage:
    uv run python -m src.ai_embedded_company.tools.connection_tester
    uv run python -m src.ai_embedded_company.tools.connection_tester --verbose
    uv run python -m src.ai_embedded_company.tools.connection_tester --json
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request

BASE_URL = "http://127.0.0.1:8765"


def fetch_json(path: str, timeout: float = 5.0) -> tuple[dict | list | None, float, int]:
    """GET a JSON resource, return (data, elapsed_seconds, status_code)."""
    url = f"{BASE_URL}{path}"
    start = time.monotonic()
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = time.monotonic() - start
            body = resp.read().decode()
            status = resp.status
            return json.loads(body), round(elapsed, 3), status
    except urllib.error.HTTPError as e:
        elapsed = time.monotonic() - start
        return None, round(elapsed, 3), e.code
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        elapsed = time.monotonic() - start
        return None, round(elapsed, 3), 0


def check_health(verbose: bool) -> tuple[bool, dict]:
    """Check the /health endpoint."""
    data, elapsed, status = fetch_json("/health")
    ok = status == 200 and data is not None
    if verbose or not ok:
        detail = {
            "endpoint": "/health",
            "status": status,
            "elapsed_s": elapsed,
            "data": data,
        }
        if verbose:
            print(f"  /health → {status} in {elapsed}s", flush=True)
            if data:
                print(f"    {json.dumps(data)}", flush=True)
    return ok, {} if not data else data


def check_status(verbose: bool) -> tuple[bool, dict]:
    """Check the /status endpoint."""
    data, elapsed, status = fetch_json("/status")
    ok = status == 200 and data is not None
    if verbose or not ok:
        detail = {
            "endpoint": "/status",
            "status": status,
            "elapsed_s": elapsed,
            "data": data,
        }
        if verbose:
            print(f"  /status → {status} in {elapsed}s", flush=True)
            if data:
                print(f"    {json.dumps(data)}", flush=True)
    return ok, {} if not data else data


def discover_endpoints(verbose: bool) -> tuple[bool, list[str]]:
    """List all API endpoints from the OpenAPI schema."""
    data, elapsed, status = fetch_json("/openapi.json")
    if status != 200 or data is None:
        if verbose:
            print(f"  /openapi.json → {status} in {elapsed}s — FAILED", flush=True)
        return False, []
    paths = sorted(data.get("paths", {}).keys())
    ok = len(paths) > 0
    if verbose:
        print(f"  /openapi.json → {status} in {elapsed}s — {len(paths)} endpoints found", flush=True)
        for p in paths:
            print(f"    {p}", flush=True)
    return ok, paths


def main() -> int:
    parser = argparse.ArgumentParser(description="API Connection Tester")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON report")
    args = parser.parse_args()

    results: dict[str, bool | float | list[str] | None] = {}

    if args.verbose:
        print("🔍 API Connection Tester", flush=True)
        print(f"   Target: {BASE_URL}", flush=True)
        print()

    # --- Health check ---
    if args.verbose:
        print("─ Health check ─")
    ok_health, health_data = check_health(args.verbose)
    results["health"] = ok_health

    # --- Status check ---
    if args.verbose:
        print("─ Status check ─")
    ok_status, status_data = check_status(args.verbose)
    results["status"] = ok_status

    # --- Discover endpoints ---
    if args.verbose:
        print("─ Endpoint discovery ─")
    ok_endpoints, endpoint_list = discover_endpoints(args.verbose)
    results["endpoints_found"] = endpoint_list

    all_ok = ok_health and ok_status and ok_endpoints
    results["all_ok"] = all_ok

    if args.json:
        print(json.dumps(results, indent=2), flush=True)
    elif args.verbose:
        print()
        verdict = "✅ ALL CHECKS PASSED" if all_ok else "❌ SOME CHECKS FAILED"
        print(f"  {verdict}", flush=True)

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
