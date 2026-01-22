# FlowLinkOS Development Guidelines

## Project Overview
FlowLinkOS is a Django-based unified intelligence layer for personal productivity that integrates notes, files, messages, bookmarks, and tasks into a semantic knowledge graph.

## Code Style & Standards
- Follow PEP 8 style guide
- Use 4 spaces for indentation
- Keep lines under 100 characters
- Write descriptive docstrings for all functions and classes
- Use type hints where applicable

## Development Workflow
- Create feature branches: `feature/description`
- Create bug fix branches: `bugfix/description`
- Commit messages should be clear and descriptive
- Run tests before committing
- Ensure all migrations are created and included

## Testing Requirements
- Write tests for all new models and views
- Maintain minimum 80% code coverage
- Use pytest for testing
- Run `pytest --cov` before submitting PRs

## Code Quality Tools
- Use `black` for code formatting
- Use `isort` for import sorting
- Run `flake8` for linting
- Run `pylint` for code analysis

Commands:
```bash
black .
isort .
flake8 .
pylint **/*.py
```

## Database
- Always create migrations for model changes
- Test migrations locally before committing
- Include migration files in commits
- Use descriptive migration names

## API Development
- Follow REST principles
- Use viewsets and routers where applicable
- Include proper error handling
- Document all endpoints
- Use appropriate HTTP status codes

## Environment Setup
- Copy `.env.example` to `.env` for development
- Use SQLite for development (default)
- Configure PostgreSQL for production
- Ensure Redis is running for Celery tasks
