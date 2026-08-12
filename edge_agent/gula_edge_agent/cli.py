"""Edge agent CLI entry point.

Usage:
    python -m gula_edge_agent.cli register
    python -m gula_edge_agent.cli run
    python -m gula_edge_agent.cli status

The CLI reads `config.toml` from the current directory (override with
GULA_EDGE_CONFIG=path).
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any

import httpx

from .agent import EdgeAgent
from .runtime import make_runtime
from .security import generate_keypair
from .state import AgentState

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"),
                    format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("gula.edge.cli")


def _load_config(path: str | None) -> dict[str, Any]:
    cfg_path = Path(path or os.getenv("GULA_EDGE_CONFIG", "config.toml"))
    if not cfg_path.exists():
        sys.exit(f"config not found at {cfg_path} — copy config.example.toml")
    import tomllib  # type: ignore
    with cfg_path.open("rb") as f:
        return tomllib.load(f)
    import tomli  # type: ignore
    with cfg_path.open("rb") as f:
        return tomli.load(f)


def _cmd_register(cfg: dict[str, Any]) -> int:
    state = AgentState(cfg["storage"]["state_dir"])
    if state.is_registered():
        log.error("device already registered (device_id=%s) — delete state to re-register",
                  state.get("device_id"))
        return 2

    bootstrap_token = cfg["bootstrap"].get("owner_user_token", "")
    if not bootstrap_token:
        log.error("bootstrap.owner_user_token is empty in config")
        return 2

    private_pem, public_pem = generate_keypair()

    backend_url = cfg["backend"]["url"].rstrip("/")
    edge_path   = cfg["backend"].get("edge_path", "/edge")

    body = {
        "public_key_pem": public_pem,
        "role_mode":      cfg["device"]["role_mode"],
        "display_name":   cfg["device"].get("display_name"),
        "agent_version":  __import__("gula_edge_agent").__version__,
        "os_platform":    sys.platform,
        "capabilities":   {"kinds": sorted(__import__(
                              "gula_edge_agent.security",
                              fromlist=["ALLOWED_KINDS"]).ALLOWED_KINDS)},
    }

    log.info("registering with %s ...", backend_url)
    r = httpx.post(
        f"{backend_url}{edge_path}/devices/register",
        json=body,
        headers={"Authorization": f"Bearer {bootstrap_token}"},
        timeout=30.0,
    )
    if r.status_code >= 400:
        log.error("registration failed: %s %s", r.status_code, r.text[:500])
        return 1
    data = r.json()
    state.set(
        device_id=data["device_id"],
        agent_token=data["agent_token"],
        cert_fingerprint=data["cert_fingerprint"],
        private_key_pem=private_pem,
        public_key_pem=public_pem,
        last_seen_nonce=data.get("nonce", ""),
        backend_url=backend_url,
        edge_path=edge_path,
    )
    log.info("registered: device_id=%s", data["device_id"])
    return 0


def _cmd_status(cfg: dict[str, Any]) -> int:
    state = AgentState(cfg["storage"]["state_dir"])
    if not state.is_registered():
        return 0
    return 0


async def _cmd_run(cfg: dict[str, Any]) -> int:
    state = AgentState(cfg["storage"]["state_dir"])
    if not state.is_registered():
        log.error("not registered — run `register` first")
        return 2

    runtime = make_runtime(cfg["runtime"]["type"],
                           ollama_url=cfg["runtime"].get("ollama_url",
                                                         "http://127.0.0.1:11434"))
    agent = EdgeAgent(
        backend_url=cfg["backend"]["url"],
        edge_path=cfg["backend"].get("edge_path", "/edge"),
        state=state, runtime=runtime,
        cpu_cap_pct=cfg["resources"].get("cpu_cap_pct", 60),
        ram_cap_mb=cfg["resources"].get("ram_cap_mb", 2048),
        battery_floor_pct=cfg["resources"].get("battery_floor_pct", 30),
        idle_only=cfg["resources"].get("idle_only", True),
    )
    try:
        await agent.run_forever()
    except KeyboardInterrupt:
        log.info("stopping ...")
        agent.stop()
    return 0


def main() -> int:
    p = argparse.ArgumentParser("gula-edge")
    p.add_argument("command", choices=("register", "run", "status"))
    p.add_argument("--config", default=None,
                   help="path to config.toml (default: ./config.toml)")
    args = p.parse_args()
    cfg = _load_config(args.config)

    if args.command == "register":
        return _cmd_register(cfg)
    if args.command == "status":
        return _cmd_status(cfg)
    if args.command == "run":
        return asyncio.run(_cmd_run(cfg))
    return 1


if __name__ == "__main__":
    sys.exit(main())
