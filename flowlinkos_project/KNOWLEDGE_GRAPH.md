# FlowLinkOS Knowledge Graph System

## Overview

The Knowledge Graph system automatically connects your notes, files, messages, bookmarks, and tasks into a unified semantic graph. It intelligently detects relationships, clusters topics, and enables powerful querying across all your information.

## Architecture

### Components

1. **Embedding Service** (`embeddings.py`)
    - Generates semantic vector embeddings using sentence-transformers
    - Computes similarity between text entities
    - Supports batch processing for efficiency

2. **Data Ingestion Pipeline** (`ingestion.py`)
    - Extracts data from multiple sources (notes, files, messages, bookmarks, tasks)
    - Normalizes data into standard format
    - Handles source-specific metadata

3. **Relationship Detection Engine** (`relationship_detector.py`)
    - Extracts named entities using NLP
    - Detects relationships through pattern matching
    - Infers relationships via semantic similarity
    - Performs topic clustering

4. **Background Task Processing** (`tasks.py`)
    - Asynchronous Celery tasks for indexing
    - Batch processing of items
    - Graph snapshot updates
    - Maintenance and cleanup

5. **API Endpoints** (`views.py`, `serializers.py`)
    - RESTful API for graph querying
    - Entity search and similarity
    - Relationship analysis
    - Path finding between entities
    - Graph statistics and health

6. **Management Commands** (`management/commands/`)
    - Graph initialization and setup
    - Graph rebuilding
    - Item indexing
    - Maintenance and cleanup

## Data Model

### Entity

Represents a concept, person, place, or topic in the graph.

```python
Entity {
    id: int
    user: User (FK)
    name: str (max 500)
    entity_type: str (concept|person|place|organization|project|topic|other)
    description: str
    embedding: List[float] (semantic vector)
    metadata: dict
    frequency_score: int (how often mentioned)
}
```

### Relationship

Represents a connection between two entities.

```python
Relationship {
    id: int
    user: User (FK)
    source_entity: Entity (FK)
    target_entity: Entity (FK)
    relationship_type: str (mentions|related_to|depends_on|part_of|similar_to|created_by|assigned_to|references|custom)
    strength: float (0-1, confidence of relationship)
    metadata: dict
}
```

### EntityItemLink

Links entities to the items (notes, files, etc.) they appear in.

```python
EntityItemLink {
    id: int
    entity: Entity (FK)
    item: Item (FK)
    mention_count: int
    context: str (context of mention)
}
```

### Graph

Represents a snapshot of the user's knowledge graph.

```python
Graph {
    id: int
    user: User (FK)
    name: str
    entity_count: int
    relationship_count: int
    health_score: float (0-1)
    last_indexed: datetime
}
```

## API Endpoints

### Entities

#### List & Search Entities

```
GET /api/knowledge-graph/entities/
GET /api/knowledge-graph/entities/search/?q=python&entity_type=concept&min_frequency=5
```

#### Get Entity Details

```
GET /api/knowledge-graph/entities/{id}/
```

#### Find Similar Entities

```
GET /api/knowledge-graph/entities/{id}/similar/?top_k=5&threshold=0.6
```

#### Get Entity Connections

```
GET /api/knowledge-graph/entities/{id}/connections/?depth=2
```

### Relationships

#### List Relationships

```
GET /api/knowledge-graph/relationships/
```

#### Query Relationships

```
POST /api/knowledge-graph/relationships/query/
{
    "entity_id": 123,
    "relationship_type": "related_to",
    "depth": 2
}
```

### Graph Operations

#### Get Graph Statistics

```
GET /api/knowledge-graph/graph/statistics/
```

Response:

```json
{
    "total_entities": 450,
    "total_relationships": 1200,
    "average_connections_per_entity": 2.67,
    "top_entities": [
        {
            "id": 1,
            "name": "Python",
            "entity_type": "Concept",
            "frequency_score": 45
        }
    ],
    "health_score": 0.89,
    "last_updated": "2024-01-22T10:30:00Z"
}
```

#### Find Path Between Entities

```
POST /api/knowledge-graph/graph/find_path/
{
    "source_entity_id": 10,
    "target_entity_id": 50,
    "max_hops": 5
}
```

Response:

```json
{
    "found": true,
    "path": [
        { "id": 10, "name": "Project A", "type": "Project" },
        { "id": 25, "name": "Team Lead", "type": "Person" },
        { "id": 50, "name": "Budget", "type": "Concept" }
    ],
    "hops": 2,
    "relationships": [
        {
            "from": "Project A",
            "to": "Team Lead",
            "type": "created_by",
            "strength": 0.95
        },
        {
            "from": "Team Lead",
            "to": "Budget",
            "type": "manages",
            "strength": 0.85
        }
    ]
}
```

#### Perform Batch Operations

```
POST /api/knowledge-graph/graph/operations/
{
    "operation": "index_items",
    "item_ids": [1, 2, 3, 4, 5]
}
```

Available operations:

- `index_items` - Index specific items or all unindexed items
- `rebuild_graph` - Clear and rebuild entire graph
- `update_snapshot` - Update graph statistics
- `cleanup` - Clean up old or orphaned data

### Entity-Item Links

#### Get Item Mentions

```
GET /api/knowledge-graph/entity-links/?entity__name=Python
```

## Usage Workflow

### 1. Initialize Graph (One-time Setup)

```bash
python manage.py init_graph <user_id> --async
```

This will:

- Create a default Graph entry
- Ingest data from all active sources
- Queue items for indexing

### 2. Index New Items (Ongoing)

Items are automatically indexed when:

- Created via API
- Imported from connected sources
- Manually triggered via management command

Manual indexing:

```bash
python manage.py index_items <user_id> --item-type note --batch-size 50
```

### 3. Query the Graph

#### Search Entities

```python
# Python example
import requests

headers = {'Authorization': f'Bearer {token}'}

# Search for entities
response = requests.get(
    'http://localhost:8000/api/knowledge-graph/entities/search/',
    params={'q': 'machine learning', 'min_frequency': 3},
    headers=headers
)
```

#### Find Relationships

```python
response = requests.post(
    'http://localhost:8000/api/knowledge-graph/relationships/query/',
    json={'entity_id': 123, 'relationship_type': 'related_to'},
    headers=headers
)
```

#### Find Similar Concepts

```python
response = requests.get(
    'http://localhost:8000/api/knowledge-graph/entities/123/similar/',
    params={'top_k': 10, 'threshold': 0.65},
    headers=headers
)
```

### 4. Maintenance

Regular maintenance ensures graph quality:

```bash
# Clean up old data (entities not updated in 90 days)
python manage.py graph_maintenance <user_id> --cleanup-threshold 90

# Remove orphaned entities (no relationships)
python manage.py graph_maintenance <user_id> --remove-orphans

# Remove duplicate entities and consolidate
python manage.py graph_maintenance <user_id> --remove-duplicates

# Update graph statistics
python manage.py graph_maintenance <user_id> --update-stats

# Dry-run to see what would be deleted
python manage.py graph_maintenance <user_id> --remove-orphans --dry-run
```

## Celery Background Tasks

Tasks are automatically queued and processed asynchronously:

### Available Tasks

1. **index_item_in_graph**
    - Indexes single item
    - Extracts entities and relationships
    - Updates entity frequencies

2. **batch_index_items**
    - Batch index multiple items
    - Optimized for efficiency
    - Transactional consistency

3. **update_graph_snapshot**
    - Updates graph statistics
    - Calculates health score
    - Tracks entity/relationship counts

4. **ingest_from_source**
    - Ingests data from configured sources
    - Normalizes across data types
    - Triggers subsequent indexing

5. **rebuild_graph_for_user**
    - Complete graph rebuild
    - Clears old data
    - Re-indexes all items

## Configuration

### Settings

Add to `settings.py`:

```python
# Knowledge Graph Configuration
KNOWLEDGE_GRAPH = {
    'EMBEDDING_MODEL': 'all-MiniLM-L6-v2',  # sentence-transformers model
    'BATCH_SIZE': 50,  # Items per batch during indexing
    'MAX_ENTITY_NAME_LENGTH': 500,
    'SIMILARITY_THRESHOLD': 0.6,  # For relationship inference
    'CLEANUP_DAYS': 90,  # Delete old relationships
}

# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
```

### Required Dependencies

All dependencies are in `requirements.txt`:

- `sentence-transformers` - Embedding generation
- `nltk` - NLP and entity extraction
- `scikit-learn` - Topic clustering
- `networkx` - Graph algorithms
- `celery` & `redis` - Background tasks
- `pandas` & `numpy` - Data processing

## Performance Considerations

### Embedding Service

- Uses efficient `all-MiniLM-L6-v2` model by default
- Batch processing for multiple texts
- Cached service instance (singleton pattern)
- Handles up to 1000 char texts

### Ingestion Pipeline

- Lazy loading of items
- Batch processing of sources
- Memory-efficient streaming

### Relationship Detection

- Pattern-based for speed
- Semantic similarity for accuracy
- Limited recursion depth (max 3 levels)

### API Query Performance

- Database indexes on user, item_type, created_at
- Pagination (default 20 per page)
- Efficient relationship queries

## Troubleshooting

### Graph Not Updating

```bash
# Check if Celery is running
celery -A flowlinkos worker -l info

# Check task queue
celery -A flowlinkos inspect active

# Re-queue failed tasks
python manage.py index_items <user_id>
```

### Duplicate Entities

```bash
# Consolidate duplicates
python manage.py graph_maintenance <user_id> --remove-duplicates
```

### Poor Entity Detection

Try with richer content:

- Ensure items have meaningful titles
- Include context in descriptions
- Add tags and categories

### Slow Queries

```bash
# Update statistics and health score
python manage.py graph_maintenance <user_id> --update-stats

# Rebuild if very large graph
python manage.py rebuild_graph <user_id> --confirm
```

## Examples

### Find all people related to a project

```python
# Get project entity
project = Entity.objects.get(name='ProjectX', entity_type='project')

# Get all incoming relationships of type 'created_by'
relationships = Relationship.objects.filter(
    target_entity=project,
    relationship_type='created_by'
).select_related('source_entity')

people = [rel.source_entity for rel in relationships]
```

### Find topics discussed in messages

```python
# Get all messages
messages = Item.objects.filter(item_type='message')

# Get all entities mentioned in these messages
message_entities = EntityItemLink.objects.filter(
    item__in=messages
).values_list('entity', flat=True).distinct()

topics = Entity.objects.filter(
    id__in=message_entities,
    entity_type__in=['topic', 'concept']
).order_by('-frequency_score')
```

### Build knowledge path

```python
# From source entity to target entity
source = Entity.objects.get(id=10)
target = Entity.objects.get(id=50)

# Use API endpoint
POST /api/knowledge-graph/graph/find_path/
{
    "source_entity_id": 10,
    "target_entity_id": 50,
    "max_hops": 5
}
```

## Future Enhancements

- [ ] Graph visualization endpoints
- [ ] Advanced semantic search with filters
- [ ] Custom relationship types per user
- [ ] Graph collaboration features
- [ ] Export/import functionality
- [ ] ML-based relationship confidence scoring
- [ ] Real-time graph updates
- [ ] Cache layer for frequent queries
- [ ] Neo4j integration for complex queries
- [ ] Social network analysis features
