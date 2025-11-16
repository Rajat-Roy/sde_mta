# AI-Enabled District-Level Marketplace

**Name:** Rajat Roy
**Roll No:** M25AI1128

## Abstract

This project presents the architectural design of a scalable modular monolith system for an AI-assisted local marketplace intended for district-level commerce. The platform enables both regular shop owners and irregular, one-time sellers—such as farmers, artisans, and small producers—to list and sell products within their immediate locality.

### Key Features

- **Multimodal Input:** Sellers can upload product details via voice, image, or text
- **AI-Powered Ingestion:** Gemini Flash API automatically converts unstructured inputs into structured listings
- **Intelligent Search:** Multimodal search (voice, image, text) with vector similarity and geo-location ranking
- **District-Bounded:** Commerce confined to local district for community-scale operations
- **Order Management:** Complete order tracking, invoicing, and delivery management

## Demo Video

<div align="center">
  <a href="https://drive.google.com/file/d/1Z4rorIgbIwWkTZFpoVHnLqIRCemeBDw4/view?usp=sharing">
    <img src="https://drive.google.com/thumbnail?id=1Z4rorIgbIwWkTZFpoVHnLqIRCemeBDw4&sz=w1000" alt="Demo Video" width="640" />
  </a>

  <p><em>Click the thumbnail above to watch the full demo video</em></p>

  **See the platform in action, demonstrating multimodal product listing, AI-powered ingestion**
</div>

## Architecture

**Full architectural documentation with diagrams:** See [ARCHITECTURE.md](ARCHITECTURE.md)

The system follows a **modular monolith** architecture with domain-driven design principles, containerized using Docker Compose.

### Technology Stack

- **Backend:** Django 5.0.1 + Django REST Framework
- **Database:** PostgreSQL (configured via .env)
- **AI/ML:** Google Gemini Flash API
- **Async Tasks:** Celery + Redis
- **Caching:** Django Redis Cache
- **Frontend:** Django Templates + Bootstrap 5

### Project Structure

```
sde_mta/
├── marketplace/          # Main Django project
├── users/               # User management
├── products/            # Product models and listings
├── orders/              # Order management
├── search/              # Multimodal search service
├── ai_ingestion/        # AI-powered ingestion pipeline
├── templates/           # Django templates
├── static/              # Static files
├── media/               # Uploaded files
└── venv/                # Virtual environment
```

## Setup Instructions

### Option 1: Docker Setup (Recommended)

#### Prerequisites
- Docker Desktop or Docker Engine
- Docker Compose

#### Quick Start with Docker

1. **Clone the repository**
```bash
git clone https://github.com/Rajat-Roy/sde_mta.git
cd sde_mta
```

2. **Configure environment variables**

The `.env` file is already configured. Update if needed:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

3. **Build and start all services**
```bash
docker-compose up --build
```

This single command will:
- Build the Django application image
- Start PostgreSQL database
- Start Redis server
- Run database migrations
- Start Django web server (port 8000)
- Start Celery worker for async tasks
- Start Celery beat for scheduled tasks

4. **Access the application**
- Web interface: `http://localhost:8000`
- Admin panel: `http://localhost:8000/admin`
  - Username: `admin`
  - Password: `admin123`

#### Docker Commands

**Start services (detached mode)**
```bash
docker-compose up -d
```

**View logs**
```bash
docker-compose logs -f web      # Django logs
docker-compose logs -f celery   # Celery logs
docker-compose logs -f db       # PostgreSQL logs
```

**Stop services**
```bash
docker-compose down
```

**Stop and remove volumes (reset database)**
```bash
docker-compose down -v
```

**Rebuild containers**
```bash
docker-compose up --build
```

**Development mode with hot reload**
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

**Run Django commands**
```bash
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py shell
docker-compose exec web python manage.py test
```

**Access database**
```bash
docker-compose exec db psql -U mkt_user -d mkt_db
```

---

### Option 2: Local Development Setup

#### Prerequisites
- Python 3.13+
- PostgreSQL database
- Redis server
- Gemini API key

#### Installation Steps

1. **Clone the repository**
```bash
git clone https://github.com/Rajat-Roy/sde_mta.git
cd sde_mta
```

2. **Create and activate virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**

Update `.env` file:
```env
# Use localhost for local development
DB_HOST=localhost
DB_PORT=5432
DB_USER=mkt_user
DB_NAME=mkt_db
DB_PASSWORD=your_db_password

# Gemini API
GEMINI_API_KEY=your_gemini_api_key

# Django Settings
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Redis
REDIS_URL=redis://localhost:6379/0
```

5. **Run migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Create superuser**
```bash
python manage.py createsuperuser
```

7. **Start Redis server** (in separate terminal)
```bash
redis-server
```

8. **Start Celery worker** (in separate terminal)
```bash
celery -A marketplace worker -l info
```

9. **Run development server**
```bash
python manage.py runserver
```

Visit `http://localhost:8000` to access the application.

## API Endpoints

### Products
- `GET /products/api/products/` - List all products
- `POST /products/api/products/` - Create product
- `GET /products/api/products/{id}/` - Product detail
- `GET /products/api/categories/` - List categories

### AI Ingestion
- `POST /ingest/api/create/` - Create ingestion job
- `GET /ingest/api/status/{job_id}/` - Check job status

### Search
- `POST /search/api/` - Multimodal search

## Quality Attributes

### 1. Performance
- Asynchronous processing with Celery
- Redis caching for frequently accessed data
- Database indexing on critical fields

### 2. Scalability
- Modular architecture with clear boundaries
- Event-driven design with Celery queues
- Stateless REST API design

### 3. Usability
- Multimodal inputs (voice, image, text)
- Automatic location capture
- Intelligent AI-powered search

## Docker Setup

For detailed Docker instructions, see [DOCKER_GUIDE.md](DOCKER_GUIDE.md).

**Quick Docker Start:**
```bash
docker-compose up --build
```

Access at `http://localhost:8000` (admin: admin/admin123)

## Files Structure

```
.
├── docker-compose.yml      # Docker services configuration
├── docker-compose.dev.yml  # Development overrides
├── Dockerfile              # Application container
├── entrypoint.sh           # Container startup script
├── Makefile                # Convenient Docker commands
├── DOCKER_GUIDE.md         # Detailed Docker documentation
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables
├── manage.py               # Django management script
├── marketplace/            # Main Django project
├── users/                  # User management app
├── products/               # Products app
├── orders/                 # Orders app
├── search/                 # Search functionality
├── ai_ingestion/           # AI ingestion pipeline
└── templates/              # Django templates
```

## Documentation

### Architectural Diagrams

See [ARCHITECTURE.md](ARCHITECTURE.md) for comprehensive diagrams including:

- **System Context Diagram** - High-level system interactions
- **Container Architecture** - Docker services and dependencies
- **Component Architecture** - Django app modules and boundaries
- **Sequence Diagrams:**
  - Product listing flow (multimodal input → AI extraction → preview → create)
  - Search flow (vector similarity + geo-ranking)
  - Async job processing
- **Deployment Architecture** - Docker Compose orchestration
- **Data Flow Diagrams:**
  - AI ingestion pipeline
  - Search ranking pipeline
- **Database Schema** - Entity-relationship diagram

### Performance & Quality Attributes

See [QUALITY_ATTRIBUTES.md](QUALITY_ATTRIBUTES.md) for:

- Performance proof (load testing results)
- Scalability analysis (database optimization, concurrent users)
- Usability metrics (AI extraction accuracy, task completion time)

### Load Testing

See [load_tests/README.md](load_tests/README.md) for:

- Load test scenarios and instructions
- Performance targets and thresholds
- Results analysis

---

## License

Academic project for IIT Jodhpur
