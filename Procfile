web: gunicorn flowlinkos.wsgi --log-file -
worker: celery -A flowlinkos worker -l info
beat: celery -A flowlinkos beat -l info
