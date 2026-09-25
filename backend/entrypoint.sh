#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $DB_HOST $DB_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --no-input

# Start server
# Using Daphne for WebSocket support (Django Channels)
exec daphne -b 0.0.0.0 -p 8000 config.asgi:application
