# Knowledge Graph Testing & Validation Guide

## Unit Tests

Create `knowledge_graph/tests.py`:

```python
from django.test import TestCase
from django.contrib.auth.models import User
from api.models import Item
from core.models import Source
from knowledge_graph.models import Entity, Relationship, EntityItemLink, Graph
from knowledge_graph.embeddings import get_embedding_service
from knowledge_graph.relationship_detector import RelationshipDetector
from knowledge_graph.ingestion import DataIngestionPipeline

class EmbeddingServiceTest(TestCase):
    def setUp(self):
        self.service = get_embedding_service()

    def test_embed_text(self):
        text = "Hello world"
        embedding = self.service.embed_text(text)
        self.assertIsNotNone(embedding)
        self.assertEqual(len(embedding), self.service.embedding_dim)

    def test_compute_similarity(self):
        text1 = "machine learning"
        text2 = "deep learning"

        emb1 = self.service.embed_text(text1)
        emb2 = self.service.embed_text(text2)

        similarity = self.service.compute_similarity(emb1, emb2)
        self.assertGreaterEqual(similarity, 0.0)
        self.assertLessEqual(similarity, 1.0)
        # Similar topics should have high similarity
        self.assertGreater(similarity, 0.5)

class RelationshipDetectorTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'pass')
        self.detector = RelationshipDetector()

    def test_entity_extraction(self):
        text = "John Smith works at Google in California"
        results = self.detector.detect_from_text(text, self.user.id)

        self.assertGreater(len(results['entities']), 0)
        entity_names = [e['name'] for e in results['entities']]
        # Should find some entities
        self.assertTrue(any(name for name in entity_names))

class IngestionPipelineTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'pass')
        self.source = Source.objects.create(
            user=self.user,
            source_type='notes',
            name='Test Notes',
            is_active=True
        )

        # Create test item
        self.item = Item.objects.create(
            user=self.user,
            source=self.source,
            item_type='note',
            title='Test Note',
            content='This is a test note about Python programming'
        )

    def test_ingestion_pipeline(self):
        pipeline = DataIngestionPipeline(self.user)
        results = pipeline.ingest_source('notes')

        self.assertGreater(results['total_items'], 0)
        self.assertIn('note', results['by_type'] or {})

class EntityTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'pass')

    def test_create_entity(self):
        entity = Entity.objects.create(
            user=self.user,
            name='Python',
            entity_type='concept',
            description='Programming language'
        )

        self.assertEqual(entity.name, 'Python')
        self.assertEqual(entity.entity_type, 'concept')
        self.assertEqual(entity.user, self.user)

class RelationshipTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'pass')
        self.entity1 = Entity.objects.create(
            user=self.user,
            name='Python',
            entity_type='concept'
        )
        self.entity2 = Entity.objects.create(
            user=self.user,
            name='Django',
            entity_type='concept'
        )

    def test_create_relationship(self):
        rel = Relationship.objects.create(
            user=self.user,
            source_entity=self.entity1,
            target_entity=self.entity2,
            relationship_type='related_to',
            strength=0.8
        )

        self.assertEqual(rel.source_entity, self.entity1)
        self.assertEqual(rel.target_entity, self.entity2)
        self.assertEqual(rel.strength, 0.8)
```

## Integration Tests

```python
from django.test import TestCase, Client
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

class GraphAPITest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'pass')
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_list_entities(self):
        response = self.client.get('/api/knowledge-graph/entities/')
        self.assertEqual(response.status_code, 200)

    def test_search_entities(self):
        response = self.client.get('/api/knowledge-graph/entities/search/?q=test')
        self.assertEqual(response.status_code, 200)

    def test_graph_statistics(self):
        response = self.client.get('/api/knowledge-graph/graph/statistics/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('total_entities', response.data)
```

## Manual Testing Checklist

### 1. Setup

- [ ] Redis is running: `redis-cli ping`
- [ ] Celery worker is running: `celery -A flowlinkos worker -l info`
- [ ] Django server is running: `python manage.py runserver`

### 2. Data Ingestion

- [ ] Create test user and source
- [ ] Create test items (notes, files, messages, bookmarks, tasks)
- [ ] Run: `python manage.py init_graph <user_id> --async`
- [ ] Verify tasks are queued in Celery

### 3. Entity Extraction

- [ ] Check if entities are created: `python manage.py shell`
    ```python
    from knowledge_graph.models import Entity
    Entity.objects.filter(user_id=<user_id>).count()
    ```
- [ ] Verify embeddings are generated
- [ ] Check frequency scores

### 4. Relationship Detection

- [ ] Verify relationships are created
    ```python
    from knowledge_graph.models import Relationship
    Relationship.objects.filter(user_id=<user_id>).count()
    ```
- [ ] Check relationship types
- [ ] Verify strength scores (0-1)

### 5. API Testing

#### Test Entity Search

```bash
curl "http://localhost:8000/api/knowledge-graph/entities/search/?q=python" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Expected: Returns list of entities matching "python"

#### Test Entity Similarity

```bash
curl "http://localhost:8000/api/knowledge-graph/entities/1/similar/?top_k=5" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Expected: Returns similar entities with similarity scores

#### Test Relationships Query

```bash
curl -X POST http://localhost:8000/api/knowledge-graph/relationships/query/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"entity_id": 1}'
```

Expected: Returns relationships for entity 1

#### Test Path Finding

```bash
curl -X POST http://localhost:8000/api/knowledge-graph/graph/find_path/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_entity_id": 1,
    "target_entity_id": 10,
    "max_hops": 5
  }'
```

Expected: Returns path between entities or not found

#### Test Graph Statistics

```bash
curl http://localhost:8000/api/knowledge-graph/graph/statistics/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Expected: Returns graph stats with entity/relationship counts

### 6. Batch Operations

- [ ] Test indexing: POST `/api/knowledge-graph/graph/operations/`
    ```json
    { "operation": "index_items", "item_ids": [1, 2, 3] }
    ```
- [ ] Test rebuild: `python manage.py rebuild_graph <user_id> --confirm`
- [ ] Verify Celery processes tasks

### 7. Maintenance

- [ ] Test cleanup: `python manage.py graph_maintenance <user_id> --cleanup-threshold 90 --dry-run`
- [ ] Test duplicate removal: `python manage.py graph_maintenance <user_id> --remove-duplicates --dry-run`
- [ ] Test orphan removal: `python manage.py graph_maintenance <user_id> --remove-orphans --dry-run`

### 8. Performance Validation

- [ ] Index 100+ items and measure time
- [ ] Query graph with 500+ entities and check response time
- [ ] Test batch operations with large datasets
- [ ] Monitor Celery task queue

### 9. Error Handling

- [ ] Test with invalid entity ID: Should return 404
- [ ] Test with no authentication: Should return 401
- [ ] Test with invalid relationship type: Should handle gracefully
- [ ] Test with incomplete data: Should use defaults

## Performance Benchmarks

```python
import time
from django.contrib.auth.models import User
from knowledge_graph.tasks import batch_index_items

# Benchmark batch indexing
user_id = 1
item_ids = list(range(1, 101))  # 100 items

start = time.time()
task = batch_index_items.delay(user_id, item_ids)
result = task.get()
elapsed = time.time() - start

print(f"Indexed {result['successful']} items in {elapsed:.2f}s")
print(f"Rate: {result['successful']/elapsed:.1f} items/second")
```

Expected performance:

- 100 items: 10-20 seconds
- 1000 items: 100-200 seconds
- Single item: 100-200ms

## Debugging

### Enable Debug Logging

Add to settings.py:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
        },
    },
    'loggers': {
        'knowledge_graph': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

### Monitor Celery

```bash
# Watch active tasks
watch -n 1 'celery -A flowlinkos inspect active'

# View task results
celery -A flowlinkos inspect result
```

### Database Queries

```python
from django.db import connection
from django.test.utils import CaptureQueriesContext

with CaptureQueriesContext(connection) as ctx:
    # Perform operations
    pass

for query in ctx:
    print(query['sql'])
```

## Continuous Integration

Example GitHub Actions workflow:

```yaml
name: Knowledge Graph Tests

on: [push, pull_request]

jobs:
    test:
        runs-on: ubuntu-latest

        services:
            postgres:
                image: postgres:13
                env:
                    POSTGRES_PASSWORD: postgres
                options: >-
                    --health-cmd pg_isready
                    --health-interval 10s
                    --health-timeout 5s
                    --health-retries 5

            redis:
                image: redis:6
                options: >-
                    --health-cmd "redis-cli ping"
                    --health-interval 10s

        steps:
            - uses: actions/checkout@v2
            - uses: actions/setup-python@v2
              with:
                  python-version: "3.9"

            - name: Install dependencies
              run: |
                  pip install -r requirements.txt
                  pip install pytest pytest-django

            - name: Run tests
              run: pytest knowledge_graph/tests.py -v

            - name: Run management commands
              run: |
                  python manage.py migrate
                  python manage.py init_graph 1
```

## Validation Checklist

- [ ] All files created without errors
- [ ] Database migrations run successfully
- [ ] Celery tasks queue and execute
- [ ] API endpoints respond correctly
- [ ] Entity extraction works
- [ ] Relationship detection works
- [ ] Embeddings are generated
- [ ] Search and similarity work
- [ ] Path finding works
- [ ] Batch operations work
- [ ] Maintenance commands work
- [ ] Error handling is robust
- [ ] Performance is acceptable
- [ ] Documentation is complete

## Success Criteria

✅ System successfully implemented when:

1. **Data Ingestion**: All data types (notes, files, messages, bookmarks, tasks) are ingested and normalized
2. **Entity Extraction**: NLP pipeline extracts entities from content with >80% accuracy
3. **Relationships**: Detected relationships appear logical and meaningful
4. **API Performance**: Graph queries respond in <500ms for typical graphs
5. **Scalability**: System handles 1000+ entities without performance degradation
6. **Reliability**: Background tasks execute reliably with proper error handling
7. **Usability**: API is intuitive and well-documented
8. **Maintainability**: Code is clean, well-structured, and easy to extend
