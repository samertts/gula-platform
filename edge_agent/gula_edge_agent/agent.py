"""Edge Agent main loop.

Lifecycle:
  1. ensure registered (state file has device_id + agent_token)
  2. start heartbeat loop on a slow timer (default 30s)
  3. on heartbeat:
       - send capabilities + telemetry
       - server replies with optional task
       - execute task in runtime
       - report result

Sandboxing rules enforced here (NOT delegated to the runtime):
  * task.kind must be in security.ALLOWED_KINDS
  * payload byte size must not exceed MAX_PAYLOAD_BYTES
  * total wallclock per task is capped by `timeout_s`
  * battery / idle / cpu floors are checked before pulling work

The agent never invokes shell commands from the server.
"""
from __future__ import annotations

import asyncio
import json
import logging
import platform
import time
from typing import Any

import httpx

from .runtime import Runtime
from .security import ALLOWED_KINDS, MAX_PAYLOAD_BYTES
from .state import AgentState

try:
    import psutil  # type: ignore
except ImportError:
    psutil = None  # graceful fallback

logger = logging.getLogger("gula.edge.agent")


class EdgeAgent:
    def __init__(self, *, backend_url: str, edge_path: str,
                 state: AgentState, runtime: Runtime,
                 cpu_cap_pct: int = 60, ram_cap_mb: int = 2048,
                 battery_floor_pct: int = 30, idle_only: bool = True):
        self.base_url = backend_url.rstrip("/") + edge_path
        self.state    = state
        self.runtime  = runtime
        self.cpu_cap_pct      = cpu_cap_pct
        self.ram_cap_mb       = ram_cap_mb
        self.battery_floor_pct = battery_floor_pct
        self.idle_only        = idle_only
        self._client          = httpx.AsyncClient(timeout=30.0)
        self._stopping        = False
        self._heartbeat_s     = 30
        self._counters        = {"completed": 0, "failed": 0,
                                 "started_at": time.time()}

    # ── HTTP ──────────────────────────────────────────────────────────────────

    def _auth_header(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.state.get('agent_token')}"}

    async def _post(self, path: str, body: dict, *, timeout: float = 30.0) -> dict:
        r = await self._client.post(f"{self.base_url}{path}",
                                    json=body, headers=self._auth_header(),
                                    timeout=timeout)
        r.raise_for_status()
        return r.json() if r.content else {}

    # ── Resource gating ───────────────────────────────────────────────────────

    def _gather_telemetry(self) -> dict[str, Any]:
        sample: dict[str, Any] = {
            "agent_uptime_s": int(time.time() - self._counters["started_at"]),
            "task_completed_total": self._counters["completed"],
            "task_failed_total":    self._counters["failed"],
        }
        if psutil is None:
            return sample
        try:
            sample["cpu_pct"] = float(psutil.cpu_percent(interval=None))
            vm = psutil.virtual_memory()
            sample["mem_mb"]       = round(vm.used / (1024 * 1024), 1)
            sample["mem_total_mb"] = round(vm.total / (1024 * 1024), 1)
            bat = psutil.sensors_battery() if hasattr(psutil, "sensors_battery") else None
            if bat:
                sample["battery_pct"] = float(bat.percent)
                sample["on_battery"]  = not bat.power_plugged
        except Exception as exc:
            logger.debug("telemetry partial: %s", exc)
        return sample

    def _can_take_work(self, telemetry: dict[str, Any]) -> tuple[bool, str]:
        cpu = telemetry.get("cpu_pct")
        if cpu is not None and cpu > self.cpu_cap_pct:
            return False, f"cpu_above_cap({cpu}>{self.cpu_cap_pct})"
        if telemetry.get("on_battery") and \
           (telemetry.get("battery_pct") or 100) < self.battery_floor_pct:
            return False, "battery_below_floor"
        return True, "ok"

    # ── Heartbeat ─────────────────────────────────────────────────────────────

    async def _heartbeat_once(self) -> dict:
        telemetry = self._gather_telemetry()
        body = {
            "agent_version": __import__(__name__.split(".")[0]).__version__,
            "capabilities": {
                "kinds":  sorted(ALLOWED_KINDS),
                "os":     platform.system().lower(),
                "arch":   platform.machine(),
                "cpu_cap_pct": self.cpu_cap_pct,
                "ram_cap_mb":  self.ram_cap_mb,
            },
            "telemetry": telemetry,
        }
        try:
            return await self._post("/agent/heartbeat", body)
        except httpx.HTTPStatusError as e:
            logger.error("heartbeat HTTP %s: %s", e.response.status_code,
                         e.response.text[:200])
            return {}
        except Exception as e:
            logger.warning("heartbeat error: %s", e)
            return {}

    # ── Task execution ────────────────────────────────────────────────────────

    async def _execute_task(self, task: dict[str, Any]) -> None:
        task_uid = task["task_uid"]
        kind     = task["kind"]
        payload  = task.get("payload") or {}
        timeout_s = int(task.get("timeout_s", 60))

        # Hard sandbox checks
        if kind not in ALLOWED_KINDS:
            await self._report_result(task_uid, success=False,
                                      error=f"agent rejects unknown kind: {kind}")
            return

        try:
            payload_bytes = len(json.dumps(payload).encode("utf-8"))
        except Exception:
            payload_bytes = MAX_PAYLOAD_BYTES + 1
        if payload_bytes > MAX_PAYLOAD_BYTES:
            await self._report_result(task_uid, success=False,
                                      error=f"payload too large: {payload_bytes}")
            return

        t0 = time.perf_counter()
        try:
            result = await asyncio.wait_for(
                self.runtime.run(kind, payload),
                timeout=timeout_s,
            )
            self._counters["completed"] += 1
            await self._report_result(
                task_uid, success=True, result=result,
                duration_ms=int((time.perf_counter() - t0) * 1000),
            )
        except TimeoutError:
            self._counters["failed"] += 1
            await self._report_result(task_uid, success=False,
                                      error=f"runtime timeout after {timeout_s}s")
        except Exception as exc:
            self._counters["failed"] += 1
            await self._report_result(task_uid, success=False,
                                      error=f"runtime error: {exc}")

    async def _report_result(self, task_uid: str, *, success: bool,
                             result: dict | None = None,
                             error: str | None = None,
                             duration_ms: int | None = None) -> None:
        body = {"success": success, "result": result, "error": error,
                "duration_ms": duration_ms}
        try:
            await self._post(f"/agent/tasks/{task_uid}/result", body)
        except Exception as exc:
            logger.warning("result reporting failed: %s", exc)

    # ── Main loop ─────────────────────────────────────────────────────────────

    async def run_forever(self) -> None:
        logger.info("Edge agent starting, base_url=%s device_id=%s",
                    self.base_url, self.state.get("device_id"))
        while not self._stopping:
            try:
                resp = await self._heartbeat_once()
                if resp.get("kill_switched"):
                    logger.warning("Kill switch active — sleeping 5min")
                    await asyncio.sleep(300)
                    continue
                if resp.get("quarantined"):
                    logger.warning("Device quarantined by control plane")
                    await asyncio.sleep(120)
                    continue

                models = resp.get("models") or []
                if models:
                    try:
                        await self.runtime.warmup(models)
                    except Exception as exc:
                        logger.warning("warmup failed: %s", exc)

                # Resource gate
                tele = self._gather_telemetry()
                ok, reason = self._can_take_work(tele)

                task = resp.get("task")
                if task and ok:
                    await self._execute_task(task)
                elif task and not ok:
                    await self._report_result(
                        task["task_uid"], success=False,
                        error=f"agent declined: {reason}",
                    )

                self._heartbeat_s = int(resp.get("next_heartbeat_s", 30))
            except Exception as exc:
                logger.exception("loop error: %s", exc)

            await asyncio.sleep(max(5, self._heartbeat_s))

    def stop(self) -> None:
        self._stopping = True
