app_start:
	poetry run gunicorn -w 5 -b 0.0.0.0:8000 mango_api.wsgi:application

celery_start:
	poetry run celery -A mango_api worker --loglevel=info

celery_beat_start:
	poetry run celery -A mango_api beat --loglevel=info

makemigrations:
	poetry run python manage.py makemigrations mango_api

migrate:
	poetry run python manage.py migrate

createsuperuser:
	poetry run python manage.py createsuperuser
