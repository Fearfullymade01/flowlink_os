"""
Celery configuration settings for flowlinkos
"""

# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes

# Add to settings.py if using Celery
# from . import celery_config
# CELERY_BROKER_URL = celery_config.CELERY_BROKER_URL
# CELERY_RESULT_BACKEND = celery_config.CELERY_RESULT_BACKEND
