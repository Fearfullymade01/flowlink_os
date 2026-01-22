# FlowLinkOS - Unified Intelligence Layer for Personal Productivity

<div align="center">

**FlowLinkOS connects notes, files, messages, bookmarks, and tasks into a semantic knowledge graph that auto‑organizes itself, answers intent‑based queries, generates summaries, and learns user workflows.**

[Features](#features) • [Quick Start](#quick-start) • [Architecture](#architecture) • [API Documentation](#api-documentation) • [Contributing](#contributing)

</div>

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Development](#development)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

FlowLinkOS is a sophisticated Django-based personal productivity system that brings unified intelligence to your digital life. It integrates multiple data sources (notes, files, messages, bookmarks, tasks) into a semantic knowledge graph, enabling intelligent querying, automatic summarization, and workflow learning.

### Key Capabilities

- **Semantic Knowledge Graph**: Auto-organizes information by understanding relationships and concepts
- **Intent-Based Queries**: Ask questions in natural language and get intelligent results
- **Auto-Generated Summaries**: Get digests of your information (daily, weekly, by category)
- **Workflow Learning**: Automatically learns your patterns and adapts to your workflow
- **Multi-Source Integration**: Connect notes, files, messages, bookmarks, tasks, and more
- **Real-time Synchronization**: Stay updated across all devices and sources

## ✨ Features

### Core Features

1. **Unified Data Management**
    - Store items from multiple sources in a centralized location
    - Support for notes, files, messages, bookmarks, tasks, and custom sources
    - Automatic metadata extraction and enrichment

2. **Semantic Knowledge Graph**
    - Builds intelligent entity relationships automatically
    - Supports entity types: concepts, persons, places, organizations, projects, topics
    - Relationship tracking with confidence scores
    - Vector embeddings for semantic similarity

3. **Intelligent Query System**
    - Natural language intent-based queries
    - Fast semantic search across all items
    - Query history with confidence scores
    - Result relevance scoring

4. **Summary Generation**
    - Automatic daily/weekly summaries
    - Category-specific summaries
    - Query-based summaries
    - Customizable summary formats

5. **Workflow Learning**
    - Learns user patterns over time
    - Auto-suggests next actions
    - Confidence-based workflow recommendations
    - Workflow analytics and insights

6. **Advanced Search & Filtering**
    - Full-text search across content
    - Tag-based filtering
    - Priority and urgency filtering
    - Time-range filtering

## 🏗️ Architecture

### Project Structure

```
flowlinkos_project/
├── flowlinkos/              # Project configuration
│   ├── settings.py          # Django settings
│   ├── urls.py              # URL routing
│   ├── wsgi.py              # WSGI configuration
│   ├── asgi.py              # ASGI configuration
│   ├── celery.py            # Celery configuration
│   └── celery_config.py     # Celery settings
├── core/                    # Core functionality
│   ├── models.py            # UserProfile, Source, Workflow models
│   ├── views.py             # Core views
│   ├── admin.py             # Django admin configuration
│   └── migrations/
├── api/                     # REST API
│   ├── models.py            # Item, Query, Summary models
│   ├── views.py             # API viewsets
│   ├── urls.py              # API routing
│   ├── admin.py             # Admin configuration
│   └── migrations/
├── knowledge_graph/         # Knowledge graph engine
│   ├── models.py            # Entity, Relationship, Graph models
│   ├── views.py             # Graph API viewsets
│   ├── urls.py              # Graph routing
│   ├── admin.py             # Admin configuration
│   └── migrations/
├── static/                  # Static files
│   ├── css/
│   └── js/
├── templates/               # Django templates
├── logs/                    # Application logs
├── manage.py                # Django management
├── requirements.txt         # Python dependencies
├── .env.example             # Environment template
└── .gitignore
```

### Technology Stack

**Backend**

- Django 4.2 - Web framework
- Django REST Framework - API development
- PostgreSQL/SQLite - Database
- Redis - Caching and message broker

**NLP & AI**

- spaCy - Named entity recognition and NLP
- sentence-transformers - Semantic embeddings
- scikit-learn - Machine learning
- NLTK - Natural language processing

**Knowledge Graph**

- NetworkX - Graph algorithms
- Neo4j (optional) - Graph database

**Task Queue**

- Celery - Asynchronous task processing
- Redis - Message broker

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 12+ (or SQLite for development)
- Redis 6.0+ (for background tasks)
- Git

### Installation

1. **Clone the repository**

    ```bash
    cd c:\Users\gbeng\flowlink_os\flowlinkos_project
    ```

2. **Create and activate virtual environment**

    ```bash
    # Create venv
    python -m venv venv

    # Activate on Windows
    venv\Scripts\activate

    # Or on macOS/Linux
    source venv/bin/activate
    ```

3. **Install dependencies**

    ```bash
    pip install -r requirements.txt
    ```

4. **Download NLP models**

    ```bash
    python -m spacy download en_core_web_sm
    python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
    ```

5. **Configure environment**

    ```bash
    # Copy .env.example to .env
    copy .env.example .env

    # Edit .env with your settings
    ```

6. **Run migrations**

    ```bash
    python manage.py migrate
    ```

7. **Create superuser**

    ```bash
    python manage.py createsuperuser
    ```

8. **Run development server**
    ```bash
    python manage.py runserver
    ```

Access the application at `http://localhost:8000`

- Admin panel: `http://localhost:8000/admin`
- API: `http://localhost:8000/api/`

## 📚 API Documentation

### Authentication

All API endpoints (except public ones) require authentication:

```bash
# Obtain token
curl -X POST http://localhost:8000/api-token-auth/ \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'
```

Use token in headers:

```bash
curl -H "Authorization: Token YOUR_TOKEN_HERE" \
  http://localhost:8000/api/items/
```

### Core Endpoints

#### Items API

**List Items**

```http
GET /api/items/
Query Parameters:
  - item_type: note|file|message|bookmark|task
  - is_archived: true|false
  - priority: 0|1|2
  - search: search terms
```

**Create Item**

```http
POST /api/items/
{
  "item_type": "note",
  "title": "My Note",
  "content": "Note content",
  "tags": "important,review",
  "priority": 2
}
```

**Get Items by Type**

```http
GET /api/items/by_type/
```

#### Queries API

**List Queries**

```http
GET /api/queries/
```

**Execute Query**

```http
POST /api/queries/execute_query/
{
  "query_text": "What are my high priority tasks for today?"
}
Response:
{
  "id": 1,
  "query_text": "...",
  "results": [...],
  "confidence_score": 0.75
}
```

#### Knowledge Graph API

**Get Current Graph**

```http
GET /api/knowledge-graph/graph/current_graph/
```

**List Entities**

```http
GET /api/knowledge-graph/entities/
Query Parameters:
  - entity_type: concept|person|place|organization|project|topic
  - search: search terms
```

**Get Related Entities**

```http
GET /api/knowledge-graph/entities/{id}/related_entities/
```

**Rebuild Graph**

```http
POST /api/knowledge-graph/graph/rebuild_graph/
```

### Response Format

Success response:

```json
{
    "id": 1,
    "title": "Sample Item",
    "created_at": "2024-01-22T10:30:00Z",
    "updated_at": "2024-01-22T10:30:00Z"
}
```

Error response:

```json
{
    "error": "Error message",
    "detail": "Detailed explanation"
}
```

## 💻 Development

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_models.py

# Run with coverage
pytest --cov=.
```

### Code Quality

```bash
# Format code
black .

# Sort imports
isort .

# Lint
flake8 .
pylint **/*.py
```

### Running Celery (Background Tasks)

```bash
# Start Celery worker
celery -A flowlinkos worker -l info

# Start Celery beat (scheduler)
celery -A flowlinkos beat -l info
```

## 🔧 Configuration

### Database

**Development (SQLite)**

```bash
# Already configured in .env
USE_POSTGRES=False
```

**Production (PostgreSQL)**

```bash
USE_POSTGRES=True
DB_NAME=flowlinkos_db
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432
```

### NLP Models

Configure in `.env`:

```
SPACY_MODEL=en_core_web_sm
SENTENCE_TRANSFORMER_MODEL=all-MiniLM-L6-v2
```

### Redis Configuration

```
REDIS_URL=redis://localhost:6379/0
```

## 🚢 Deployment

### With Gunicorn

```bash
gunicorn --bind 0.0.0.0:8000 flowlinkos.wsgi:application
```

### With Docker (Optional)

Create a `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "flowlinkos.wsgi:application"]
```

### Environment Variables for Production

- `SECRET_KEY`: Strong random key
- `DEBUG`: False
- `ALLOWED_HOSTS`: Your domain
- `DB_*`: Database credentials
- `CORS_ALLOWED_ORIGINS`: Allowed origins

## 📝 Common Tasks

### Create a Data Source

```bash
python manage.py shell
>>> from core.models import Source
>>> from django.contrib.auth.models import User
>>> user = User.objects.first()
>>> source = Source.objects.create(
...     user=user,
...     source_type='notes',
...     name='My Notes'
... )
```

### Reset Database

```bash
python manage.py flush
```

### Create Sample Data

```bash
python manage.py shell < scripts/sample_data.py
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Write tests for new features
- Update documentation
- Keep commits atomic and descriptive

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙋 Support & Contact

For questions, issues, or suggestions:

- 📧 Email: support@flowlinkos.dev
- 🐛 Issues: GitHub Issues
- 💬 Discussions: GitHub Discussions

## 🎉 Acknowledgments

- Django and Django REST Framework communities
- spaCy and sentence-transformers
- All contributors and supporters

---

Made with ❤️ for better personal productivity
