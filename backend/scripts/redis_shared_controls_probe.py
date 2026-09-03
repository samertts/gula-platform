"""Prove shared Redis controls across independent Python processes.

This disposable probe exercises the same `_RedisWrapper` used by the app. It
requires GULA_PROOF_REDIS_URL and deletes all generated keys before returning.
It is not a production load test.
"""
from __future__ import annotations

import multiprocessing
import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.security.redis_client import _RedisWrapper


def increment_worker(url: str, key: str, barrier, output) -> None:
    cache = _RedisWrapper(url)
    barrier.wait(timeout=10)
    count = cache.incr(key)
    if count == 1:
        cache.expire(key, 30)
    output.put(count)


def read_marker_worker(url: str, key: str, output) -> None:
    cache = _RedisWrapper(url)
    output.put(cache.get(key))


def main() -> int:
    url = os.environ.get("GULA_PROOF_REDIS_URL")
    if not url:
        raise SystemExit("GULA_PROOF_REDIS_URL is required; no Redis endpoint is selected implicitly")

    cache = _RedisWrapper(url)
    suffix = uuid.uuid4().hex
    counter_key = f"gula:proof:{suffix}:counter"
    marker_key = f"gula:proof:{suffix}:revoked"
    context = multiprocessing.get_context("spawn")
    barrier = context.Barrier(2)
    output = context.Queue()
    processes = [
        context.Process(target=increment_worker, args=(url, counter_key, barrier, output)),
        context.Process(target=increment_worker, args=(url, counter_key, barrier, output)),
    ]
    try:
        for process in processes:
            process.start()
        for process in processes:
            process.join(15)
            if process.exitcode != 0:
                raise RuntimeError(f"Redis counter worker failed with exit code {process.exitcode}")
        counts = sorted(output.get(timeout=5) for _ in processes)
        if counts != [1, 2] or cache.get(counter_key) != "2":
            raise AssertionError(f"unexpected shared counter result: {counts}")

        cache.set(marker_key, "revoked", ex=30)
        reader = context.Process(target=read_marker_worker, args=(url, marker_key, output))
        reader.start()
        reader.join(15)
        if reader.exitcode != 0:
            raise RuntimeError(f"Redis marker worker failed with exit code {reader.exitcode}")
        if output.get(timeout=5) != "revoked":
            raise AssertionError("revocation marker was not visible across processes")

        sys.stdout.write("redis_shared_counter_proof=pass\n")
        sys.stdout.write("redis_revocation_visibility=pass\n")
        return 0
    finally:
        cache.delete(counter_key)
        cache.delete(marker_key)
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(5)


if __name__ == "__main__":
    raise SystemExit(main())
