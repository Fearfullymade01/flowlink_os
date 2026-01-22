# FlowLinkOS Setup Guide

## 🚀 Quick Setup (5 minutes)

### 1. Prerequisites

- Python 3.10+
- pip package manager
- Git (optional)

### 2. Navigate to Project Directory

```bash
cd c:\Users\gbeng\flowlink_os\flowlinkos_project
```

### 3. Activate Virtual Environment

```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 4. Install Dependencies (if not already done)

```bash
pip install -r requirements.txt
```

### 5. Run Database Migrations

```bash
python manage.py migrate
```

### 6. Create Admin User (first time only)

```bash
python manage.py createsuperuser
# Follow prompts to create username, email, and password
```

### 7. Start Development Server

```bash
python manage.py runserver
```

Server will be available at: `http://localhost:8000`

### 8. Access Admin Panel

- URL: `http://localhost:8000/admin`
- Use credentials from step 6

### 9. Explore API

- API Root: `http://localhost:8000/api/`
- Knowledge Graph: `http://localhost:8000/api/knowledge-graph/`

## 📦 First-Time NLP Model Download

After first installation, download NLP models:

```bash
# Download spaCy model
python -m spacy download en_core_web_sm

# Download sentence transformer (auto-downloaded on first use)
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

## 🔧 Configuration

### Environment Variables

Edit `.env` file:

- `SECRET_KEY`: Change to a secure random string for production
- `DEBUG`: Set to False for production
- `ALLOWED_HOSTS`: Add your domain/IP for production
- `DB_*`: Configure database (PostgreSQL for production)

### Database Options

**Development (SQLite - Default)**

- No configuration needed
- Data stored in `db.sqlite3`
- Suitable for development only

**Production (PostgreSQL)**

```
USE_POSTGRES=True
DB_NAME=flowlinkos_db
DB_USER=postgres
DB_PASSWORD=secure_password
DB_HOST=your-host.com
DB_PORT=5432
```

## 📚 Key Commands

### Development

```bash
# Run server
python manage.py runserver

# Create migrations for model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Open Django shell
python manage.py shell

# Create static files
python manage.py collectstatic

# Run tests
pytest

# Format code
black .
isort .

# Check for issues
python manage.py check
flake8 .
```

### Admin Tasks

```bash
# Create superuser
python manage.py createsuperuser

# Change password
python manage.py changepassword username

# Flush database (WARNING: deletes all data)
python manage.py flush

# Load sample data
python manage.py loaddata sample_data
```

### Celery (Background Tasks)

```bash
# Start Celery worker
celery -A flowlinkos worker -l info

# Start Celery beat (scheduler)
celery -A flowlinkos beat -l info

# Start both with options
celery -A flowlinkos worker -B -l info
```

## 🔐 Security Checklist

For production deployment:

- [ ] Change `SECRET_KEY` to a strong random string
- [ ] Set `DEBUG = False`
- [ ] Update `ALLOWED_HOSTS` with your domain
- [ ] Use PostgreSQL instead of SQLite
- [ ] Set up HTTPS/SSL
- [ ] Configure secure password requirements
- [ ] Set up proper logging
- [ ] Use environment variables for secrets
- [ ] Enable CSRF protection
- [ ] Configure CORS properly
- [ ] Set up security headers

## 🚢 Deployment

### Using Gunicorn

```bash
# Install gunicorn (already in requirements.txt)
pip install gunicorn

# Run with gunicorn
gunicorn --bind 0.0.0.0:8000 --workers 4 flowlinkos.wsgi:application
```

### Using Docker

Create `Dockerfile`:

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

Build and run:

```bash
docker build -t flowlinkos .
docker run -p 8000:8000 flowlinkos
```

## 🐛 Troubleshooting

### Virtual Environment Issues

```bash
# Recreate venv if issues persist
rm -rf venv
python -m venv venv
venv\Scripts\activate  # or source venv/bin/activate
pip install -r requirements.txt
```

### Database Issues

```bash
# Reset database
python manage.py flush
python manage.py migrate

# Create superuser again
python manage.py createsuperuser
```

### Port Already in Use

```bash
# Run on different port
python manage.py runserver 8001
```

### Module Not Found

```bash
# Verify virtual environment is activated
# Reinstall requirements
pip install -r requirements.txt
```

### NLP Model Not Found

```bash
# Manually download spaCy model
python -m spacy download en_core_web_sm
```

## 📖 API Quick Start

### Get Authentication Token

```bash
curl -X POST http://localhost:8000/api-token-auth/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your-username", "password": "your-password"}'
```

### Create Item

```bash
curl -X POST http://localhost:8000/api/items/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "item_type": "note",
    "title": "My First Note",
    "content": "This is a test note",
    "tags": "important,review",
    "priority": 2
  }'
```

### List Items

```bash
curl http://localhost:8000/api/items/ \
  -H "Authorization: Token YOUR_TOKEN"
```

### Execute Query

```bash
curl -X POST http://localhost:8000/api/queries/execute_query/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query_text": "Show me my high priority tasks"}'
```

## 📞 Support

For issues or questions:

1. Check the README.md
2. Review Django documentation: https://docs.djangoproject.com/
3. Check Django REST Framework docs: https://www.django-rest-framework.org/
4. Open an issue on GitHub

## 🎉 Next Steps

1. Create a superuser account
2. Log in to admin panel
3. Create sample data
4. Explore API endpoints
5. Read the full README.md
6. Start building features!

Happy coding! 🚀
