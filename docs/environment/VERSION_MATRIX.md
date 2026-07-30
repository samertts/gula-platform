# GULA Platform — Version Matrix

| Tool | Version | Source | Verification |
|------|---------|--------|-------------|
| Ubuntu | 22.04.5 LTS (Jammy) | WSL2 / GitHub Actions | `cat /etc/os-release` |
| WSL | 2.6.3.0 | Windows | `wsl.exe --version` |
| Kernel | 6.6.87.2-microsoft-standard-WSL2 | WSL2 | `uname -r` |
| Python | 3.12.13 | deadsnakes PPA | `python3.12 --version` |
| pip | 26.1.2 | pip self-upgrade | `pip --version` |
| pipx | 1.0.0 | apt/pip | `pipx --version` |
| uv | 0.11.26 | pipx | `uv --version` |
| virtualenv | 21.5.1 | pip | `virtualenv --version` |
| pytest | 9.1.1 | pip (venv) | `pytest --version` |
| ruff | 0.16.0 | pip (venv) | `ruff --version` |
| mypy | 2.3.0 | pip (venv) | `mypy --version` |
| pre-commit | 4.6.0 | pipx | `pre-commit --version` |
| Node.js | 24.18.0 | NodeSource | `node --version` |
| npm | 11.16.0 | ships with Node | `npm --version` |
| pnpm | 11.18.0 | npm global | `pnpm --version` |
| corepack | 0.35.0 | ships with Node | `corepack --version` |
| Docker | 29.1.3 | apt (docker.io) | `docker --version` |
| Docker Compose | 2.40.3+ds1 | apt (docker-compose-v2) | `docker compose version` |
| BuildKit | Built-in (Docker >=23) | docker.io | Built into `docker build` |
| Git | 2.34.1 | apt | `git --version` |
| Git LFS | 3.0.2 | apt | `git lfs version` |
| OpenSSH | 8.9p1 | apt (system) | `ssh -V` |
| OpenSSL | 3.0.2 | apt (system) | `openssl version` |
| Rust | 1.96.0 | rustup | `rustc --version` |
| Cargo | 1.96.0 | rustup | `cargo --version` |
| Java | 21.0.11 (OpenJDK) | apt | `java -version` |
| GCC | 11.4.0 | apt (system) | `gcc --version` |
| Make | 4.3 | apt (system) | `make --version` |
| CMake | 3.22.1 | apt (system) | `cmake --version` |
| Redis (Docker) | 7-alpine | Docker Hub | `docker compose ps` |
| PostgreSQL (Docker) | 17-alpine | Docker Hub | `docker compose ps` |
| Nginx | 1.18.0 | apt (system) | `nginx -v` |
| OpenCode | latest (snap) | snap | `which opencode` |
| VS Code | 1.121.0 | Windows | `code --version` |

## CI Alignment

| CI Env Var | CI Value | Local Value | Match |
|------------|----------|-------------|-------|
| PYTHON_VERSION | 3.12 | 3.12.13 | ✓ |
| NODE_VERSION | 24 | 24.18.0 | ✓ |
| POSTGRES_VERSION | 17-alpine | 17-alpine | ✓ |
| REDIS_VERSION | 7-alpine | 7-alpine | ✓ |
| Flutter | 3.27.0 | Not installed (CI-only) | N/A |
