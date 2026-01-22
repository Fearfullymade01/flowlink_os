# Project Structure Summary

## 📁 FlowLinkOS Project Structure

```
flowlinkos_project/
│
├── flowlinkos/                    # Main project configuration
│   ├── __init__.py
│   ├── settings.py               # Django settings
│   ├── urls.py                   # URL configuration
│   ├── wsgi.py                   # WSGI application
│   ├── asgi.py                   # ASGI application (async)
│   ├── celery.py                 # Celery task queue
│   └── celery_config.py          # Celery configuration
│
├── core/                         # Core functionality app
│   ├── migrations/
│   ├── __init__.py
│   ├── models.py                 # UserProfile, Source, Workflow models
│   ├── views.py                  # Core views
│   ├── admin.py                  # Django admin configuration
│   └── apps.py                   # App configuration
│
├── api/                          # REST API app
│   ├── migrations/
│   ├── __init__.py
│   ├── models.py                 # Item, Query, Summary models
│   ├── views.py                  # API viewsets
│   ├── urls.py                   # API routing
│   ├── admin.py                  # Admin configuration
│   └── apps.py                   # App configuration
│
├── knowledge_graph/              # Knowledge graph engine
│   ├── migrations/
│   ├── __init__.py
│   ├── models.py                 # Entity, Relationship, Graph models
│   ├── views.py                  # Graph API viewsets
│   ├── urls.py                   # Graph routing
│   ├── admin.py                  # Admin configuration
│   └── apps.py                   # App configuration
│
├── static/                       # Static files (CSS, JS)
│   ├── css/
│   └── js/
│
├── templates/                    # HTML templates
│   └── (add Django templates here)
│
├── logs/                         # Application logs
│
├── manage.py                     # Django management command
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables (local)
├── .env.example                  # Environment template
├── .gitignore                    # Git ignore rules
│
├── .vscode/
│   └── tasks.json               # VS Code task configuration
│
├── .github/
│   └── copilot-instructions.md  # Development guidelines
│
├── README.md                     # Main documentation
├── SETUP.md                      # Setup guide
└── PROJECT_STRUCTURE.md          # This file

```

## 🎯 Apps Overview

### **core** - Core Functionality

- **UserProfile**: Extended user information
- **Source**: Data sources (notes, files, messages, etc)
- **Workflow**: Learned user workflows and patterns

### **api** - REST API

- **Item**: Individual items from any source
- **Query**: Intent-based user queries
- **Summary**: Auto-generated summaries

### **knowledge_graph** - Semantic Knowledge Graph

- **Entity**: Concepts, persons, places, organizations
- **Relationship**: Connections between entities
- **EntityItemLink**: Links entities to items
- **Graph**: Knowledge graph snapshots

## 📊 Data Flow

```
User Input
    ↓
Sources (Notes, Files, Messages, etc.)
    ↓
Items (API)
    ↓
Knowledge Graph (Entities & Relationships)
    ↓
Queries & Summaries
    ↓
User Interface
```

## 🔌 Key Features Implementation

### Multi-Source Integration

- Support for notes, files, messages, bookmarks, tasks
- Flexible source type system
- Metadata storage for each source

### Semantic Knowledge Graph

- Entity recognition and classification
- Relationship mapping
- Embedding storage for semantic similarity
- Graph health monitoring

### Intent-Based Queries

- Natural language query execution
- Confidence scoring
- Result relevance ranking
- Query history tracking

### Auto-Generated Summaries

- Daily/weekly summaries
- Category-based summaries
- Query-based summaries
- Multi-item source support

### Workflow Learning

- Pattern detection
- Workflow suggestions
- Confidence-based recommendations
- Workflow analytics

## 🛠️ Technology Stack

- **Backend**: Django 4.2
- **API**: Django REST Framework
- **Database**: PostgreSQL (prod) / SQLite (dev)
- **NLP**: spaCy, sentence-transformers
- **Graph**: NetworkX
- **Tasks**: Celery + Redis
- **Testing**: pytest
- **Code Quality**: black, flake8, isort

## 📡 API Endpoints

```
Admin: /admin/
API Root: /api/

Items: /api/items/
Queries: /api/queries/
Summaries: /api/summaries/

Knowledge Graph:
  Entities: /api/knowledge-graph/entities/
  Relationships: /api/knowledge-graph/relationships/
  Graph: /api/knowledge-graph/graph/
```

## 🚀 Getting Started

1. See SETUP.md for detailed setup instructions
2. See README.md for comprehensive documentation
3. Access admin at http://localhost:8000/admin
4. Explore API at http://localhost:8000/api/

## 📝 Development Guidelines

See `.github/copilot-instructions.md` for:

- Code style standards
- Development workflow
- Testing requirements
- Git conventions
- Code quality tools

## 🔐 Environment Setup

Key environment variables in `.env`:

- `SECRET_KEY`: Django secret key
- `DEBUG`: Debug mode
- `ALLOWED_HOSTS`: Allowed hostnames
- `DB_*`: Database configuration
- `REDIS_URL`: Redis connection
- NLP model settings

See `.env.example` for all available options.

---

**Happy Development!** 🎉
