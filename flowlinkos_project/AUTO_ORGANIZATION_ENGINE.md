# Auto-Organization Engine - Complete Guide

## Overview

The **Auto-Organization Engine** automatically organizes your content into intelligent collections based on semantic similarity and clustering algorithms. No manual tagging required—the system analyzes your items and groups related content into projects, topics, timelines, and themes.

## Features

### ✨ Core Capabilities

- **Automatic Clustering**: Groups items based on embeddings and semantic similarity
- **Smart Collections**: Auto-generated "folders" for projects, topics, themes, and timelines
- **Confidence Scoring**: Each collection gets a 0-1 confidence score indicating cluster quality
- **Dynamic Updates**: Collections refresh as new items are added
- **User Control**: Rename, merge, or customize collections
- **Multiple Algorithms**: K-Means, HDBSCAN, and Hierarchical clustering support
- **Category Inference**: Automatically detects collection type (project, topic, theme, timeline)
- **Zero Manual Work**: No tagging, categorization, or manual sorting required

---

## How It Works

### 1. **Clustering Algorithm**

The system uses **K-Means clustering** by default with automatic K selection:

- **Adaptive K**: Automatically determines optimal number of clusters using silhouette score
- **Embeddings**: Uses semantic embeddings from items and linked entities
- **Normalization**: Standardizes embeddings before clustering for consistency
- **Confidence**: Silhouette score normalized to 0-1 confidence metric

**Algorithm Selection**:

```
- K-Means (default): Fast, works well with 3-1000 items
- Hierarchical: Better for detecting sub-topics
- HDBSCAN: Good for variable-density clusters (experimental)
```

### 2. **Smart Collection Structure**

Each collection contains:

```python
{
    "id": 123,
    "name": "Q4 Planning",  # Auto-generated from item content
    "description": "",
    "category": "project",  # Inferred: project, topic, theme, timeline
    "confidence_score": 0.87,  # 0-1, how confident the system is
    "item_count": 15,
    "algorithm": "kmeans",
    "is_custom": False,  # True if user modified
    "is_active": True,
    "created_at": "2026-01-22T12:00:00Z",
    "items": [
        {
            "item_id": 42,
            "item_title": "Q4 budget review",
            "relationship_strength": 0.92  # 0-1
        },
        ...
    ]
}
```

### 3. **Category Inference**

The system infers collection categories from linked entities:

- **Project**: Items linked to project entities
- **Topic**: Items linked to topic entities
- **Theme**: Default fallback or pattern-based
- **Timeline**: Date-based patterns in item metadata

---

## API Endpoints

### List Collections

```
GET /api/knowledge-graph/smart-collections/
```

Query parameters:

- `category`: Filter by category (project, topic, theme, timeline)
- `is_active`: Filter by active status
- `page_size`: Pagination size (default: 20)
- `ordering`: Order by confidence_score, item_count, etc.

**Example**:

```
GET /api/knowledge-graph/smart-collections/?category=project&page_size=10
```

### Get Collection Details

```
GET /api/knowledge-graph/smart-collections/{id}/
```

Returns collection with all items and metadata.

### Collection Statistics

```
GET /api/knowledge-graph/smart-collections/statistics/
```

Returns:

```json
{
    "total_collections": 12,
    "avg_confidence_score": 0.82,
    "avg_items_per_collection": 8.5,
    "categories_breakdown": {
        "Project": 5,
        "Topic": 4,
        "Theme": 3
    },
    "top_collections": [...],
    "total_items_organized": 102
}
```

### Rename Collection

```
POST /api/knowledge-graph/smart-collections/{id}/rename/
Content-Type: application/json

{
    "new_name": "H1 2026 Planning",
    "new_description": "Planning for first half of 2026"
}
```

### Merge Collections

```
POST /api/knowledge-graph/smart-collections/merge/
Content-Type: application/json

{
    "source_collection_id": 1,
    "target_collection_id": 2,
    "new_name": "Combined Planning"
}
```

Merges source into target and deletes source.

### Rebuild Collections

```
POST /api/knowledge-graph/smart-collections/rebuild/
Content-Type: application/json

{
    "algorithm": "kmeans",  # or "hdbscan", "hierarchical"
    "force_rebuild": false,
    "min_items": 3
}
```

Triggers background clustering task (returns `task_id`).

### Add Item to Collection

```
POST /api/knowledge-graph/smart-collections/add_item/
Content-Type: application/json

{
    "collection_id": 5,
    "item_id": 42,
    "relationship_strength": 0.85
}
```

### Remove Item from Collection

```
DELETE /api/knowledge-graph/smart-collections/{id}/remove_item/?item_id=42
```

---

## Management Commands

### Initialize Auto-Clustering

Cluster all items for a user or all users:

```bash
# For all users
python manage.py init_auto_clustering

# For specific user
python manage.py init_auto_clustering --user-id 5

# With specific algorithm
python manage.py init_auto_clustering --algorithm kmeans --force-rebuild

# With minimum item threshold
python manage.py init_auto_clustering --min-items 2
```

**Output**:

```
🔄 Starting Auto-Clustering Engine
   Algorithm: kmeans
   Force Rebuild: False

📊 Found 3 user(s) to cluster

[1/3] Processing user: john_doe (ID: 1)
  ✓ Created 5 collections (avg confidence: 0.84) with 18 items
    - Q4 Planning (4 items, confidence: 0.91)
    - Research Notes (5 items, confidence: 0.88)
    ...

============================================================
✓ AUTO-CLUSTERING COMPLETE
============================================================
Success:            3/3
Failed:             0/3
Total Collections:  15
Items Organized:    52
============================================================

All users clustered successfully!
```

---

## Background Tasks (Celery)

### Auto-Cluster New Items

Triggered automatically when items are indexed:

```python
from knowledge_graph.tasks import auto_cluster_new_items
auto_cluster_new_items.delay(user_id, [item_id_1, item_id_2])
```

### Refresh Collections

Manual trigger for background clustering:

```python
from knowledge_graph.tasks import refresh_auto_clusters
task = refresh_auto_clusters.delay(user_id, algorithm='kmeans', force_rebuild=False)
print(task.id)  # Check task status
```

### Merge Collections

Background merge task:

```python
from knowledge_graph.tasks import merge_collections_task
task = merge_collections_task.delay(user_id, source_id, target_id, new_name)
```

---

## Integration with Existing Systems

### Knowledge Graph Integration

Smart collections work with the knowledge graph:

1. **Entity Linking**: Collections link to entities through clustered items
2. **Relationship Detection**: Relationships between entities inform clustering
3. **Semantic Embeddings**: Uses same embeddings as entity similarity

### Ingestion Pipeline Integration

When new items are ingested:

1. Item is indexed into knowledge graph
2. Entities and relationships are extracted
3. **Auto-clustering is triggered** for user's collections
4. Item is assigned to relevant smart collections
5. Confidence scores are updated

### API Integration

Collections are accessible alongside knowledge graph endpoints:

```
/api/knowledge-graph/entities/          # Knowledge graph entities
/api/knowledge-graph/relationships/      # Entity relationships
/api/knowledge-graph/smart-collections/  # Smart collections (NEW)
```

---

## Best Practices

### ✅ Do's

- **Trust the system**: Initial clustering is usually accurate
- **Customize gradually**: Rename collections as you understand them
- **Merge when needed**: Combine similar collections to reduce clutter
- **Monitor confidence**: Review low-confidence collections (< 0.6)
- **Rebuild periodically**: Run rebuild after adding many new items
- **Let it auto-update**: System updates collections as new items arrive

### ❌ Don'ts

- **Don't over-customize**: Leave most collections auto-generated
- **Don't force K**: Let the system determine cluster count
- **Don't ignore confidence**: Collections < 0.5 may need merging
- **Don't disable auto-clustering**: Keep background tasks enabled

---

## Configuration

### Default Settings

In `knowledge_graph/clustering.py`:

```python
min_items = 3  # Minimum items to form a cluster
embedding_dim = 384  # MiniLM embedding dimension
confidence_threshold = 0.5  # Minimum to show collection
```

### Algorithm Parameters

```python
# K-Means
max_k = sqrt(n_items)  # Maximum clusters to test
silhouette_scoring = True  # Use silhouette for K selection
init = 'k-means++'  # Smart centroid initialization

# Hierarchical
linkage = 'ward'  # Ward linkage for agglomerative
distance = 'euclidean'  # Euclidean distance metric
```

### Collection Names

Auto-generated from item titles:

```python
# Strategy
1. Extract words from top 5 item titles
2. Remove stopwords (a, an, the, and, etc.)
3. Find 2 most common words
4. Capitalize and combine
Example: "budget" + "review" → "Budget Review"
```

---

## Examples

### Example 1: Automatic Project Organization

**Before**:

- 47 items spread across notes, files, bookmarks
- No organization or categorization

**After Running Auto-Clustering**:

```
✓ Q4 Planning (8 items, confidence: 0.91)
✓ Research & Development (6 items, confidence: 0.87)
✓ Client Feedback (5 items, confidence: 0.85)
✓ Meeting Notes (7 items, confidence: 0.79)
✓ Personal Development (4 items, confidence: 0.73)
```

### Example 2: Merging Similar Collections

```bash
# After clustering, user notices two similar collections
POST /api/knowledge-graph/smart-collections/merge/
{
    "source_collection_id": 7,  # "Dev Tasks"
    "target_collection_id": 3,  # "Development Projects"
    "new_name": "Development & Tasks"
}

# Result
✓ Collections merged
✓ 12 items now in "Development & Tasks"
✓ Confidence: 0.86
```

### Example 3: Rebuilding with Different Algorithm

```bash
# User wants to try hierarchical clustering
python manage.py init_auto_clustering \
    --algorithm hierarchical \
    --user-id 5 \
    --force-rebuild

# Result
[1/1] Processing user: jane_smith (ID: 5)
  ✓ Created 8 collections (avg confidence: 0.79) with 34 items
```

---

## Troubleshooting

### Issue: Low Confidence Scores

**Problem**: Collections have confidence < 0.6

**Solution**:

1. Merge similar collections
2. Run with `--force-rebuild` to recalculate
3. Ensure items have good embeddings (add content)

### Issue: Too Many Collections

**Problem**: System creates too many small clusters

**Solution**:

```bash
# Increase minimum item threshold
python manage.py init_auto_clustering --min-items 5

# Or merge manually via API
POST /api/knowledge-graph/smart-collections/merge/
```

### Issue: Collections Not Updating

**Problem**: Collections don't update when new items are added

**Solution**:

1. Ensure Celery is running: `celery -A flowlinkos worker`
2. Check task queue: Celery logs
3. Manual rebuild: `POST /smart-collections/rebuild/`

### Issue: Embeddings Not Available

**Problem**: "sentence-transformers unavailable" warning

**Solution**:

1. Install proper version:

```bash
pip install sentence-transformers==3.0.0
pip install huggingface-hub==0.18.0
```

2. System falls back to hash-based embeddings (works but less accurate)

---

## Performance Notes

### Clustering Time

- **10 items**: < 1 second
- **100 items**: 1-2 seconds
- **1000 items**: 5-10 seconds
- **10k items**: 30-60 seconds

Background tasks recommended for > 100 items.

### Storage

- SmartCollection: ~200 bytes
- ClusterItem link: ~150 bytes

For 1000 items in 10 collections: ~2 MB

---

## Future Enhancements

- [ ] Visual clustering visualization (D3.js/Plotly)
- [ ] LLM-powered collection naming
- [ ] Temporal clustering (timelines)
- [ ] Cross-user collaboration on collections
- [ ] Collection sharing and permissions
- [ ] Advanced similarity metrics (BERTScore, etc.)
- [ ] Recursive/hierarchical clustering
- [ ] Real-time clustering updates

---

## Support & Questions

For issues or questions:

1. Check the [API Documentation](#api-endpoints)
2. Review [Troubleshooting](#troubleshooting) section
3. Inspect Celery logs for task failures
4. Check confidence scores to evaluate cluster quality
5. Run `init_auto_clustering` with different algorithms
