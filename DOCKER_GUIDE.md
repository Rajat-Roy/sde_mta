# Docker Guide - District Marketplace

This guide provides detailed instructions for running the District Marketplace application using Docker.

## Quick Start

The fastest way to get the application running:

```bash
# Start all services
docker-compose up --build

# Or in detached mode
docker-compose up -d --build
```

Access the application at `http://localhost:8000`

Default admin credentials:
- Username: `admin`
- Password: `admin123`

## Architecture

The Docker setup includes these services:

1. **web** - Django application (port 8000)
2. **db** - PostgreSQL 16 database (port 5432)
3. **redis** - Redis 7 for caching and message broker (port 6379)
4. **celery** - Celery worker for async tasks
5. **celery-beat** - Celery beat for scheduled tasks

## Using the Makefile

We provide a Makefile for common operations:

```bash
# View all available commands
make help

# Start services
make up          # Start in foreground
make up-d        # Start in background

# View logs
make logs        # All services
make logs-web    # Django only
make logs-celery # Celery only

# Django commands
make shell              # Django shell
make migrate            # Run migrations
make makemigrations     # Create migrations
make createsuperuser    # Create admin user
make test               # Run tests

# Database operations
make db-shell    # PostgreSQL shell
make reset-db    # Reset database (WARNING: deletes data)

# Stop services
make down        # Stop all services
make clean       # Remove everything including volumes
```

## Docker Compose Commands

### Starting Services

```bash
# Build and start all services
docker-compose up --build

# Start in detached mode (background)
docker-compose up -d

# Start specific services
docker-compose up web celery

# Development mode with hot reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f celery
docker-compose logs -f db
docker-compose logs -f redis

# Last 100 lines
docker-compose logs --tail=100 web
```

### Running Django Commands

```bash
# Run any Django management command
docker-compose exec web python manage.py <command>

# Examples:
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py collectstatic
docker-compose exec web python manage.py shell
docker-compose exec web python manage.py test
```

### Database Operations

```bash
# Access PostgreSQL shell
docker-compose exec db psql -U mkt_user -d mkt_db

# Create database backup
docker-compose exec db pg_dump -U mkt_user mkt_db > backup.sql

# Restore database
cat backup.sql | docker-compose exec -T db psql -U mkt_user -d mkt_db

# Reset database
docker-compose down -v
docker-compose up -d
```

### Accessing Containers

```bash
# Open bash shell in web container
docker-compose exec web bash

# Open PostgreSQL shell
docker-compose exec db psql -U mkt_user -d mkt_db

# Open Redis CLI
docker-compose exec redis redis-cli
```

### Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (deletes database data)
docker-compose down -v

# Stop and remove images
docker-compose down --rmi all

# Complete cleanup
docker-compose down -v --rmi all --remove-orphans
```

## Environment Variables

The `.env` file contains all configuration:

```env
# Database (use service name 'db' for Docker)
DB_HOST=db
DB_PORT=5432
DB_USER=mkt_user
DB_NAME=mkt_db
DB_PASSWORD=mkt_user

# Redis (use service name 'redis' for Docker)
REDIS_URL=redis://redis:6379/0

# Gemini API
GEMINI_API_KEY=your_key_here

# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

## Development Workflow

### 1. First Time Setup

```bash
# Clone and enter directory
git clone <repo-url>
cd sde_mta

# Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Start services
docker-compose up -d --build

# Check logs
docker-compose logs -f
```

### 2. Daily Development

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f web

# Make code changes (automatically reloaded)

# Run tests
docker-compose exec web python manage.py test

# Stop when done
docker-compose down
```

### 3. Database Migrations

```bash
# After changing models
docker-compose exec web python manage.py makemigrations

# Apply migrations
docker-compose exec web python manage.py migrate

# Or use Makefile
make makemigrations
make migrate
```

### 4. Adding Dependencies

```bash
# Add to requirements.txt
echo "new-package==1.0.0" >> requirements.txt

# Rebuild containers
docker-compose up -d --build
```

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000
kill -9 <PID>

# Or change port in docker-compose.yml
ports:
  - "8001:8000"
```

### Database Connection Issues

```bash
# Check database is running
docker-compose ps db

# View database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### Celery Not Processing Tasks

```bash
# Check Celery worker status
docker-compose logs celery

# Restart Celery
docker-compose restart celery

# Check Redis connection
docker-compose exec redis redis-cli ping
```

### Reset Everything

```bash
# Complete reset (deletes all data)
docker-compose down -v --rmi all
docker-compose up -d --build
```

### View Container Resources

```bash
# Show resource usage
docker stats

# Show running containers
docker-compose ps

# Show container details
docker inspect marketplace_web
```

## Production Deployment

### Building for Production

```bash
# Set production environment variables
export DEBUG=False
export SECRET_KEY=<strong-secret-key>

# Build production image
docker-compose -f docker-compose.yml build

# Start services
docker-compose -f docker-compose.yml up -d

# Use external PostgreSQL
# Update DB_HOST in .env to external host
```

### Using External Database

Update `.env`:
```env
DB_HOST=your-external-db-host.com
DB_PORT=5432
DB_USER=your_user
DB_NAME=your_db
DB_PASSWORD=your_password
```

Then comment out the `db` service in `docker-compose.yml`.

### Security Checklist

- [ ] Set `DEBUG=False` in production
- [ ] Use strong `SECRET_KEY`
- [ ] Change default database password
- [ ] Use HTTPS/SSL
- [ ] Configure firewall rules
- [ ] Enable PostgreSQL SSL
- [ ] Set up log rotation
- [ ] Regular backups
- [ ] Monitor container health

## Monitoring

### Health Checks

Services include health checks:

```bash
# Check service health
docker-compose ps

# Manual health check
docker-compose exec web curl -f http://localhost:8000/ || exit 1
docker-compose exec db pg_isready -U mkt_user
docker-compose exec redis redis-cli ping
```

### Logs

```bash
# View all logs
docker-compose logs -f

# Export logs to file
docker-compose logs > logs.txt

# View specific time range
docker-compose logs --since "2024-01-01T00:00:00"
```

## Performance Tips

1. **Use volumes for development** - Code changes reload automatically
2. **Use multi-stage builds** - Smaller production images
3. **Limit resources** - Add resource constraints in docker-compose.yml
4. **Use BuildKit** - Faster builds with `DOCKER_BUILDKIT=1`
5. **Cache layers** - Order Dockerfile commands by change frequency

## Common Issues

### Permission Errors

```bash
# Fix file permissions
docker-compose exec web chown -R 1000:1000 /app/media
docker-compose exec web chown -R 1000:1000 /app/staticfiles
```

### Out of Space

```bash
# Clean up Docker
docker system prune -a --volumes

# Remove unused images
docker image prune -a
```

### Slow Build Times

```bash
# Use BuildKit
export DOCKER_BUILDKIT=1
docker-compose build

# Clear build cache
docker builder prune
```

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/)
