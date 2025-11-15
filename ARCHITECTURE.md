# Architectural Design Documentation

**Project:** AI-Enabled District-Level Marketplace
**Student:** Rajat Roy (M25AI1128)
**Architecture Style:** Modular Monolith with Domain-Driven Design

---

## Table of Contents

1. [System Context Diagram](#system-context-diagram)
2. [Container Architecture](#container-architecture)
3. [Component Architecture](#component-architecture)
4. [Sequence Diagrams](#sequence-diagrams)
5. [Deployment Architecture](#deployment-architecture)
6. [Data Flow Diagrams](#data-flow-diagrams)
7. [Database Schema](#database-schema)

---

## System Context Diagram

High-level view of the system and its external interactions.

```mermaid
graph TB
    subgraph "District Marketplace System"
        DMS[District Marketplace<br/>Platform]
    end

    Seller[Sellers<br/>Farmers, Artisans,<br/>Shop Owners]
    Buyer[Buyers<br/>Local Customers]
    Admin[Administrators<br/>Platform Managers]

    Gemini[Google Gemini API<br/>AI Services]
    Web[Internet<br/>Web Scraping Sources]

    Seller -->|List products via<br/>text/voice/image| DMS
    Buyer -->|Search & Browse<br/>products| DMS
    Admin -->|Manage platform| DMS

    DMS -->|Extract product info<br/>Generate embeddings| Gemini
    DMS -->|Scrape product data<br/>from marketplaces| Web

    DMS -->|Product listings<br/>Search results| Buyer
    DMS -->|Confirmation<br/>AI-extracted data| Seller

    style DMS fill:#667eea,stroke:#333,stroke-width:4px,color:#fff
    style Gemini fill:#fbbc04,stroke:#333,stroke-width:2px
    style Web fill:#34a853,stroke:#333,stroke-width:2px
```

---

## Container Architecture

Docker-based containerized architecture showing all services.

```mermaid
graph TB
    subgraph "Client Layer"
        Browser[Web Browser<br/>HTML/CSS/JS]
        Mobile[Mobile Browser<br/>Responsive UI]
    end

    subgraph "Application Layer - Docker Containers"
        Web[Django Web Server<br/>Gunicorn:3 workers<br/>Port 8000]
        Celery[Celery Worker<br/>Async Task Processing]
        Beat[Celery Beat<br/>Scheduled Tasks]
    end

    subgraph "Data Layer - Docker Containers"
        PostgreSQL[PostgreSQL 16<br/>Relational Database<br/>Port 5432]
        Redis[Redis 7<br/>Cache & Message Broker<br/>Port 6379]
    end

    subgraph "Storage"
        Media[Media Files<br/>Product Images]
        Static[Static Files<br/>CSS/JS]
    end

    subgraph "External Services"
        GeminiAPI[Google Gemini API<br/>AI Processing]
        Marketplaces[E-commerce Sites<br/>Amazon, Flipkart, etc.]
    end

    Browser --> Web
    Mobile --> Web

    Web --> PostgreSQL
    Web --> Redis
    Web --> Media
    Web --> Static
    Web --> GeminiAPI
    Web --> Marketplaces
    Web --> Celery

    Celery --> PostgreSQL
    Celery --> Redis
    Celery --> Media
    Celery --> GeminiAPI

    Beat --> Redis
    Beat --> Celery

    style Web fill:#667eea,stroke:#333,stroke-width:2px,color:#fff
    style Celery fill:#764ba2,stroke:#333,stroke-width:2px,color:#fff
    style PostgreSQL fill:#336791,stroke:#333,stroke-width:2px,color:#fff
    style Redis fill:#dc382d,stroke:#333,stroke-width:2px,color:#fff
```

---

## Component Architecture

Django apps and their responsibilities (Domain-Driven Design).

```mermaid
graph TB
    subgraph "Django Project - Modular Monolith"

        subgraph "Core Configuration"
            Settings[marketplace/<br/>Settings & URLs]
        end

        subgraph "Products Domain"
            Products[products/<br/>Product Catalog<br/>CRUD Operations]
            PModels[Models:<br/>Product, Category,<br/>ProductImage, Review]
            PViews[Views:<br/>ProductViewSet<br/>API & Templates]
            PSerializers[Serializers:<br/>DRF Serialization]
        end

        subgraph "AI Ingestion Domain"
            AIIngestion[ai_ingestion/<br/>Multimodal Input<br/>Processing]
            AIServices[Services:<br/>GeminiIngestionService<br/>MockGeminiService]
            AITasks[Tasks:<br/>Celery Async Jobs]
            AIViews[Views:<br/>Extract & Create APIs]
        end

        subgraph "Search Domain"
            Search[search/<br/>Vector Similarity<br/>Search]
            SearchService[Services:<br/>Semantic Search<br/>Geo-location Ranking]
            SearchModels[Models:<br/>SearchQuery,<br/>SearchResult]
        end

        subgraph "Users Domain"
            Users[users/<br/>Authentication<br/>User Profiles]
            UserModels[Models:<br/>CustomUser<br/>with Location]
        end

        subgraph "Orders Domain"
            Orders[orders/<br/>Transaction<br/>Management]
            OrderModels[Models:<br/>Order, OrderItem,<br/>Payment]
        end

    end

    Products --> PModels
    Products --> PViews
    Products --> PSerializers

    AIIngestion --> AIServices
    AIIngestion --> AITasks
    AIIngestion --> AIViews
    AIIngestion --> Products

    Search --> SearchService
    Search --> SearchModels
    Search --> Products
    Search --> AIIngestion

    Users --> UserModels

    Orders --> OrderModels
    Orders --> Products
    Orders --> Users

    Settings --> Products
    Settings --> AIIngestion
    Settings --> Search
    Settings --> Users
    Settings --> Orders

    style Products fill:#4ecdc4,stroke:#333,stroke-width:2px
    style AIIngestion fill:#ff6b6b,stroke:#333,stroke-width:2px
    style Search fill:#ffd93d,stroke:#333,stroke-width:2px
    style Users fill:#95e1d3,stroke:#333,stroke-width:2px
    style Orders fill:#f38181,stroke:#333,stroke-width:2px
```

---

## Sequence Diagrams

### 1. Product Listing Flow (Multimodal Input)

```mermaid
sequenceDiagram
    actor Seller
    participant UI as Web Interface
    participant View as CreateIngestionJobView
    participant Service as GeminiService<br/>(Real or Mock)
    participant Gemini as Google Gemini API
    participant Web as Web Scraper
    participant DB as PostgreSQL

    Seller->>UI: Enter product description<br/>(text/voice/image)
    UI->>View: POST /ingest/api/extract/

    View->>Service: process_text_input(text)
    Service->>Gemini: Extract product info<br/>(name, price, category, etc.)
    Gemini-->>Service: Structured JSON data

    Service->>Web: search_product_images(name)
    Web-->>Service: Image URLs from marketplaces

    Service->>Gemini: enrich_product_from_web(name)
    Gemini-->>Service: Description, features,<br/>price range, related products

    Service-->>View: Extracted + Enriched data
    View-->>UI: JSON response with<br/>product details & images

    UI->>Seller: Display Preview Modal<br/>(editable fields)
    Seller->>UI: Review & Edit data
    Seller->>UI: Click "Create Product"

    UI->>View: POST /ingest/api/create/
    View->>Service: generate_embedding(text)
    Service->>Gemini: Get vector embedding
    Gemini-->>Service: 768-dim vector

    View->>DB: Create Product with<br/>embedding & images
    DB-->>View: Product saved
    View-->>UI: Success response
    UI-->>Seller: Product listed successfully
```

### 2. Multimodal Search Flow

```mermaid
sequenceDiagram
    actor Buyer
    participant UI as Search Interface
    participant View as MultimodalSearchView
    participant SearchSvc as SearchService
    participant GeminiSvc as GeminiService
    participant DB as PostgreSQL

    Buyer->>UI: Enter search query<br/>example: laptop with good camera
    UI->>View: POST /search/api/

    View->>SearchSvc: search(query, type, location)
    SearchSvc->>GeminiSvc: generate_embedding(query)
    GeminiSvc-->>SearchSvc: Query vector (768-dim)

    SearchSvc->>DB: Fetch active products<br/>with embeddings
    DB-->>SearchSvc: Product list with vectors

    SearchSvc->>SearchSvc: Calculate cosine similarity<br/>for each product

    alt User has location
        SearchSvc->>SearchSvc: Calculate geodesic distance<br/>from user to each product
        SearchSvc->>SearchSvc: Compute weighted score:<br/>70% similarity + 30% proximity
    else No location
        SearchSvc->>SearchSvc: Score = 100% similarity
    end

    SearchSvc->>DB: Apply filters<br/>(district, category)
    SearchSvc->>SearchSvc: Sort by combined score
    SearchSvc->>SearchSvc: Return top N results

    SearchSvc-->>View: Ranked product list<br/>with scores
    View-->>UI: JSON response
    UI-->>Buyer: Display search results<br/>with relevance scores
```

### 3. Asynchronous Job Processing (Optional Mode)

```mermaid
sequenceDiagram
    participant Client
    participant WebServer as Django Web
    participant Redis as Redis Broker
    participant Celery as Celery Worker
    participant DB as PostgreSQL
    participant Gemini as Gemini API

    Client->>WebServer: POST /ingest/api/create/<br/>(async mode)
    WebServer->>DB: Create IngestionJob<br/>status='pending'
    DB-->>WebServer: Job ID

    WebServer->>Redis: Queue task<br/>process_ingestion_job(job_id)
    Redis-->>WebServer: Task queued
    WebServer-->>Client: Job ID (immediate response)

    Client->>WebServer: Poll /ingest/api/status/{job_id}
    WebServer->>DB: Get job status
    DB-->>WebServer: status='pending'
    WebServer-->>Client: Still processing...

    Note over Celery: Async processing starts
    Celery->>Redis: Dequeue task
    Redis-->>Celery: Job ID

    Celery->>DB: Update status='processing'
    Celery->>Gemini: Extract & Enrich
    Gemini-->>Celery: Product data
    Celery->>DB: Create Product
    Celery->>DB: Update status='completed'

    Client->>WebServer: Poll /ingest/api/status/{job_id}
    WebServer->>DB: Get job status
    DB-->>WebServer: status='completed'<br/>product_id
    WebServer-->>Client: Product created successfully
```

---

## Deployment Architecture

Docker Compose orchestration with volume management.

```mermaid
graph TB
    subgraph "Docker Host Machine"

        subgraph "Docker Network: marketplace_default"

            subgraph "Web Container"
                Django[Django + Gunicorn<br/>Python 3.13<br/>Workers: 3<br/>Port: 8000]
            end

            subgraph "Database Container"
                PG[PostgreSQL 16<br/>Alpine Linux<br/>Port: 5432]
            end

            subgraph "Cache Container"
                RedisC[Redis 7<br/>Alpine Linux<br/>Port: 6379]
            end

            subgraph "Worker Container"
                CeleryW[Celery Worker<br/>Python 3.13<br/>Concurrency: Auto]
            end

            subgraph "Scheduler Container"
                CeleryB[Celery Beat<br/>Python 3.13<br/>Periodic Tasks]
            end

        end

        subgraph "Docker Volumes (Persistent Storage)"
            PGData[(postgres_data<br/>Database files)]
            RedisData[(redis_data<br/>Cache data)]
            MediaVol[(media_volume<br/>Product images)]
            StaticVol[(static_volume<br/>CSS/JS files)]
        end

    end

    subgraph "External Access"
        Client[Client Browser<br/>localhost:8000]
        DBClient[DB Client<br/>localhost:5432]
    end

    Client -->|HTTP| Django
    DBClient -->|PostgreSQL| PG

    Django --> PG
    Django --> RedisC
    Django --> MediaVol
    Django --> StaticVol

    CeleryW --> PG
    CeleryW --> RedisC
    CeleryW --> MediaVol

    CeleryB --> RedisC

    PG --> PGData
    RedisC --> RedisData

    style Django fill:#667eea,stroke:#333,stroke-width:2px,color:#fff
    style PG fill:#336791,stroke:#333,stroke-width:2px,color:#fff
    style RedisC fill:#dc382d,stroke:#333,stroke-width:2px,color:#fff
    style CeleryW fill:#37b24d,stroke:#333,stroke-width:2px,color:#fff
    style CeleryB fill:#fab005,stroke:#333,stroke-width:2px,color:#fff
```

---

## Data Flow Diagrams

### AI Ingestion Pipeline

```mermaid
graph LR
    subgraph "Input Sources"
        Text[Text Input<br/>Natural Language]
        Voice[Voice Input<br/>Audio File]
        Image[Image Input<br/>Product Photo]
    end

    subgraph "AI Processing Layer"
        TextProc[Text Extraction<br/>Gemini Flash Lite]
        VoiceProc[Speech-to-Text<br/>+ Text Extraction]
        ImageProc[Vision Analysis<br/>+ Text Extraction]

        Enrich[Web Enrichment<br/>Google Search Grounding]
        Scraper[Image Scraper<br/>BeautifulSoup]
        Embed[Embedding Generation<br/>text-embedding-004]
    end

    subgraph "Storage Layer"
        ProdDB[(Products Table<br/>PostgreSQL)]
        ImageDB[(Product Images<br/>File Storage)]
        EmbedDB[(Vector Embeddings<br/>JSON Field)]
    end

    subgraph "Output"
        Product[Created Product<br/>with AI Metadata]
    end

    Text --> TextProc
    Voice --> VoiceProc
    Image --> ImageProc

    TextProc --> Enrich
    VoiceProc --> Enrich
    ImageProc --> Enrich

    Enrich --> Scraper
    Scraper --> ImageDB

    Enrich --> Embed

    Embed --> EmbedDB
    EmbedDB --> ProdDB
    ImageDB --> ProdDB

    ProdDB --> Product

    style TextProc fill:#fbbc04,stroke:#333,stroke-width:2px
    style VoiceProc fill:#fbbc04,stroke:#333,stroke-width:2px
    style ImageProc fill:#fbbc04,stroke:#333,stroke-width:2px
    style Enrich fill:#34a853,stroke:#333,stroke-width:2px
    style Embed fill:#4285f4,stroke:#333,stroke-width:2px
```

### Search Ranking Pipeline

```mermaid
graph TB
    Query[User Search Query<br/>laptop with good camera]

    subgraph QueryProc["Query Processing"]
        EmbedQ[Generate Query<br/>Embedding Vector<br/>768 dimensions]
    end

    subgraph ProdRetrieval["Product Retrieval"]
        Filter[Apply Filters<br/>District, Category,<br/>Active Status]
        FetchDB[(Fetch Products<br/>with Embeddings)]
    end

    subgraph SimCalc["Similarity Calculation"]
        CosineSim[Compute Cosine<br/>Similarity Score<br/>dot product / norms]
    end

    subgraph GeoRank["Geo-location Ranking"]
        HasLoc{User Has<br/>Location?}
        GeoDist[Calculate Geodesic<br/>Distance in KM<br/>Haversine Formula]
        DistScore[Distance Score<br/>1 / 1 + distance]
    end

    subgraph CombScore["Combined Scoring"]
        WeightedScore[Final Score<br/>0.7 x Similarity<br/>0.3 x Distance]
        NoLocScore[Final Score<br/>Similarity Only]
    end

    subgraph Results["Result Ranking"]
        Sort[Sort by<br/>Final Score DESC]
        TopN[Return Top N<br/>Results]
    end

    Query --> EmbedQ
    EmbedQ --> Filter
    Filter --> FetchDB
    FetchDB --> CosineSim

    CosineSim --> HasLoc
    HasLoc -->|Yes| GeoDist
    HasLoc -->|No| NoLocScore

    GeoDist --> DistScore
    DistScore --> WeightedScore

    WeightedScore --> Sort
    NoLocScore --> Sort
    Sort --> TopN

    style CosineSim fill:#4285f4,stroke:#333,stroke-width:2px,color:#fff
    style WeightedScore fill:#34a853,stroke:#333,stroke-width:2px,color:#fff
```

---

## Database Schema

Entity-Relationship Diagram for core models.

```mermaid
erDiagram
    User ||--o{ Product : "sells"
    User ||--o{ Order : "places"
    User ||--o{ Review : "writes"

    Category ||--o{ Product : "categorizes"
    Category ||--o| Category : "has parent"

    Product ||--o{ ProductImage : "has"
    Product ||--o{ Review : "receives"
    Product ||--o{ OrderItem : "included in"
    Product ||--o| IngestionJob : "created from"

    Order ||--o{ OrderItem : "contains"

    Product ||--o{ SearchResult : "appears in"
    SearchQuery ||--o{ SearchResult : "returns"

    User {
        int id PK
        string username
        string email
        string password_hash
        decimal latitude
        decimal longitude
        string district
        datetime created_at
    }

    Category {
        int id PK
        string name UK
        text description
        int parent_id FK
        datetime created_at
    }

    Product {
        int id PK
        int seller_id FK
        int category_id FK
        string name
        text description
        decimal price
        int quantity
        string unit
        decimal latitude
        decimal longitude
        string district "INDEXED"
        string input_method
        json ai_metadata
        json embedding "768-dim vector"
        boolean is_active "INDEXED"
        datetime created_at "INDEXED"
    }

    ProductImage {
        int id PK
        int product_id FK
        string image_path
        boolean is_primary
        string caption
        datetime created_at
    }

    Review {
        int id PK
        int product_id FK
        int buyer_id FK
        int rating
        text comment
        datetime created_at
    }

    Order {
        int id PK
        int buyer_id FK
        decimal total_amount
        string status
        datetime created_at
    }

    OrderItem {
        int id PK
        int order_id FK
        int product_id FK
        int quantity
        decimal price_at_purchase
    }

    IngestionJob {
        int id PK
        int user_id FK
        string input_type
        text input_text
        string status
        json extracted_data
        int product_id FK
        datetime created_at
    }

    SearchQuery {
        int id PK
        int user_id FK
        string query_text
        json query_embedding
        string search_type
        datetime created_at
    }

    SearchResult {
        int id PK
        int search_query_id FK
        int product_id FK
        float similarity_score
        int rank
    }
```

---

## Key Architectural Decisions

### 1. Modular Monolith Architecture

**Decision:** Use Django apps as module boundaries instead of microservices.

**Rationale:**
- Simpler deployment for district-level scale (100-500 concurrent users)
- Shared database transactions (ACID guarantees)
- Lower operational complexity
- Easy to extract modules into microservices later if needed

**Trade-offs:**
- Modules share same codebase (requires discipline)
- Cannot scale modules independently (acceptable for current scale)

### 2. Synchronous + Optional Async Processing

**Decision:** Support both synchronous (preview/edit) and asynchronous (bulk) modes.

**Rationale:**
- **Synchronous:** Better UX for single product listing (immediate feedback)
- **Asynchronous:** Better performance for bulk operations
- Feature flag `USE_ASYNC_PROCESSING` enables both modes

**Implementation:**
- Default: Synchronous with preview modal
- Optional: Celery tasks for background processing

### 3. Mock AI Service for Testing

**Decision:** Implement `MockGeminiService` alongside real `GeminiIngestionService`.

**Rationale:**
- Enable unlimited load testing without API costs
- Fast responses (<100ms vs 2-15s)
- Consistent test data
- No external dependencies during development

**Implementation:**
- Environment variable `USE_MOCK_AI=True/False`
- Same interface as real service
- Returns realistic fake data

### 4. Vector Embeddings in JSON Field

**Decision:** Store 768-dimensional embeddings as JSON arrays in PostgreSQL.

**Rationale:**
- No need for specialized vector database (pgvector) at current scale
- Simpler deployment
- Acceptable performance for district-level scale (<10,000 products)
- Can migrate to pgvector or dedicated vector DB later

**Trade-offs:**
- Slower similarity search than specialized vector DB
- Acceptable: Search completes in <100ms for 10,000 products

### 5. Container Orchestration with Docker Compose

**Decision:** Use Docker Compose instead of Kubernetes.

**Rationale:**
- Appropriate for single-server deployment
- Simpler than Kubernetes for district-level scale
- Easy local development with docker-compose.dev.yml
- Can migrate to Kubernetes if scaling beyond single server

---

## Scalability Considerations

### Horizontal Scaling Points

```mermaid
graph LR
    subgraph "Current Single-Server Setup"
        Web1[Web Server<br/>3 workers]
        Celery1[Celery Worker<br/>1 instance]
        DB1[(PostgreSQL)]
        Redis1[(Redis)]
    end

    subgraph "Multi-Server Scaling (Future)"
        LB[Load Balancer]
        Web2[Web Server 1<br/>5 workers]
        Web3[Web Server 2<br/>5 workers]
        Web4[Web Server N<br/>5 workers]

        Celery2[Celery Worker 1]
        Celery3[Celery Worker 2]
        Celery4[Celery Worker N]

        DBMaster[(PostgreSQL<br/>Primary)]
        DBReplica[(PostgreSQL<br/>Read Replica)]

        RedisCluster[(Redis Cluster<br/>3 nodes)]
    end

    LB --> Web2
    LB --> Web3
    LB --> Web4

    Web2 --> DBMaster
    Web3 --> DBMaster
    Web4 --> DBReplica

    Web2 --> RedisCluster
    Web3 --> RedisCluster
    Web4 --> RedisCluster

    Celery2 --> DBMaster
    Celery3 --> DBMaster
    Celery4 --> DBMaster

    Celery2 --> RedisCluster
    Celery3 --> RedisCluster
    Celery4 --> RedisCluster

    style Web2 fill:#667eea,stroke:#333,stroke-width:2px,color:#fff
    style Web3 fill:#667eea,stroke:#333,stroke-width:2px,color:#fff
    style Web4 fill:#667eea,stroke:#333,stroke-width:2px,color:#fff
```

### Database Optimization Strategy

**Indexes Created:**
- Single column: `district`, `category`, `is_active`, `created_at`, `seller`
- Composite: `(district, is_active)`, `(category, is_active)`, `(district, category, is_active)`

**Query Optimization:**
- `select_related()` for ForeignKeys (category, seller)
- `prefetch_related()` for reverse FKs (images, reviews)
- Result: 80% query reduction (15 → 3 queries per request)

---

## Technology Stack Summary

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | HTML, CSS, JavaScript, Bootstrap 5 | Responsive UI |
| **Backend** | Django 5.0, Django REST Framework | Web framework, APIs |
| **Database** | PostgreSQL 16 | Relational data storage |
| **Cache/Broker** | Redis 7 | Caching, Celery message broker |
| **Task Queue** | Celery 5.3 | Async job processing |
| **Web Server** | Gunicorn 21.2 | WSGI HTTP server |
| **AI/ML** | Google Gemini 2.0 Flash Lite | Text/image/voice processing |
| **Embeddings** | text-embedding-004 | 768-dim vector generation |
| **Search** | NumPy, scikit-learn | Cosine similarity, ranking |
| **Geolocation** | GeoPy | Distance calculation |
| **Web Scraping** | BeautifulSoup4 | Marketplace data extraction |
| **Containerization** | Docker, Docker Compose | Service orchestration |
| **Load Testing** | Locust | Performance testing |
| **Monitoring** | Django Debug Toolbar | Query profiling |

---

## Conclusion

This architecture demonstrates:

1. **Modularity:** Clear separation of concerns via Django apps
2. **Scalability:** Database indexes, query optimization, horizontal scaling readiness
3. **Performance:** Async processing, caching, mock AI mode for testing
4. **Maintainability:** Domain-driven design, clean boundaries
5. **Flexibility:** Support for multimodal inputs, vector similarity search
6. **Testability:** Mock services, load testing infrastructure

The design balances simplicity (modular monolith) with scalability (containerization, async processing) appropriate for district-level commerce (100-500 concurrent users, 10,000-100,000 products).

---

**Last Updated:** 2025-01-16
**Author:** Rajat Roy (M25AI1128)
