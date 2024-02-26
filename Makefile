app_start:
	poetry run python manage.py runserver

celery_start:
	poetry run celery -A mango_api worker --loglevel=info

celery_beat_start:
	poetry run celery -A mango_api beat --loglevel=info

makemigrations:
	poetry run python manage.py makemigrations mango_api

migrate:
	poetry run python manage.py migrate
