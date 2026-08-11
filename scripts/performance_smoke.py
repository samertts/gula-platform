#!/usr/bin/env python3
"""Safe, read-only latency smoke test for a running GULA API.

The script deliberately probes only liveness/read-only endpoints and never
creates, updates, or deletes clinical data. It is intended for demo/staging
validation, not as a substitute for a PostgreSQL load test.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class Sample:
    path: str
    status: int
    elapsed_ms: float
    error: str | None = None


def request_once(base_url: str, path: str, timeout: float) -> Sample:
    started = time.perf_counter()
    request = Request(
        f"{base_url.rstrip('/')}{path}",
        method="GET",
        headers={"Accept": "application/json", "User-Agent": "gula-performance-smoke/1.0"},
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            response.read()
            status = response.status
            error = None if 200 <= status < 400 else f"http_{status}"
    except HTTPError as exc:
        status = exc.code
        error = f"http_{exc.code}"
    except (URLError, TimeoutError, OSError) as exc:
        status = 0
        error = type(exc).__name__
    elapsed_ms = (time.perf_counter() - started) * 1000
    return Sample(path, status, elapsed_ms, error)


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * fraction))))
    return ordered[index]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--requests", type=int, default=120)
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument(
        "--path",
        action="append",
        dest="paths",
        default=["/health", "/health/ready", "/test-types"],
    )
    args = parser.parse_args()
    if args.requests < 1 or args.concurrency < 1 or not args.paths:
        parser.error("requests, concurrency, and at least one path must be positive")

    jobs = [args.paths[index % len(args.paths)] for index in range(args.requests)]
    started = time.perf_counter()
    samples: list[Sample] = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [executor.submit(request_once, args.url, path, args.timeout) for path in jobs]
        for future in as_completed(futures):
            samples.append(future.result())
    wall_ms = (time.perf_counter() - started) * 1000

    latencies = [sample.elapsed_ms for sample in samples]
    failures = [sample for sample in samples if sample.error]
    by_path: dict[str, dict[str, float | int]] = {}
    for path in args.paths:
        values = [sample.elapsed_ms for sample in samples if sample.path == path]
        path_failures = sum(1 for sample in samples if sample.path == path and sample.error)
        by_path[path] = {
            "requests": len(values),
            "errors": path_failures,
            "p50_ms": round(percentile(values, 0.50), 2),
            "p95_ms": round(percentile(values, 0.95), 2),
            "p99_ms": round(percentile(values, 0.99), 2),
            "max_ms": round(max(values) if values else 0.0, 2),
        }

    result = {
        "url": args.url,
        "requests": len(samples),
        "concurrency": args.concurrency,
        "wall_ms": round(wall_ms, 2),
        "throughput_rps": round(len(samples) / (wall_ms / 1000), 2) if wall_ms else 0.0,
        "errors": len(failures),
        "error_rate": round(len(failures) / len(samples), 4) if samples else 1.0,
        "overall": {
            "p50_ms": round(percentile(latencies, 0.50), 2),
            "p95_ms": round(percentile(latencies, 0.95), 2),
            "p99_ms": round(percentile(latencies, 0.99), 2),
            "max_ms": round(max(latencies) if latencies else 0.0, 2),
            "mean_ms": round(statistics.mean(latencies) if latencies else 0.0, 2),
        },
        "by_path": by_path,
        "read_only": True,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
