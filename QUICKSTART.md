# Quick Start Guide

Get the AI-Enabled District Marketplace running in under 5 minutes with Docker!

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed
- Git

## Installation (3 Steps)

### 1. Clone the Repository

```bash
git clone https://github.com/Rajat-Roy/sde_mta.git
cd sde_mta
```

### 2. Configure (Optional)

The `.env` file is pre-configured. If you have a Gemini API key, update it:

```bash
# Edit .env and replace the GEMINI_API_KEY value
nano .env
# or
vim .env
```

### 3. Start Everything

```bash
docker-compose up --build
```

That's it! The first run takes 2-3 minutes to build and initialize.

## Access the Application

Once you see `Starting development server at http://0.0.0.0:8000/`, visit:

- **Main App**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
  - Username: `admin`
  - Password: `admin123`

## What's Running?

Docker Compose automatically starts:
- Django web server (port 8000)
- PostgreSQL database (port 5432)
- Redis cache (port 6379)
- Celery worker (async tasks)
- Celery beat (scheduled tasks)

## Quick Commands

Use the Makefile for common operations:

```bash
# View all commands
make help

# Start services (background)
make up-d

# View logs
make logs

# Stop everything
make down

# Django shell
make shell

# Run tests
make test
```

## Testing the Features

### 1. Browse Products

Visit http://localhost:8000/products/

### 2. Multimodal Search

```bash
# Search via API
curl -X POST http://localhost:8000/search/api/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "fresh vegetables",
    "search_type": "text"
  }'
```

### 3. AI Product Listing (Text)

```bash
# Create product via AI (requires login)
curl -X POST http://localhost:8000/ingest/api/create/ \
  -H "Content-Type: application/json" \
  -d '{
    "input_type": "text",
    "text": "Fresh organic tomatoes, 5 kg, Rs 100 per kg"
  }'
```

## Create Your Own User

```bash
docker-compose exec web python manage.py createsuperuser
```

## Stop Services

```bash
# Stop but keep data
docker-compose down

# Stop and remove all data
docker-compose down -v
```

## Next Steps

- Read the full [README.md](README.md)
- Check [DOCKER_GUIDE.md](DOCKER_GUIDE.md) for advanced Docker usage
- Explore the [API documentation](#api-endpoints) in README.md

## Troubleshooting

### Port 8000 Already in Use

```bash
# Find and kill the process
lsof -i :8000
kill -9 <PID>

# Or change the port in docker-compose.yml
```

### Rebuild Everything

```bash
make clean
docker-compose up --build
```

### View Logs

```bash
# All services
make logs

# Specific service
docker-compose logs -f web
docker-compose logs -f celery
docker-compose logs -f db
```

## Development Mode

For automatic code reloading during development:

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

---

**Need Help?** Check the full documentation in [README.md](README.md) or [DOCKER_GUIDE.md](DOCKER_GUIDE.md)
