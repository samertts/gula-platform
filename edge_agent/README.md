# GULA Edge Agent

Reference implementation of the **Managed Edge Node Agent** for the GULA Platform.

This agent runs on user devices (laptops, clinic PCs, mini-servers) and joins
the GULA control plane as a sandboxed, trust-scored, policy-enforced edge node
for local AI inference and distributed processing.

See `EDGE_PLATFORM.md` at the repo root for the full directive.

## Quick start

```bash
# 1. Install Python 3.10+
pip install -r requirements.txt

# 2. Configure
cp config.example.toml config.toml
# Edit config.toml — set GULA_BACKEND_URL, LAB_ID, OWNER_USER_TOKEN

# 3. Register the device (one-time)
python -m gula_edge_agent.cli register

# 4. Run as a service
python -m gula_edge_agent.cli run

# Or as a Linux systemd unit:
sudo cp packaging/gula-edge.service /etc/systemd/system/
sudo systemctl enable --now gula-edge
```

## Operating modes

| Mode | Purpose |
|------|---------|
| `personal`   | Single-user laptop. Local AI execution only. |
| `clinic`     | Lab front desk PC. Acts as a small edge server for the lab. |
| `enterprise` | Managed fleet member (Iraq Ministry deployments). |

## Files

| Path | Description |
|------|-------------|
| `gula_edge_agent/__init__.py` | Package init |
| `gula_edge_agent/cli.py`      | `register` and `run` commands |
| `gula_edge_agent/agent.py`    | Heartbeat loop + task executor |
| `gula_edge_agent/runtime.py`  | Pluggable AI runtime layer (Ollama / GGUF) |
| `gula_edge_agent/security.py` | Keypair generation + task signature verification |
| `gula_edge_agent/state.py`    | On-disk encrypted state (token, queue) |
| `config.example.toml`         | Sample config |

## Security boundary (NON-NEGOTIABLE)

* Tasks must arrive HMAC-signed by the server. Bad signatures → quarantine.
* Only kinds in `ALLOWED_KINDS` (mirrored from server) may execute.
* No raw payment/PHI data leaves the device — payloads contain references only.
* All state is encrypted on disk (`cryptography.Fernet`).
* Agent never executes shell commands from the server.
