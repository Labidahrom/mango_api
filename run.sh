#!/bin/bash

# Start Django application with Gunicorn
echo "Starting Django application with Gunicorn..."
poetry run gunicorn -w 5 -b 0.0.0.0:8000 mango_api.wsgi:application &


# Wait for 2 minutes before starting Celery Beat
echo "Waiting for 3 seconds before starting Celery Worker..."
sleep 3

# Start Celery worker
echo "Starting Celery worker..."
poetry run celery -A mango_api worker --loglevel=info &

# Wait for 2 minutes before starting Celery Beat
echo "Waiting for 2 minutes before starting Celery Beat..."
sleep 120

# Start Celery Beat
echo "Starting Celery Beat..."
poetry run celery -A mango_api beat --loglevel=info

# Keep the script running to maintain the processes
wait
