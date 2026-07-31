# GULA Platform — Developer Bootstrap Guide

## Quick Start

```bash
# 1. Clone repository
git clone https://github.com/samertts/gula-platform.git
cd gula-platform

# 2. Activate backend environment
source backend/.venv/bin/activate

# 3. Install frontend dependencies
cd frontend-v3
npm ci
cd ..

# 4. Start infrastructure
docker compose up -d

# 5. Run database migrations
cd backend
alembic upgrade head
cd ..

# 6. Start backend
cd backend
uvicorn app.main:app --reload --port 10000
cd ..

# 7. Start frontend (separate terminal)
cd frontend-v3
npm run dev
```

## Environment Verification

```bash
# Check everything is installed correctly:
python3.12 --version        # → 3.12.x
node --version              # → v24.x
docker compose version      # → 2.x
git lfs version             # → 3.x
```

## Daily Workflow

```bash
# Start services
docker compose up -d

# Activate backend
source backend/.venv/bin/activate

# Run tests
cd backend && pytest && cd ..

# Run linter
ruff check backend/app/

# Type check
mypy backend/app/
```

## Common Issues

### `alembic upgrade head` fails

Ensure PostgreSQL is running: `docker compose ps`

### Frontend build fails

Clear node_modules and reinstall:
```bash
cd frontend-v3
rm -rf node_modules
npm ci
```

### Docker out of disk space

```bash
docker system prune -af --volumes
```

## First-time Setup Checklist

- [ ] Python 3.12 installed
- [ ] Backend venv created (`python3.12 -m venv backend/.venv`)
- [ ] Dependencies installed (`uv pip install -r backend/requirements.txt`)
- [ ] Dev tools installed (`uv pip install pytest ruff mypy`)
- [ ] Node.js 24 installed
- [ ] npm dependencies installed (`cd frontend-v3 && npm ci`)
- [ ] Git LFS installed and configured
- [ ] Pre-commit hooks installed
- [ ] Docker Compose v2 plugin installed
- [ ] Docker services running (`docker compose up -d`)
- [ ] Database migrations applied (`alembic upgrade head`)
