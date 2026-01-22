# Knowledge Graph System Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER INTERFACE LAYER                        │
│              (Web/Mobile App - REST Clients)                    │
└──────────────────────┬──────────────────────────────────────────┘
                       │ HTTP Requests
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API LAYER                                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐    │
│  │ EntityViewSet│ │ Relationship │ │    GraphViewSet      │    │
│  │              │ │   ViewSet    │ │                      │    │
│  │ - search     │ │              │ │ - statistics         │    │
│  │ - similar    │ │ - query      │ │ - find_path          │    │
│  │ - connections│ │              │ │ - operations         │    │
│  └──────────────┘ └──────────────┘ └──────────────────────┘    │
│                                                                  │
│  Serializers: Entity, Relationship, Graph, Search Results      │
│  Pagination, Filtering, Ordering enabled                        │
└──────────────────────┬──────────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
│  Data Layer  │ │ Processing   │ │ Background Tasks │
│              │ │ Services     │ │                  │
└──────────────┘ └──────────────┘ └──────────────────┘


┌──────────────────────────────────────────────────────────────────┐
│                   DATA ACCESS LAYER                              │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Django ORM Models                           │   │
│  │                                                          │   │
│  │  Entity ◄──── Relationship ───► Entity                  │   │
│  │    │                                                    │   │
│  │    └─── EntityItemLink ──► Item                        │   │
│  │         (From API app)                                 │   │
│  │                                                          │   │
│  │  Graph (user's knowledge graph snapshot)               │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌────────────────────────────────────┐                         │
│  │    PostgreSQL Database             │                         │
│  │  - Entities (with embeddings)      │                         │
│  │  - Relationships (with strength)   │                         │
│  │  - Entity-Item Links               │                         │
│  │  - Graph Snapshots                 │                         │
│  └────────────────────────────────────┘                         │
└──────────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────┐
│              PROCESSING SERVICES LAYER                           │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Data Ingestion Pipeline (ingestion.py)                   │  │
│  │                                                            │  │
│  │  ItemExtractor ─┐                                         │  │
│  │  NoteExtractor  ├─► DataExtractor ─► Item Normalization  │  │
│  │  FileExtractor  │                                         │  │
│  │  MessageExtractor                                         │  │
│  │  BookmarkExtractor                                        │  │
│  │  TaskExtractor                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Relationship Detection Engine (relationship_detector.py)  │  │
│  │                                                            │  │
│  │  EntityExtractor           ┐                             │  │
│  │  ├─ Named Entity Recognition  ├─► RelationshipDetector  │  │
│  │  ├─ Noun Phrase Extraction    │                          │  │
│  │  └─ Keyword Extraction        │                          │  │
│  │                               │                          │  │
│  │  TopicClusterer (TF-IDF+KMeans) ┤                       │  │
│  │  └─ Document Clustering        │                        │  │
│  │                               │                          │  │
│  │  Pattern Matching            ┤                           │  │
│  │  Semantic Similarity         ┘                           │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Embedding Service (embeddings.py)                        │  │
│  │                                                            │  │
│  │  EmbeddingService:                                       │  │
│  │  ├─ embed_text()           (sentence-transformers)      │  │
│  │  ├─ embed_texts()          (batch processing)           │  │
│  │  ├─ compute_similarity()   (cosine similarity)          │  │
│  │  ├─ find_similar()         (top-k retrieval)           │  │
│  │  └─ batch_similarity()     (matrix computation)        │  │
│  │                                                            │  │
│  │  Model: all-MiniLM-L6-v2 (384-dim vectors)             │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────┐
│           ASYNCHRONOUS TASK PROCESSING LAYER                     │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │           Celery Task Queue (tasks.py)                      │ │
│  │                                                             │ │
│  │  Item Indexing Tasks:                                      │ │
│  │  ├─ index_item_in_graph()     (single item)              │ │
│  │  └─ batch_index_items()       (batch processing)         │ │
│  │                                                             │ │
│  │  Graph Operations:                                         │ │
│  │  ├─ update_graph_snapshot()   (stats update)             │ │
│  │  ├─ rebuild_graph_for_user()  (complete rebuild)        │ │
│  │  ├─ ingest_from_source()      (data ingestion)          │ │
│  │  └─ delete_old_relationships()                           │ │
│  │                                                             │ │
│  │  All tasks have:                                          │ │
│  │  - Retry logic (exponential backoff)                     │ │
│  │  - Error handling                                         │ │
│  │  - Transactional consistency                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                          │                                        │
│                 Task Broker Connection                           │
│                          │                                        │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                  Redis Queue                               │ │
│  │  (or RabbitMQ/other AMQP broker)                          │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                          │                                        │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │           Celery Worker Processes                          │ │
│  │  (Multiple workers for parallel processing)               │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────┐
│           MANAGEMENT & MAINTENANCE LAYER                         │
│                                                                   │
│  Django Management Commands:                                    │
│  ├─ init_graph           (initialize user's graph)             │
│  ├─ rebuild_graph        (clear and rebuild)                   │
│  ├─ index_items          (index specific items)                │
│  └─ graph_maintenance    (cleanup and optimization)            │
│                                                                  │
│  Maintenance Operations:                                         │
│  ├─ Clean up old entities (>90 days)                           │
│  ├─ Remove orphaned entities                                    │
│  ├─ Consolidate duplicates                                      │
│  ├─ Update statistics                                           │
│  └─ Dry-run validation                                          │
└──────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

### Item Ingestion & Indexing Flow

```
User Creates/Updates Item
        │
        ▼
API Endpoint: POST /items/
        │
        ▼
Item Stored in Database
        │
        ▼
Signal Triggers (optional)
        │
        ▼
Queue Celery Task: index_item_in_graph
        │
        ▼
Celery Worker Receives Task
        │
        ├─► Data Extraction
        │   └─► Get item content (title, body, metadata)
        │
        ├─► Entity Detection
        │   ├─► Named Entity Recognition (NER)
        │   ├─► Noun Phrase Extraction
        │   └─► Keyword Extraction
        │
        ├─► Generate Embeddings
        │   └─► sentence-transformers model
        │
        ├─► Relationship Detection
        │   ├─► Pattern-based matching
        │   └─► Semantic similarity
        │
        └─► Database Update (Transaction)
            ├─► Create/Update Entities
            ├─► Create/Update Relationships
            ├─► Create EntityItemLinks
            └─► Update frequency scores

Task Complete
        │
        ▼
Update Graph Statistics
        │
        ▼
Graph Ready for Query
```

### Query Flow

```
API Request: GET /entities/search/?q=python
        │
        ▼
Request Validation & Authentication
        │
        ▼
Query Parameters Parsed
        │
        ▼
Database Query with Filters
        │
        Filter by user
        │
        └─► Full-text search on name/description
        │
        └─► Entity type filtering
        │
        └─► Frequency scoring
        │
        ▼
Results Sorted & Paginated
        │
        ▼
Serializer Converts to JSON
        │
        ▼
HTTP Response (200 OK)
        │
        ▼
Client Receives Data
```

### Similarity Search Flow

```
API Request: GET /entities/1/similar/
        │
        ▼
Load Source Entity with Embedding
        │
        ▼
Get All Other Entities with Embeddings
        │
        ▼
Compute Similarity Matrix
        │
        └─► For each candidate entity:
            └─► cosine_similarity(source_embedding, candidate_embedding)
            │
            └─► Normalize to [0, 1]
        │
        ▼
Filter by Threshold (default: 0.6)
        │
        ▼
Sort by Similarity (descending)
        │
        ▼
Return Top-K Results (default: 5)
        │
        ▼
Serialize & Return JSON
```

### Path Finding Flow (BFS)

```
API Request: POST /graph/find_path/
        │
        ├─► source_entity_id: 10
        ├─► target_entity_id: 50
        └─► max_hops: 5
        │
        ▼
Initialize BFS Queue
        │
        queue = [(source_id, [source_id])]
        │
        ▼
Process Queue (BFS)
        │
        while queue is not empty:
        │   ├─► current_entity, path = queue.pop()
        │   │
        │   ├─► if current == target:
        │   │   └─► Build entity details and relationships
        │   │
        │   ├─► if path length < max_hops:
        │   │   └─► Get outgoing relationships
        │   │       └─► Add neighbors to queue
        │   │
        │   └─► Continue
        │
        ▼
Path Found or Not Found
        │
        ▼
Return Result with Path Details
```

## Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMPONENT INTERACTIONS                       │
└─────────────────────────────────────────────────────────────────┘

API ViewSet ──► Serializer ──► Validator
    │                             │
    ▼                             ▼
Database Models ◄─────── Query Layer
    │
    ├─► Entity
    ├─► Relationship
    ├─► EntityItemLink
    └─► Graph


Celery Task ──► Ingestion Pipeline ──► Data Extractor
    │                                      │
    ├─► Get Item                           ├─► NoteExtractor
    ├─► Extract Data                       ├─► FileExtractor
    │                                      ├─► MessageExtractor
    └─► Process                            ├─► BookmarkExtractor
        └─► Relationship Detector          └─► TaskExtractor
            │
            ├─► Entity Extractor
            │   ├─► Named Entity Recognition
            │   ├─► Noun Phrase Extraction
            │   └─► Keyword Extraction
            │
            ├─► Embedding Service
            │   ├─► Text to Vector
            │   └─► Similarity Computation
            │
            └─► Topic Clusterer
                └─► TF-IDF + KMeans


User ──► API ──► ViewSet ──► Business Logic ──► Database
            │
            └─► Serializer
                ├─► Validation
                └─► Transformation
```

## Technology Stack

```
Frontend Layer:
├─ REST API Client (Browser/Mobile)
└─ HTTP/REST

Application Layer:
├─ Django 4.2
├─ Django REST Framework
├─ Django Filters
└─ CORS Headers

Core Services:
├─ Sentence Transformers (Embeddings)
├─ NLTK (NLP)
├─ scikit-learn (ML/Clustering)
├─ NetworkX (Graph Algorithms)
└─ spaCy (Advanced NLP)

Data Processing:
├─ Pandas
├─ NumPy
└─ Python Standard Library

Storage:
├─ PostgreSQL (Primary Data)
└─ Python Pickle/JSON (Embeddings)

Task Processing:
├─ Celery
├─ Redis (Broker & Result Backend)
└─ Python multiprocessing

Utilities:
├─ python-decouple (Config)
├─ requests (HTTP)
└─ PyYAML (Config)

Testing:
├─ pytest
├─ pytest-django
└─ factory-boy
```

## Scalability Considerations

### Horizontal Scaling

```
Load Balancer
    │
    ├─► Django Instance 1
    ├─► Django Instance 2
    └─► Django Instance 3

All connecting to:
    ├─► PostgreSQL (with replication)
    ├─► Redis (with sentinel)
    └─► Celery Workers (multiple)
```

### Vertical Scaling

- Increase worker processes
- Optimize batch sizes
- Cache frequently accessed entities
- Index database columns

### Performance Optimizations

- Database query optimization
- Embedding cache layer
- Relationship query optimization
- Async task processing
- Pagination for large results

## Security Architecture

```
Authentication & Authorization:
├─ Token-based Authentication
├─ User-scoped Queries
├─ Permission Classes
└─ CORS Configuration

Data Protection:
├─ SQL Injection Prevention (ORM)
├─ CSRF Protection
├─ XSS Protection
└─ SQL Injection Prevention

Deployment:
├─ HTTPS/TLS
├─ Environment Variables
├─ Secret Key Management
└─ Database Credentials Encrypted
```

## Monitoring & Observability

```
Logging:
├─ Django Logging
├─ Celery Task Logging
├─ Application Logs
└─ Error Tracking

Metrics:
├─ Task Processing Time
├─ API Response Time
├─ Database Query Time
├─ Error Rates
└─ Graph Health Score

Debugging:
├─ Django Debug Toolbar
├─ Celery Inspect
├─ Database Query Analysis
└─ Logging Configuration
```

This architecture provides:

- ✅ Modularity and separation of concerns
- ✅ Scalability through async processing
- ✅ Reliability with error handling and retries
- ✅ Performance through caching and optimization
- ✅ Maintainability through clear interfaces
- ✅ Extensibility for future enhancements
