# Knowledge Graph Quick Start Guide

## Installation & Setup

### 1. Ensure Dependencies are Installed

```bash
pip install -r requirements.txt
```

All required packages are already listed:

- `sentence-transformers` - Semantic embeddings
- `nltk` - NLP processing
- `scikit-learn` - Topic clustering
- `celery` & `redis` - Background tasks
- `django`, `djangorestframework` - Framework

### 2. Run Database Migrations

```bash
python manage.py migrate
```

This creates the necessary database tables for:

- Entities
- Relationships
- EntityItemLinks
- Graphs

### 3. Start Celery Worker (for background tasks)

In a separate terminal:

```bash
# With Redis running
celery -A flowlinkos worker -l info

# Or use in-memory broker for testing
celery -A flowlinkos worker -l info --broker=memory://
```

### 4. Initialize Knowledge Graph for a User

```bash
# Initialize with user ID (async mode)
python manage.py init_graph 1 --async

# Or synchronous mode
python manage.py init_graph 1
```

## First-Time Usage

### Step 1: Create Sample Data

```bash
python manage.py shell

# Create a user if needed
from django.contrib.auth.models import User
user = User.objects.create_user('testuser', 'test@example.com', 'password')

# Create a source
from core.models import Source
source = Source.objects.create(
    user=user,
    source_type='notes',
    name='My Notes',
    is_active=True
)

# Create sample items
from api.models import Item
note1 = Item.objects.create(
    user=user,
    source=source,
    item_type='note',
    title='Python Programming Guide',
    content='Learn Python: variables, functions, classes, decorators, async programming',
    tags='python,programming,tutorial'
)

note2 = Item.objects.create(
    user=user,
    source=source,
    item_type='note',
    title='Django REST Framework',
    content='Build APIs with Django REST Framework: serializers, viewsets, permissions, authentication',
    tags='django,api,rest,backend'
)

note3 = Item.objects.create(
    user=user,
    source=source,
    item_type='note',
    title='Web Development',
    content='Full-stack web development with Python and JavaScript',
    tags='web,development,python,javascript'
)
```

### Step 2: Index Items into Graph

```bash
# Via management command
python manage.py index_items 1

# Via API (after starting server)
curl -X POST http://localhost:8000/api/knowledge-graph/graph/operations/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"operation": "index_items"}'
```

### Step 3: Query the Graph

```bash
# Start development server
python manage.py runserver

# In another terminal, test API endpoints

# 1. Get graph statistics
curl http://localhost:8000/api/knowledge-graph/graph/statistics/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# 2. Search entities
curl 'http://localhost:8000/api/knowledge-graph/entities/search/?q=python' \
  -H "Authorization: Bearer YOUR_TOKEN"

# 3. Find similar entities
curl 'http://localhost:8000/api/knowledge-graph/entities/1/similar/?top_k=5' \
  -H "Authorization: Bearer YOUR_TOKEN"

# 4. Get entity connections
curl 'http://localhost:8000/api/knowledge-graph/entities/1/connections/?depth=2' \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Common Commands

### Initialize Graph

```bash
python manage.py init_graph <user_id> --async
```

### Rebuild Graph (clear and rebuild)

```bash
python manage.py rebuild_graph <user_id> --confirm
```

### Index Items

```bash
# All unindexed items
python manage.py index_items <user_id>

# Specific items
python manage.py index_items <user_id> --item-ids 1 2 3

# By type
python manage.py index_items <user_id> --item-type note

# With batch size
python manage.py index_items <user_id> --batch-size 100
```

### Graph Maintenance

```bash
# Clean up old data (90+ days)
python manage.py graph_maintenance <user_id> --cleanup-threshold 90

# Remove orphaned entities
python manage.py graph_maintenance <user_id> --remove-orphans

# Remove duplicates
python manage.py graph_maintenance <user_id> --remove-duplicates

# Update statistics
python manage.py graph_maintenance <user_id> --update-stats

# Dry run (see what would be deleted)
python manage.py graph_maintenance <user_id> --remove-orphans --dry-run
```

## API Examples

### Python Client Example

```python
import requests
from django.contrib.auth.models import User

# Get auth token (assuming token auth is set up)
user = User.objects.get(id=1)
token = user.auth_token.key  # Requires Token authentication

headers = {'Authorization': f'Token {token}'}
base_url = 'http://localhost:8000/api/knowledge-graph'

# 1. Get graph statistics
response = requests.get(f'{base_url}/graph/statistics/', headers=headers)
print(response.json())

# 2. Search entities
response = requests.get(
    f'{base_url}/entities/search/',
    params={'q': 'python', 'min_frequency': 2},
    headers=headers
)
print(response.json())

# 3. Get entity details
response = requests.get(f'{base_url}/entities/1/', headers=headers)
print(response.json())

# 4. Find similar entities
response = requests.get(
    f'{base_url}/entities/1/similar/',
    params={'top_k': 5, 'threshold': 0.6},
    headers=headers
)
print(response.json())

# 5. Find path between entities
response = requests.post(
    f'{base_url}/graph/find_path/',
    json={
        'source_entity_id': 1,
        'target_entity_id': 5,
        'max_hops': 5
    },
    headers=headers
)
print(response.json())

# 6. Query relationships
response = requests.post(
    f'{base_url}/relationships/query/',
    json={'entity_id': 1, 'relationship_type': 'related_to'},
    headers=headers
)
print(response.json())
```

### JavaScript/Frontend Example

```javascript
const baseUrl = "http://localhost:8000/api/knowledge-graph";
const token = localStorage.getItem("authToken");

const headers = {
    Authorization: `Token ${token}`,
    "Content-Type": "application/json",
};

// Get graph statistics
fetch(`${baseUrl}/graph/statistics/`, { headers })
    .then((r) => r.json())
    .then((data) => console.log("Graph Stats:", data));

// Search entities
fetch(`${baseUrl}/entities/search/?q=python&min_frequency=2`, { headers })
    .then((r) => r.json())
    .then((data) => console.log("Search Results:", data));

// Find path
fetch(`${baseUrl}/graph/find_path/`, {
    headers,
    method: "POST",
    body: JSON.stringify({
        source_entity_id: 1,
        target_entity_id: 5,
        max_hops: 5,
    }),
})
    .then((r) => r.json())
    .then((data) => console.log("Path Found:", data));
```

## Monitoring & Debugging

### Check Celery Tasks

```bash
# View active tasks
celery -A flowlinkos inspect active

# View scheduled tasks
celery -A flowlinkos inspect scheduled

# View task stats
celery -A flowlinkos inspect stats
```

### Check Database

```bash
python manage.py shell

# Count entities
from knowledge_graph.models import Entity
Entity.objects.count()

# Count relationships
from knowledge_graph.models import Relationship
Relationship.objects.count()

# List top entities
Entity.objects.order_by('-frequency_score')[:10]

# Check graph status
from knowledge_graph.models import Graph
Graph.objects.all()
```

### View Logs

```bash
# Django logs
tail -f logs/django.log

# Celery logs
tail -f logs/celery.log

# Check for errors
grep -i error logs/*.log
```

## Troubleshooting

### Celery Not Processing Tasks

```bash
# 1. Check if Redis is running
redis-cli ping  # Should return PONG

# 2. Check if Celery worker is running
celery -A flowlinkos inspect active

# 3. Restart Celery
pkill -f "celery -A"
celery -A flowlinkos worker -l info
```

### No Entities Found After Indexing

```bash
# 1. Check if items exist
python manage.py shell
from api.models import Item
Item.objects.count()

# 2. Check if Celery task completed
celery -A flowlinkos inspect active

# 3. Manually re-index
python manage.py index_items <user_id> --batch-size 10
```

### Slow Queries

```bash
# 1. Update statistics
python manage.py graph_maintenance <user_id> --update-stats

# 2. Check database indexes
python manage.py sqlsequencereset knowledge_graph | python manage.py dbshell

# 3. Consider rebuilding for very large graphs
python manage.py rebuild_graph <user_id> --confirm
```

## Performance Tips

1. **Batch Operations**: Index items in batches of 50-100
2. **Regular Maintenance**: Run maintenance weekly to remove old data
3. **Use Pagination**: Always use pagination for list endpoints
4. **Cache Results**: Cache frequently accessed entity searches
5. **Monitor Health**: Check graph health score regularly

## Next Steps

1. **Customize Entities**: Add domain-specific entity types
2. **Custom Relationships**: Define relationships relevant to your domain
3. **Integration**: Connect with external data sources
4. **Visualization**: Build graph visualization frontend
5. **Analytics**: Add insights and recommendations
