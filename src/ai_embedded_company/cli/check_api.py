"""CLI connection checker — probe the Autonomous API server and report status.

Usage:
    uv run python -m ai_embedded_company.cli.check_api
    uv run python -m ai_embedded_company.cli.check_api --verbose
    uv run python -m ai_embedded_company.cli.check_api --host 192.168.1.100 --port 8765
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field

# ── Default endpoints to probe ──────────────────────────────────────────────
DEFAULT_ENDPOINTS: list[str] = [
    "/health",
    "/api/projects",
    "/api/tasks",
    "/api/ideas",
    "/api/teams",
    "/api/pipelines",
    "/api/evolution/status",
]

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
DEFAULT_TIMEOUT = 5.0


@dataclass
class ProbeResult:
    """Outcome of probing a single endpoint."""

    name: str
    ok: bool
    elapsed: float
    status_code: int
    error: str | None = None


class ApiProbe:
    """Probe an API server's endpoints and collect timing / status data."""

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        timeout: float = DEFAULT_TIMEOUT,
        endpoints: list[str] | None = None,
    ) -> None:
        self.base_url = f"http://{host}:{port}"
        self.timeout = timeout
        self.endpoints = endpoints or DEFAULT_ENDPOINTS

    def _probe_single(self, endpoint: str) -> ProbeResult:
        """Probe one endpoint and return a ProbeResult."""
        url = f"{self.base_url}{endpoint}"
        req = urllib.request.Request(url, method="GET")
        start = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                elapsed = time.monotonic() - start
                # Drain the response body so we don't leak connections
                resp.read()
                return ProbeResult(
                    name=endpoint,
                    ok=resp.status == 200,
                    elapsed=round(elapsed, 3),
                    status_code=resp.status,
                )
        except urllib.error.HTTPError as e:
            elapsed = time.monotonic() - start
            return ProbeResult(
                name=endpoint,
                ok=False,
                elapsed=round(elapsed, 3),
                status_code=e.code,
                error=f"HTTP {e.code}",
            )
        except urllib.error.URLError as e:
            elapsed = time.monotonic() - start
            return ProbeResult(
                name=endpoint,
                ok=False,
                elapsed=round(elapsed, 3),
                status_code=0,
                error=f"Connection failed: {e.reason}",
            )
        except TimeoutError:
            elapsed = time.monotonic() - start
            return ProbeResult(
                name=endpoint,
                ok=False,
                elapsed=round(elapsed, 3),
                status_code=0,
                error=f"Timed out after {self.timeout}s",
            )
        except OSError as e:
            elapsed = time.monotonic() - start
            return ProbeResult(
                name=endpoint,
                ok=False,
                elapsed=round(elapsed, 3),
                status_code=0,
                error=str(e),
            )

    def probe_all(self) -> list[ProbeResult]:
        """Probe every configured endpoint and return all results."""
        return [self._probe_single(ep) for ep in self.endpoints]

    @staticmethod
    def report(results: list[ProbeResult]) -> None:
        """Print a formatted report to stdout."""
        ok_count = sum(1 for r in results if r.ok)
        total = len(results)
        times = [r.elapsed for r in results]

        # Header
        print(f"API Connection Report — {results[0].name.rsplit('/', 1)[0] if results else '?'}", flush=True)
        print("━" * 50, flush=True)

        # Per-endpoint lines
        for r in results:
            status = "OK" if r.ok else "FAIL"
            detail = f"({r.elapsed}s)" if r.ok else f"({r.elapsed}s, {r.error})"
            print(f" {r.name:40s} {status:4s} {detail}", flush=True)

        print("━" * 50, flush=True)

        if times:
            fastest = min(times)
            slowest = max(times)
            average = round(sum(times) / len(times), 3)
            fastest_name = next((r.name for r in results if r.elapsed == fastest), "?")
            slowest_name = next((r.name for r in results if r.elapsed == slowest), "?")
            print(f" Fastest    {fastest}s  ({fastest_name})", flush=True)
            print(f" Slowest    {slowest}s  ({slowest_name})", flush=True)
            print(f" Average    {average}s", flush=True)

        print("━" * 50, flush=True)

        if ok_count == total:
            print(f" Status: ALL {total} endpoints OK", flush=True)
        else:
            failed = total - ok_count
            print(f" Status: {failed} of {total} endpoints FAILED", flush=True)
            for r in results:
                if not r.ok:
                    print(f"   FAIL: {r.name} — {r.error}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="API Connection Checker")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"API host (default {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"API port (default {DEFAULT_PORT})")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help=f"Per-endpoint timeout in seconds (default {DEFAULT_TIMEOUT})")
    args = parser.parse_args()

    probe = ApiProbe(
        host=args.host,
        port=args.port,
        timeout=args.timeout,
    )

    if args.verbose:
        print(f"🔍 Probing {probe.base_url}", flush=True)
        print()

    results = probe.probe_all()

    if args.verbose or any(not r.ok for r in results):
        ApiProbe.report(results)

    return 0 if all(r.ok for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
