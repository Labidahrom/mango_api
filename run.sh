#!/bin/bash

echo "Starting Django application with Gunicorn..."
poetry run gunicorn -w 5 -b 0.0.0.0:8000 mango_api.wsgi:application &


echo "Waiting for 3 seconds before starting Celery Worker for database update"
sleep 3

echo "Starting Flower for monitoring"
poetry run celery -A mango_api flower &

sleep 2

echo "Starting Celery worker..."
poetry run celery -A mango_api worker --loglevel=info &

echo "Waiting for 5 seconds before database update"
sleep 5

echo "Starting database update on app start"
poetry run python manage.py startup_tasks &

echo "Waiting for 30 seconds before starting Celery Beat..."
sleep 30

echo "Starting Celery Beat..."
poetry run celery -A mango_api beat --loglevel=info

wait
