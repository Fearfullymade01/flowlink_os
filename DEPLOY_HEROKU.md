# Deploy FlowLinkOS to Heroku

This guide sets up Heroku with Postgres, Redis, and separate dynos for the web app and Celery workers.

## Prerequisites

- Heroku account and CLI (`heroku login`)
- GitHub repo connected or local git remote
- Environment variables prepared (SECRET_KEY, etc.)

## 1) Create app and addons

```bash
heroku create flowlinkos-app

# Postgres (production tier recommended)
heroku addons:create heroku-postgresql:standard-0 -a flowlinkos-app

# Redis for Celery broker + cache
heroku addons:create heroku-redis:premium-0 -a flowlinkos-app
```

## 2) Config vars

```bash
# Basic Django settings
heroku config:set DJANGO_SETTINGS_MODULE=flowlinkos.settings -a flowlinkos-app
heroku config:set SECRET_KEY="change-me" -a flowlinkos-app
heroku config:set DEBUG=False -a flowlinkos-app

# Allowed hosts (include your Heroku app domain)
heroku config:set ALLOWED_HOSTS="flowlinkos-app.herokuapp.com,127.0.0.1,localhost" -a flowlinkos-app

# Celery broker/result from Redis
heroku config:set CELERY_BROKER_URL=$(heroku config:get REDIS_URL -a flowlinkos-app) -a flowlinkos-app
heroku config:set CELERY_RESULT_BACKEND=$(heroku config:get REDIS_URL -a flowlinkos-app) -a flowlinkos-app

# Optional CORS origins
heroku config:set CORS_ALLOWED_ORIGINS="https://flowlinkos-app.herokuapp.com,http://127.0.0.1:8000" -a flowlinkos-app
```

Note: Heroku injects `DATABASE_URL` and `REDIS_URL` automatically for Postgres/Redis.

## 3) Procfile processes

We use three processes defined in `Procfile` (repo root):

```
web: gunicorn --chdir flowlinkos_project flowlinkos.wsgi --log-file -
worker: sh -c "cd flowlinkos_project && celery -A flowlinkos worker -l info"
beat: sh -c "cd flowlinkos_project && celery -A flowlinkos beat -l info"
```

Scale them as needed:

```bash
heroku ps:scale web=1 worker=1 beat=1 -a flowlinkos-app
```

## 4) Deploy

```bash
git push heroku main
heroku run python flowlinkos_project/manage.py migrate -a flowlinkos-app
heroku run python flowlinkos_project/manage.py collectstatic --noinput -a flowlinkos-app
```

## 5) Verify

- App: https://flowlinkos-app.herokuapp.com/
- Admin: https://flowlinkos-app.herokuapp.com/admin/
- API: https://flowlinkos-app.herokuapp.com/api/
- Q&A UI: https://flowlinkos-app.herokuapp.com/ask/

## Notes

- Static files served by WhiteNoise (configured in `settings.py`).
- Embeddings fallback to lightweight mode if `sentence-transformers` fails; consider caching or pgvector for scale.
- For media storage, add S3 via `django-storages` (not required for MVP).
- For vector search, enable `pgvector` on Postgres or add an external vector DB.
