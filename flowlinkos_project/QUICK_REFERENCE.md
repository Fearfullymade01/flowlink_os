# FlowLinkOS Quick Reference

## 🎯 Essential Commands

### Server & Development

```bash
# Activate virtual environment
venv\Scripts\activate

# Run development server
python manage.py runserver

# Run on specific port
python manage.py runserver 8001

# Open Django shell
python manage.py shell

# Check Django setup
python manage.py check
```

### Database

```bash
# Create migrations for model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations

# Flush database (WARNING)
python manage.py flush
```

### Users & Admin

```bash
# Create superuser
python manage.py createsuperuser

# Change password
python manage.py changepassword username

# Access admin: http://localhost:8000/admin
```

### Code Quality

```bash
# Format code with black
black .

# Sort imports with isort
isort .

# Lint with flake8
flake8 .

# Lint with pylint
pylint **/*.py
```

### Testing

```bash
# Run all tests
pytest

# Run specific file
pytest tests/test_models.py

# Run with coverage
pytest --cov
```

## 🔌 API Quick Reference

### Items Endpoint

```http
GET /api/items/                    # List items
POST /api/items/                   # Create item
GET /api/items/{id}/               # Get item
PUT /api/items/{id}/               # Update item
DELETE /api/items/{id}/            # Delete item
GET /api/items/by_type/            # Items by type
```

### Queries Endpoint

```http
GET /api/queries/                  # List queries
POST /api/queries/execute_query/   # Execute query
```

### Knowledge Graph Endpoint

```http
GET /api/knowledge-graph/entities/                    # List entities
GET /api/knowledge-graph/entities/{id}/related_entities/  # Related
GET /api/knowledge-graph/relationships/               # List relationships
GET /api/knowledge-graph/graph/current_graph/         # Current graph
POST /api/knowledge-graph/graph/rebuild_graph/        # Rebuild
```

## 🔐 Environment Variables

**Key variables** in `.env`:

```env
SECRET_KEY=your-secret-key
DEBUG=True (False in production)
ALLOWED_HOSTS=localhost,127.0.0.1
USE_POSTGRES=False (True for production)
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

See `.env.example` for complete list.

## 📁 Important Files

| File                     | Purpose                |
| ------------------------ | ---------------------- |
| `manage.py`              | Django management      |
| `flowlinkos/settings.py` | Configuration          |
| `requirements.txt`       | Python dependencies    |
| `.env`                   | Local environment vars |
| `.env.example`           | Environment template   |
| `README.md`              | Full documentation     |
| `SETUP.md`               | Setup guide            |
| `PROJECT_STRUCTURE.md`   | Project overview       |

## 🚀 First Time Setup

```bash
# 1. Navigate to project
cd flowlinkos_project

# 2. Activate environment
venv\Scripts\activate

# 3. Install packages
pip install -r requirements.txt

# 4. Migrate database
python manage.py migrate

# 5. Create admin user
python manage.py createsuperuser

# 6. Start server
python manage.py runserver

# 7. Open browser
# http://localhost:8000/admin
```

## 📊 Model Overview

### Core Models

- `UserProfile` - Extended user info
- `Source` - Data sources
- `Workflow` - Learned patterns

### API Models

- `Item` - User items
- `Query` - User queries
- `Summary` - Generated summaries

### Knowledge Graph Models

- `Entity` - Concepts, people, places
- `Relationship` - Entity connections
- `EntityItemLink` - Entity to item links
- `Graph` - Graph snapshots

## 🛠️ Common Tasks

### Reset Database

```bash
python manage.py flush
python manage.py migrate
python manage.py createsuperuser
```

### Download NLP Models

```bash
python -m spacy download en_core_web_sm
```

### Export Data

```bash
python manage.py dumpdata > backup.json
python manage.py loaddata backup.json
```

### Create Static Files

```bash
python manage.py collectstatic
```

## 🔗 Useful URLs

| URL                                          | Purpose             |
| -------------------------------------------- | ------------------- |
| `http://localhost:8000`                      | Home                |
| `http://localhost:8000/admin`                | Admin panel         |
| `http://localhost:8000/api/`                 | API root            |
| `http://localhost:8000/api/items/`           | Items API           |
| `http://localhost:8000/api/queries/`         | Queries API         |
| `http://localhost:8000/api/knowledge-graph/` | Knowledge graph API |

## 💡 Tips & Tricks

1. **Virtual Environment Issues**: Delete and recreate if problems
2. **Port 8000 in Use**: Use `python manage.py runserver 8001`
3. **Permission Denied**: Try `python -m pip install --upgrade pip`
4. **Module Not Found**: Ensure virtual environment is activated
5. **Database Locked**: Restart the development server

## 🆘 Quick Troubleshooting

### Error: "Port 8000 already in use"

```bash
python manage.py runserver 8001
```

### Error: "Module not found"

```bash
# Verify venv is activated
pip install -r requirements.txt
```

### Error: "Database is locked"

```bash
# Restart server (Ctrl+C then run again)
python manage.py runserver
```

### Error: "Permission denied"

```bash
# Try upgrading pip
python -m pip install --upgrade pip
```

## 📚 Additional Resources

- Django Docs: https://docs.djangoproject.com/
- DRF Docs: https://www.django-rest-framework.org/
- spaCy Docs: https://spacy.io/
- pytest Docs: https://docs.pytest.org/

---

**For complete documentation, see README.md and SETUP.md**

Last updated: January 22, 2025
