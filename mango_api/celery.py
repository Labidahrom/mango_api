import os
from celery import Celery
from celery.schedules import crontab
from datetime import timedelta

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mango_api.settings')

# Ensure Django is ready before proceeding further
import django
django.setup()

# Now, it's safe to import Django models and tasks
# from mango_api.api import run_database_update_on_app_start

app = Celery('mango_api')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.update(
    worker_hijack_root_logger=False,
)

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

app.conf.ONCE = {
    'backend': 'celery_once.backends.Redis',
    'settings': {
        'url': 'redis://localhost:6379/1',
        'default_timeout': 30 * 60
    }
}

app.conf.beat_schedule = {
    'update-call-history': {
        'task': 'mango_api.api.get_call_history_from_last_entry',
        'schedule': timedelta(seconds=60),
    },
    'update-other-tables': {
        'task': 'mango_api.api.update_tables_except_call_history',
        'schedule': timedelta(seconds=600),
    },
    'daily-database-check-for-missing-calls-for-4-hours': {
        'task': 'mango_api.api.get_call_history_by_gap',
        'schedule': timedelta(seconds=14400),
    },
}
