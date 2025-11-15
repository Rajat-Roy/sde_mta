# Database Configuration Guide

This project supports two database configurations for Docker:

## Option 1: Local PostgreSQL (Default) ✨

**File:** `docker-compose.yml`

### What it does:
- Runs PostgreSQL 16 container locally
- Creates a fresh database in Docker
- Data persists in Docker volume
- Completely isolated from remote DB

### Usage:
```bash
# Start with local database
docker compose up --build

# Or using Makefile
make up
make up-d     # detached mode
```

### Pros:
- Fast setup
- No network dependency
- Safe for testing
- Complete data isolation

### Cons:
- Fresh/empty database
- Different data than production
- Uses extra disk space

---

## Option 2: Remote PostgreSQL (Production DB)

**File:** `docker-compose.remote-db.yml`

### What it does:
- Connects to remote PostgreSQL at `64.227.129.253`
- Uses the same database as production
- No local PostgreSQL container
- Only runs Redis, Django, and Celery

### Usage:
```bash
# Start with remote database
docker compose -f docker-compose.remote-db.yml up --build

# Or using Makefile
make remote-up
make remote-up-d     # detached mode
make remote-down     # stop
make remote-build    # rebuild
```

### Pros:
- Same data as production
- Shared across team members
- Smaller Docker footprint
- No database migrations needed

### Cons:
- Requires network connection
- Slower (network latency)
- Risk of affecting production data
- Shared with other developers

---

## Current Configuration

The `.env` file is currently set to:
```env
DB_HOST=64.227.129.253  # Remote database
```

### For Local Development (without Docker):
```bash
source venv/bin/activate
python manage.py runserver
# Uses remote DB at 64.227.129.253
```

### For Docker with Local DB:
```bash
docker compose up
# Overrides DB_HOST=db (local container)
```

### For Docker with Remote DB:
```bash
docker compose -f docker-compose.remote-db.yml up
# Uses DB_HOST from .env (remote)
```

---

## Switching Between Configurations

### Currently Running Local Dev Server → Docker (Remote DB)
```bash
# Stop local dev server (Ctrl+C or kill the process)

# Update .env for remote DB (already set)
DB_HOST=64.227.129.253

# Start Docker with remote DB
make remote-up-d
```

### Docker (Local DB) → Docker (Remote DB)
```bash
# Stop local DB setup
make down

# Start remote DB setup
make remote-up
```

### Docker → Local Development
```bash
# Stop Docker
docker compose down
# or
make down

# Ensure .env has remote DB
DB_HOST=64.227.129.253

# Start local dev
source venv/bin/activate
python manage.py runserver
```

---

## Quick Reference

| Setup | Command | Database | Best For |
|-------|---------|----------|----------|
| **Local Dev** | `python manage.py runserver` | Remote | Quick development |
| **Docker Local DB** | `docker compose up` | Local container | Isolated testing |
| **Docker Remote DB** | `make remote-up` | Remote shared | Team collaboration |

---

## Database Credentials

All setups use the same credentials from `.env`:

```env
DB_NAME=mkt_db
DB_USER=mkt_user
DB_PASSWORD=mkt_user
DB_PORT=5432
```

**Remote Host:** `64.227.129.253`
**Local Docker Host:** `db` (container name)

---

## Recommendations

### For Development
- Use **local dev server** (`python manage.py runserver`) - fastest
- Or **Docker with remote DB** - same as production data

### For Testing
- Use **Docker with local DB** - safe, isolated environment

### For Production Simulation
- Use **Docker with remote DB** - exact production setup

### For Team Collaboration
- Use **Docker with remote DB** - shared database

---

## Troubleshooting

### Can't connect to remote DB
```bash
# Check if remote DB is accessible
nc -zv 64.227.129.253 5432

# Check .env file
cat .env | grep DB_HOST
```

### Docker using wrong database
```bash
# Check which compose file you're using
docker compose config | grep DB_HOST

# For remote DB, ensure you use:
docker compose -f docker-compose.remote-db.yml up
```

### Reset local Docker database
```bash
docker compose down -v
docker compose up --build
```

---

## Current Status

**Local development server is running**
- Using remote PostgreSQL database
- Port 8000
- No Redis/Celery (run separately if needed)

To switch to Docker with full stack (Redis + Celery):
```bash
# Stop current server (Ctrl+C)
make remote-up-d
```
