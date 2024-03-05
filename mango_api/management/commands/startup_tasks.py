from django.core.management.base import BaseCommand
from mango_api.api import run_database_update_on_app_start

class Command(BaseCommand):
    help = 'Enqueue startup tasks'

    def handle(self, *args, **options):
        run_database_update_on_app_start.delay()
        self.stdout.write(self.style.SUCCESS('Successfully enqueued startup tasks'))
