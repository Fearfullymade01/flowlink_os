# Auto-Organization Engine - Quick Start

## 🚀 Get Started in 5 Minutes

### Step 1: Initialize Auto-Clustering for Your Items

```bash
cd c:/Users/gbeng/flowlink_os/flowlinkos_project

# For all users
python manage.py init_auto_clustering

# For specific user
python manage.py init_auto_clustering --user-id 1

# With different algorithm
python manage.py init_auto_clustering --algorithm hierarchical
```

**Expected Output**:

```
🔄 Starting Auto-Clustering Engine
   Algorithm: kmeans
   Force Rebuild: False

📊 Found 1 user(s) to cluster

[1/1] Processing user: admin (ID: 1)
  ✓ Created 3 collections (avg confidence: 0.82) with 12 items
    - Project Alpha (4 items, confidence: 0.89)
    - Research Notes (5 items, confidence: 0.78)
    - Planning (3 items, confidence: 0.79)

============================================================
✓ AUTO-CLUSTERING COMPLETE
============================================================
Success:            1/1
Failed:             0/1
Total Collections:  3
Items Organized:    12
============================================================

All users clustered successfully!
```

### Step 2: View Your Collections

**Via API**:

```
http://127.0.0.1:8000/api/knowledge-graph/smart-collections/
```

**Response** (JSON):

```json
{
    "count": 3,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "Project Alpha",
            "description": "",
            "category": "project",
            "confidence_score": 0.89,
            "item_count": 4,
            "algorithm": "kmeans",
            "is_custom": false,
            "is_active": true,
            "created_at": "2026-01-22T23:12:00Z",
            "updated_at": "2026-01-22T23:12:00Z"
        },
        {
            "id": 2,
            "name": "Research Notes",
            "description": "",
            "category": "topic",
            "confidence_score": 0.78,
            "item_count": 5,
            "algorithm": "kmeans",
            "is_custom": false,
            "is_active": true,
            "created_at": "2026-01-22T23:12:00Z",
            "updated_at": "2026-01-22T23:12:00Z"
        }
    ]
}
```

### Step 3: View Collection Details

```
GET http://127.0.0.1:8000/api/knowledge-graph/smart-collections/1/
```

**Response** (includes all items):

```json
{
    "id": 1,
    "name": "Project Alpha",
    "description": "",
    "category": "project",
    "category_display": "Project",
    "confidence_score": 0.89,
    "item_count": 4,
    "algorithm": "kmeans",
    "algorithm_display": "K-Means",
    "is_custom": false,
    "is_active": true,
    "items": [
        {
            "id": 10,
            "item": 42,
            "item_title": "Project kickoff meeting",
            "item_type": "Note",
            "relationship_strength": 0.95,
            "created_at": "2026-01-22T23:12:00Z"
        },
        {
            "id": 11,
            "item": 43,
            "item_title": "Project timeline",
            "item_type": "File",
            "relationship_strength": 0.88,
            "created_at": "2026-01-22T23:12:00Z"
        }
    ],
    "created_at": "2026-01-22T23:12:00Z",
    "updated_at": "2026-01-22T23:12:00Z"
}
```

### Step 4: Get Statistics

```
GET http://127.0.0.1:8000/api/knowledge-graph/smart-collections/statistics/
```

**Response**:

```json
{
    "total_collections": 3,
    "avg_confidence_score": 0.82,
    "avg_items_per_collection": 4.0,
    "categories_breakdown": {
        "Project": 1,
        "Topic": 2
    },
    "total_items_organized": 12,
    "top_collections": [
        {
            "id": 1,
            "name": "Project Alpha",
            "confidence_score": 0.89,
            "item_count": 4,
            "category": "project"
        }
    ]
}
```

---

## 🎯 Common Tasks

### Rename a Collection

```bash
curl -X POST http://127.0.0.1:8000/api/knowledge-graph/smart-collections/1/rename/ \
  -H "Content-Type: application/json" \
  -d '{
    "new_name": "Q1 2026 Project",
    "new_description": "All Q1 planning and execution"
  }'
```

**Response**:

```json
{
  "success": true,
  "message": "Collection renamed to 'Q1 2026 Project'",
  "collection": {...}
}
```

### Merge Two Collections

```bash
curl -X POST http://127.0.0.1:8000/api/knowledge-graph/smart-collections/merge/ \
  -H "Content-Type: application/json" \
  -d '{
    "source_collection_id": 2,
    "target_collection_id": 1,
    "new_name": "Project & Planning"
  }'
```

**Response**:

```json
{
  "success": true,
  "message": "Collections merged into 'Project & Planning'",
  "collection": {...}
}
```

### Rebuild Collections (Background Task)

```bash
curl -X POST http://127.0.0.1:8000/api/knowledge-graph/smart-collections/rebuild/ \
  -H "Content-Type: application/json" \
  -d '{
    "algorithm": "kmeans",
    "force_rebuild": false,
    "min_items": 3
  }'
```

**Response**:

```json
{
    "success": true,
    "message": "Collection rebuild started in background",
    "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

### Add Item to Collection

```bash
curl -X POST http://127.0.0.1:8000/api/knowledge-graph/smart-collections/add_item/ \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": 1,
    "item_id": 42,
    "relationship_strength": 0.85
  }'
```

### Remove Item from Collection

```bash
curl -X DELETE "http://127.0.0.1:8000/api/knowledge-graph/smart-collections/1/remove_item/?item_id=42"
```

---

## 📊 Understanding Confidence Scores

Confidence scores range from **0 to 1** and indicate cluster quality:

| Score    | Quality   | Action           |
| -------- | --------- | ---------------- |
| 0.9-1.0  | Excellent | Keep as-is       |
| 0.7-0.89 | Good      | Possibly refine  |
| 0.5-0.69 | Fair      | Consider merging |
| < 0.5    | Poor      | Merge or rebuild |

**Example**:

```
✓ Q1 Planning (0.89)      - Excellent, keep
✓ Research (0.72)         - Good, refine if needed
⚠ Misc Notes (0.48)       - Poor, consider merging with another
```

---

## 🔄 Automatic Updates

When you **add new items** via the API or ingestion pipeline:

1. Items are indexed into the knowledge graph
2. **Auto-clustering is triggered automatically** (no action needed)
3. New items are assigned to relevant collections
4. Confidence scores are recalculated
5. Collections may split, merge, or reorganize

**Example Flow**:

```
POST /api/items/ (create new note)
  ↓ (Item saved)
  ↓ (Knowledge graph indexing starts)
  ↓ (Entities extracted, relationships detected)
  ↓ (Batch indexing completes)
  ↓ 🔄 Auto-clustering triggered
  ↓ (Collections updated)
  ✓ Collections reflect new item
```

---

## 🛠️ Configuration

### Environment Variables (None Required)

Auto-organization works out of the box with sensible defaults.

### Settings to Consider

In `knowledge_graph/clustering.py`:

```python
# Minimum items to form a cluster
min_items = 3

# Maximum clusters to test (for K selection)
max_k = sqrt(n_items)

# Clustering algorithms available
algorithms = ['kmeans', 'hierarchical']  # hdbscan if installed
```

---

## 🐛 Troubleshooting

### Problem: "No collections created"

**Cause**: Items may not have embeddings or enough content

**Solution**:

1. Ensure items have good titles and content
2. Check that knowledge graph indexing completed
3. Run with verbose output:
    ```bash
    python manage.py init_auto_clustering --user-id 1
    ```

### Problem: "Confidence scores are too low"

**Cause**: Items are too diverse, clustering is finding weak patterns

**Solution**:

1. Merge collections manually
2. Run rebuild with different algorithm:
    ```bash
    python manage.py init_auto_clustering --algorithm hierarchical --force-rebuild
    ```

### Problem: "Celery tasks not running"

**Cause**: Celery worker not started

**Solution**:

1. Start Celery worker:
    ```bash
    celery -A flowlinkos worker --loglevel=info
    ```
2. Verify Redis is running
3. Check task logs in Celery output

### Problem: "Embedding error: sentence-transformers unavailable"

**Cause**: ML dependencies not installed or version mismatch

**Solution**:

1. System automatically falls back to hash-based embeddings (still works!)
2. Or install proper versions:
    ```bash
    pip install sentence-transformers==3.0.0 huggingface-hub==0.18.0
    ```

---

## 📚 Learn More

- **Full Documentation**: [AUTO_ORGANIZATION_ENGINE.md](AUTO_ORGANIZATION_ENGINE.md)
- **Implementation Details**: [AUTO_ORGANIZATION_IMPLEMENTATION.md](AUTO_ORGANIZATION_IMPLEMENTATION.md)
- **API Reference**: [/api/knowledge-graph/smart-collections/](http://127.0.0.1:8000/api/knowledge-graph/smart-collections/)

---

## 💡 Tips & Best Practices

1. **Start Simple**: Run default clustering first
2. **Monitor Confidence**: Collections < 0.6 should be merged
3. **Rename Strategically**: Rename once you understand the collections
4. **Trust the System**: Initial clustering is usually accurate
5. **Batch Updates**: Let system update automatically when adding items
6. **Rebuild Periodically**: After adding many items, run rebuild
7. **Don't Over-Customize**: Let auto-clustering do the work

---

## 🎓 Next Steps

1. ✅ Initialize collections (see Step 1)
2. 📊 Review collections (see Step 2)
3. 🔧 Customize as needed (rename, merge)
4. 🔄 Add new items (auto-clustering updates collections)
5. 📈 Monitor and optimize

**You're all set!** Your content is now automatically organized. No more manual tagging or categorization needed.
