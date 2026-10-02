#!/bin/sh
# Runs every time the backend container starts.
set -e   # stop at the first failing command

# With arguments, run them instead (e.g. `docker compose run --rm backend
# python manage.py create_admin`) without starting the server.
if [ "$#" -gt 0 ]; then
    exec "$@"
fi

python manage.py migrate --noinput
python manage.py load_seed
python manage.py seed_system_account

# Gunicorn is a production web server, needed since Django's runserver
# is for development only.
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
