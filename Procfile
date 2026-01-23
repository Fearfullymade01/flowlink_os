web: gunicorn --chdir flowlinkos_project flowlinkos.wsgi --log-file -
worker: sh -c "cd flowlinkos_project && celery -A flowlinkos worker -l info"
beat: sh -c "cd flowlinkos_project && celery -A flowlinkos beat -l info"
